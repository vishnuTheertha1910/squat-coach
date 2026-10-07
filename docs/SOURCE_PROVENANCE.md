# Source provenance

The recorded-video squat rules are adapted from the LearnOpenCV example
[`AI-Fitness-Trainer-Using-MediaPipe-Analyzing-Squats`](https://github.com/spmallick/learnopencv/tree/cb8089c79eaab366a9d78e125605805c7c77ad5d/AI-Fitness-Trainer-Using-MediaPipe-Analyzing-Squats),
by LearnOpenCV / Satya Mallick and contributors. The repository was cloned
sparsely at commit `cb8089c79eaab366a9d78e125605805c7c77ad5d` in
`vendor/upstream-repo` in the original development workspace. That nested Git
checkout is omitted from this standalone repository. `vendor/learnopencv` is
a byte-identical source snapshot; SHA-256 values appear in
`docs/source_manifest.json`. All 12 snapshot hashes were rechecked during packaging.

The upstream code has no LICENSE file at repository root in the pinned tree;
there is no asserted reuse or media redistribution license here. The included
`output_sample.mp4` originated as a local test asset in the source snapshot.
The user explicitly requested this public archive including inputs and outputs;
its inclusion does not establish a media redistribution or reuse license.
It is not presented as a licensed demo or an expert-labeled benchmark.

`backend/engine.py` preserves the source's integer pixel rounding, approximate
angle conversion, and state sequence for uninterrupted valid video. Added
recording timestamps, explicit low-visibility/view handling, interrupted-rep
reset, persisted session totals, and form details are local extensions. A
completed rep starts only at an accepted transition (`s2`); upstream may count
an improper event if footage begins directly with an invalid bottom/shin cue
and returns to standing. This deliberate exclusion avoids inventing a rep
boundary before the clip. Upstream feedback display uses a 51-frame latch;
invalid frames clear that latch in the local engine so stale cues do not return.
`outputs/evidence/parity_result.json` and `outputs/evidence/api_sample_result.json` hold the local run evidence. The upstream source snapshot remains unchanged.
