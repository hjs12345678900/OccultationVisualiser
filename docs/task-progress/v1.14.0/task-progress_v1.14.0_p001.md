# v1.14.0

- TASK-0041: Calculate signed cross-track coordinates including Earth rotation and geographic north orientation. Validate analytic moving-station cases, reversed motion and the Altona order. Implemented.
- TASK-0042: Re-export Altona with path-ordered rows/colors and verify measured UTC/D/R parity; package and validate native Apple Silicon application. All 67 source tests and frozen arm64 package/GUI tests pass. Real Altona order is R. Paine (+36.166 km), Unimelb 2 (-0.365 km), Unimelb 1 (-5.968 km), Peter Shottle (-12.841 km). Per-station source frames, original D/R, physical UTC timeline, playback holds and frame-position rows are identical to v1.13.1. Rows/map colors verified visually. Complete.
