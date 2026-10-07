# Recorded-video feature checklist

Status reflects the implementation and checks on 2026-10-04. The app is rule-based; no model training or classifier project was used. Live mode is excluded by the user's later instruction.

| Feature | Status | Evidence / limit |
|---|---|---|
| Interactive 3D pose view | Implemented and tested | Real example contains 17,853 world points across 541 frames; synchronized estimated pose, rotation/tilt/zoom, presets and playback controls; older sessions need re-upload |
| Detailed per-repetition feedback | Implemented and tested | Measured peak/threshold and cue-time explanations; advisory cues distinguished from failing rules; three new evidence-bound regression tests; real correct-rep UI exercised |
| Upstream Git clone, commit pin, unchanged snapshot and attribution | Implemented and tested | Sparse clone and 12 snapshot hashes checked by the independent reviewer |
| Real MediaPipe video analysis and automatic repetition state machine | Implemented and tested | Original analyzer/new engine parity on the same 541-frame clip; actual browser upload completes |
| Correct/improper verdicts, specific feedback, phase | Implemented and tested | Both profiles match counts, displayed feedback and states on the observed clip; fault/latch fixtures exercise additional rules |
| Spatial silver-white UI | Implemented and tested | Actual desktop and 390px mobile screenshots; horizontal page overflow repaired |
| Synchronized playback and skeleton toggle | Implemented and tested | Video, canvas and inspector checked at transition, bottom and return; source video is already annotated |
| Invalid input/view/person/landmark handling | Implemented and tested | Browser corrupt upload; invalid-view/landmark and one-frame no-person fixtures; not every case exercised on a real human recording |
| Playback failure and retry | Implemented and tested | Browser media request deliberately blocked, readable error shown, blocking removed, Retry restores decoded playback |
| Rep table, bounded replay, looping, chart seek | Implemented and tested | Replay starts at 7.5517s, pauses at 14.7586s; chart seek at 8.8966s agrees with inspector; loop stays within selected rep |
| Thigh-inclination chart, depth proxy and phase indicator | Implemented and tested | Same stored timestamp contract; this is not anatomical knee flexion or physical depth |
| Counts, tempo, documented rule score and animated gauges | Implemented and tested | Real sample: 1 correct, 0 improper, 7.21s average rep, max 89 degrees; undefined zero-rep score tested |
| SQLite history and basic progress chart | Implemented and tested | Actual history survives fresh server launch; open/reload and history chart exercised |
| CSV and PDF reports | Implemented and tested | Real contents checked; PDF rendered and inspected; report endpoints/API fixture checks pass |
| Save uploaded session videos | Implemented and tested | Source and playable copy are retained with the session; playable copy download is exposed on playback error |
| Safe deletion of app-owned files | Implemented and tested | API tests check owned-file cleanup and row removal; deletion during long conversion yielding retryable 409 remains unexercised |
| Stale-result clearing | Implemented and tested | Replacing a completed session with corrupt/new input clears video, counts, score and table; late-response generation guard inspected |
| Keyboard controls and feedback announcements | Implemented and tested | Timeline Home/ArrowRight and button Enter exercised; notifications use status/alert roles; dialog Escape/focus trap checked |
| Tablet breakpoint / odd-size video padding | Implemented but unverified | Responsive rules and aspect/landmark remapping exist; real tablet hardware and odd-size end-to-end playback not exercised |
| Overlapping response race / long cancellation edge | Implemented but unverified | Guards and bounded deletion implemented; these exact concurrent timing cases were not injected |
| Windows launcher | Implemented and tested | `start.ps1` launched the delivered build on this machine |
| Linux launcher | Implemented but unverified | `start.sh` provided; no Linux run occurred |
| Licensed public Demo mode | Not implemented | Available source example has no established media license; no nonfunctional Demo control |
| Live/webcam/optional webcam recording | Not implemented | Removed at the user's explicit request |
| Optional switch to avoid retaining uploaded video | Not implemented | History currently retains app-owned videos until session deletion |
| Full original Streamlit/WebRTC frontend | Not implemented | Original `ProcessFrame` analyzer ran headlessly; the new app replaces its frontend |
| Independent final integrated sign-off | Not completed | Initial plan/code reviews ran and repairs were made; requested reviewer hit account usage limit before final sign-off |

Software tests and one annotated example establish bounded behavior. They do not establish expert coaching accuracy or broad real-world generalization.
