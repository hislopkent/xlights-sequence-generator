import os, sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from xlights_seq import ai_planner
from xlights_seq.ai_planner import AIPlanError, generate_ai_plan, _build_prompt, _validate_plan


CONTEXT = {
    "bpm": 120.0,
    "duration_s": 30.0,
    "section_times": [0.0, 15.0],
    "groups": [{"name": "Roofline", "model_count": 3}],
    "house_style": "Keep it classy.",
    "style_prompt": "energetic and red/green",
    "palette": ["#FF0000", "#00FF00"],
}


def test_build_prompt_includes_context():
    prompt = _build_prompt(CONTEXT)
    assert "Roofline" in prompt
    assert "120.0" in prompt
    assert "energetic and red/green" in prompt
    assert "#FF0000" in prompt
    assert "On" in prompt  # effects catalog rendered


def test_generate_ai_plan_without_api_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(AIPlanError):
        generate_ai_plan(CONTEXT)


def test_validate_plan_drops_unknown_effects_and_empty_sections():
    raw = {
        "sections": [
            {
                "name": "S1",
                "start_s": 0.0,
                "end_s": 10.0,
                "cues": [
                    {"group": "Roofline", "effect": "On", "params": {"color": "#123456"}, "snap_to": "beat"},
                    {"group": "Roofline", "effect": "NotARealEffect", "params": {}, "snap_to": "beat"},
                ],
            },
            {"name": "Empty", "start_s": 10.0, "end_s": 20.0, "cues": []},
        ]
    }
    plan = _validate_plan(raw)
    assert len(plan["sections"]) == 1
    assert len(plan["sections"][0]["cues"]) == 1
    assert plan["sections"][0]["cues"][0]["params"]["color"] == "#123456"


def test_validate_plan_raises_when_nothing_survives():
    with pytest.raises(AIPlanError):
        _validate_plan({"sections": [{"name": "S1", "start_s": 0, "end_s": 1, "cues": []}]})


class _FakeBlock:
    def __init__(self, type_, name=None, input_=None):
        self.type = type_
        self.name = name
        self.input = input_


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _FakeMessages:
    def __init__(self, response):
        self._response = response

    def create(self, **kwargs):
        return self._response


class _FakeAnthropic:
    def __init__(self, response):
        self.messages = _FakeMessages(response)


def test_generate_ai_plan_success_with_mocked_client(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    plan_input = {
        "sections": [
            {
                "name": "S1",
                "start_s": 0.0,
                "end_s": 10.0,
                "cues": [
                    {"group": "Roofline", "effect": "On", "params": {"color": "#FFFFFF"}, "snap_to": "beat"}
                ],
            }
        ]
    }
    fake_response = _FakeResponse([_FakeBlock("tool_use", "emit_plan", plan_input)])

    import anthropic

    monkeypatch.setattr(anthropic, "Anthropic", lambda **kwargs: _FakeAnthropic(fake_response))

    plan = generate_ai_plan(CONTEXT)
    assert plan["sections"][0]["cues"][0]["group"] == "Roofline"


def test_generate_ai_plan_wraps_client_errors(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    class _Boom:
        def __init__(self, **kwargs):
            raise RuntimeError("network down")

    import anthropic

    monkeypatch.setattr(anthropic, "Anthropic", _Boom)

    with pytest.raises(AIPlanError):
        generate_ai_plan(CONTEXT)
