# v1.18.1

- TASK-0051: Windows v1.18.0 source tests correctly caught an observer-name assertion reading UTF-8 output with CP1252. Specify UTF-8 in the test without changing its expected Unicode value; add a bundled Lagarith decoder availability check to every frozen AVI test. Validation in progress.
- TASK-0052: Release complete Windows/macOS packages with actual Protogeneia AVI validation, no PyOTE JSON requirement, explicit frame identity and no invented exposure/independent UTC. Preserve both original CSVs and all observation bytes. Three-platform validation pending.
