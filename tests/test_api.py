import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import api


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DATA", tmp_path)
    monkeypatch.setattr(api, "DB", tmp_path / "sessions.sqlite3")
    api.init_database()


def wait_for(client, session_id):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        item = client.get(f"/api/sessions/{session_id}").json()
        if item["status"] != "processing":
            return item
        time.sleep(0.01)
    raise AssertionError("background job did not finish")


def test_corrupt_repeated_upload_reports_and_safe_delete(monkeypatch):
    client = TestClient(api.app)
    short = client.post("/api/sessions", files={"file": ("bad.mp4", b"bad", "video/mp4")})
    assert short.status_code == 400

    def fake_analysis(source: Path, playable: Path, mode: str, cancel=None):
        assert source.is_file() and source.stat().st_size == 128
        playable.write_bytes(b"placeholder video for API lifecycle test")
        return {"duration_s": 1.0, "width": 640, "height": 480,
                "summary": {"total": 1, "correct": 0, "improper": 1, "rule_score": 0,
                            "mean_tempo_s": 0.6, "max_thigh_angle": 55},
                "reps": [{"index": 1, "start_s": 0.1, "bottom_s": 0.4, "end_s": 0.7,
                          "duration_s": 0.6, "max_thigh_angle": 55, "verdict": "improper",
                          "fault_codes": ["shallow"]}],
                "samples": [{"t": 0.1, "phase": "transition", "thigh_angle": 55,
                             "hip_angle": 0, "shin_angle": 0, "landmarks": None,
                             "feedback_codes": [], "validity": "valid"}], "metrics": {}}

    monkeypatch.setattr(api, "analyze_video", fake_analysis)
    ids = []
    for _ in range(2):
        response = client.post("/api/sessions", files={"file": ("same.mp4", b"x" * 128, "video/mp4")})
        assert response.status_code == 202
        ids.append(response.json()["id"])
    assert ids[0] != ids[1]
    for session_id in ids:
        item = wait_for(client, session_id)
        assert item["summary"]["total"] == 1
        assert client.get(f"/api/sessions/{session_id}").json()["summary"] == item["summary"]
        assert any(record["id"] == session_id for record in client.get("/api/sessions").json())
        csv_response = client.get(f"/api/sessions/{session_id}/report.csv")
        assert "shallow" in csv_response.text and "rule_score_percent" in csv_response.text
        pdf_response = client.get(f"/api/sessions/{session_id}/report.pdf")
        assert pdf_response.content.startswith(b"%PDF")
        assert client.get(f"/api/sessions/{session_id}/video").status_code == 200
        folder = api.DATA / session_id
        assert client.delete(f"/api/sessions/{session_id}").json() == {"deleted": True}
        assert not folder.exists()
        assert client.get(f"/api/sessions/{session_id}").status_code == 404


def test_corrupt_decodable_extension_fails_job():
    client = TestClient(api.app)
    response = client.post("/api/sessions", files={"file": ("corrupt.mp4", b"x" * 128, "video/mp4")})
    assert response.status_code == 202
    session_id = response.json()["id"]
    item = wait_for(client, session_id)
    assert item["status"] == "failed"
    assert item["error"]
    assert client.delete(f"/api/sessions/{session_id}").status_code == 200
