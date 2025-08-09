import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from xlights_seq.generator import build_rgbeffects, DOWNBEAT_COLOR, PALETTE
from xlights_seq.parsers import ModelInfo


def test_build_rgbeffects_structure():
    models = [ModelInfo(name="m1"), ModelInfo(name="m2")]
    beat_times = [0.0, 0.5]
    tree = build_rgbeffects(models, beat_times, duration_ms=1000, preset="solid_pulse")
    root = tree.getroot()
    assert root.tag == "xrgb"

    timing = root.find("timing[@name='AutoBeat']")
    markers = timing.findall("marker")
    assert [m.get("timeMS") for m in markers] == ["0", "500"]

    models_elems = root.findall("model")
    assert len(models_elems) == 2
    for mdl in models_elems:
        layer = mdl.find("effectLayer")
        effects = layer.findall("effect")
        assert len(effects) == 2
        assert effects[0].get("startMS") == "0" and effects[0].get("endMS") == "550"
        assert effects[1].get("startMS") == "500" and effects[1].get("endMS") == "1000"
        assert all(eff.get("type") == "On" for eff in effects)
        colors = [e.find("./param[@name='Color1']").get("value") for e in effects]
        assert colors[0] == DOWNBEAT_COLOR
        assert colors[1] == PALETTE[1]
