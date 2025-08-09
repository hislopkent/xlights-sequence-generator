import json
import os
import sys
import uuid

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app


def test_preview_endpoint():
    job = "job" + uuid.uuid4().hex
    job_dir = os.path.join(app.config["OUTPUT_FOLDER"], job)
    os.makedirs(job_dir, exist_ok=True)
    data = {
        "beatTimes": [0.0, 1.0, 2.0],
        "sections": [{"time": 1.0, "label": "Section 2"}],
    }
    with open(os.path.join(job_dir, "preview.json"), "w") as f:
        json.dump(data, f)
    with app.test_client() as client:
        resp = client.get("/preview.json", query_string={"job": job})
        assert resp.status_code == 200
        j = resp.get_json()
        assert j["ok"] is True
        assert j["beatTimes"] == data["beatTimes"]
        assert j["sections"] == data["sections"]

