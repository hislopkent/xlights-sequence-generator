import xml.etree.ElementTree as ET

# mapping of preset names to effect configuration
PRESET_MAP = {
    "solid_pulse": {"type": "On"},
    "bars": {
        "type": "Bars",
        "params": {"Bars": "6", "Direction": "LeftRight"},
    },
    "meteor": {
        "type": "Meteor",
        # downbeat/normal parameter sets for speed/intensity
        "params": {
            "downbeat": {"Speed": "100", "Intensity": "100"},
            "normal": {"Speed": "50", "Intensity": "60"},
        },
    },
}

# presets that tend to render heavy effects; tiny models can skip them
HEAVY_PRESETS = {"meteor"}

# thresholds below which a model is considered too small for heavy effects
MIN_STRINGS = 2
MIN_NODES = 10

# color cycle used by the solid_pulse preset
COLOR_CYCLE = [
    "#FF0000",
    "#00FF00",
    "#0000FF",
    "#FFFF00",
    "#FF00FF",
    "#00FFFF",
]


def build_rgbeffects(models, beat_times, duration_ms, preset: str):
    """Generate an xLights RGB effects file using a preset."""

    root = ET.Element("xrgb", version="2024.05", showDir=".")
    # timing track
    timing = ET.SubElement(root, "timing", name="AutoBeat")
    for bt in beat_times:
        ET.SubElement(timing, "marker", timeMS=str(int(bt * 1000)))

    preset_cfg = PRESET_MAP.get(preset, PRESET_MAP["solid_pulse"])

    # simple per-beat effect per model
    for m in models:
        # skip tiny models for heavy presets
        if preset in HEAVY_PRESETS:
            if (
                m.strings is not None and m.strings < MIN_STRINGS
            ) or (
                m.nodes is not None and m.nodes < MIN_NODES
            ):
                continue

        mdl = ET.SubElement(root, "model", name=m.name)
        layer = ET.SubElement(mdl, "effectLayer", name="Layer 1")
        for i, bt in enumerate(beat_times):
            start = int(bt * 1000)
            end = int(
                min(duration_ms, (beat_times[i + 1] * 1000))
                if i + 1 < len(beat_times)
                else duration_ms
            )
            eff = ET.SubElement(
                layer,
                "effect",
                startMS=str(start),
                endMS=str(end),
                type=preset_cfg["type"],
            )

            if preset == "solid_pulse":
                color = COLOR_CYCLE[i % len(COLOR_CYCLE)]
                ET.SubElement(eff, "param", name="Color1", value=color)
            elif preset == "bars":
                params = preset_cfg["params"].copy()
                # Adjust bar count based on model metadata
                bars_val = None
                if m.strings is not None:
                    bars_val = m.strings
                elif m.nodes is not None:
                    bars_val = max(1, m.nodes // 50)
                if bars_val is not None:
                    params["Bars"] = str(bars_val)
                for name, value in params.items():
                    ET.SubElement(eff, "param", name=name, value=value)
            elif preset == "meteor":
                is_downbeat = i % 4 == 0
                params = preset_cfg["params"]["downbeat" if is_downbeat else "normal"].copy()
                params["Color1"] = "#FFFFFF"
                for name, value in params.items():
                    ET.SubElement(eff, "param", name=name, value=value)
            else:
                for name, value in preset_cfg.get("params", {}).items():
                    ET.SubElement(eff, "param", name=name, value=value)
    return ET.ElementTree(root)

def write_rgbeffects(tree, out_path: str):
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
