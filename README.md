# OccultationVisualiser

**English** | [简体中文](README.zh-CN.md)

Turn an occultation observation into a synchronized star-field and light-curve animation (GIF, MP4 and PNG preview). An occultation is a star temporarily hidden by an intervening object. This tool visualises **existing photometry**; it does not extract a light curve from a video or run PyOTE fitting. No Tangra, PyMovie or PyOTE installation is needed to render already exported inputs.

Previously **OccultationMedia**. New builds use `OccultationVisualiser.app` / `OccultationVisualiser.exe` and the `occultationvisualiser` command. The Python import `occultation_media` and old `occultation-media` commands remain compatible. The GitHub repository is now OccultationVisualiser; existing local checkouts may retain the old folder name.

## GUI quick start (v1.8)

All inputs are available in the desktop window; writing JSON is not required.

1. Fill in the shared **event, target star, UTC date, display step** and output language. Choose **D/R windows** (10 seconds before D and after R by default) or **manual UTC**. Only manual mode requires start/end UTC; use a full date-time across midnight.
2. Choose or drop an output folder. **Add**, **Edit** (or double-click), and **Delete** manage 1–8 observers sharing absolute UTC.
3. In each observer editor, switch **Tangra / PyMovie–PyOTE**, then browse or drop the curve, image source and optional PyOTE result. Use the FITS-folder button or drop a whole sequence folder. Each file box accepts one file/folder at a time.
4. Set the observer name, exposure in milliseconds, original frame ID at source index 0, optional **Expected UTC**, and geographic latitude/longitude (north/east positive). **North → south** sorts by latitude and shows coordinates; altitude is optional. Verify the suggested PyMovie signal column if several targets exist.
5. **Advanced** contains supplied D/R, target coordinates, FITS HDU, SER byte order, known camera offset and UTC tolerance. There is no start/middle/end selector.
6. **Verify** checks inputs and native timestamps without encoding. **Generate** creates GIF, MP4 and PNG; use **Open output** to inspect media and timestamp audit records.
7. **Save / Open** retains shared event information and all observers as a GUI project. No JSON editing is needed. Each run separately saves its resolved configuration for reproducibility.

Choose **skip / keep gaps** and **real time / fixed duration** in the video settings. D/R windows require saved PyOTE results or supplied boundaries for every observer. Skipped gaps have `//` plot-axis marks and an absolute UTC clock jump. Source clocks and D/R remain unchanged; missing images inside retained windows stay blank. Fixed duration changes playback speed only; H.264 uses 25 fps (nearest 40 ms total duration), GIF uses centiseconds. Old GUI projects open in manual/input-order mode.

Station headers automatically show baseline per-exposure SNR (`B / sigmaB`). Saved PyOTE baseline parameters are preferred; otherwise calculate directly from valid saved exposures wholly outside supplied D/R. Tangra LC values are labelled `(LC baseline)`; other fallback curves are labelled as estimated. The statistic uses the full saved curve and is independent of video cuts. See [SNR definitions and provenance](docs/native_station_media.md#baseline-snr-labels).

**Noise diagnostics** opens a station table, capture/photometry details and a selectable station-pair scatter plot on shared UTC. This action needs curves and exposure conventions, with saved or supplied D/R to identify baselines; image sources and manual media start/end times are optional. **View report** reopens an existing `quality_report.json`. Saved-fit SNR and the separately calculated guarded baseline SNR are labelled separately. The diagnostic guard defaults to one second on either side of D/R, independent of video padding. Pair comparisons exclude both events and retain whole exposures within shared recording coverage; recordings without overlap are explicitly unavailable.

Camera/binning/gain metadata come from saved headers and nearby `CameraSettings.txt`, or a file selected in Advanced. Linear residual and adjacent-difference scatter are diagnostic statistics; they do not replace original counts or saved SNR. PyMovie spatial-background noise permits an approximate `sigma_pixel*sqrt(N_mask)` budget, assuming independent representative pixels. It is not isolated read noise and omits source shot noise and background-estimator uncertainty. C3/C4 count scaling disables the raw-pixel budget. Full definitions, selected frames and source hashes are saved with JSON/CSV; normal Generate/Verify also includes the report.

CLI: `occultationvisualiser --media-config project.json --quality-only`. Optional JSON `diagnostic_margin_s` adjusts the baseline guard; this mode does not audit source-image timestamps. Use Verify for that audit.

### Timestamp policy

For current SharpCap recordings, SER and FITS `DATE-OBS` mean exposure start and receive half an exposure for midpoint display. `DATE-AVG` and ADV are midpoint; RAVF uses its native start. PyMovie follows the image-source convention; Tangra CSV is interpreted as exported midpoint UTC. Saved PyOTE D/R is never shifted again.

The policy appears in the GUI and saved configuration. Source and curve UTC must still agree. Older SharpCap versions, externally retimed data or already-converted CSVs may differ: investigate mismatches rather than arbitrarily enlarging tolerance. [SharpCap author's explanation](https://forums.sharpcap.co.uk/viewtopic.php?t=9540).

### Input checklist

| Workflow | Files |
| --- | --- |
| Tangra full field | Photometry CSV (object 1) or timed LC curve + ADV2/SER/RAVF/timed FITS sequence |
| Tangra cutout | CSV or LC curve + matching LC image source; only the 35×35 recorded target stamp |
| PyMovie | CSV + original image source; optional original tracking CSV |
| PyOTE interval | Add compatible result JSON, or enter both D/R UTC in Advanced |

AVI/MP4 are not supported inputs. Screenshots, reports and CSV alone cannot provide recorded images. Strict timing mode does not accept FITS cubes without individual frame times.

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

Run `Build-Windows.bat` or `Build-Mac.command` to test and build. Packaging alone: `python package_windows_only.py` on Windows, or `python -m PyInstaller --noconfirm --clean OccultationVisualiser.spec` on Mac. Release archives include this guide, its Chinese translation and editable JSON templates beside the application. GitHub Actions supports manual builds and release tags. See [THIRD_PARTY.md](THIRD_PARTY.md) for licenses.
