"""MediaPipe Pose adapter; the rule engine accepts plain landmark dictionaries."""
from __future__ import annotations

import cv2
import mediapipe as mp


class PoseBackend:
    def __init__(self):
        if not hasattr(mp, "solutions"):
            raise RuntimeError("MediaPipe legacy Pose API is required; use the pinned environment")
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=False, model_complexity=1, smooth_landmarks=True,
            min_detection_confidence=0.5, min_tracking_confidence=0.5,
        )

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)
        if result.pose_landmarks is None:
            return None
        world = result.pose_world_landmarks
        points = []
        for index, point in enumerate(result.pose_landmarks.landmark):
            item = {"x": round(point.x, 6), "y": round(point.y, 6),
                    "z": round(point.z, 6), "visibility": round(point.visibility, 5)}
            if world is not None:
                estimate = world.landmark[index]
                item.update(world_x=round(estimate.x, 6), world_y=round(estimate.y, 6),
                            world_z=round(estimate.z, 6))
            points.append(item)
        return points

    def close(self):
        self.pose.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
