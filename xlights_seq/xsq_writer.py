import xml.etree.ElementTree as ET


def add_timing_track(root, name, times_s):
    t = ET.SubElement(root, "timing", name=name)
    for ts in (times_s or []):
        ET.SubElement(t, "marker", timeMS=str(int(round(ts*1000))))


def choose_effect_for(model_name: str, strings: int|None, nodes: int|None, downbeat=False):
    n = (model_name or "").lower()
    # basic heuristics; tweak as you like
    if "tree" in n:      et, params = "Spirals", {"Color1":"#00FFFF"}
    elif "matrix" in n:  et, params = "Bars", {"Bars": str(max(6, min(24, (strings or 12))))}
    elif "arch" in n:    et, params = "Waves", {"Color1":"#FF00FF"}
    else:                et, params = "On", {"Color1":"#FFFFFF"}
    if downbeat: params["IntensityBoost"] = "1"
    return et, params


def build_xsq(models, beat_times, duration_ms, *, downbeat_times=None, section_times=None, preset="auto"):
    """
    models: list of ModelInfo(name, strings, nodes) parsed from xlights_rgbeffects.xml
    Timing & effects are written into the XSQ doc. Layout stays in rgbeffects.
    """
    root = ET.Element("xseq", version="2024.05")  # neutral root name that xLights accepts
    # Timing tracks
    add_timing_track(root, "Beats", beat_times)
    add_timing_track(root, "Downbeats", downbeat_times or [])
    add_timing_track(root, "Sections", section_times or [])

    # Per-model effects (simple MVP aligned to beats)
    for m in models:
        mdl = ET.SubElement(root, "model", name=m.name)
        layer = ET.SubElement(mdl, "effectLayer", name="Layer 1")
        for i, bt in enumerate(beat_times):
            start = int(bt*1000)
            end = int(min(duration_ms, (beat_times[i+1]*1000)) if i+1 < len(beat_times) else duration_ms)
            downbeat = (i % 4 == 0)
            etype, params = choose_effect_for(m.name, m.strings, m.nodes, downbeat)
            eff = ET.SubElement(layer, "effect", startMS=str(start), endMS=str(end), type=etype)
            for k,v in (params or {}).items():
                ET.SubElement(eff, "param", name=k, value=str(v))
    return ET.ElementTree(root)


def write_xsq(tree: ET.ElementTree, out_path: str):
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
