"""Local FastAPI service for recorded-video sessions and reports."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
import csv
import json
import sqlite3
import threading
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

from .video import VideoError, analyze_video

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "sessions.sqlite3"
EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="squat-analyze")
JOBS: dict[str, tuple[threading.Event, object]] = {}
JOBS_LOCK = threading.Lock()


def connect():
    db = sqlite3.connect(DB, timeout=30)
    db.row_factory = sqlite3.Row
    return db


def init_database(mark_interrupted=False):
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL, mode TEXT NOT NULL, source TEXT NOT NULL, filename TEXT NOT NULL, result TEXT, error TEXT)")
        if mark_interrupted:
            db.execute("UPDATE sessions SET status='failed', error='Analysis interrupted by server restart' WHERE status='processing'")


init_database()


def get_row(session_id: str):
    with connect() as db:
        row = db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Session not found")
    return row


def get_session(session_id: str):
    row = get_row(session_id)
    result = json.loads(row["result"]) if row["result"] else {}
    return {"id": row["id"], "created_at": row["created_at"], "status": row["status"],
            "mode": row["mode"], "source": row["source"], "duration_s": result.get("duration_s"),
            "width": result.get("width"), "height": result.get("height"),
            "summary": result.get("summary"), "reps": result.get("reps", []),
            "samples": result.get("samples", []), "metrics": result.get("metrics"),
            "video_url": f"/api/sessions/{session_id}/video" if row["status"] == "completed" else None,
            "error": row["error"]}


def run_job(session_id: str, source: Path, playable: Path, mode: str, cancelled: threading.Event):
    try:
        result = analyze_video(source, playable, mode, cancel=cancelled.is_set)
        if not cancelled.is_set():
            with connect() as db:
                db.execute("UPDATE sessions SET status='completed', result=?, error=NULL WHERE id=?",
                           (json.dumps(result, separators=(",", ":")), session_id))
    except Exception as exc:
        if not cancelled.is_set():
            error = str(exc) if isinstance(exc, VideoError) else f"Analysis failed: {type(exc).__name__}: {exc}"
            with connect() as db:
                db.execute("UPDATE sessions SET status='failed', error=? WHERE id=?", (error, session_id))
    finally:
        with JOBS_LOCK:
            JOBS.pop(session_id, None)


app = FastAPI(title="Squat Coach", version="0.1.0")
app.add_event_handler("startup", lambda: init_database(mark_interrupted=True))


@app.post("/api/sessions", status_code=202)
async def upload(file: UploadFile = File(...), mode: str = Form("beginner")):
    if mode not in ("beginner", "pro"):
        raise HTTPException(400, "mode must be beginner or pro")
    extension = Path(file.filename or "").suffix.lower()
    if extension not in (".mp4", ".mov", ".avi", ".webm", ".mkv"):
        raise HTTPException(400, "Use an MP4, MOV, AVI, WebM or MKV video")
    session_id = str(uuid.uuid4())
    folder = DATA / session_id
    folder.mkdir()
    source = folder / f"source{extension}"
    size = 0
    try:
        with source.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > 200 * 1024 * 1024:
                    raise HTTPException(413, "Video exceeds the 200 MB upload limit")
                output.write(chunk)
        if size < 128:
            raise HTTPException(400, "Video is empty or corrupt")
        created = datetime.now(timezone.utc).isoformat()
        with connect() as db:
            db.execute("INSERT INTO sessions (id, created_at, status, mode, source, filename) VALUES (?, ?, ?, ?, ?, ?)",
                       (session_id, created, "processing", mode, file.filename or "video", source.name))
        cancelled = threading.Event()
        future = EXECUTOR.submit(run_job, session_id, source, folder / "playable.mp4", mode, cancelled)
        with JOBS_LOCK:
            JOBS[session_id] = (cancelled, future)
        return {"id": session_id, "status": "processing"}
    except Exception:
        if not source.exists() or size < 128 or size > 200 * 1024 * 1024:
            source.unlink(missing_ok=True)
            folder.rmdir()
        raise


@app.get("/api/sessions")
def history():
    with connect() as db:
        rows = db.execute("SELECT id FROM sessions ORDER BY created_at DESC").fetchall()
    return [get_session(row["id"]) | {"samples": []} for row in rows]


@app.get("/api/sessions/{session_id}")
def session(session_id: str):
    return get_session(session_id)


@app.get("/api/sessions/{session_id}/video")
def video(session_id: str):
    row = get_row(session_id)
    path = DATA / session_id / "playable.mp4"
    if row["status"] != "completed" or not path.is_file():
        raise HTTPException(404, "Playable video is unavailable")
    return FileResponse(path, media_type="video/mp4", filename="squat-session.mp4")


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    row = get_row(session_id)
    with JOBS_LOCK:
        active = JOBS.get(session_id)
    if active:
        active[0].set()
        active[1].cancel()
        try:
            active[1].result(timeout=35)
        except Exception:
            if not active[1].done():
                raise HTTPException(409, "Analysis is stopping; try deletion again shortly")
    folder = DATA / session_id
    for name in (row["filename"], "playable.mp4"):
        (folder / name).unlink(missing_ok=True)
    if folder.is_dir():
        folder.rmdir()
    with connect() as db:
        db.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    return {"deleted": True}


def report_result(session_id):
    item = get_session(session_id)
    if item["status"] != "completed":
        raise HTTPException(409, "Session analysis is not complete")
    return item


@app.get("/api/sessions/{session_id}/report.csv")
def csv_report(session_id: str):
    item = report_result(session_id)
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(["session_id", "mode", "total", "correct", "improper", "rule_score_percent"])
    writer.writerow([item["id"], item["mode"], item["summary"]["total"], item["summary"]["correct"],
                     item["summary"]["improper"], item["summary"]["rule_score"]])
    writer.writerow([])
    writer.writerow(["rep", "start_s", "bottom_s", "end_s", "duration_s", "max_thigh_inclination_upstream_degrees", "verdict", "fault_codes"])
    for rep in item["reps"]:
        writer.writerow([rep["index"], rep["start_s"], rep["bottom_s"], rep["end_s"], rep["duration_s"],
                         rep["max_thigh_angle"], rep["verdict"], ";".join(rep["fault_codes"])])
    return Response(stream.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=squat-session.csv"})


@app.get("/api/sessions/{session_id}/report.pdf")
def pdf_report(session_id: str):
    item = report_result(session_id)
    data = BytesIO()
    canvas = Canvas(data, pagesize=letter)
    canvas.setTitle("Squat Coach Session Report")
    canvas.setFont("Helvetica-Bold", 20)
    canvas.drawString(48, 735, "Squat Coach Session")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(48, 710, f"Session {item['id']} | {item['mode'].title()} | {item['created_at'][:10]}")
    summary = item["summary"]
    canvas.drawString(48, 682, f"Completed {summary['total']}   Correct {summary['correct']}   Improper {summary['improper']}")
    canvas.drawString(48, 665, f"Rule score: {summary['rule_score'] if summary['rule_score'] is not None else 'N/A'}%   Mean tempo: {summary['mean_tempo_s'] or 'N/A'} s")
    canvas.drawString(48, 648, "Thigh inclination is an image-based depth proxy, not anatomical knee flexion.")
    canvas.drawString(48, 633, "Rule verdicts are not validated coaching or medical assessments.")
    y = 598
    for rep in item["reps"]:
        if y < 55:
            canvas.showPage()
            canvas.setFont("Helvetica", 10)
            y = 740
        fault = ", ".join(rep["fault_codes"]) or "none"
        canvas.drawString(48, y, f"Rep {rep['index']}  {rep['start_s']:.2f}-{rep['end_s']:.2f}s  {rep['verdict']}  {rep['max_thigh_angle']} deg  faults: {fault}")
        y -= 18
    canvas.save()
    return Response(data.getvalue(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=squat-session.pdf"})


DIST = ROOT / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/", response_class=HTMLResponse)
def index():
    index_file = DIST / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Squat Coach</h1><p>Build the frontend, then reload this page.</p>")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))
