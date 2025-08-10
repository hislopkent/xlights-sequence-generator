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


def test_inspect_layout_ok(client, tmp_path):
    xml = "<layout><model name='Tree' StringCount='1'/></layout>"
    path = tmp_path / "layout.xml"
    path.write_text(xml)
    with path.open('rb') as f:
        data = {"layout": (f, "layout.xml")}
        resp = client.post("/inspect-layout", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    j = resp.get_json()
    assert j["ok"] is True
    assert j["modelCount"] == 1
    assert j["tree"]["children"][0]["name"] == "Tree"


def test_inspect_layout_bad_file(client, tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("not xml")
    with bad.open('rb') as f:
        data = {"layout": (f, "bad.txt")}
        resp = client.post("/inspect-layout", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    j = resp.get_json()
    assert j["ok"] is False
