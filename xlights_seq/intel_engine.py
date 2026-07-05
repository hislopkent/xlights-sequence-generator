from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Intent:
    target_group: str     # style/plan group label as referenced by the cue
    layout_group: str     # resolved layout group name (member models come from here)
    effect: str
    start_s: float
    end_s: float
    params: Dict[str, Any]


def _times_in_range(times: List[float], start: float, end: float) -> List[float]:
    return [t for t in times if start <= t < end]


def build_intents(plan: dict, timing: dict, mapping: Dict[str, str]) -> List[Intent]:
    """Expand a section/cue plan into per-group Intents.

    ``plan["sections"]`` entries look like:
        {"name", "start_s", "end_s", "cues": [
            {"group", "effect", "params", "snap_to", "at", "duration_s"}, ...
        ]}

    ``snap_to`` drives how a cue is expanded against ``timing`` (seconds):
      - "beat"/"downbeat"/"bar": one short intent per matching time in the section
      - "at": one intent per explicit time in the cue's ``at`` list
      - "section" (default): a single intent spanning the whole section

    ``mapping`` resolves a cue's group name to the actual layout group name;
    groups absent from ``mapping`` are used as-is, since both the AI planner and
    the deterministic fallback planner reference real layout group names directly.
    """
    beats = timing.get("beats", [])
    downbeats = timing.get("downbeats", [])
    bars = timing.get("bars", downbeats)

    intents: List[Intent] = []
    for section in plan.get("sections", []):
        start = float(section.get("start_s", 0.0))
        end = float(section.get("end_s", start))
        for cue in section.get("cues", []):
            group = cue["group"]
            layout_group = mapping.get(group, group)
            effect = cue["effect"]
            params = cue.get("params", {})
            duration = float(cue.get("duration_s", 0.25))
            snap_to = cue.get("snap_to", "section")

            if snap_to == "beat":
                times = _times_in_range(beats, start, end)
            elif snap_to == "downbeat":
                times = _times_in_range(downbeats, start, end)
            elif snap_to == "bar":
                times = _times_in_range(bars, start, end)
            elif snap_to == "at":
                times = [t for t in cue.get("at", []) if start <= t < end]
            else:  # "section" (or anything unrecognized) -> one cue for the whole span
                intents.append(Intent(group, layout_group, effect, start, end, params))
                continue

            for t in times:
                intents.append(
                    Intent(group, layout_group, effect, t, min(end, t + duration), params)
                )

    return intents
