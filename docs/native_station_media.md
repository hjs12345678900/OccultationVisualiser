# Native curves and absolute UTC station media

For first-time setup, required input files and the supported PyOTE JSON schema, start with the [README](../README.md).

In the desktop app add/edit observers and select their files; JSON editing is optional. The application creates a fresh directory, retaining earlier results. CLI equivalents:

```bash
python launch.py --media-config examples/native_single.json --verify-only
python launch.py --media-config examples/native_single.json
python launch.py --media-config examples/four_stations.json
```

The examples are templates: replace input paths, dates, UTC window, exposure and timing conventions with the recording's actual values. Relative paths resolve against the JSON's directory. Observations and videos are external files, not repository fixtures. `--verify-only` produces the complete timestamp audit and input hashes without rendering.

## Configuration

Top-level fields: `event`, `target`, `date_utc` (first sample UTC date), `alignment: "absolute_utc"`, `step_s >= 0.01`, `language: "en"/"zh"/"both"`, `output_root`, and `stations` (one to eight entries). `--output-dir` overrides `output_root`. Between 2 and 2,000 displayed samples **after cuts**; increase the display step for longer timelines. Original curve samples retain their full cadence.

| Presentation field | Meaning |
| --- | --- |
| `window_mode` | `full` uses curve coverage without D/R; `manual` (legacy JSON default) needs ISO `start_utc/end_utc`; `dr` (new GUI default) needs saved/supplied D/R |
| `event_padding_s` | In `dr` mode, nonnegative seconds before D and after R; default 5 |
| `gap_mode` | `accelerate` (new GUI default), `skip` or `keep`; explicit values override legacy `skip_gaps`. Continuous transit has compressed plot-axis width, without a break |
| `gap_speed` | Finite multiplier >1, default 50. Event windows play at 1x; gaps update at 25 fps. Fixed total duration rescales both afterward |
| `skip_gaps` | Boolean, legacy default false. True merges D/R windows, or retains only the union of station curve coverage within manual limits. Individual missing images remain blank |
| `playback_mode` | `real_time` (default) or `fixed_duration`; only presentation speed changes |
| `video_duration_s` | Positive target seconds in fixed mode, at least 0.04; H.264 duration rounded to the nearest 40 ms, GIF to centiseconds |
| `station_order` | `path_north_to_south` uses nominal north-positive impact parameters and needs prediction elements; `north_to_south` is explicit legacy latitude order; `input` retains input order. Unknown offsets/locations remain last |

D/R windows are `[D-padding, R+padding)` and overlaps are merged. With gap skipping off, the continuous range covers the earliest D-padding to latest R+padding. With skipping on, both animation and shared plot axis omit the empty intervals. Double slashes mark plot-axis breaks; the UTC clock jumps to the next retained window. No station is shifted to align its event with another. The last hold in each window ends at its exact boundary before playback quantization. Legacy manual/no-gap runs retain their inclusive endpoint hold. `timeline_plan` records all intervals, removed gaps and per-frame presentation durations, and outputs record actual H.264 duration/frame count.

Each station supplies:

