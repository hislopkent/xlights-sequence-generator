import importlib
import pytest
import os
import sys

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
        yield client, log_file


def test_health_endpoint(client):
    test_client, _ = client
    resp = test_client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}


def test_logging_to_file(client):
    test_client, log_file = client
    test_client.get("/health")
    contents = log_file.read_text()
    assert "Started GET /health" in contents
    assert "Completed GET /health" in contents
