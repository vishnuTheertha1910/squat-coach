import math

import pytest

from backend.engine import Analyzer, Config, upstream_angle


def landmarks(thigh=10, shin=0, visible=True, front=False):
    points = [{"x": 0.5, "y": 0.5, "visibility": 1.0} for _ in range(33)]
    knee_x, knee_y = 0.55, 0.65
    hip_x = knee_x + 0.06 * math.tan(math.radians(thigh))
    for shoulder, elbow, wrist, hip, knee, ankle, foot in ((11, 13, 15, 23, 25, 27, 31), (12, 14, 16, 24, 26, 28, 32)):
        dx = 0 if shoulder == 11 else 0.01
        points[shoulder].update(x=hip_x + dx, y=0.35)
        points[elbow].update(x=hip_x + dx, y=0.43)
        points[wrist].update(x=hip_x + dx, y=0.51)
        points[hip].update(x=hip_x + dx, y=0.59)
        points[knee].update(x=knee_x + dx, y=knee_y)
        points[ankle].update(x=knee_x + dx + 0.20 * math.tan(math.radians(shin)), y=0.85)
        points[foot].update(x=knee_x + dx, y=0.95 if foot == 31 else 0.90)
    points[0].update(x=hip_x + 0.005, y=0.23 if not front else 0.35)
    if not visible:
        points[23]["visibility"] = 0.0
    return points


def feed(engine, angles, dt=0.1, start=0):
    events = []
    for index, angle in enumerate(angles):
        _, rep = engine.step(start + index * dt, landmarks(angle), 1000, 1000)
        if rep:
            events.append(rep)
    return events


def test_angle_convention_preserved():
    assert upstream_angle((0, -1), (1, 0)) == 89


@pytest.mark.parametrize("mode,bottom", [("beginner", 80), ("pro", 85)])
def test_complete_rep_and_boundaries(mode, bottom):
    engine = Analyzer(Config(mode=mode))
    reps = feed(engine, [10, 50, bottom, 50, 10])
    assert len(reps) == 1
    assert reps[0]["verdict"] == "correct"
    assert reps[0]["start_s"] == 0.1
    assert reps[0]["bottom_s"] == 0.2
    assert reps[0]["end_s"] == 0.4
    assert engine.summary()["rule_score"] == 100


def test_shallow_and_unfinished():
    shallow = Analyzer()
    assert feed(shallow, [10, 50, 10])[0]["fault_codes"] == ["shallow"]
    assert shallow.summary()["improper"] == 1
    unfinished = Analyzer()
    feed(unfinished, [10, 50, 80])
    assert unfinished.summary()["total"] == 0
    assert unfinished.summary()["rule_score"] is None


def test_invalid_pose_breaks_continuity():
    engine = Analyzer()
    feed(engine, [10, 50, 80])
    sample, rep = engine.step(0.3, None, 1000, 1000)
    assert sample["validity"] == "no_person" and rep is None
    feed(engine, [50, 10], start=0.4)
    assert engine.summary()["correct"] == 0


def test_gap_and_nonmonotonic_time_break_continuity():
    engine = Analyzer()
    feed(engine, [10, 50, 80])
    assert engine.step(2.0, landmarks(50), 1000, 1000)[0]["validity"] == "time_gap"
    assert engine.step(1.9, landmarks(10), 1000, 1000)[0]["validity"] == "invalid_timestamp"
    assert engine.summary()["total"] == 0


def test_visibility_and_unsuitable_view():
    engine = Analyzer()
    assert engine.step(0, landmarks(50, visible=False), 1000, 1000)[0]["validity"] == "missing_landmarks"
    assert engine.step(0.1, landmarks(50, front=True), 1000, 1000)[0]["validity"] == "unsuitable_view"


def test_no_s2_start_is_excluded_from_completed_reps():
    engine = Analyzer()
    engine.step(0, landmarks(80, shin=55), 1000, 1000)
    engine.step(0.1, landmarks(10), 1000, 1000)
    assert engine.summary()["total"] == 0


def test_fault_latches_to_completed_rep():
    engine = Analyzer()
    poses = [landmarks(10), landmarks(50, shin=55), landmarks(80), landmarks(50), landmarks(10)]
    for index, pose in enumerate(poses):
        engine.step(index * 0.1, pose, 1000, 1000)
    assert engine.summary()["improper"] == 1
    assert engine.reps[0]["fault_codes"] == ["shin_over_toe"]


def test_feedback_lifetime_and_invalid_clear():
    engine = Analyzer()
    displays = []
    for index in range(52):
        displays.append(engine.step(index * 0.1, landmarks(50, shin=55), 1000, 1000)[0]["feedback_codes"])
        if index == 50:
            assert engine.display == {}  # expired after the 51st shown frame
        if index == 51:
            assert engine.display["shin_over_toe"] == 1
    assert all("shin_over_toe" in codes for codes in displays[:51])
    assert "shin_over_toe" in displays[51]  # sustained trigger starts the next latch
    missing = engine.step(5.2, None, 1000, 1000)[0]
    assert missing["feedback_codes"] == []
    standing = engine.step(5.3, landmarks(10), 1000, 1000)[0]
    assert standing["feedback_codes"] == []


def test_fps_variation_keeps_rep_count_and_changes_duration():
    fast = Analyzer()
    slow = Analyzer()
    feed(fast, [10, 50, 80, 50, 10], dt=1 / 30)
    feed(slow, [10, 50, 80, 50, 10], dt=1 / 15)
    assert fast.summary()["correct"] == slow.summary()["correct"] == 1
    assert slow.reps[0]["duration_s"] > fast.reps[0]["duration_s"]
