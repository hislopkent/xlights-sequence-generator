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


def test_custom_palette_overrides_default():
    models = [ModelInfo(name="tree")]
    beat_times = [0.0, 1.0, 2.0, 3.0]
    duration_ms = 4000
    custom = ["#111111", "#222222", "#333333"]

    tree = build_rgbeffects(
        models, beat_times, duration_ms, preset="solid_pulse", palette=custom
    )
    root = tree.getroot()
    effects = root.find("./model").findall(".//effect")
    colors = [e.find("./param[@name='Color1']").get("value") for e in effects]

    assert colors[1:] == ["#222222", "#333333", "#111111"]


def test_section_boundary_changes_effect():
    models = [ModelInfo(name="m1")]
    beat_times = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
    duration_ms = 4000

    tree = build_rgbeffects(
        models,
        beat_times,
        duration_ms,
        preset="solid_pulse",
        section_times=[2.0],
    )
    root = tree.getroot()
    effects = root.find("./model").findall(".//effect")
    types = [e.get("type") for e in effects]

    assert types[:4] == ["On"] * 4
    assert types[4:] == ["Shockwave"] * 4

