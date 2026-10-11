# v1.4.0

- TASK-0010: Standalone Python 3.13 installation verified; 23 tests passed, including bilingual four-station exports, absent event frames and true four-minute UTC separation.
- TASK-0011: Real Altona input audit verified 391/391 ADV, 524/524 SER, 135/723 Peter FITS and 233/233 Paine FITS/LC. Residuals and preserved D/R are documented in [UTC validation](../../native_station_media.md).
- TASK-0012: Source application self-test passed for SER/FITS/RAVF, native PyMovie SER, Chinese/English fonts, GIF/PNG/MP4 and input integrity. Final Altona bilingual media generated using the standalone package, with Peter's missing event images explicitly blank.
- TASK-0013: Release build workflow tests frozen Windows/macOS packages before uploading to a draft release. Per-platform results accompany downloadable packages; pyproject.toml is the authoritative version.
