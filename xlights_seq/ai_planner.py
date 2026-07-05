"""Claude-backed sequence planner.

Turns audio analysis + detected layout groups into a section/cue plan (the same
shape ``xlights_seq.intel_engine.build_intents`` expects), by asking Claude to
emit structured JSON via forced tool-use. Any failure — missing dependency,
missing API key, network/timeout error, or a response that doesn't survive
effects-catalog validation — raises ``AIPlanError`` so the caller can fall back
to the deterministic planner instead of crashing the request.
"""

import os
from typing import Any, Dict, List

from .effects_catalog import describe_catalog_for_prompt, validate_effect

DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_TIMEOUT_S = 20.0

_PLAN_TOOL = {
    "name": "emit_plan",
    "description": "Emit a section-by-section holiday light sequence plan.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "start_s": {"type": "number"},
                        "end_s": {"type": "number"},
                        "cues": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "group": {
                                        "type": "string",
                                        "description": "Must be one of the layout group names provided.",
                                    },
                                    "effect": {"type": "string"},
                                    "params": {"type": "object"},
                                    "snap_to": {
                                        "type": "string",
                                        "enum": ["beat", "downbeat", "bar", "section", "at"],
                                    },
                                    "at": {"type": "array", "items": {"type": "number"}},
                                    "duration_s": {"type": "number"},
                                },
                                "required": ["group", "effect", "snap_to"],
                            },
                        },
                    },
                    "required": ["name", "start_s", "end_s", "cues"],
                },
            }
        },
        "required": ["sections"],
    },
}


class AIPlanError(RuntimeError):
    """Raised whenever the AI planner cannot produce a usable plan."""


def _build_prompt(context: Dict[str, Any]) -> str:
    groups = context.get("groups") or []
    group_lines = "\n".join(
        f"- {g['name']} ({g.get('model_count', '?')} models)" for g in groups
    ) or "(no groups detected — reference the layout's model names directly)"

    section_times = context.get("section_times") or []
    lines = [
        "You are directing a synchronized holiday light show for xLights.",
        f"Song duration: {context.get('duration_s', 0):.1f}s, tempo: {context.get('bpm', 0):.1f} BPM.",
        f"Section boundaries (seconds): {[round(float(t), 1) for t in section_times]}",
        "",
        "Layout groups available (use these exact names in \"group\"):",
        group_lines,
        "",
        describe_catalog_for_prompt(),
        "",
        "House style guidance:",
        context.get("house_style", "(none provided)"),
    ]
    if context.get("style_prompt"):
        lines.append(f"\nUser direction: {context['style_prompt']}")
    if context.get("palette"):
        lines.append(f"\nPreferred palette (hex): {', '.join(context['palette'])}")
    lines.append(
        "\nCover the whole song with sections whose start_s/end_s are contiguous "
        "(first starts at 0, last ends at/after the song duration). Use snap_to "
        "\"beat\"/\"downbeat\"/\"bar\" for rhythmic cues and \"section\" for a cue "
        "that should just hold for the whole section."
    )
    return "\n".join(lines)


def _validate_plan(raw: Dict[str, Any]) -> Dict[str, Any]:
    sections: List[Dict[str, Any]] = []
    for sec in raw.get("sections", []):
        cues = []
        for cue in sec.get("cues", []):
            group = cue.get("group")
            effect = cue.get("effect")
            if not group or not effect:
                continue
            cleaned_params = validate_effect(effect, cue.get("params"))
            if cleaned_params is None:
                continue  # effect type not in the whitelist -> drop the cue
            at_times = [t for t in (cue.get("at") or []) if isinstance(t, (int, float))]
            cues.append(
                {
                    "group": group,
                    "effect": effect,
                    "params": cleaned_params,
                    "snap_to": cue.get("snap_to") or "section",
                    "at": at_times,
                    "duration_s": float(cue.get("duration_s") or 0.25),
                }
            )
        if not cues:
            continue
        try:
            start_s = float(sec.get("start_s", 0.0))
            end_s = float(sec.get("end_s", start_s))
        except (TypeError, ValueError):
            continue
        sections.append(
            {"name": sec.get("name") or "Section", "start_s": start_s, "end_s": end_s, "cues": cues}
        )

    if not sections:
        raise AIPlanError("AI plan had no usable sections/cues after validation")
    return {"sections": sections}


def generate_ai_plan(context: Dict[str, Any], *, timeout: float = DEFAULT_TIMEOUT_S) -> Dict[str, Any]:
    """Call Claude to generate a validated section/cue plan. Raises AIPlanError on any failure."""
    try:
        import anthropic
    except ImportError as e:
        raise AIPlanError("the 'anthropic' package is not installed") from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise AIPlanError("ANTHROPIC_API_KEY is not set")

    prompt = _build_prompt(context)

    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
        response = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
            max_tokens=4096,
            tools=[_PLAN_TOOL],
            tool_choice={"type": "tool", "name": "emit_plan"},
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        raise AIPlanError(f"Anthropic API call failed: {e}") from e

    plan_input = None
    for block in getattr(response, "content", []):
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == "emit_plan":
            plan_input = block.input
            break
    if plan_input is None:
        raise AIPlanError("model did not return a structured plan via tool use")

    return _validate_plan(plan_input)
