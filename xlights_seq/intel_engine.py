from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Intent:
    target_group: str     # style group label (e.g., "Metronome_Outlines")
    layout_group: str     # resolved layout group name
    effect: str
    start_s: float
    end_s: float
    params: Dict[str, Any]


def build_intents(plan: dict, timing: dict, mapping: dict) -> List[Intent]:
    intents = []
    palette = plan.get("meta", {}).get("palette", ["#FFFFFF"])
    fade_def = float(plan.get("global", {}).get("fade_default", 0.18))
    beats = timing["beats"]
    down = timing["downbeats"]
    bars = timing["bars"]
    secs = timing["sections"]
    # Example: metronome on outlines → short SingleStrand hits every beat
    if "Metronome_Outlines" in mapping:
        g = "Metronome_Outlines"
        lay = mapping[g]
        dur = min(0.25, (beats[1] - beats[0]) if len(beats) > 1 else 0.25)
        for b in beats:
            intents.append(
                Intent(
                    g,
                    lay,
                    "SingleStrand",
                    b,
                    b + dur,
                    {"color": palette[0], "fade": fade_def},
                )
            )
    # Example: Focal_Tree spirals over choruses (bars) with lift
    if "Focal_Tree" in mapping:
        g = "Focal_Tree"
        lay = mapping[g]
        for i, b in enumerate(bars):
            intents.append(
                Intent(
                    g,
                    lay,
                    "Spirals",
                    b,
                    b
                    + max(
                        1.5,
                        (beats[1] - beats[0]) * 4 if len(beats) > 1 else 2.0,
                    ),
                    {"rotation": 0.4 + 0.05 * (i % 4), "arms": 3},
                )
            )
    # Example: Shockwave accents on downbeats
    if "Focal_Spinners" in mapping:
        g = "Focal_Spinners"
        lay = mapping[g]
        for d in down:
            intents.append(
                Intent(
                    g,
                    lay,
                    "Shockwave",
                    d,
                    d + 0.35,
                    {"brightness": 0.9},
                )
            )
    # TODO: walk plan['sections'] for explicit cues like blackout_at, On@times, etc.
    return intents
