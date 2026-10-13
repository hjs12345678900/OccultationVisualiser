# v1.16.0 — page 001

- TASK-0045: Implement AVI input with sequential FFmpeg, explicit first-frame/curve-clock contracts, null independent UTC, GUI persistence, metadata warnings and shadow-table provenance. Validate raw/FFV1/MJPEG, partial/cropped/sparse mapping, midnight and bilingual exports.
- TASK-0046: Audit geometry, UTC, formats, maps, GUI and packaging. Quantify Altona's changing ground footprint; fix geodetic horizon, legacy Tangra midnight and missing frozen source snapshots. Source suite: 75 tests. Real Altona: 1794 identical mappings, D/R and 255 UTC display samples. Native arm64 bundle and GUI validation recorded in dist/v1.16.0/package-self-test.json; findings and limits in docs/review_v1.16.0.md.
