import importlib
import os, sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

LAYOUT_XML = "<layout><model name='Tree' StringCount='1'/></layout>"
FAKE_ANALYSIS = {
    "bpm": 120.0,
    "duration_s": 2.0,
    "beat_times": [0.0, 0.5, 1.0, 1.5],
    "downbeat_times": [0.0, 1.0],
    "section_times": [0.0, 1.0],
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    import xlights_seq.config as config
    importlib.reload(config)
    config.Config.UPLOAD_FOLDER = str(tmp_path / "uploads")
    config.Config.OUTPUT_FOLDER = str(tmp_path / "generated")
    log_file = tmp_path / "app.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    import app
    importlib.reload(app)
    with app.app.test_client() as client:
        yield client, app


def _post(test_client, tmp_path, extra_fields=None):
    layout_path = tmp_path / "layout.xml"
    layout_path.write_text(LAYOUT_XML)
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake")
    with layout_path.open("rb") as lf, audio_path.open("rb") as af:
        data = {"layout": (lf, "layout.xml"), "audio": (af, "audio.mp3")}
        data.update(extra_fields or {})
        return test_client.post("/generate", data=data, content_type="multipart/form-data")


def test_ai_used_when_planner_succeeds(client, tmp_path, monkeypatch):
    test_client, app_module = client
    monkeypatch.setattr(app_module, "analyze_beats_plus", lambda path: FAKE_ANALYSIS)
    monkeypatch.setattr(app_module, "OFFLINE", False)

    canned_plan = {
        "sections": [
            {
                "name": "S1",
                "start_s": 0.0,
                "end_s": 2.0,
                "cues": [{"group": "Tree", "effect": "On", "params": {}, "snap_to": "beat"}],
            }
        ]
    }
    monkeypatch.setattr(app_module, "generate_ai_plan", lambda ctx: canned_plan)

    resp = _post(test_client, tmp_path, {"use_ai": "true"})
    assert resp.status_code == 200
    j = resp.get_json()
    assert j["aiUsed"] is True
    assert j["aiFallbackReason"] is None
    assert j["downloadUrl"]


def test_falls_back_when_planner_raises(client, tmp_path, monkeypatch):
    test_client, app_module = client
    monkeypatch.setattr(app_module, "analyze_beats_plus", lambda path: FAKE_ANALYSIS)
    monkeypatch.setattr(app_module, "OFFLINE", False)

    def _boom(ctx):
        raise app_module.AIPlanError("simulated failure")

    monkeypatch.setattr(app_module, "generate_ai_plan", _boom)

    resp = _post(test_client, tmp_path, {"use_ai": "true"})
    assert resp.status_code == 200
    j = resp.get_json()
    assert j["aiUsed"] is False
    assert j["aiFallbackReason"] == "simulated failure"
    assert j["downloadUrl"]


def test_offline_mode_skips_ai_without_calling_it(client, tmp_path, monkeypatch):
    test_client, app_module = client
    monkeypatch.setattr(app_module, "analyze_beats_plus", lambda path: FAKE_ANALYSIS)
    monkeypatch.setattr(app_module, "OFFLINE", True)

    def _should_not_be_called(ctx):
        raise AssertionError("generate_ai_plan should not be called when OFFLINE")

    monkeypatch.setattr(app_module, "generate_ai_plan", _should_not_be_called)

    resp = _post(test_client, tmp_path, {"use_ai": "true"})
    assert resp.status_code == 200
    j = resp.get_json()
    assert j["aiUsed"] is False
    assert j["aiFallbackReason"] == "AI director disabled (OFFLINE mode)"


def test_default_behavior_unchanged_when_ai_not_requested(client, tmp_path, monkeypatch):
    test_client, app_module = client
    monkeypatch.setattr(app_module, "analyze_beats_plus", lambda path: FAKE_ANALYSIS)

    resp = _post(test_client, tmp_path)
    assert resp.status_code == 200
    j = resp.get_json()
    assert j["aiUsed"] is False
    assert j["aiFallbackReason"] is None
    assert j["durationMs"] == 2000
    assert j["beatCount"] == 4
