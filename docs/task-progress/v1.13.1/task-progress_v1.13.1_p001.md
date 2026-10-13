# v1.13.1

- TASK-0039: Restore visible time-scale changes for accelerated gaps and avoid overlapping UTC ticks. Implemented.
- TASK-0040: Re-export Altona media, compare physical UTC/frame/D/R parity and validate native Apple Silicon package. All 63 source tests, frozen arm64 package self-tests and GUI startup pass. Real Altona preview visually confirms shaded bands, paired slashes and English/Chinese speed captions. Compared with v1.13.0: identical UTC timeline, selected source frames, D/R and both position CSVs. Complete.
