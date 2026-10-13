# v1.22.1 — task progress

## TASK-0064

GitHub run 38377799224 exposed a Windows CP1252 console regression: the newly printed bilingual UTC labels caused UnicodeEncodeError in six tests and one CLI export. Keep raw labels ASCII and translate at the GUI boundary. Add a strict CP1252-console verification regression and read audit JSON fixtures explicitly as UTF-8. v1.22.0 remains an unpublished draft; rebuild v1.22.1 for all three platforms and verify their frozen-app self-tests before publication.
