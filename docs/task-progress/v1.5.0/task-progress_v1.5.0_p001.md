# v1.5.0

- TASK-0015: 25 tests pass, including real two/three-station H.264 encoding; GUI observer edits, deletion, save/open and drop registration checked. Real Tangra LC: 233 timestamp/frame matches and 3 decoded stamps. SharpCap policy is explicit and source UTC validation remains mandatory. New GUI/model/controller files each remain below 200 lines; scientific readers and renderer retain separate responsibilities.

- Packaged Intel macOS app passed frozen codec self-test and GUI startup. Native drop callback preserves paths with spaces; window visually inspected. ZIP version and included v1.5 guide verified. Fixed repeat-build staging symlink collisions. Windows packaging remains untested on this host.
