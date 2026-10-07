# FORM — recorded squat trainer

Open **http://127.0.0.1:8790** while the local server is running.

This is the separate LearnOpenCV-based squat coach requested in the brief. It uses pretrained MediaPipe pose estimation and explicit LearnOpenCV angle/state rules. No classifier is trained, no REHAB24-6 source is used, and live mode has been removed at your request.

## Start on this Windows machine

Open PowerShell in this folder and run:

```powershell
.\start.ps1
```

Then open http://127.0.0.1:8790 in a browser. Keep the terminal running; Ctrl+C stops the app. The supplied environment and production frontend are already built. The launcher creates an environment only if it is missing.

## Use the app

1. Choose Beginner or Pro, then upload a recorded squat video. Use a side view with the full body visible and sufficient light. Upload limit: 200 MiB; decoded video limit: one hour, 240 FPS, and 3840 × 2160 pixels.
2. Wait for local pose extraction and analysis. Repetition boundaries are detected automatically by the upstream state sequence.
3. Play the recording, seek with the timeline or angle chart, and toggle the synchronized skeleton. The inspector shows the current phase, measured inclination and rule-triggered cues; counts are final session totals.
4. Replay a repetition from the table. Replay stops at its end; enable the loop button to repeat it. The timeline provides a keyboard-accessible alternative to chart seeking.
5. Download CSV or PDF reports. Sessions stores history locally, with a basic rule-score progress chart. Deleting a session removes its app-owned recording and analysis files.

### 3D pose and detailed feedback

For a newly analyzed recording, click **3D pose** above the video. The additional panel uses MediaPipe's estimated world landmarks, synchronized with the recording. Rotate by dragging or with the keyboard-accessible sliders; use Camera view, Rotate 90°, Reset, and Play/Pause 3D playback. The viewer is a 3D skeleton, not a full human mesh or calibrated body scan. No model was trained and no new inference dependency was added.

Scroll to **Repetition: what the rules observed** for measured angle/tempo context, failing-rule explanations, advisory torso cues, and **View moment** links where a cue occurred. Failing rules and non-failing cues are distinguished. The original 2D verdict rules are unchanged; the 3D display does not add validated coaching judgments.

Old sessions did not retain 3D world coordinates. Re-upload those recordings to capture the new data. A verified local example is saved under Sessions as **3d-review-example.mp4**. CSV/PDF retain their existing report layout; expanded explanations appear in the UI and session JSON.

Uploads, pose processing and stored results stay on this computer. Videos are converted to H.264 for browser playback; the conversion strips audio. The app does not require accounts or a remote inference service.

## What the measurements mean

- **Thigh inclination** is the upstream image-based angle from thigh to upward vertical, using its integer pixel and degree approximation. It is a depth proxy, not anatomical knee flexion or depth in centimeters.
- **Rule score** = 100 × correct completed repetitions / all completed repetitions. With no completed reps the score is unavailable.
- **Tempo** uses the first accepted transition as the repetition start, maximum inclination as bottom, and return to standing as end. It does not measure the earliest physical movement before the transition threshold.
- Rule feedback is a heuristic, not a validated expert, medical or injury-risk assessment. View and tracking interruptions cancel incomplete repetitions. Session totals persist across inactivity.

## Verification and remaining limits

See `FEATURE_STATUS.md` and `evidence/VERIFICATION.md` for the three-state feature checklist and actual checks. The preserved upstream analyzer was compared against the new engine on the same cached poses from one 541-frame annotated upstream clip. Both profiles matched counts, displayed feedback and states on that clip. This does not establish coaching accuracy on new recordings.

Windows launch and actual browser upload/playback were exercised. Linux has a launch script but has not been run. A public Demo mode is omitted because the available example's media license was not established. The original upstream analyzer ran headlessly; its Streamlit/WebRTC interface was not launched.

## Source and development

The real sparse Git clone is in `vendor/upstream-repo`, pinned to `cb8089c79eaab366a9d78e125605805c7c77ad5d`. `vendor/learnopencv` preserves an unchanged source snapshot; `SOURCE_PROVENANCE.md` and `source_manifest.json` document attribution and hashes. No reuse/media license is asserted where the upstream tree provides none.

Backend: Python 3.11, FastAPI, SQLite, MediaPipe, OpenCV, ReportLab. Frontend: React, TypeScript, Vite, Tailwind baseline CSS and Recharts. Dependencies are pinned in `requirements.txt`, `requirements.lock`, `frontend/package.json` and `frontend/pnpm-lock.yaml`.

```powershell
# From this folder; installs are unnecessary on the current machine.
.venv\Scripts\python.exe -m pytest -q tests
# From frontend/, with pnpm available:
pnpm install --frozen-lockfile
pnpm run build
```

On Linux with Python 3.11 and the built frontend available: `bash start.sh`. This path remains unverified. The full Python lock reflects the tested Windows environment; direct dependency pins are the portable installation entry point.

The chart dependency graph caused excessive Rollup tree-shaking during the first build. `treeshake: false` makes the verified local production build bounded; the bundle is about 709 kB before compression. No CDN is required.