| Field | Meaning |
| --- | --- |
| `name`, `curve`, `source` | Display label, saved photometry, and original AVI/ADV/SER/RAVF or timed FITS image/sequence |
| `observer` | Optional observer attribution string, separate from the station name. Blank or omitted means hidden. Preserved in projects, resolved config and media metadata; rendered above the light curve. Long display credits are shortened to fit, while metadata keeps the full text. Does not change station order, map labels or colors |
| `color` | Optional `#RRGGBB` station display color; omitted, null or blank means automatic. Custom colors follow the station through sorting and are shared by curve/image labels, curve traces, normal target borders and map markers/legend. Event highlighting retains its red meaning. Eight automatic colors avoid exact matches with custom choices. `media_metadata.json` records `display_color` and `color_mode`; automatic config fields stay absent |
| `latitude_deg`, `longitude_deg` | Optional geographic degrees, north/east positive and south/west negative; provide both or leave both absent. Displayed as N/S and E/W; never star RA/Dec |
| `altitude_m`, `coordinate_source` | Optional elevation and coordinate provenance |
| `coordinate_source_file`, `source_manifest` | Optional coordinate evidence and source selection manifest, both hashed with the inputs |
| `reported_snr`, `snr_source_file` | Optional separately reported metric object and evidence file (hashed); preserved in metadata, never substituted for baseline SNR |
| `curve_format` | `pymovie_csv`, `tangra_csv`, or `tangra_lc` |
| `target_column` | Native net-count column such as `signal-target` or `signal-Altona`; no extra background subtraction |
| `exposure_s` | Positive CSV exposure in resolved JSON; GUI reads recorded metadata or explicit advanced override. LC retains its recorded durations |
| `exposure_evidence` | GUI records exposure seconds, method and evidence path (hashed); cadence is never substituted for exposure |
| `timestamp_reference` | CSV `start`, `midpoint`, or `end` |
| `source_timestamp_reference` | Required for SER or FITS dates without DATE-AVG; ADV midpoint and RAVF start are intrinsic |
| `source_first_frame` | `auto` (new default) matches recorded UTC; optional integer overrides original curve frame ID at source index 0 for ADV/SER/RAVF. Independent of displayed UTC crops |
| `mapping_tolerance_s` | Explicit finite nonnegative source/curve residual tolerance, justified by export precision |
| `source_minus_curve_s` | Optional known native-source minus already-corrected curve UTC; validates correction without applying it twice |
| `ser_byte_order` | `header` (specification), `little`, or `big`; use a documented override for nonconforming writers |
| `pyote_result` | Optional saved `native_results.json`; D/R validity, mode, frame identity and UTC agreement are checked |
| `native_mode` | `raw` (default), `C3` or `C4`, matching the saved PyOTE result |
| `camera_settings_file` | Optional capture-settings text file; otherwise detect a nearby `.CameraSettings.txt` |
| `tracking_csv` | Optional original native CSV for coordinates/defect flags when normalized exports omit them; every frame and UTC must match |
| `tracking_target_column` | Tracking CSV's target column, defaults to `target_column` |
| `D_utc/R_utc` | Optional pair of supplied observation UTC boundaries when no native fit is supplied |
| `timing_source_file` | Optional source report, hashed for provenance |
| `source_sha256` | Optional original recording hash; changed video is rejected |
| `target_xy` | Optional Tangra initial source (x,y), zero based; native/LC uses stored per-frame centroids |
| `fits_hdu`, `adv_python` | Optional explicit FITS image HDU / compatible ADV decoder executable |

For C3/C4 set `curve` to the saved `native_analysis.csv`, `tracking_csv` to `pymovie_native.csv`, `native_mode` to the saved mode and `pyote_result` to that mode's native results. The normalized values are read exactly as saved; no normalization, smoothing, integration or fitting runs in this tool. Without supplied D/R the curve and fields still render, with no invented event overlay.

## Baseline SNR labels

Each station displays dimensionless per-exposure baseline `SNR = B / sigmaB` beside its coordinates. Saved native PyOTE baseline mean B and noise sigmaB are preferred. Event-drop `DNR = (B-A)/sigmaB` is recorded separately and is never labelled baseline SNR. The noise is single-exposure scatter, not uncertainty in the mean.

If native baseline parameters are absent, calculate mean and population standard deviation (`ddof=0`) directly from valid saved exposures wholly outside supplied D/R. This includes the net-count series embedded in a Tangra LC: there is no need to re-extract photometry from FITS or export CSV. Exclude exposures straddling either transition. Use the full saved recording, independently of display cuts; apply no smoothing, detrending, clipping, integration or new timing fit. Tangra LC values are labelled `(LC baseline)` / `（LC 基线）`; other fallback curves use `≈ (estimated)` / `≈（估算）`. Missing D/R, fewer than three baseline exposures, or nonpositive mean/scatter produces an unavailable label. `baseline_snr` metadata stores parameters, method and selected frame IDs; input curves/results are hashed. Separately reported software SNR values retain their own labels and source rather than assuming identical definitions.

