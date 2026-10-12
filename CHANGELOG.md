# 1.7.0

- Display baseline per-exposure SNR beside each station's coordinates, using saved PyOTE B/sigmaB when available.
- Calculate missing baseline parameters directly from valid saved exposures wholly outside supplied D/R; mark Tangra LC values as LC baseline, other fallback curves as estimated.
- Save metric definitions, parameters and baseline-frame selection in run metadata. Keep DNR and separately reported software metrics distinct from baseline SNR; no new fitting or photometry.

# 1.6.1

- Reserve a separate coordinate header above each plot so latitude/longitude cannot overlap its top ADU tick.

# 1.6.0

- Configure per-station D/R windows with the selected seconds before D and after R, or use manual UTC limits.
- Skip gaps between station event windows/recordings while keeping absolute UTC; show explicit breaks on the shared curve axis.
- Choose real-time playback or a fixed total video duration. Quantize cumulative presentation holds to 25 fps without changing source or measured timestamps.
- Sort observers north to south by signed latitude and display terrestrial coordinates. GUI exposes timing/playback and station location fields; old projects retain their settings.

# 1.5.0

- Complete GUI input workflow with file browsing/drop targets, Tangra/PyMovie switching, shared events and editable 1–8 observers.
- Save/open GUI projects; verify or generate without writing JSON.
- Record SharpCap timing policy; preserve saved D/R. Support LC stamps and even-height multi-observer exports.

# 1.4.1

- Rename desktop application, distribution, build artifacts and primary commands to OccultationVisualiser; retain old commands and Python imports for compatibility.
- Include bilingual user guides and editable JSON templates beside the packaged app.
- Document first-use Tangra and PyMovie workflows, the saved PyOTE JSON contract, input limitations and troubleshooting in English and Chinese.

# Changes

## 1.4.0

- Import native PyMovie and saved PyOTE raw/C3/C4 counts, tracking and D/R.
- Add desktop JSON entry point and CLI for one or four observers on absolute UTC: curves left, actual fields and target details right, explicit blanks for missing recording coverage.
- Verify ADV/SER/RAVF/FITS timing before encoding, retaining nanoseconds, midnight, exposure conventions and previously applied clock corrections. Record per-frame residuals, hashes and source snapshots.
- Stream long bilingual MP4/GIF exports. Avoid floating-point endpoint loss by building timelines in integer ns.
- Run native timestamp/codec self-tests in frozen packages and build desktop packages on release tags.
