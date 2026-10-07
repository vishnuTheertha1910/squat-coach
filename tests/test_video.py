import cv2
import numpy as np
import pytest

from backend import video


def test_single_frame_without_person_has_correct_error(tmp_path, monkeypatch):
    class EmptyPose:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def process(self, _frame):
            return None

    monkeypatch.setattr(video, "PoseBackend", EmptyPose)
    source = tmp_path / "single.mp4"
    writer = cv2.VideoWriter(str(source), cv2.VideoWriter_fourcc(*"mp4v"), 30, (64, 64))
    assert writer.isOpened()
    writer.write(np.zeros((64, 64, 3), dtype=np.uint8))
    writer.release()
    with pytest.raises(video.VideoError, match="No person was detected"):
        video.analyze_video(source, tmp_path / "playable.mp4", "beginner")
