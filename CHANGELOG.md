# 1.21.1

- Start the desktop UI in English by default, including contextual help. Retain live language switching and saved-project language preferences. Includes all v1.21.0 hover guidance.

# 1.21.0

- Add bilingual hover/focus help for desktop inputs, including supported files, where to find them, required/optional conditions, UTC, exposure and display settings. Cards dismiss on leaving, editing, Escape, language changes and window closure without taking focus.

# 1.20.1

- Keep normal processed-curve image support despite occasional short timestamp jitter: use the median of regular intervals with a conservative long-gap guard. Reproduce the supplied 62 ms outlier among 80 ms samples and verify the previously all-blank UTC phase displays all six actual frames.

# 1.20.0

- Fix blank image selections when processed curves have sampling intervals longer than single-frame exposure; bound selection conservatively and retain actual frame/UTC labels and long gaps.
- Add a bilingual image-brightness page with caption-safe AVI auto levels, legacy whole-field levels, manual black/white and asinh strength; fix levels for the entire clip and record their estimator region. Preserve all photometry.
- Import native PyMovie v1 binary aperture records without decoding them as CSV, retaining Unicode names, saved net signals, frames and UTC. Reject field/half-frame records clearly and retain partial-tail provenance.
- Keep all v1.19 native PyOTE TXT imports, matching raw tracking for processed curves, and legacy adapter JSON compatibility.

# 1.19.0

- Import native PyOTE `fit_metrics.txt` and `.pyote_log.txt` directly, retaining saved D/R, baseline parameters, log block integration and 95% timing errors. Legacy adapter JSON remains compatible.
- Match target/source and require explicit selection for distinct repeated fits; reject incomplete, invalid or wrong-format results with readable errors.
- Clarify bilingual file inputs and label fitted-reading SNR separately from original camera-frame noise. Match processed CSV tracking by exact source frame/UTC, allowing additional raw tracking rows.

# 1.18.1

- Make the observer-name export regression read UTF-8 metadata explicitly on Windows ANSI systems; keep the assertion of exact Chinese/English observer text.
- Verify the bundled Lagarith decoder in the frozen AVI self-test on every platform. Real supplied Protogeneia Lagarith AVI and original PyMovie CSV map all 5977 frames and export successfully with the PyOTE JSON field blank.
- Distinguish 40 ms raw frame cadence and 80 ms PyOTE block cadence from missing camera exposure metadata; the real-data compatibility test uses an explicitly unverified 40 ms placeholder, not a timing calibration.

# 1.18.0

- Add a saved map-view choice: full shadow path (default) or follow asteroid. Follow mode centers the real shadow position at each displayed UTC, with fixed projection and zoom throughout the clip.
- Cache projected offline geography and corridor vectors, redraw cities and geographic north for the moving viewport, and preserve shared station colors.
- Keep physical frame/display positions, UTC, D/R and gap timing independent of the camera. Old projects retain the full-path overview. Validate both modes in bilingual exports and the frozen self-test.

# 1.17.0

- Add an optional station color picker, hex entry, preview and reset to automatic. Preserve explicit choices in projects and exported configuration.
- Share station colors between curves, image labels/normal target borders, map markers and legends; preserve color identity across station sorting. Record actual display colors and automatic/custom mode in media metadata.
- Extend automatic colors to eight distinct palette entries while retaining the original first four, and avoid exact collisions with manually chosen colors. Old projects remain automatic.

# 1.16.0

- Add sequential AVI decoding with bundled FFmpeg; require explicit source-frame identity and CSV timestamp convention. Keep source UTC/residual null and label curve-derived timing in images and metadata.
- Validate raw BGR, FFV1 and MJPEG, cropped/sparse frame mapping, midnight, irregular cadence and bilingual exports, including the frozen application.
- Correct the ellipsoid horizon test to use the geodetic local normal in coverage and path-order calculations.
- Fix midnight rollover and whole-second UTC labels in the legacy Tangra CSV entry point.
- Include matching Python sources in the frozen bundle so exported source snapshots and hashes are complete; verify them in the frozen self-test.
- Quantify Altona shadow deformation: a fixed 76.2 km fundamental-plane circle becomes a changing ground ellipse; preserve the physically expected projection and fixed map scale.
- Preserve existing Observer fields, 1794 real source-frame matches, D/R, station order and 50x continuous gaps. Document remaining limb-rendering and AVI identity limits.

# 1.15.0

- Add an optional Observer field separate from the station name in the desktop editor and station list. Preserve it across project save/load and JSON media configuration.
- Display supplied observer credits above the corresponding light curve in MP4, GIF and PNG outputs; leave blank credits hidden. Keep full text in media metadata, even when a long display label is shortened.
- Keep path-based station ordering, map identities/colors, recorded UTC and D/R windows independent of attribution. Older projects retain their station names with no inferred observer.

# 1.14.0

- Add path north-to-south station ordering from the signed fundamental-plane impact parameter at each station's own predicted closest approach. Include Earth's rotation and local geographic north orientation.
- Apply the resulting order consistently to station rows, source-frame selections, quality reports and map colors. Save nominal offsets, predicted approach UTC and solver residuals in station_path_order.json and station metadata.
- Support prediction-based ordering with the map disabled; reject missing predictions and place uncomputable offsets last with explicit reasons. Keep latitude sorting as a separately labeled option.
- Upgrade saved GUI north/south ordering with an enabled prediction map to path ordering. Preserve original frame UTC, photometry, measured D/R, ±5 s windows and accelerated-gap presentation.

