# Repository packaging verification — 2026-10-07

The standalone public repository packages the existing application; it does not retrain a model or change its analysis rules. The original working app remains in its original directory.

## Checks completed

- All eight completed sessions exported from the local SQLite archive, preserving timestamps, modes, full analysis JSON, source/display names and errors.
- Four unique inputs and four unique playback outputs copied byte-for-byte. SHA-256 values and sizes recorded in `outputs/manifest.json`; repeated videos deduplicated within each category.
- CSV and PDF reports generated through the existing app report functions for every session.
- All 12 files in the unchanged pinned LearnOpenCV snapshot match `docs/source_manifest.json`.
- Restoration created eight session rows and their runtime media. A second restoration created zero rows and preserved existing sessions.
- Existing test suite: **17 passed, one third-party AnyIO/Starlette deprecation warning**, 3.23 seconds on this Windows machine using the existing pinned Python environment.
- Packaged app started independently at temporary port 8791. All eight restored sessions served through the API; CSV/PDF endpoints, HTTP range video playback, and bundled frontend HTML passed checks.
- Tracked package is approximately 95.6 MB across 102 files before this note; largest file approximately 30.2 MB. No file requires Git LFS or exceeds GitHub's 100 MiB regular-file limit.
- Common GitHub/OpenAI token and private-key patterns scanned in packaged text; no matches found. Local environments, caches, runtime databases and nested Git metadata are excluded.
- Public repository successfully pushed to `https://github.com/vishnuTheertha1910/squat-coach`. A fresh shallow clone from GitHub restored all eight sessions, passed a repeat restoration without duplicate rows, matched all 12 upstream file hashes, and served frontend HTML/assets, session endpoints, CSV/PDF and HTTP range video playback through the API test client. The first clone attempt encountered a network reset; the retry completed successfully.

## Limits

The frontend source and its previously verified production build were copied without modification; no redundant UI build or pose extraction was performed. First-time dependency installation on a separate computer has not been exercised. Python 3.11 is required; the direct pins are provided for installation, while `requirements.lock` records the full original Windows environment. Linux/macOS startup remains unverified.

These packaging checks do not establish expert-labeled squat-form accuracy, calibrated 3D accuracy, or media reuse rights. See the evaluation protocol and provenance documents. Historical independent final integrated sign-off remains pending.
