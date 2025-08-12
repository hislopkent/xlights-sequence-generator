import importlib
import pytest
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def client(tmp_path, monkeypatch):
    log_file = tmp_path / "app.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    import xlights_seq.config as config
    importlib.reload(config)
    import app
    importlib.reload(app)
    with app.app.test_client() as client:
        yield client


def test_render_layout_ok(client, tmp_path):
    xml = "<layout><model name='Tree'><node x='1' y='2'/><node x='3' y='4'/></model></layout>"
    path = tmp_path / "layout.xml"
    path.write_text(xml)
    with path.open('rb') as f:
        data = {"layout": (f, "layout.xml")}
        resp = client.post("/render-layout", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    j = resp.get_json()
    assert j["ok"] is True
    fig = j["figure"]
    assert fig["data"][0]["type"] == "scattergl"
    assert fig["data"][0]["x"] == [1.0, 3.0]
    assert fig["data"][0]["y"] == [2.0, 4.0]
    assert fig["layout"]["yaxis"]["autorange"] == "reversed"


def test_render_layout_bad_file(client, tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("not xml")
    with bad.open('rb') as f:
        data = {"layout": (f, "bad.txt")}
        resp = client.post("/render-layout", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    j = resp.get_json()
    assert j["ok"] is False
