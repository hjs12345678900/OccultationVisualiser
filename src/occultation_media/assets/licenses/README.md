# OccultationVisualiser

**English** | [简体中文](README.zh-CN.md)

Turn an occultation observation into a synchronized star-field and light-curve animation (GIF, MP4 and PNG preview). An occultation is a star temporarily hidden by an intervening object. This tool visualises **existing photometry**; it does not extract a light curve from a video or run PyOTE fitting. No Tangra, PyMovie or PyOTE installation is needed to render already exported inputs.

Previously **OccultationMedia**. New builds use `OccultationVisualiser.app` / `OccultationVisualiser.exe` and the `occultationvisualiser` command. The Python import `occultation_media` and old `occultation-media` commands remain compatible. The GitHub repository is now OccultationVisualiser; existing local checkouts may retain the old folder name.

## 1. Prepare your files

| Your existing result | Required files | How to open it |
| --- | --- | --- |
| Tangra, full recorded field | Tangra photometry CSV **and** the matching ADV2 / SER / RAVF recording or FITS images | Main desktop form |
| Tangra, target cutout only | Tangra photometry CSV **and** matching Tangra `.lc` file containing target stamps | Main desktop form; select `.lc` as observation file |
| PyMovie, one observer | Saved PyMovie CSV **and** matching original recording or timed FITS sequence **and** a configuration JSON | **PyMovie / four-station JSON…** |
| PyMovie with saved PyOTE fit | The preceding files **plus** compatible `native_results.json` (optional D/R overlay) | Same JSON workflow |
| Four observers | One curve and image source per observer, with one JSON listing exactly four stations | Same JSON workflow |

**A plot screenshot, PyOTE report alone, CSV alone, or a shortcut to a recording cannot supply the recorded star-field images.** Ordinary AVI/MP4 input is not implemented. MP4 is an output format. A Tangra LC stamp contains only a 35×35 target cutout, not the full field. Configuration mode currently accepts **one or four**, not two or three, stations.

Also collect: the UTC date of the first curve sample, asteroid/event and star names, actual exposure duration, timestamp convention (exposure start/midpoint/end), and frame mapping. GUI exposure is in **milliseconds**; JSON `exposure_s` is in **seconds**. Predicted UTC and ± uncertainty are optional in the Tangra form.

## 2. Start the application

