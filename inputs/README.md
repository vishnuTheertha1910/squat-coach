# Bundled inputs

Four distinct video files were exported from the existing saved-session archive on 2026-10-07. This is a convenience snapshot, not an expert-labeled benchmark or a training cohort.

| File | Origin / scope |
|---|---|
| `output_sample.mp4` | Pinned LearnOpenCV example; source already includes annotations. Repeated example uploads share this one input. |
| `20261006-0231-36.9013994.mp4` | User-supplied screen recording tested on 2026-10-06. Rear-oblique view, cropped feet and rack occlusion; zero complete reps detected with 44/737 accepted frames. |
| `squat.mp4` | Present in the user's local saved sessions at packaging time. Original source and expert reference labels were not established. |
| `correct_results.mp4` | Present in the user's local saved sessions at packaging time. Its filename is not an independent correctness label; original source and expert reference labels were not established. |

Session IDs, checksums, file sizes, outputs and original display names are in `../outputs/manifest.json`. The filename `3d-review-example.mp4` refers to a repeated upload of the same upstream input, not an additional independent video. The two Pexels videos rejected and deleted by the user are absent.

These recordings were included at the user's explicit request for a public project repository. No redistribution or downstream reuse license is established for the media. Do not treat source annotations or titles as ground truth.
