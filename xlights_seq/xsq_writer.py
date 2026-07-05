import xml.etree.ElementTree as ET


def write_xsq(tree: ET.ElementTree, out_path: str):
    tree.write(out_path, encoding="utf-8", xml_declaration=True)


def write_timing_tracks(root, timing):
    for name, arr in [
        ("Beats", timing.get("beats", [])),
        ("Downbeats", timing.get("downbeats", [])),
        ("Bars", timing.get("bars", [])),
        ("Sections", timing.get("sections", [])),
    ]:
        t = ET.SubElement(root, "timing", name=name)
        for s in arr:
            ET.SubElement(t, "marker", timeMS=str(int(round(s * 1000))))


def write_effect(layer, eff_type, start_s, end_s, params: dict):
    e = ET.SubElement(
        layer,
        "effect",
        startMS=str(int(start_s * 1000)),
        endMS=str(int(end_s * 1000)),
        type=eff_type,
    )
    for k, v in (params or {}).items():
        ET.SubElement(e, "param", name=str(k), value=str(v))


def build_xsq_from_intents(
    models_by_group: dict[str, list[str]],
    timing: dict,
    intents: list,
    duration_s: float,
):
    root = ET.Element("xseq", version="2024.05")
    write_timing_tracks(root, timing)
    # Expand intents per group to each member model
    for intent in intents:
        members = models_by_group.get(intent.layout_group, [])
        for model_name in members:
            mdl = root.find(f".//model[@name='{model_name}']")
            if mdl is None:
                mdl = ET.SubElement(root, "model", name=model_name)
            layer = mdl.find(".//effectLayer[@name='Layer 1']")
            if layer is None:
                layer = ET.SubElement(mdl, "effectLayer", name="Layer 1")
            write_effect(layer, intent.effect, intent.start_s, intent.end_s, intent.params)
    return ET.ElementTree(root)
