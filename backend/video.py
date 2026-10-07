"""Recorded video decoding and browser-playable derivative."""
from __future__ import annotations

from pathlib import Path
import math
import subprocess
import time

import cv2
import imageio_ffmpeg

from .engine import Analyzer, Config
from .pose import PoseBackend
from .feedback import enrich_reps


class VideoError(Exception):
    pass


def make_playable(source: Path, target: Path):
    executable = imageio_ffmpeg.get_ffmpeg_exe()
    command = [executable, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
               "-map", "0:v:0", "-an", "-vf", "setpts=PTS-STARTPTS,pad=ceil(iw/2)*2:ceil(ih/2)*2:0:0", "-fps_mode", "vfr",
               "-c:v", "libx264", "-crf", "24", "-preset", "veryfast", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", str(target)]
    done = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if done.returncode or not target.exists() or target.stat().st_size < 100:
        target.unlink(missing_ok=True)
        raise VideoError("Could not convert this video for browser playback")


def analyze_video(source: Path, playable: Path, mode: str, cancel=None) -> dict:
    started = time.perf_counter()
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise VideoError("This video could not be opened. Try an MP4, MOV, AVI or WebM recording.")
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if fps <= 0 or fps > 240 or width < 64 or height < 64 or width * height > 3840 * 2160:
        capture.release()
        raise VideoError("Invalid video timing or dimensions")
    analyzer = Analyzer(Config(mode=mode))
    first_stamp = None
    last_stamp = None
    fallback_frames = 0
    frame_count = 0
    try:
        with PoseBackend() as pose:
            while True:
                if cancel and cancel():
                    raise VideoError("Session deleted")
                ok, frame = capture.read()
                if not ok:
                    break
                stamp_ms = capture.get(cv2.CAP_PROP_POS_MSEC)
                if first_stamp is None:
                    first_stamp = stamp_ms if stamp_ms >= 0 else 0.0
                candidate = (stamp_ms - first_stamp) / 1000
                if candidate < 0 or (last_stamp is not None and candidate <= last_stamp):
                    candidate = frame_count / fps
                    fallback_frames += 1
                if last_stamp is not None and candidate <= last_stamp:
                    candidate = last_stamp + 1 / fps
                if candidate > 3600:
                    raise VideoError("Video exceeds the one-hour analysis limit")
                landmarks = pose.process(frame)
                analyzer.step(candidate, landmarks, width, height)
                last_stamp = candidate
                frame_count += 1
    finally:
        capture.release()
    if frame_count == 0:
        raise VideoError("This video contains no decodable frames")
    if analyzer.valid_frames == 0:
        counts = analyzer.invalid_counts
        majority = math.ceil(frame_count / 2)
        if counts.get("unsuitable_view", 0) >= majority:
            raise VideoError("The camera view is unsuitable. Record your full body from the side.")
        if counts.get("missing_landmarks", 0) >= majority:
            raise VideoError("Required pose landmarks were not visible. Keep your full body in frame.")
        raise VideoError("No person was detected. Keep your full body in frame.")
    make_playable(source, playable)
    playback = cv2.VideoCapture(str(playable))
    playable_width = int(playback.get(cv2.CAP_PROP_FRAME_WIDTH))
    playable_height = int(playback.get(cv2.CAP_PROP_FRAME_HEIGHT))
    playback.release()
    if playable_width < width or playable_height < height:
        raise VideoError("Converted video dimensions are invalid")
    if playable_width != width or playable_height != height:
        for sample in analyzer.samples:
            if sample["landmarks"]:
                for point in sample["landmarks"]:
                    point["x"] = round(point["x"] * width / playable_width, 6)
                    point["y"] = round(point["y"] * height / playable_height, 6)
    enrich_reps(analyzer.reps, analyzer.samples, mode)
    return {"duration_s": round((last_stamp or 0) + 1 / fps, 3), "width": playable_width, "height": playable_height,
            "summary": analyzer.summary(), "reps": analyzer.reps, "samples": analyzer.samples,
            "metrics": {"frames": frame_count, "fps_metadata": round(fps, 3),
                        "timestamp_fallback_frames": fallback_frames,
                        "analysis_seconds": round(time.perf_counter() - started, 3),
                        "throughput_fps": round(frame_count / max(0.001, time.perf_counter() - started), 2),
                        "valid_frames": analyzer.valid_frames, "invalid_counts": analyzer.invalid_counts}}