## Timestamp contract

All arithmetic uses `numpy.datetime64[ns]`; UTC `Z` and `+00:00` are accepted, local timezone offsets rejected. CSV clock labels retain fractional seconds and roll forward at midnight. Small backward jumps and duplicates fail. The first sample's date is required explicitly.

Exposure midpoint conversion is `t_mid = t_recorded + f × exposure`, with `f=+1/2, 0, -1/2` for start/midpoint/end. This applies to sample/field display, never to saved PyOTE D/R. PyOTE boundary dates are resolved independently against their original frame, including midnight.

SER verifies original trailer ticks and frame IDs without reading pixels or inventing cadence. ADV verifies native midpoint ns. RAVF uses native start and exposure ns. FITS DATE-AVG is already a midpoint; DATE-OBS/DATE-BEG follows the explicitly supplied convention. FITS TIMESYS other than UTC fails. Timeless FITS cubes are not accepted in strict configuration mode; export a sequence with per-frame UTC. The legacy Tangra form retains its existing index-based workflow.

For known acquisition correction, verification uses `source_midpoint = curve_midpoint + source_minus_curve_s` within the declared tolerance. The curve remains unchanged. Metadata records both timestamps, the known offset, and every residual. When source UTC differs, the image panel labels its native source UTC separately from the curve UTC.

FITS sequences are matched by recorded UTC rather than assuming file 0 is measurement 0. Partial coverage leaves missing images blank. Duplicate image matches, unordered source times and mismatching ADV/SER/RAVF times fail. Nearest displayed images retain their actual frame/time; no images are reused beyond a station's recording or across long gaps. Four observers share the same absolute UTC axis, preserving actual clock differences.

## Validation and artifacts

Native single-station output is 1920×526; four-station output is 1920×1440. Other station counts use an even-height canvas with one row per observer. Each row pairs original net ADU with an entire field and a real target crop. Original orientation/aspect is retained. A station's first displayed full frame sets fixed 0.5/99.95 percentile limits and factor-8 asinh for both field and target detail.

Outputs include bilingual H.264/yuv420p MP4, scaled GIF, PNG previews, stages/contact sheets, resolved configuration, source snapshot, `media_metadata.json` and `run_metadata.json`. Input hashes are checked again after generation. This verifies consistency with recorded clocks; it does not independently calibrate those clocks.

v1.4.0 validation: 23 tests, including native midnight/100-ns ticks, saved D/R without a second half-exposure shift, corrected UTC applied once, normalized counts/raw tracking, partial FITS, missing coverage and real bilingual codecs. The frozen self-test also exercises native SER timing and package metadata.

Real Altona mapping (2026-09-12):

| Station | Curve/image matches | Residual after known correction |
| --- | --- | --- |
| Unimelb 1 | 391/391 ADV | −0.1997 to +0.7953 ms; Tangra already subtracts 32.2 ms acquisition delay |
| Unimelb 2 | 524/524 SER | 0 ns; recording hash verified, saved exposure 0.3000711 s; explicit little-endian override matches the native reader |
| Peter Shottle | 135/723 FITS | −0.356 to −0.272 ms; supplied FITS ends before the event, RAVF shortcut has no image data |
| R. Paine | 233/233 FITS vs LC | −21.0 to +42.5 µs; actual recording near 09:58 UTC retained |

The metadata preserves exact native D/R for the first three stations and the supplied observer report for Paine. No event-midpoint alignment is applied.

## Optional shadow simulation (v1.12.0)

Configuration example (paths resolve relative to the JSON file):

```json
"shadow_simulation": {
  "enabled": true,
  "prediction_file": "altona_20260912.occelmnt"
}
```

Alternatively replace `prediction_file` with `xml`, containing exactly one
`Occultations/Event`. Omission or `enabled=false` keeps the existing canvas.
The GUI saves the checkbox, file path and pasted XML with its project; older
projects load with simulation disabled. Quality-only jobs ignore this display option.

