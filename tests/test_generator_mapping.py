import os
import xml.etree.ElementTree as ET
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from xlights_seq.generator import build_rgbeffects
from xlights_seq.parsers import ModelInfo


def test_bars_count_proportional():
    models = [ModelInfo(name="m1", strings=8), ModelInfo(name="m2", nodes=200)]
    beat_times = [0, 1]
    tree = build_rgbeffects(models, beat_times, duration_ms=1000, preset="bars")
    root = tree.getroot()
    model_elems = root.findall("model")

    # First model uses strings to determine bar count
    m1_effect = model_elems[0].find(".//effect")
    bars1 = m1_effect.find("./param[@name='Bars']").get("value")
    assert bars1 == "8"

    # Second model uses nodes to determine bar count (200 // 50 = 4)
    m2_effect = model_elems[1].find(".//effect")
    bars2 = m2_effect.find("./param[@name='Bars']").get("value")
    assert bars2 == "4"


def test_skip_small_model_for_heavy_effect():
    small = ModelInfo(name="small", nodes=5)
    big = ModelInfo(name="big", nodes=100)
    beat_times = [0, 1]
    tree = build_rgbeffects([small, big], beat_times, duration_ms=1000, preset="meteor")
    root = tree.getroot()
    names = [m.get("name") for m in root.findall("model")]
    assert "small" not in names
    assert "big" in names
