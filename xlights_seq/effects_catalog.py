"""Whitelist of xLights effect types the writer supports, with param validators.

Used two ways: (1) rendered into the AI prompt so Claude only picks from effects
we can actually write, and (2) to validate/repair whatever JSON the model (or the
deterministic fallback planner) produces before it reaches ``xsq_writer`` — unknown
effect types or malformed params are dropped/clamped, never passed through raw.
"""

import re
from typing import Any, Callable, Dict, Optional, Tuple

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _color(v: Any, default: str) -> str:
    if isinstance(v, str) and _HEX.match(v):
        return v.upper()
    return default


def _unit(v: Any, default: float) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, f))


def _int_range(lo: int, hi: int):
    def validator(v: Any, default: int) -> int:
        try:
            i = int(v)
        except (TypeError, ValueError):
            return default
        return max(lo, min(hi, i))

    return validator


def _enum(choices: Tuple[str, ...]):
    def validator(v: Any, default: str) -> str:
        return v if v in choices else default

    return validator


# effect name -> {param name -> (validator(value, default) -> cleaned_value, default)}
EFFECTS_CATALOG: Dict[str, Dict[str, Tuple[Callable[[Any, Any], Any], Any]]] = {
    "On": {
        "color": (_color, "#FFFFFF"),
        "opacity": (_unit, 1.0),
    },
    "Bars": {
        "color": (_color, "#FFFFFF"),
        "bars": (_int_range(1, 32), 6),
        "direction": (_enum(("LeftRight", "RightLeft", "Up", "Down")), "LeftRight"),
    },
    "Meteor": {
        "color": (_color, "#00FFFF"),
        "count": (_int_range(1, 50), 10),
        "speed": (_int_range(1, 100), 25),
    },
    "Spirals": {
        "color": (_color, "#00FFFF"),
        "arms": (_int_range(1, 8), 3),
        "rotation": (_unit, 0.4),
    },
    "Shockwave": {
        "color": (_color, "#FFFFFF"),
        "brightness": (_unit, 0.9),
    },
    "Waves": {
        "color": (_color, "#FF00FF"),
        "speed": (_int_range(1, 100), 20),
    },
    "SingleStrand": {
        "color": (_color, "#FFFFFF"),
        "fade": (_unit, 0.18),
        "opacity": (_unit, 1.0),
    },
    "Shader": {
        "color": (_color, "#FFFFFF"),
        "opacity": (_unit, 0.5),
    },
}


def validate_effect(effect: str, params: Optional[dict]) -> Optional[Dict[str, Any]]:
    """Return cleaned params for ``effect``, or ``None`` if ``effect`` isn't whitelisted."""
    spec = EFFECTS_CATALOG.get(effect)
    if spec is None:
        return None
    params = params or {}
    cleaned = {}
    for key, (validator, default) in spec.items():
        cleaned[key] = validator(params.get(key), default)
    return cleaned


def describe_catalog_for_prompt() -> str:
    """Human-readable menu of effects + params, for the AI prompt."""
    lines = ["Available effects (use ONLY these types and param names):"]
    for effect, spec in EFFECTS_CATALOG.items():
        params_desc = ", ".join(f"{k} (default {v!r})" for k, (_, v) in spec.items())
        lines.append(f"- {effect}: {params_desc}")
    return "\n".join(lines)
