import xml.etree.ElementTree as ET

# mapping of preset names to effect configuration
PRESETS = {
    "solid_pulse": {"type": "On", "params": {"Color1": "#FFFFFF"}},
    "bars": {
        "type": "Bars",
        "params": {"Bars": "6", "Direction": "LeftRight"},
    },
    "meteor": {
        "type": "Meteor",
        "params": {"Count": "10", "Speed": "25", "Color1": "#00FFFF"},
    },
}

# rotating color palette applied per beat
PALETTE = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]

# color used to accentuate downbeats
DOWNBEAT_COLOR = "#FFFFFF"

# interval in beats used to mark downbeats when explicit downbeat times are not provided
DOWNBEAT_INTERVAL = 4

# presets that tend to render heavy effects; tiny models can swap them out
HEAVY_PRESETS = {"meteor"}

# node count below which we avoid heavy presets and use a simple effect
SMALL_MODEL_NODES = 25


def choose_effect_for(name: str):
    """Select a basic effect type and parameters based on model name heuristics."""
    n = name.lower()
    if "mega" in n or "tree" in n:
        return ("Butterfly", {"Color1": "#00FFFF"})
    if "matrix" in n or "panel" in n:
        return ("Bars", {"Bars": "12"})
    if "arch" in n:
        return ("Waves", {"Color1": "#FF00FF"})
    return ("On", {"Color1": "#FFFFFF"})


def add_timing_track(root, name, times_s):
    """Create a timing track with a list of marker times in seconds."""
    track = ET.SubElement(root, "timing", name=name)
    for tsec in times_s:
        ET.SubElement(track, "marker", timeMS=str(int(round(tsec * 1000))))


def build_rgbeffects(
    models,
    beat_times,
    duration_ms,
    preset: str,
    downbeat_times=None,
    section_times=None,
    palette=None,
):
    """Generate an xLights RGB effects file using a preset.

    Parameters
    ----------
    models : list
        Sequence of ``ModelInfo`` objects describing the layout models.
    beat_times : list[float]
        Beat timestamps in seconds.
    duration_ms : int
        Total duration of the song in milliseconds.
    preset : str
        Name of the effect preset to apply.
    downbeat_times : list[float], optional
        Optional list of downbeat timestamps in seconds. If provided, a
        "Downbeats" timing track will be added and downbeat coloring will use
        these times instead of the fixed interval.
    section_times : list[float], optional
        Optional list of section boundary timestamps in seconds. A "Sections"
        timing track will be added if present.
    palette : list[str], optional
        Optional list of hex colors (e.g. ``"#FF0000"``) used for Color1 cycling.
        If not provided, falls back to the module ``PALETTE``.
    """

    root = ET.Element("xrgb", version="2024.05", showDir=".")

    # timing tracks
    add_timing_track(root, "Beats", beat_times)
    if downbeat_times:
        add_timing_track(root, "Downbeats", downbeat_times)
    if section_times:
        add_timing_track(root, "Sections", section_times)

    preset_cfg = PRESETS.get(preset, PRESETS["solid_pulse"])

    # pre-compute downbeat times and section start indices
    downbeat_ms = (
        [int(dt * 1000) for dt in downbeat_times]
        if downbeat_times
        else [int(beat_times[i] * 1000) for i in range(len(beat_times)) if i % DOWNBEAT_INTERVAL == 0]
    )
    section_indices = []
    if section_times:
        for st in section_times:
            for idx, bt in enumerate(beat_times):
                if bt + 1e-3 >= st:  # first beat at or after the section boundary
                    section_indices.append(idx)
                    break

    # simple per-beat effect per model
    active_palette = palette or PALETTE
    for m in models:
        mdl = ET.SubElement(root, "model", name=m.name)
        layer = ET.SubElement(mdl, "effectLayer", name="Layer 1")
        base_type, base_params = choose_effect_for(m.name)
        for i, bt in enumerate(beat_times):
            start = int(bt * 1000)
            if i + 1 < len(beat_times):
                next_ms = int(beat_times[i + 1] * 1000)
            else:
                next_ms = duration_ms
            end = next_ms

            # start with routing defaults
            eff_type = base_type
            eff_params = base_params.copy()

            # fall back to preset when routing gives default effect
            if eff_type == "On" and eff_params.get("Color1") == "#FFFFFF":
                eff_type = preset_cfg["type"]
                eff_params.update(preset_cfg.get("params", {}))

            # rotating color palette
            color = active_palette[i % len(active_palette)]

            # determine if this effect window contains a downbeat
            is_downbeat = any(start <= db < end for db in downbeat_ms)
            if is_downbeat:
                color = DOWNBEAT_COLOR
                end = min(duration_ms, end + 50)

            # adjust for section boundaries
            in_section_measure = any(
                si <= i < si + DOWNBEAT_INTERVAL for si in section_indices
            )
            if in_section_measure:
                eff_type = "Shockwave"
                eff_params = {"Color1": color}

            eff_params["Color1"] = color

            # tiny models get a simple "On" instead of heavy effects
            if (
                eff_type == preset_cfg["type"]
                and preset in HEAVY_PRESETS
                and m.nodes is not None
                and m.nodes < SMALL_MODEL_NODES
            ):
                eff_type = PRESETS["solid_pulse"]["type"]
                eff_params = PRESETS["solid_pulse"]["params"].copy()
                eff_params["Color1"] = color

            if eff_type == "Bars":
                bars = max(4, min(24, (m.strings or 8)))
                eff_params["Bars"] = str(bars)

            eff = ET.SubElement(
                layer,
                "effect",
                startMS=str(start),
                endMS=str(end),
                type=eff_type,
            )

            for name, value in eff_params.items():
                ET.SubElement(eff, "param", name=name, value=value)
    return ET.ElementTree(root)

def write_rgbeffects(tree, out_path: str):
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
