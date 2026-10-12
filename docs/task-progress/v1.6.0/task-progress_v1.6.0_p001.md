# v1.6.0

- TASK-0016: 30 tests pass, covering cross-midnight disjoint windows, gap retention/removal, exact short final holds, coordinate validation, southern-hemisphere sorting and unchanged UTC under fixed playback.
- TASK-0017: Real bilingual codecs export a fixed 2-second video with a UTC jump and sorted stations; legacy single/four-station codec tests pass.
- TASK-0018: Desktop fields expose padding, gaps, duration, ordering and station coordinates. Previous GUI projects retain manual windows/input order. New modules remain below 200 lines and measured photometry/D/R readers are unchanged.
- Source codec self-test passed. Tk 8.6 startup and populated project controls passed; the 1100×921 window contains its full output log, and the observer editor is 989×694. Source architecture audit has zero errors; one pre-existing 249-line legacy renderer remains unchanged.
