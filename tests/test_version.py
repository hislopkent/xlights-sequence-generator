import importlib
import pytest
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

EXPECTED_VERSION = "build.5+abcdef1"


@pytest.fixture
def client(tmp_path, monkeypatch):
    log_file = tmp_path / "app.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.setenv("GITHUB_SHA", "abcdef1234567")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "5")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "")
    monkeypatch.delenv("GITHUB_REF_TYPE", raising=False)
    monkeypatch.delenv("GITHUB_REF_NAME", raising=False)
    monkeypatch.delenv("PR_NUMBER", raising=False)
    import xlights_seq.versioning as versioning
    importlib.reload(versioning)
    import xlights_seq.config as config
    importlib.reload(config)
    import app
    importlib.reload(app)
    with app.app.test_client() as client:
        yield client


def test_version_endpoint(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    assert resp.get_json() == {"version": EXPECTED_VERSION}


def test_version_in_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b'id="appver"' in resp.data


def test_health_includes_version(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True, "version": EXPECTED_VERSION}
