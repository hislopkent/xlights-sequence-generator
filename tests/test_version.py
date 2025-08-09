import importlib
import pytest
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def client(tmp_path, monkeypatch):
    log_file = tmp_path / "app.log"
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.setenv("LOG_FILE", str(log_file))
    import xlights_seq.config as config
    importlib.reload(config)
    import app
    importlib.reload(app)
    with app.app.test_client() as client:
        yield client


def test_version_endpoint(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    assert resp.get_json() == {"version": "1.2.3"}


def test_version_in_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Version: 1.2.3" in resp.data
