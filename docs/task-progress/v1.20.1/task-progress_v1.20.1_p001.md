# v1.20.1

- TASK-0058: Use the median regular saved cadence while excluding intervals longer than three times the shortest interval, preserving short-jitter tolerance and long-gap blanks. Validate the supplied-file half-cadence phase, native PyOTE imports and binary PyMovie in complete packages. In progress.

- Source validation: 105 tests pass, including the supplied 62/80 ms jitter pattern and three-sample long-gap guard. Actual supplied processed CSV again passes the 0/6-old versus 6/6-new phase audit after the corrected cadence guard. Camera exposure and saved timestamps remain unchanged. Three-platform/frozen validation pending.