Enabled export appends a 1920×540 map panel: one station becomes 1920×1066;
four become 1920×1980. GIF keeps its 1280-pixel width and proportional even
height. The map uses bundled country polygons and makes no network requests.
Unknown locations remain listed but have no invented map markers.

The supplied Elements[6:14] are cubic (x,y) coefficients in equatorial Earth
radii, with UT hours from Elements[5]; coefficients have no derivative factorials.
Earth[0] is apparent RA minus GAST at the epoch, in degrees. Star[10] supplies
apparent declination. Object[3] is the nominal circular diameter, in km. Earth
radii are 6378.14/6356.755 km, and rotation is 0.2625161 rad/h. The field mapping
and constants are checked against the Astrid implementation credited to Steve
Preston, pinned at
https://github.com/ChasinSpin/astrid/blob/11a3d320cc675567f1c28514585ff7a9c1a8cf28/app/pathcomputation.py
The independent implementation solves the ray/ellipsoid quadratic and maps
latitude geodetically. The footprint is a 128-vertex instantaneous circle in the
fundamental plane, projected onto the star-facing Earth surface. Missing rays
at the horizon remain unavailable. Off-Earth centers produce no silhouette or invented path.

The global footprint uses the displayed absolute UTC. Station-frame CSV records
use each verified image's corrected curve midpoint UTC. Source UTC is
retained separately and an already-applied source-minus-curve offset is never
applied again. Playback rescaling and skipped gaps leave these times unchanged.
Coordinates use signed north/east-positive degrees. Optional altitude is treated
as height above the model ellipsoid; no geoid/terrain correction is attempted.

`shadow_frame_positions.csv` covers all verified source-image mappings, rather
than only downsampled output frames. It includes original frame ID, both UTCs,
saved offset seconds, shadow-center latitude/longitude degrees, station
coordinates, FP separation km, star visibility and nominal circular coverage.
`shadow_display_positions.csv` contains the displayed clock and center position.
`shadow_prediction.occelmnt` snapshots the supplied event; input and map hashes
are recorded with the run. `shadow_simulation.json` records source, assumptions,
units, unknown stations and prediction provenance.

The prediction date must match the observation date. Frame/display times more
than one hour from the prediction epoch are rejected to prevent event-local
polynomial extrapolation; this guard is not a physical accuracy estimate.
Astrometric error, diameter error, actual silhouette, polar motion, terrain,
weather and daylight are not modelled. Predicted coverage is separate from
measured D/R and the recorded brightness.

### Path-aligned presentation (v1.12.1)

The bottom map uses its full 1848×430-pixel viewport and has no information
sidebar. A spherical oblique Mercator is constructed from the first and last
visible shadow centers as its new equator. All coastlines, station locations,
path and instantaneous footprints pass through this same geographic transform.
It uses equal projected-kilometre pixel scales, rather than rotating/stretching
an existing raster. The path runs left to right, preserving small physical
curvature. The drawing sphere uses the model equatorial radius; geographic
shadow positions remain those computed on the oblate ellipsoid.

By default, the viewport fits the entire retained trajectory, its nominal footprints and
known stations, with diameter-based padding. The static corridor is the binary
union of densely sampled instantaneous circular footprints; it is a drawing aid,
not a new uncertainty estimate. A dark disk with a light outline shows the
moving silhouette. Stations remain visible as colored points over the disk,
using the same row order/colors as the light curves and a compact bottom legend.
MP4/GIF UTC cuts are preserved: skipping a recording gap also skips that part of
the motion. CSV frame-time evidence is unchanged.

Projection equations and conventions: PROJ General Oblique Transformation,
new-equator points, and Mercator Mathematical definition / Spherical form:
https://proj.org/en/stable/operations/projections/ob_tran.html
https://proj.org/en/stable/operations/projections/merc.html


### Continuous accelerated transit and landmarks (v1.13.0)

