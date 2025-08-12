import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from xlights_seq.xsq_writer import build_xsq_from_intents
from xlights_seq.intel_engine import Intent


def test_build_xsq_from_intents_basic():
    models_by_group = {"GroupA": ["Model1", "Model2"]}
    timing = {"beats": [0.0, 1.0], "downbeats": [], "bars": [], "sections": []}
    intents = [
        Intent("SG", "GroupA", "On", 0.0, 0.5, {"color": "#FFFFFF"})
    ]
    tree = build_xsq_from_intents(models_by_group, timing, intents, 2.0)
    root = tree.getroot()

    models = {m.get("name"): m for m in root.findall("model")}
    assert set(models) == {"Model1", "Model2"}
    for m in models.values():
        eff = m.find("./effectLayer/effect")
        assert eff is not None
        assert eff.get("type") == "On"
        assert eff.get("startMS") == "0"
        assert eff.get("endMS") == "500"
    beats_track = root.find("timing[@name='Beats']")
    assert beats_track is not None
    assert beats_track.find("marker").get("timeMS") == "0"