# 1.13.1

- Mark accelerated UTC gaps on every station axis with a shaded band, double slashes at scale boundaries and a localized speed label. Keep shadow motion continuous and the original D/R windows unchanged.
- Keep ordinary UTC tick labels clear of the compression caption. Narrow bands use a second-line multiplier.
- Map rendering remains completely offline using packaged Natural Earth coastlines and city coordinates.

# 1.13.0

- Remove the two explanatory station-footer lines and close up the space above the map.
- Add offline major-city labels and a geographic north arrow computed through the path-aligned projection.
- Add continuous accelerated gaps (default 50x), with 25-fps transit motion in MP4/GIF and a compressed, continuous UTC plot axis. Preserve original frame timestamps and measured D/R.
- Default new projects to D/R windows with five seconds before D and after R. Keep existing projects' saved skip/keep choices.

# 1.12.1

- Replace the bottom map/sidebar with a full-width path-focused map. Apply one oblique geographic projection to coastlines, stations and shadow so motion runs left to right with equal map scale.
- Show the moving nominal circular silhouette over its shadow corridor, plus station-colored dots and a compact legend matching the light-curve rows. Remove repeated frame/coordinate/status labels from the map.
- Keep original frame-time CSVs, measured D/R, UTC cuts and playback behavior unchanged. Verify projected geography, dateline handling and visible silhouette movement.

# 1.12.0

- Add an optional synchronized shadow map beneath station curves/images in MP4, GIF and PNG outputs. Import one Occult prediction file or paste its XML through the desktop interface.
- Compute the nominal circular shadow on a rotating oblate Earth using supplied prediction elements. Use existing station coordinates; unknown locations remain explicitly unavailable.
- Keep global display UTC and each selected image’s corrected exposure midpoint distinct. Export positions for every verified original frame with source UTC, saved clock offset and predicted station separation/coverage.
- Bundle offline Natural Earth coastlines. Preserve project opt-in settings; legacy projects load with simulation disabled. Validate event dates and reject extrapolation beyond one hour around the prediction epoch.

# 1.11.1

- Fix Windows ANSI decoding failures when loading UTF-8 PyOTE results with non-ASCII notes. Read saved mode, D/R and SNR with an explicit UTF-8 BOM-aware encoding.
- Specify UTF-8 for internal JSON files, worker requests/results, run provenance and media metadata. Accept UTF-8 BOMs in user-edited projects/configurations.
- Reproduce the reported undefined CP1252 byte 0x90 before the fix; verify saved UTC and SNR remain unchanged under an ANSI default. Add a frozen desktop-worker export with Chinese paths and UTF-8 BOM PyOTE results on all three platforms.

# 1.11.0

- Add a native Apple Silicon macOS package alongside Intel macOS and Windows x64. Rosetta is not needed for the Apple Silicon package, including ADV2 decoding.
- Build ARM ADVCore from a checksum-pinned, unmodified source archive with its MPL notice; keep build dependencies private to the project.
- Pin drag-and-drop to the Tcl/Tk 8.6-compatible release and smoke-test the frozen Mac GUI. Build-Mac.command defaults to the current interpreter architecture.
- Verify exact synthetic ADV pixels, exposure and nanosecond UTC in all frozen packages; give release reports unique platform/architecture names.

# 1.10.0

- Add a custom asteroid-occultation cover and coordinated transparent application icon, with original imagegen prompts and asset hashes.
- Show a dismissible 1.2-second launch cover; reopen it from Cover/About. Add the icon to the desktop header, native macOS app bundle and Windows executable.
- Ship artwork beside the application and in Python packages; frozen self-tests verify all branding resources.

# 1.9.0

- Add an obvious top-right Chinese/English interface picker, live translations of the event/editor/diagnostics windows and stable saved values independent of caption language.
- Separate required inputs from optional location/prediction/advanced overrides. Coordinates are optional; north-to-south sorting appends unknown locations without inventing positions.
- Replace ambiguous manual-UTC wording with contextual crop help; default new projects to complete recording coverage without D/R or typed start/end times.
- Read exposure from recorded FITS/ADV/RAVF/LC metadata, PyMovie shutter headers or CameraSettings. Never use cadence as exposure; preserve explicit overrides in historical projects.
- Match source frames by native UTC automatically; retain optional advanced frame-ID overrides. Explain raw/C3/C4 as imported curve types, and read the saved result mode automatically.

# 1.8.0

- Add desktop Noise diagnostics and View report actions, with curve-only runs and immutable JSON/CSV output.
- Keep saved SNR separate from whole-exposure guarded baseline statistics; compare stations on shared absolute UTC, excluding both D/R windows. Display unavailable comparisons when recordings do not overlap.
- Show capture camera/binning/exposure evidence, raw/linear-residual/adjacent-difference scatter, PyMovie default-mask statistics and approximate spatial-background pixel budgets. Do not infer isolated read noise or camera performance.
- Include quality reports in normal configuration generation and verification, and exercise the new pipeline in frozen-package self-tests.

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