New projects use D/R windows with five seconds before D and after R and 50x gap
playback. Overlapping event windows merge before inserting gap segments.
Every transit sample retains its actual UTC; only its presentation hold is
shortened. Transit sampling at 25 fps is independent of the event display step.
Both MP4 and GIF retain that cadence. Legacy saved skip/keep choices remain intact.
`timeline_plan` records `event_intervals`, `segments`, `accelerated_gaps`,
`gap_speed` and `axis_durations_s`; fixed-duration rescaling applies only to the
final holds, gap presentation durations and axis weights. `presentation_scale`
records that final scaling; segment speeds are relative to the event windows.
The common plot axis uses these duration weights and draws no cut
marks at adjoining accelerated segments. Original frame matching, exposure
midpoints, D/R and frame-position CSVs are unchanged.

The two explanatory lines below the station rows are removed; with a shadow
map the canvas is shortened to place the map directly below the rows. Offline
Natural Earth city labels are prioritized by scalerank/population and checked
for collisions inside the existing viewport. They never enlarge the map.
A north arrow is calculated at its displayed map location: inverse-project
that point, differentiate the same oblique projection toward increasing
geographic latitude, and reverse the screen y axis. North therefore rotates
with the geography, rather than assuming the screen's upward direction.


### Explicit compression marks (v1.13.1)

Accelerated UTC intervals are shaded on every station axis, with double slashes
at both boundaries and an English/Chinese gap label with the relative speed.
This marks the change of time scale while playback remains continuous. Ordinary
UTC ticks stay outside the caption; narrow intervals use a second-line speed
label. No timeline, frame-selection or prediction calculation changes.
All geographic rendering is offline: countries.geojson and cities.json are
packaged inside the application. No online tile server or map API is used.


### Path north-to-south station order (v1.14.0)

Select `station_order: "path_north_to_south"` and supply the prediction in
`shadow_simulation.prediction_file` or `shadow_simulation.xml`. The map's
`enabled` flag may be false; prediction data are still validated and hashed.
All station rows, colors, frame-selection columns and diagnostic tables share
this order. GUI projects with legacy north/south ordering and an enabled map
upgrade to path ordering; raw legacy JSON keeps its explicit latitude meaning.

For station s, r_s(t)=site_xy(t)-shadow_xy(t) in the Bessel fundamental plane.
The station coordinates rotate with the Earth. Minimize |r_s(t)|² independently
for each station over the prediction's ±1 h validity interval: a 30 s search
followed by golden-section refinement to a bracket <0.1 ms. No measured D/R
or midpoint alignment enters this calculation. At closest approach use relative
shadow velocity v_s=-dr_s/dt, and the unit normal n_s=(-v_y,v_x)/|v_s|, flipped
so its projection onto geographic north is positive. The signed nominal chord
offset is b_s=EARTH_A_KM*r_s·n_s in km; sort decreasing b_s. This retains the
transverse meaning across different station longitudes and passage times.

`station_path_order.json` records the prediction provenance and station status,
`cross_track_km`, `closest_approach_utc`, `closest_separation_fp_km`,
`along_track_residual_km`, `normal_fp`, `north_alignment` and relative speed.
The same station evidence is included in media metadata. Missing coordinates,
no visible/bounded approach, degenerate motion or an undefined geographic
north/south normal remain unranked at the end, in input order, with a reason.
Offsets use the nominal circular prediction without uncertainty propagation;
they are presentation coordinates, not measured occultation chords.


## AVI input (v1.16.0)

AVI is decoded by the bundled FFmpeg, sequentially from zero, selecting the first
video stream. Autorotation and frame duplication/dropping are disabled. Actual
decoded frames establish the count; container FPS/duration never establish UTC,
exposure or the original first-frame identity. Raw BGR, lossless FFV1 and MJPEG
fixtures are validated in source and frozen self-tests. Other codecs depend on
the bundled FFmpeg decoder; unsupported/corrupt streams fail explicitly.

For a CSV + AVI station, supply:

```json
"source": "recording.avi",
"source_first_frame": 100,
"timestamp_reference": "midpoint",
"exposure_s": 0.1,
"source_minus_curve_s": 0
```

