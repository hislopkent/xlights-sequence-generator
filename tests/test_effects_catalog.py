import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from xlights_seq.effects_catalog import validate_effect, describe_catalog_for_prompt


def test_valid_effect_passes_through():
    cleaned = validate_effect("On", {"color": "#ff0000", "opacity": 0.5})
    assert cleaned == {"color": "#FF0000", "opacity": 0.5}


def test_unknown_effect_rejected():
    assert validate_effect("TotallyMadeUp", {"color": "#FFFFFF"}) is None


def test_missing_params_get_defaults():
    cleaned = validate_effect("Bars", {})
    assert cleaned == {"color": "#FFFFFF", "bars": 6, "direction": "LeftRight"}


def test_out_of_range_and_invalid_values_are_clamped_or_defaulted():
    cleaned = validate_effect("Shockwave", {"color": "not-a-color", "brightness": 5})
    assert cleaned["color"] == "#FFFFFF"  # invalid hex -> default
    assert cleaned["brightness"] == 1.0  # clamped to unit range

    cleaned = validate_effect("Bars", {"bars": 999, "direction": "Sideways"})
    assert cleaned["bars"] == 32  # clamped to max
    assert cleaned["direction"] == "LeftRight"  # invalid enum -> default


def test_describe_catalog_lists_all_effects():
    desc = describe_catalog_for_prompt()
    for effect in ("On", "Bars", "Meteor", "Spirals", "Shockwave", "Waves", "SingleStrand", "Shader"):
        assert effect in desc
