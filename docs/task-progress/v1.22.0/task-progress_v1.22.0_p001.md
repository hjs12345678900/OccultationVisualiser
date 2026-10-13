# v1.22.0 — task progress

## TASK-0063

Remove duplicate manual entry of asteroid name, target and UTC date when the user imports prediction elements. Add an event-form entry point and replace the old date-dependent dialog validation with a complete-event import. Invalid imports leave existing form state intact. The prediction supplies event metadata; source/curve timestamp verification remains independent. Desktop packaging is pending.

Validation: all 115 tests passed on Python 3.13, including file/paste imports, blank/stale dates, atomic rejection, map preference and media config without a map. Native macOS Tk dialogs passed actual paste/save checks in English and Chinese after retrying outside the GUI-restricted sandbox. `git diff --check` passed. New import module and regression file remain below 200 lines.

Release follow-up: the v1.22.0 Windows build exposed an ANSI diagnostic-output regression, so this tag remains a draft. The feature ships in verified v1.22.1; see TASK-0064.
