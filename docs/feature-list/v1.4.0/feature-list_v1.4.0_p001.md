# v1.4.0

- FEAT-0010: Native net-count and raw/C3/C4 import with saved per-frame tracking and PyOTE D/R; no scientific rerun.
- FEAT-0011: One/four station desktop JSON and CLI workflow, absolute UTC, complete original fields and explicit missing images.
- FEAT-0012: Exact timestamp verification, exposure conventions, known clock offset once, midnight handling, per-frame residuals and immutable input/code provenance.
- FEAT-0013: Streamed bilingual MP4/GIF with fixed field stretch; native tests in frozen packages and tag-triggered desktop builds.

Responsibilities: input/timing modules perform data I/O, saved-boundary selection is deterministic, `make_station_media` orchestrates runs, and renderer/encoder modules only display stable records. New modules are below 200 lines. Existing 249-line legacy renderer retains its established single render responsibility.
