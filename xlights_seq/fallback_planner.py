"""Deterministic (non-AI) section/cue planner.

Produces the same ``{"sections": [...]}`` shape as ``ai_planner.generate_ai_plan``,
so both paths converge on ``intel_engine.build_intents`` /
``xsq_writer.build_xsq_from_intents``. Used when the AI planner is disabled,
unavailable, or fails.
"""

from typing import Any, Dict, List, Optional, Sequence

from .effects_catalog import validate_effect

# A small, house-style-inspired kit cycled across groups/sections.
_EFFECTS_CYCLE = [
    ("On", {}),
    ("Bars", {}),
    ("Waves", {}),
    ("Shockwave", {}),
]

_DEFAULT_PALETTE = ["#FFFFFF", "#FF0000", "#00FF00"]


def build_fallback_plan(
    section_times: Sequence[float],
    duration_s: float,
    groups: Sequence[str],
    palette: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Cycle a small default effect kit across every layout group, per section."""
    bounds = sorted({0.0, *(float(t) for t in section_times), float(duration_s)})
    colors = list(palette) if palette else _DEFAULT_PALETTE

    sections: List[Dict[str, Any]] = []
    for i in range(len(bounds) - 1):
        start, end = bounds[i], bounds[i + 1]
        if end <= start:
            continue
        cues = []
        for gi, group in enumerate(groups):
            effect, base_params = _EFFECTS_CYCLE[(i + gi) % len(_EFFECTS_CYCLE)]
            params = dict(base_params)
            params["color"] = colors[(i + gi) % len(colors)]
            cues.append(
                {
                    "group": group,
                    "effect": effect,
                    "params": validate_effect(effect, params),
                    "snap_to": "beat",
                    "duration_s": 0.4,
                }
            )
        sections.append({"name": f"Section {i + 1}", "start_s": start, "end_s": end, "cues": cues})

    if not sections:
        sections = [{"name": "Whole Song", "start_s": 0.0, "end_s": float(duration_s), "cues": []}]
    return {"sections": sections}
