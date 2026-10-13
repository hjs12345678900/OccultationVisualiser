# v1.22.1 — task progress

## TASK-0064

GitHub run 38377799224 exposed a Windows CP1252 console regression: the newly printed bilingual UTC labels caused UnicodeEncodeError in six tests and one CLI export. Keep raw labels ASCII and translate at the GUI boundary. Add a strict CP1252-console verification regression and read audit JSON fixtures explicitly as UTF-8. v1.22.0 remains an unpublished draft; rebuild v1.22.1 for all three platforms and verify their frozen-app self-tests before publication.

Complete: 116 local regressions passed. [GitHub run 38378388318](https://github.com/hjs12345678900/OccultationVisualiser/actions/runs/38378388318) passed Windows x64, Intel Mac and Apple Silicon builds. All three downloaded frozen reports confirm version 1.22.1, ok=true and prediction_event_import=true; report SHA-256 values match GitHub assets. The downloaded Windows ZIP passes CRC validation, contains the new source modules and package version 1.22.1, and matches SHA-256 `8eb30c01159a53b97ebe3cd8c79f95dadc0c7c7e6dafa51dbb1b47b22fb45947`. Published [v1.22.1](https://github.com/hjs12345678900/OccultationVisualiser/releases/tag/v1.22.1) as latest. Local evidence is under `dist/releases/v1.22.1/`. No remote Windows installation was performed.
