# v1.13.0

- TASK-0037: Implement accelerated UTC segments without clock or frame corrections; validate exact event margins, midnight transit, merged windows and continuous weighted axes. Implemented.
- TASK-0038: Re-export real Altona station media and validate the native Apple Silicon package. All 63 tests pass. Real Altona output: 34.36 s, gap 204.5066 s played continuously at 50x, all D/R margins 5 s, 1,794 verified source frames with identical alignment/D/R and frame-position CSV to v1.12.1. Frozen arm64 package self-tests (including accelerated transit) and GUI startup pass. Complete.