Here AVI index 0 is curve frame 100, index 1 is frame 101, etc. Use the actual
recording's identity and exposure; these numbers are examples. A cropped AVI
requires the corresponding original first-frame ID. Sparse curve samples work;
curve rows outside AVI coverage remain blank. No overlap is an error. Saved
Tangra LC timing is already a midpoint; CSV timing must explicitly say start,
midpoint or end. The desktop has a dedicated AVI curve-timestamp selector and
retains it in saved projects. LC exposure can be read from the companion LC.
For CSV without exposure evidence use CameraSettings or a manual exposure.

AVI does not supply an independently verified absolute UTC. Frame alignment
records use `mapping_method=explicit_avi_frame_identity`, null
`source_midpoint_utc` / `residual_s`, and
`independent_source_utc_verified=false`. A warning and an image label distinguish
curve-derived UTC from native timestamp verification. A nonzero source clock
offset is rejected because it cannot be checked against AVI. Already corrected
curve times remain untouched. Shadow tables preserve this distinction; their
`mapped_frame_positions` includes AVI, while `verified_frame_positions` counts
only mappings with an independent source timestamp.

The mapping assumes original contiguous frame order. Transcoded files with
inserted, removed, reordered or integrated frames are not supported. Interlaced
fields are not split or deinterlaced. Timestamp overlays are not OCR'd. A user
supplied wrong first-frame identity cannot be detected without external evidence.
FFmpeg RGB8 pixels are display conversions, not calibrated detector ADU;
photometry is always read from the original saved curve. No MP4 input is added.

## Shape interpretation and review (v1.16.0)

The asteroid model has a fixed circular fundamental-plane diameter, not a
rotating 3D body or a measured silhouette. Its instantaneous intersection with
Earth changes shape with geographic position and stellar altitude. The map
uses a fixed common projected-km scale in both screen directions. Altona's
76.2 km circle gives approximately 78.86 × 76.20 km at 09:54:23.413 UTC and
90.93 × 76.20 km at 09:58:18 UTC. This expected surface stretching is retained.
See [the detailed review](review_v1.16.0.md) for methods, numerical evidence,
fixed issues and remaining limits. Near the Earth limb, partly intersecting
rims currently draw visible arcs without a filled clipped footprint; this is a
known map limitation, not an accurate closed silhouette in that regime.


### Optional station colors (v1.17.0)

The desktop editor provides a native color picker, hex entry, swatch and reset
to automatic. Cancel leaves the value unchanged; clearing it restores automatic
assignment. Old projects load with automatic colors. The original first four
automatic colors remain unchanged, with four additional colors for stations
five to eight. Intentional duplicate manual colors are allowed. This resolves
the repeated automatic-color finding in the v1.16.0 review; long map-legend
layout and the partial-limb footprint limitations remain separate.


### Selectable map view (v1.18.0)

`shadow_simulation.view_mode` accepts `full_path` (default) or `follow_shadow`.
The desktop **Map view** dropdown stores `shadow_view_mode` in the project;
opening a historical project without this field restores `full_path`.
The mode is retained in resolved configuration, `shadow_simulation.json` and
media metadata, and applies to all exported video/GIF/PNG frames.

Full-path mode uses the overview above. Follow mode translates the camera to
the physical shadow center at each displayed UTC. Projection and pixel scale
stay fixed: the viewport spans at least six times the largest sampled footprint
half-extent on each axis, with the nominal radius as a lower bound. There is no
per-frame zoom or rotation. Coastlines, corridor, station markers, cities and
geographic north all use the same camera. Stations outside the viewport remain
in the legend. If the center misses Earth, the camera uses the nearest valid
sampled center; if no center intersects Earth, it retains the overview. This
display fallback is deterministic even when preview frames are drawn out of
order; exported physical positions remain absent where the center misses Earth.
The map mode does not alter image matching, physical coordinates, UTC, D/R,
station ordering, colors or accelerated-gap timing.
