"""Deterministic rule engine adapted from the pinned LearnOpenCV squat example.

Angles intentionally preserve upstream integer pixel coordinates and its
int(180/pi) approximation. `thigh_angle` is inclination to image vertical,
not anatomical knee flexion or measured squat depth.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


SIDE = {
    "left": (11, 13, 15, 23, 25, 27, 31),
    "right": (12, 14, 16, 24, 26, 28, 32),
}
FEEDBACK = ("bend_backward", "bend_forward", "shin_over_toe", "too_deep")
FAULTS = {"shin_over_toe", "too_deep", "shallow"}


@dataclass(frozen=True)
class Config:
    mode: str = "beginner"
    min_visibility: float = 0.30
    max_gap_s: float = 0.75
    inactivity_s: float = 15.0
    feedback_frames: int = 50

    @property
    def pass_start(self) -> int:
        return 80 if self.mode == "pro" else 70

    @property
    def ankle_limit(self) -> int:
        return 30 if self.mode == "pro" else 45

    @property
    def hip_min(self) -> int:
        return 15 if self.mode == "pro" else 10

    @property
    def lower_hips_end(self) -> int:
        return 80 if self.mode == "pro" else 70


def _point(landmarks: list[dict], index: int, width: int, height: int) -> tuple[int, int]:
    item = landmarks[index]
    return int(item["x"] * width), int(item["y"] * height)


def upstream_angle(a: tuple[int, int], b: tuple[int, int], ref: tuple[int, int] = (0, 0)) -> int:
    ax, ay = a[0] - ref[0], a[1] - ref[1]
    bx, by = b[0] - ref[0], b[1] - ref[1]
    length = math.hypot(ax, ay) * math.hypot(bx, by)
    if length == 0:
        raise ValueError("degenerate landmarks")
    cosine = max(-1.0, min(1.0, (ax * bx + ay * by) / length))
    return int(int(180 / math.pi) * math.acos(cosine))


def measure(landmarks: list[dict], width: int, height: int, config: Config) -> dict[str, Any]:
    if len(landmarks) < 33:
        raise ValueError("missing_landmarks")
    for index in (0, 11, 12, 23, 24, 25, 26, 27, 28, 31, 32):
        item = landmarks[index]
        if not math.isfinite(item["x"]) or not math.isfinite(item["y"]):
            raise ValueError("missing_landmarks")
    nose = _point(landmarks, 0, width, height)
    left_shoulder = _point(landmarks, 11, width, height)
    right_shoulder = _point(landmarks, 12, width, height)
    offset = upstream_angle(left_shoulder, right_shoulder, nose)
    if offset > 35:
        raise ValueError("unsuitable_view")
    left_distance = abs(_point(landmarks, 31, width, height)[1] - left_shoulder[1])
    right_distance = abs(_point(landmarks, 32, width, height)[1] - right_shoulder[1])
    side = "left" if left_distance > right_distance else "right"
    if any(landmarks[index].get("visibility", 1.0) < config.min_visibility for index in SIDE[side][0:1] + SIDE[side][3:]):
        raise ValueError("missing_landmarks")
    shoulder, elbow, wrist, hip, knee, ankle, foot = [_point(landmarks, idx, width, height) for idx in SIDE[side]]
    hip_angle = upstream_angle(shoulder, (hip[0], 0), hip)
    thigh_angle = upstream_angle(hip, (knee[0], 0), knee)
    shin_angle = upstream_angle(knee, (ankle[0], 0), ankle)
    return {"hip_angle": hip_angle, "thigh_angle": thigh_angle, "shin_angle": shin_angle, "offset_angle": offset, "side": side}


class Analyzer:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        if self.config.mode not in ("beginner", "pro"):
            raise ValueError("mode must be beginner or pro")
        self.reps: list[dict] = []
        self.samples: list[dict] = []
        self.state_seq: list[str] = []
        self.incorrect = False
        self.rep_start: float | None = None
        self.rep_bottom: float | None = None
        self.rep_max = -1
        self.rep_min = 999
        self.rep_faults: set[str] = set()
        self.display: dict[str, int] = {}
        self.lower_hips = False
        self.last_t: float | None = None
        self.last_state: str | None = None
        self.same_state_since: float | None = None
        self.valid_frames = 0
        self.invalid_counts: dict[str, int] = {}

    def _break(self, clear_feedback: bool = False):
        self.state_seq.clear()
        self.incorrect = False
        self.rep_start = self.rep_bottom = None
        self.rep_max, self.rep_min = -1, 999
        self.rep_faults.clear()
        self.lower_hips = False
        self.last_state = self.same_state_since = None
        if clear_feedback:
            self.display.clear()

    def summary(self) -> dict:
        correct = sum(rep["verdict"] == "correct" for rep in self.reps)
        total = len(self.reps)
        return {
            "total": total, "correct": correct, "improper": total - correct,
            "rule_score": round(100 * correct / total) if total else None,
            "mean_tempo_s": round(sum(rep["duration_s"] for rep in self.reps) / total, 2) if total else None,
            "max_thigh_angle": max((rep["max_thigh_angle"] for rep in self.reps), default=None),
        }

    def step(self, timestamp_s: float, landmarks: list[dict] | None, width: int, height: int) -> tuple[dict, dict | None]:
        t = round(float(timestamp_s), 4)
        reason = None
        if not math.isfinite(t) or t < 0 or (self.last_t is not None and t <= self.last_t):
            reason = "invalid_timestamp"
        elif self.last_t is not None and t - self.last_t > self.config.max_gap_s:
            self._break(clear_feedback=True)
            reason = "time_gap"
        if math.isfinite(t) and t >= 0:
            self.last_t = t
        if landmarks is None:
            reason = reason or "no_person"
        values = None
        if reason is None:
            try:
                values = measure(landmarks, width, height, self.config)
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                reason = str(exc) if str(exc) in ("missing_landmarks", "unsuitable_view") else "missing_landmarks"
        if reason:
            self._break(clear_feedback=True)
            self.invalid_counts[reason] = self.invalid_counts.get(reason, 0) + 1
            sample = {"t": t, "phase": "unavailable", "thigh_angle": None, "hip_angle": None, "shin_angle": None,
                      "landmarks": None, "feedback_codes": [], "validity": reason}
            self.samples.append(sample)
            return sample, None

        self.valid_frames += 1
        thigh = values["thigh_angle"]
        if 0 <= thigh <= 32:
            state = "s1"
        elif 35 <= thigh <= 65:
            state = "s2"
        elif self.config.pass_start <= thigh <= 95:
            state = "s3"
        else:
            state = None
        if state == self.last_state:
            if self.same_state_since is not None and t - self.same_state_since >= self.config.inactivity_s:
                self._break()
                self.same_state_since = t
        else:
            self.same_state_since = t
        self.last_state = state
        rep = None
        if state == "s2":
            if ("s3" not in self.state_seq and self.state_seq.count("s2") == 0) or ("s3" in self.state_seq and self.state_seq.count("s2") == 1):
                self.state_seq.append("s2")
                if self.rep_start is None:
                    self.rep_start = t
        elif state == "s3" and "s3" not in self.state_seq and "s2" in self.state_seq:
            self.state_seq.append("s3")
        if self.rep_start is not None:
            if thigh > self.rep_max:
                self.rep_max, self.rep_bottom = thigh, t
            self.rep_min = min(self.rep_min, thigh)

        if state == "s1":
            verdict = None
            if len(self.state_seq) == 3 and not self.incorrect:
                verdict = "correct"
            elif self.state_seq == ["s2"]:
                verdict = "improper"
                self.rep_faults.add("shallow")
            elif self.incorrect:
                verdict = "improper"
            if verdict and self.rep_start is not None:
                bottom = self.rep_bottom if self.rep_bottom is not None else self.rep_start
                rep = {"index": len(self.reps) + 1, "start_s": self.rep_start, "bottom_s": bottom, "end_s": t,
                       "duration_s": round(t - self.rep_start, 3), "descent_s": round(bottom - self.rep_start, 3),
                       "ascent_s": round(t - bottom, 3), "min_thigh_angle": self.rep_min,
                       "max_thigh_angle": self.rep_max, "verdict": verdict,
                       "fault_codes": sorted(self.rep_faults)}
                self.reps.append(rep)
            self._break()
        else:
            hip, shin = values["hip_angle"], values["shin_angle"]
            if hip > 50:
                self.display.setdefault("bend_backward", 0)
            elif hip < self.config.hip_min and self.state_seq.count("s2") == 1:
                self.display.setdefault("bend_forward", 0)
            if 50 < thigh < self.config.lower_hips_end and self.state_seq.count("s2") == 1:
                self.lower_hips = True
            elif thigh > 95:
                self.display.setdefault("too_deep", 0)
                self.incorrect = True
                self.rep_faults.add("too_deep")
            if shin > self.config.ankle_limit:
                self.display.setdefault("shin_over_toe", 0)
                self.incorrect = True
                self.rep_faults.add("shin_over_toe")
        if "s3" in self.state_seq or state == "s1":
            self.lower_hips = False
        feedback = sorted(self.display)
        if self.lower_hips:
            feedback.append("lower_hips")
        for code in list(self.display):
            self.display[code] += 1
            if self.display[code] > self.config.feedback_frames:
                del self.display[code]
        sample = {"t": t, "phase": {"s1": "standing", "s2": "transition", "s3": "bottom"}.get(state, "between"),
                  "thigh_angle": thigh, "hip_angle": values["hip_angle"], "shin_angle": values["shin_angle"],
                  "landmarks": landmarks, "feedback_codes": feedback, "validity": "valid"}
        self.samples.append(sample)
        return sample, rep
