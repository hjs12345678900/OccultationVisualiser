# Changes

## 1.4.0

- Import native PyMovie and saved PyOTE raw/C3/C4 counts, tracking and D/R.
- Add desktop JSON entry point and CLI for one or four observers on absolute UTC: curves left, actual fields and target details right, explicit blanks for missing recording coverage.
- Verify ADV/SER/RAVF/FITS timing before encoding, retaining nanoseconds, midnight, exposure conventions and previously applied clock corrections. Record per-frame residuals, hashes and source snapshots.
- Stream long bilingual MP4/GIF exports. Avoid floating-point endpoint loss by building timelines in integer ns.
- Run native timestamp/codec self-tests in frozen packages and build desktop packages on release tags.
