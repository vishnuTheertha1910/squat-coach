# 3D pose and expanded feedback extension

Uses the existing pretrained MediaPipe Pose result's `pose_world_landmarks`, retained alongside the original 2D coordinates. No training, new model, classifier import or live mode. Existing 2D angles, state transitions and verdicts are untouched.

Actual new upload: `3d-review-example.mp4`, session `73b95a94-4ef8-4aa5-b7f6-2f3862e4f62a`. 541 frames; 17,853 stored world-coordinate points; one correct, zero improper reps; maximum inclination 89 degrees; analysis/conversion 16.979s. Evidence: `3d-review-result.json`. This annotated source is the same bounded local example used previously.

Final suite: 17 backend tests passed in 2.13s. Three added feedback tests verify in-window peak/threshold/timestamp evidence, non-failing torso cues, unchanged verdicts, and an explicit unavailable measurement when a latched trigger falls outside the repetition interval. A skipped bottom band is described as a missing accepted phase, not automatically as insufficient depth when the observed peak exceeded the band. No measurement is fabricated. Feedback window lookup uses timestamp bisection so long recordings do not repeatedly scan every sample for each repetition.

TypeScript/Vite build passes: 783 modules; approximately 717kB JS / 210kB gzip. No new npm/Python dependency was required. Source text normalized to UTF-8 and the browser correctly shows degree signs and range dashes.

3D is an interactive projection of real estimated world coordinates using Canvas, with rotation, tilt and zoom; it is not an extrusion of the 2D overlay. Camera presets refer to display rotation, not proven anatomical viewing directions. Hidden landmarks are skipped by visibility. Stale/unavailable pose frames clear the model. The full body is a skeleton, not a textured mesh.

Expanded UI feedback reports fault evidence, configured threshold, cue time, and a replay link. It distinguishes hip/torso advisory cues from upstream failing rules. Correct repetitions say only that configured rules passed. The current real example has no failing faults; failing-feedback branches were verified with synthetic fixtures, not an independently annotated incorrect squat video.

Browser checks: real world-pose rendering at the recorded bottom, camera/quarter-turn/reset presets, keyboard rotation, pointer dragging (yaw changed from -30 to33 degrees; tilt12 to6), and Play/Pause 3D playback advancing the actual video timeline at12.328s. 390px mobile viewport has document width375px with browser scrollbar and no horizontal page overflow. Screenshots: `3d-and-feedback.jpg`, `3d-mobile.jpg`, `pose3d.jpg`. Expanded feedback values render correctly as89 degrees,4.3s/2.9s and70–95 degrees. 3D rendering uses the video’s current time every animation frame and resizes its canvas only when dimensions change.

CSV/PDF layouts are unchanged; expanded explanation fields are in session JSON and the UI. Older saved sessions are preserved and explicitly require a new upload for 3D/detailed cue measurements. Expert coaching accuracy, calibrated 3D geometry, real tablet hardware and Linux are not validated. Final independent review remains pending under the previously recorded requested-agent usage-limit blocker.
