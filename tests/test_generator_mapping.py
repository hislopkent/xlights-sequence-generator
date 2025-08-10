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

    # Second model falls back to default when strings are missing
    m2_effect = model_elems[1].find(".//effect")
    bars2 = m2_effect.find("./param[@name='Bars']").get("value")
    assert bars2 == "8"


def test_small_model_uses_simple_effect_for_heavy_preset():
    small = ModelInfo(name="small", nodes=5)
    big = ModelInfo(name="big", nodes=100)
    beat_times = [0, 1]
    tree = build_rgbeffects([small, big], beat_times, duration_ms=1000, preset="meteor")
    root = tree.getroot()
    names = [m.get("name") for m in root.findall("model")]
    assert "small" in names
    assert "big" in names
    small_effect = root.find("./model[@name='small']//effect")
    assert small_effect.get("type") == "On"
    big_effect = root.find("./model[@name='big']//effect")
    assert big_effect.get("type") == "Meteor"


def test_sections_timing_track():
    models = [ModelInfo(name="m1")]
    beat_times = [0, 1, 2, 3]
    section_times = [1.0, 2.0]
    tree = build_rgbeffects(
        models,
        beat_times,
        duration_ms=4000,
        preset="solid_pulse",
        section_times=section_times,
    )
    root = tree.getroot()
    timing_tracks = root.findall("timing")
    names = [t.get("name") for t in timing_tracks]
    assert "Sections" in names
    sec_track = [t for t in timing_tracks if t.get("name") == "Sections"][0]
    markers = sec_track.findall("marker")
    assert markers[0].get("timeMS") == "1000"
    assert markers[1].get("timeMS") == "2000"


def test_preferred_groups_boosts_effect():
    m1 = ModelInfo(name="plain1")
    m2 = ModelInfo(name="plain2")
    beat_times = [0, 1]
    tree = build_rgbeffects(
        [m1, m2],
        beat_times,
        duration_ms=2000,
        preset="solid_pulse",
        preferred_groups=["plain1"],
    )
    root = tree.getroot()
    e1 = root.find("./model[@name='plain1']//effect")
    e2 = root.find("./model[@name='plain2']//effect")
    assert e1.get("type") == "Bars"
    assert e2.get("type") == "On"
