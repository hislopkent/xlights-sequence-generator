import xml.etree.ElementTree as ET

def build_rgbeffects(models, beat_times, duration_ms, preset: str):
    root = ET.Element("xrgb", version="2024.05", showDir=".")
    # timing track
    timing = ET.SubElement(root, "timing", name="AutoBeat")
    for bt in beat_times:
        ET.SubElement(timing, "marker", timeMS=str(int(bt*1000)))

    # simple per-beat effect per model
    for m in models:
        mdl = ET.SubElement(root, "model", name=m.name)
        layer = ET.SubElement(mdl, "effectLayer", name="Layer 1")
        for i, bt in enumerate(beat_times):
            start = int(bt*1000)
            end = int(min(duration_ms, (beat_times[i+1]*1000)) if i+1 < len(beat_times) else duration_ms)
            eff_type = "On" if preset == "solid_pulse" else "Bars"
            eff = ET.SubElement(layer, "effect",
                                startMS=str(start), endMS=str(end), type=eff_type)
            ET.SubElement(eff, "param", name="Color1", value="#FFFFFF")
    return ET.ElementTree(root)

def write_rgbeffects(tree, out_path: str):
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