Existing packages are listed under [Releases](https://github.com/hjs12345678900/OccultationVisualiser/releases). Older releases retain the old application name; this source rename does not update an already downloaded package.

- **Windows 10/11 x64:** extract the whole ZIP and open `OccultationVisualiser.exe`. Keep `_internal` beside it.
- **macOS 14+:** extract and open `OccultationVisualiser.app`. The configured build targets Intel; Apple Silicon needs Rosetta. Packages are unsigned/unnotarized.

To run this checkout, use Python 3.13 with Tk support. Open a terminal **in the project folder**, then:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python launch.py
```

On Windows use `py -3.13 -m venv .venv`, then `.venv\Scripts\activate` instead of the first two commands. `python -m tkinter` checks whether Tk is available. The installation includes the FFmpeg dependency and bundled fonts. Keep observation files in your own event folder; no copying into this repository is required.

## 3. Tangra: easiest first animation

1. In Tangra, save the light-curve `.lc` and export photometry CSV with frame numbers, UTC, target signal and background. Target **object 1** is plotted. The parser expects `FrameNo`, `Time (UT)`, `Signal (1)` and `Background (1)` columns; it subtracts background once.
2. Select the original recording (or `.lc` for cutouts) as **Observation file**. For a FITS sequence use **FITS folder…**. Select its CSV and an output folder.
3. Fill in the names, UTC date and exposure in ms. Leave prediction fields blank if unavailable.
4. Set **CSV frame at source index 0** from the actual recording/export: e.g. `1500` if the first image corresponds to CSV frame 1500. Do not assume it is zero. LC cutouts use embedded frame IDs.
5. Optionally enter target pixel X Y (zero based); otherwise the initial position is read from CSV. The main-form marker does not track motion. Choose output language and press **Generate**.
6. Open the result folder and inspect the PNG, then play the GIF/MP4. Check the target position and simultaneous fading in the curve and image. The auto-detected low interval is only a visualization estimate; use **First/last low frames** to specify it when needed.

This form aligns images by frame index. It does **not** perform the strict native timestamp audit below. FITS cubes can be used here; strict configuration mode requires individually timed images. Rendering uses one fixed brightness stretch across the clip, so fading is not hidden by per-frame auto-contrast.

## 4. PyMovie / PyOTE: configure, verify, render

Copy [examples/native_single.json](examples/native_single.json) into your event folder. It is a template, not a runnable example dataset. Edit it in a text editor:

1. Replace `curve` and `source` with your real CSV and recording paths. Relative paths are resolved against the JSON's folder, including `output_root`.
2. Set `target_column` to the exact CSV name, e.g. `signal-target`. Required columns are `FrameNum`, `timeInfo` and the selected signal column; the header begins with `FrameNum,`. Saved signal values are already net counts and are used unchanged. At least three samples with increasing integer frame IDs and UTC are required; fractional/integrated frame IDs are rejected.
3. Set `date_utc`, `start_utc`, `end_utc`, `exposure_s`, both applicable timestamp conventions, and `source_first_frame`. Use UTC, not local clock time. Choose `step_s >= 0.01`; the displayed timeline must contain 2–2,000 frames. This changes display sampling, not the saved photometry.
4. Set `mapping_tolerance_s` from actual timestamp precision. The example's 1 ns tolerance is intentionally strict and is not a universal recording setting. SER needs its timestamp trailer; FITS needs per-image UTC. Do not enlarge tolerance to conceal an unexplained offset.
5. **If no PyOTE fit is available, remove `pyote_result`** from the template. Curves and images still render without an event overlay. For saved fits, use the contract below.
6. Verify first, then render (replace the path with your edited JSON):

```bash
python launch.py --media-config "/path/to/event/media.json" --verify-only
python launch.py --media-config "/path/to/event/media.json"
```

Alternatively choose **PyMovie / four-station JSON…** in the app, select your edited JSON, then choose an output folder. This button uses JSON settings independently of the Tangra form. For four stations start from [four_stations.json](examples/four_stations.json); all rows share absolute UTC, with unavailable images blank.

### What counts as a supported PyOTE result?

`native_results.json` is the saved native-result schema used by our reduction workflow, **not an arbitrary PyOTE report, XLSX, log or screenshot**. The filename itself is not significant. Required JSON fields are `timesAreValid: true`, `Dframe`, `Rframe`, `Dtime`, `Rtime`; `mode` defaults to `raw` and must match `native_mode`. D/R mean disappearance/reappearance. Times are numeric seconds from UTC midnight; frames refer to the same curve. Optional `xlsxDict.Derr95/Rerr95` are retained as provenance. Both boundaries must fall within the curve and agree with their frame times. Do not fabricate a JSON from guessed values.

For independently reported boundaries, omit `pyote_result` and supply both `D_utc` and `R_utc` as full UTC ISO timestamps; optionally supply `timing_source_file`. Saved D/R is displayed without re-fitting or applying another half-exposure correction. D-only/R-only fits are not supported by this overlay.

For saved C3/C4 products, point `curve` to `native_analysis.csv`, set the corresponding `native_mode`, and supply that mode's result JSON. Use the original `pymovie_native.csv` as `tracking_csv` if the analysis CSV lacks centroids. Tracking columns are `xcentroid-<target>`, `ycentroid-<target>` and optional `hit-defect-<target>`. Tracking and analysis frame/UTC identities must match exactly. No normalization or detrending is performed here.

See [the full configuration and UTC contract](docs/native_station_media.md) for Tangra JSON inputs, acquisition corrections, byte order, partial FITS coverage and all fields.

## 5. Find and check the results

Each run gets a new output directory. Expect GIF, PNG preview and MP4 (unless disabled in the Tangra form), separately for requested languages. Configuration runs also save contact sheets, resolved configuration, source snapshot, input hashes and timestamp evidence in `media_metadata.json` / `run_metadata.json`. `--verify-only` writes audit products, not animations. Desktop jobs retain `run.log` and `result.json`; configuration media is inside their `media` subfolder.

| Problem | What to check |
| --- | --- |
| File not found | Replace all template paths; check paths relative to the JSON location |
| Missing column/header | Use the original supported CSV export, not a reformatted spreadsheet; check exact target name |
| UTC/frame mismatch | First-sample date, exposure units, start/mid/end convention, source frame ID and known camera delay |
| SER/FITS lacks UTC | Supply the original timed source; strict mode cannot invent timestamps |
| Saved times invalid / wrong mode | Supply the matching saved fit or omit `pyote_result` |
| Blank station image | Recording may not cover the selected UTC; inspect timestamp audit |
| Target marker wrong | Correct X Y in the Tangra form, or provide matching native tracking columns |
| Generation failed | Read `run.log` and failed run metadata before retrying |

These products visualise recorded data; clock agreement does not independently establish clock accuracy or a formal timing measurement.

## Development and builds

```bash
python -m unittest discover -s tests -v
python launch.py --self-test
python -m pip install -e ".[build]"
```

Run `Build-Windows.bat` or `Build-Mac.command` to test and build. Packaging alone: `python package_windows_only.py` on Windows, or `python -m PyInstaller --noconfirm --clean OccultationVisualiser.spec` on Mac. New package names require a new build; no binary is regenerated by editing this README. GitHub Actions supports manual builds and release tags. See [THIRD_PARTY.md](THIRD_PARTY.md) for licenses.
