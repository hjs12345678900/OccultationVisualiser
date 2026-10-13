# v1.19.0

- TASK-0053: Implement native metrics/log imports with original-source frame/UTC checks, target/source matching, explicit repeated-fit selection and native fitted-reading SNR labels. Source and supplied-data validation in progress.
- TASK-0054: Verify native imports inside frozen Windows/Intel/Apple Silicon apps and publish complete v1.19.0 downloads. Pending.

- Source validation: 95 tests pass, including 13 native-result/processed-tracking regressions, CP1252 default decoding, BOM/Chinese paths, repeated fit selection, invalid clocks and midnight. Both supplied native TXT files retain D 14:17:23.2231 / R 14:17:30.7431 UTC and B/sigmaB=143.81/52.79; log integration=2 and 95% errors=0.3487 s remain saved values. Tk English/Chinese panels fit their actual requested dimensions. New readers/self-test/tests are 55–154 lines. The unfiltered architecture audit includes ignored environments/vendor/run snapshots; the maintained source audit has only the existing 249-line legacy renderer warning. No source data or camera exposure was changed.
