# Native curves and absolute UTC station media

In the desktop app choose **PyMovie / four-station JSON…**, then a JSON configuration and output folder. The application creates a fresh directory, retaining earlier results. CLI equivalents:

```bash
python launch.py --media-config examples/native_single.json --verify-only
python launch.py --media-config examples/native_single.json
python launch.py --media-config examples/four_stations.json
```

The examples are templates: replace input paths, dates, UTC window, exposure and timing conventions with the recording's actual values. Relative paths resolve against the JSON's directory. Observations and videos are external files, not repository fixtures. `--verify-only` produces the complete timestamp audit and input hashes without rendering.

## Configuration

Top-level fields: `event`, `target`, `date_utc` (first sample UTC date), `alignment: "absolute_utc"`, ISO `start_utc/end_utc`, positive `step_s`, `language: "en"/"zh"/"both"`, `output_root`, and `stations` (one or four entries). `--output-dir` overrides `output_root`. Maximum 2,000 displayed samples; increase the display step for longer timelines. Original curve samples retain their full cadence.

Each station supplies:

| Field | Meaning |
| --- | --- |
| `name`, `curve`, `source` | Display label, saved photometry, and original ADV/SER/RAVF or timed FITS image/sequence |
| `curve_format` | `pymovie_csv`, `tangra_csv`, or `tangra_lc` |
| `target_column` | Native net-count column such as `signal-target` or `signal-Altona`; no extra background subtraction |
| `exposure_s` | Positive supplied exposure for CSV; LC uses its recorded exposure |
| `timestamp_reference` | CSV `start`, `midpoint`, or `end` |
| `source_timestamp_reference` | Required for SER or FITS dates without DATE-AVG; ADV midpoint and RAVF start are intrinsic |
| `source_first_frame` | Original curve frame ID at source index 0; required for ADV/SER/RAVF |
| `mapping_tolerance_s` | Explicit finite nonnegative source/curve residual tolerance, justified by export precision |
| `source_minus_curve_s` | Optional known native-source minus already-corrected curve UTC; validates correction without applying it twice |
| `ser_byte_order` | `header` (specification), `little`, or `big`; use a documented override for nonconforming writers |
| `pyote_result` | Optional saved `native_results.json`; D/R validity, mode, frame identity and UTC agreement are checked |
| `native_mode` | `raw` (default), `C3` or `C4`, matching the saved PyOTE result |
| `tracking_csv` | Optional original native CSV for coordinates/defect flags when normalized exports omit them; every frame and UTC must match |
| `tracking_target_column` | Tracking CSV's target column, defaults to `target_column` |
| `D_utc/R_utc` | Optional pair of supplied observation UTC boundaries when no native fit is supplied |
| `timing_source_file` | Optional source report, hashed for provenance |
| `source_sha256` | Optional original recording hash; changed video is rejected |
| `target_xy` | Optional Tangra initial source (x,y), zero based; native/LC uses stored per-frame centroids |
| `fits_hdu`, `adv_python` | Optional explicit FITS image HDU / compatible ADV decoder executable |

For C3/C4 set `curve` to the saved `native_analysis.csv`, `tracking_csv` to `pymovie_native.csv`, `native_mode` to the saved mode and `pyote_result` to that mode's native results. The normalized values are read exactly as saved; no normalization, smoothing, integration or fitting runs in this tool. Without supplied D/R the curve and fields still render, with no invented event overlay.

## Timestamp contract

All arithmetic uses `numpy.datetime64[ns]`; UTC `Z` and `+00:00` are accepted, local timezone offsets rejected. CSV clock labels retain fractional seconds and roll forward at midnight. Small backward jumps and duplicates fail. The first sample's date is required explicitly.

Exposure midpoint conversion is `t_mid = t_recorded + f × exposure`, with `f=+1/2, 0, -1/2` for start/midpoint/end. This applies to sample/field display, never to saved PyOTE D/R. PyOTE boundary dates are resolved independently against their original frame, including midnight.

SER verifies original trailer ticks and frame IDs without reading pixels or inventing cadence. ADV verifies native midpoint ns. RAVF uses native start and exposure ns. FITS DATE-AVG is already a midpoint; DATE-OBS/DATE-BEG follows the explicitly supplied convention. FITS TIMESYS other than UTC fails. Timeless FITS cubes are not accepted in strict configuration mode; export a sequence with per-frame UTC. The legacy Tangra form retains its existing index-based workflow.

For known acquisition correction, verification uses `source_midpoint = curve_midpoint + source_minus_curve_s` within the declared tolerance. The curve remains unchanged. Metadata records both timestamps, the known offset, and every residual. When source UTC differs, the image panel labels its native source UTC separately from the curve UTC.

FITS sequences are matched by recorded UTC rather than assuming file 0 is measurement 0. Partial coverage leaves missing images blank. Duplicate image matches, unordered source times and mismatching ADV/SER/RAVF times fail. Nearest displayed images retain their actual frame/time; no images are reused beyond a station's recording or across long gaps. Four observers share the same absolute UTC axis, preserving actual clock differences.

## Validation and artifacts

Native single-station output is 1920×526; four-station output is 1920×1440. Each row pairs original net ADU with an entire field and a real target crop. Original orientation/aspect is retained. A station's first displayed full frame sets fixed 0.5/99.95 percentile limits and factor-8 asinh for both field and target detail.

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
