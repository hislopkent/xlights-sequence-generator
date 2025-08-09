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

# presets that tend to render heavy effects; tiny models can swap them out
HEAVY_PRESETS = {"meteor"}

# node count below which we avoid heavy presets and use a simple effect
SMALL_MODEL_NODES = 25


def build_rgbeffects(models, beat_times, duration_ms, preset: str, sections=None):
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
    sections : list[dict], optional
        Optional list of section markers as returned by ``analyze_beats``.
        Each item must contain ``time`` (seconds) and ``label``.
    """

    root = ET.Element("xrgb", version="2024.05", showDir=".")
    # timing track for beats
    timing = ET.SubElement(root, "timing", name="AutoBeat")
    for bt in beat_times:
        ET.SubElement(timing, "marker", timeMS=str(int(bt * 1000)))

    # optional secondary timing track for musical sections
    if sections:
        timing_sec = ET.SubElement(root, "timing", name="Sections")
        for sec in sections:
            attrs = {"timeMS": str(int(sec["time"] * 1000))}
            label = sec.get("label")
            if label:
                attrs["label"] = label
            ET.SubElement(timing_sec, "marker", **attrs)

    preset_cfg = PRESETS.get(preset, PRESETS["solid_pulse"])

    # simple per-beat effect per model
    for m in models:
        mdl = ET.SubElement(root, "model", name=m.name)
        layer = ET.SubElement(mdl, "effectLayer", name="Layer 1")
        for i, bt in enumerate(beat_times):
            start = int(bt * 1000)
            end = int(
                min(duration_ms, (beat_times[i + 1] * 1000))
                if i + 1 < len(beat_times)
                else duration_ms
            )
            eff_type = preset_cfg["type"]
            eff_params = preset_cfg.get("params", {}).copy()
            # tiny models get a simple "On" instead of heavy effects
            if (
                preset in HEAVY_PRESETS
                and m.nodes is not None
                and m.nodes < SMALL_MODEL_NODES
            ):
                eff_type = PRESETS["solid_pulse"]["type"]
                eff_params = PRESETS["solid_pulse"]["params"].copy()
            if preset == "bars":
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
