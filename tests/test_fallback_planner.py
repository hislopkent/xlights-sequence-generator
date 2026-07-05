import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from xlights_seq.fallback_planner import build_fallback_plan
from xlights_seq.effects_catalog import EFFECTS_CATALOG


def test_build_fallback_plan_covers_groups_with_valid_effects():
    plan = build_fallback_plan([10.0], 20.0, ["Roofline", "Arches"])
    assert plan["sections"][0]["start_s"] == 0.0
    assert plan["sections"][-1]["end_s"] == 20.0
    for section in plan["sections"]:
        for cue in section["cues"]:
            assert cue["effect"] in EFFECTS_CATALOG
            assert cue["group"] in ("Roofline", "Arches")


def test_build_fallback_plan_with_no_groups_still_returns_a_section():
    plan = build_fallback_plan([], 5.0, [])
    assert len(plan["sections"]) == 1
    assert plan["sections"][0]["cues"] == []
