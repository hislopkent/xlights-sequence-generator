import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from xlights_seq.generator import build_rgbeffects
from xlights_seq.parsers import ModelInfo


def test_effect_spans_and_params():
    models = [ModelInfo(name="tree")]
    beat_times = [0.0, 1.0, 2.0]
    duration_ms = 3000

    tree = build_rgbeffects(models, beat_times, duration_ms, preset="solid_pulse")
    root = tree.getroot()

    mdl = root.find("./model")
    effects = mdl.findall(".//effect")

    assert len(effects) == len(beat_times)

    expected = [(0, 1050), (1000, 2000), (2000, 3000)]
    for eff, (start, end) in zip(effects, expected):
        assert eff.get("startMS") == str(start)
        assert eff.get("endMS") == str(end)
        assert eff.find("./param[@name='Color1']") is not None

