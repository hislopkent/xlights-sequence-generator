import importlib
import os, sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

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


def test_generate_includes_version(client, tmp_path, monkeypatch):
    test_client, app_module = client
    monkeypatch.setattr(
        app_module,
        "analyze_beats_plus",
        lambda path: {
            "bpm": 120.0,
            "duration_s": 1.0,
            "beat_times": [0.0, 0.5],
            "downbeat_times": [],
            "section_times": [],
        },
    )
    layout = "<layout><model name='Tree' StringCount='1'/></layout>"
    layout_path = tmp_path / "layout.xml"
    layout_path.write_text(layout)
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake")
    with layout_path.open("rb") as lf, audio_path.open("rb") as af:
        data = {"layout": (lf, "layout.xml"), "audio": (af, "audio.mp3")}
        resp = test_client.post(
            "/generate", data=data, content_type="multipart/form-data"
        )
    assert resp.status_code == 200
    j = resp.get_json()
    assert j["version"] == app_module.APP_VERSION
