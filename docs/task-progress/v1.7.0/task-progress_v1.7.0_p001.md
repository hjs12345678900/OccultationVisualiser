# v1.7.0

- TASK-0020: 33 tests pass, including saved SNR vs DNR, exclusion of partially occulted/flagged exposures, population scatter rather than mean uncertainty, zero-noise/unknown-baseline handling and bilingual labels.
- TASK-0021: Source layout adds SNR to the reserved station-coordinate header and documents the definition in the footer. Descriptive statistics and native result I/O remain separate; source modules are below 200 lines. Display cuts, playback speed, saved counts and D/R are unchanged.
