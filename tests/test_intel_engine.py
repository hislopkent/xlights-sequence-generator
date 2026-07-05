import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from xlights_seq.intel_engine import build_intents


TIMING = {
    "beats": [0.0, 0.5, 1.0, 1.5, 2.0],
    "downbeats": [0.0, 1.0, 2.0],
    "bars": [0.0, 2.0],
    "sections": [0.0, 2.0],
}


def test_snap_to_beat_expands_one_intent_per_beat_in_range():
    plan = {
        "sections": [
            {
                "name": "S1",
                "start_s": 0.0,
                "end_s": 1.0,
                "cues": [
                    {"group": "Roofline", "effect": "On", "params": {}, "snap_to": "beat", "duration_s": 0.2}
                ],
            }
        ]
    }
    intents = build_intents(plan, TIMING, {})
    assert [i.start_s for i in intents] == [0.0, 0.5]
    assert all(i.layout_group == "Roofline" for i in intents)
    assert all(i.end_s == i.start_s + 0.2 for i in intents)


def test_snap_to_downbeat_and_bar():
    plan = {
        "sections": [
            {
                "name": "S1",
                "start_s": 0.0,
                "end_s": 2.5,
                "cues": [
                    {"group": "A", "effect": "On", "params": {}, "snap_to": "downbeat"},
                    {"group": "B", "effect": "On", "params": {}, "snap_to": "bar"},
                ],
            }
        ]
    }
    intents = build_intents(plan, TIMING, {})
    a_times = [i.start_s for i in intents if i.layout_group == "A"]
    b_times = [i.start_s for i in intents if i.layout_group == "B"]
    assert a_times == [0.0, 1.0, 2.0]
    assert b_times == [0.0, 2.0]


def test_snap_to_at_uses_explicit_times():
    plan = {
        "sections": [
            {
                "name": "S1",
                "start_s": 0.0,
                "end_s": 2.0,
                "cues": [
                    {
                        "group": "Spinners",
                        "effect": "Shockwave",
                        "params": {},
                        "snap_to": "at",
                        "at": [0.3, 1.7],
                        "duration_s": 0.1,
                    }
                ],
            }
        ]
    }
    intents = build_intents(plan, TIMING, {})
    assert [i.start_s for i in intents] == [0.3, 1.7]


def test_snap_to_section_spans_whole_section():
    plan = {
        "sections": [
            {
                "name": "S1",
                "start_s": 0.0,
                "end_s": 2.0,
                "cues": [{"group": "Wide", "effect": "Shader", "params": {}, "snap_to": "section"}],
            }
        ]
    }
    intents = build_intents(plan, TIMING, {})
    assert len(intents) == 1
    assert intents[0].start_s == 0.0 and intents[0].end_s == 2.0


def test_mapping_resolves_style_group_to_layout_group():
    plan = {
        "sections": [
            {
                "name": "S1",
                "start_s": 0.0,
                "end_s": 1.0,
                "cues": [{"group": "Focal_Tree", "effect": "On", "params": {}, "snap_to": "section"}],
            }
        ]
    }
    intents = build_intents(plan, TIMING, {"Focal_Tree": "Mega Tree"})
    assert intents[0].target_group == "Focal_Tree"
    assert intents[0].layout_group == "Mega Tree"


def test_unmapped_group_used_as_is():
    plan = {
        "sections": [
            {
                "name": "S1",
                "start_s": 0.0,
                "end_s": 1.0,
                "cues": [{"group": "Arches", "effect": "On", "params": {}, "snap_to": "section"}],
            }
        ]
    }
    intents = build_intents(plan, TIMING, {})
    assert intents[0].layout_group == "Arches"
