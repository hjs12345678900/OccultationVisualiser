# OccultationVisualiser

OccultationVisualiser creates synchronized videos of asteroid occultations from existing light curves and recorded star-field frames. It supports one to eight observing stations on a shared UTC timeline, with light curves on the left and images on the right.

[Download the latest release](https://github.com/hjs12345678900/OccultationVisualiser/releases/latest) · [简体中文](README.zh-CN.md) · [Configuration reference](docs/native_station_media.md)

## Download and open

Standalone packages include the runtime, fonts and video encoder. Python, Tangra, PyMovie and PyOTE do not need to be installed to open the app and render exported observations.

| Platform | Start |
| --- | --- |
| Windows 10/11 x64 | Extract the whole Windows ZIP, then open `OccultationVisualiser.exe`. Keep the `_internal` folder beside it. |
| macOS 14+, Apple Silicon (M series) | Download `OccultationVisualiser-macOS-Apple-Silicon.zip`, extract it and open `OccultationVisualiser.app`. Runs natively; Rosetta is not required. |
| macOS 14+, Intel | Download `OccultationVisualiser-macOS-Intel.zip`, extract it and open `OccultationVisualiser.app`. |

The macOS package is not Apple-notarized.

## Prepare your files

For an animation, choose a light curve and its matching original recording. Keep the observation files in their existing folder.

| Light curve | Matching images |
| --- | --- |
| Tangra CSV | AVI (explicit frame mapping), ADV2, SER, RAVF, timed FITS sequence, or matching Tangra LC target stamps |
| Tangra LC with recorded times | Original recording, or the target stamps embedded in the LC file |
| PyMovie CSV or native `.pymovie` v1 | AVI (explicit frame mapping), original ADV2, SER, RAVF or timed FITS sequence |
| Saved C3/C4 analysis CSV | Original recording; optionally the original tracking CSV if positions are absent |

Tangra CSV uses target object 1. PyMovie uses the selected `signal-<target>` column. LC stamps contain the recorded 35×35 target cutout; choose the original recording for a full-field view.

AVI is supported through the bundled FFmpeg decoder. Supply the curve frame ID corresponding to AVI frame 0 and choose the curve timestamp convention; the app never derives absolute UTC or exposure from container FPS. Keep original frame order: edited, integrated or frame-dropped copies need a separately validated frame map and are not supported. AVI timing comes from the curve and is marked as having no independent source UTC verification. MP4 input remains unsupported. FITS sequences need per-frame UTC records. For PyOTE, put `fit_metrics.txt` or `<name>.pyote_log.txt` in **Native PyOTE result TXT**; put the original PyMovie CSV or processed `<name>.pyote.csv` in **Light curve**. No JSON export or renaming is needed. The app imports saved D/R and `B/sigmaB` without refitting. Logs also retain recorded block integration and 95% timing errors. If several fits match the target and curve filename, select the one-based **PyOTE fit record** in Advanced. Legacy adapter JSON remains supported. See the [configuration reference](docs/native_station_media.md).

## Image brightness and native PyMovie files

In the station editor, **Image brightness** controls display only. Auto AVI
estimates fixed 0.5/99.99 percentile levels from the upper 85% of the first
visible frame, avoiding bottom timestamp captions; the complete frame remains
visible. Other sources retain whole-field automatic levels. Choose legacy
whole-field auto or manual decoded-pixel black/white values and strength
(0 = linear, default 8) when preferred. Photometry and D/R remain unchanged.

Native binary `.pymovie` aperture files (format v1) are accepted in **Light curve**,
with the matching original AVI/SER/etc. in **Images**. Saved intensity is already
background subtracted; the importer preserves it, frame IDs and UTC. It does
not treat the binary file as CSV text. Select `signal-<aperture>`; initial header
positions are static, so use a matching original tracking CSV for moving targets.
Exposure still requires independent metadata or an explicit override. Field-mode
half-frame records are currently rejected with a clear message.

Image selection uses saved sampling cadence as a conservative display support,
separately from exposure; block-integrated/sparse curves no longer become blank
just because their sample interval exceeds one camera exposure. Images retain
their actual frame/UTC labels. Recording boundaries and long gaps remain blank.
An entirely empty image selection raises an error with UTC/frame-map checks.

## Make your first video

1. Enter the asteroid name, target star and observation date in UTC. Choose an output folder.
2. Click **Add station** and select its curve and images. Check the suggested target column. Exposure is read automatically from recorded metadata.
3. Choose the time range and playback settings below.
4. Click **Verify timestamps** to check agreement between the recorded image and curve times.
5. Click **Generate**, then **Open output folder** to view the MP4, GIF and PNG previews.

Each station has a separate optional **Observer** field. Edit it below the station name; supplied credits appear above that station’s light curve and are saved in project/configuration files and media metadata. Blank credits are hidden. Observer names do not affect path ordering or map labels.

Each station also has an optional **Station color** field. Use **Choose color…**, enter `#RRGGBB`, or leave it blank for automatic assignment. **Automatic** clears a manual choice. The same color follows the station through sorting and appears in curves, image labels/borders and map markers/legend; projects preserve the choice.

Use **Save project / Open project** to reuse inputs. The top-right **中文 / English** selector changes the interface language; **Export language** independently chooses Chinese, English or both for the media.

### Time range and playback

| Setting | Meaning |
| --- | --- |
| Full recording coverage | Use the saved curves' recording range. No typed start/end UTC or D/R is required. |
| D/R event windows | Keep a selected number of seconds before disappearance D and after reappearance R. Default padding is 5 seconds (new project default). Each station needs saved or supplied D/R. |
| Custom start/end UTC | Crop the displayed video, for example 09:54:20–09:54:45 UTC. Across midnight, include the end date: `2026-09-13T00:00:10`. |
| Accelerate gaps | Default: traverse the entire UTC gap at 50× speed, with continuous shadow motion; D/R windows remain at normal speed. The multiplier is adjustable. Shading, double slashes and a speed label mark the compressed interval on the UTC axis. |
| Skip gaps | Omit gaps between retained recording/event windows. The clock still shows absolute UTC; axis breaks mark the jump. |
| Real event speed | Play retained intervals at their recorded time scale. |
| Set total video duration | Rescale playback to the chosen length, such as 20 seconds. Recorded UTC and D/R remain unchanged. |

Choose **Path north side → south side** to arrange stations by signed transverse distance to the predicted path. Import prediction elements even if the map is disabled. **Latitude north → south** remains a separate option.

Stations are synchronized by absolute UTC. A station without an image at the displayed time stays blank. MP4 duration is quantized to 25 fps; GIF duration uses centiseconds.

### Optional inputs

Coordinates, altitude and prediction are optional for one or several stations. **North → south** sorts known locations and places unknown locations last. Supply latitude and longitude together if used.

PyOTE results are optional for full-recording media. D/R can instead be entered in **Advanced**. Prediction is a separate label and is not a measured event boundary.

The first-frame field is an optional **Advanced** mapping override for cropped recordings. By default, original UTC matches images to curve samples. It does not set the video's displayed start time.

Exposure comes from FITS/ADV/RAVF/LC, PyMovie shutter metadata or CameraSettings. SER timestamps describe cadence, not exposure. If no exposure record exists, select CameraSettings or use the advanced exposure override. Older projects retain their explicit overrides.

**Curve type** describes already-exported data: `raw` means original target counts; supported `C3/C4` exports were normalized using the corresponding reference star. Auto reads the legacy adapter JSON mode; native TXT has no C3/C4 flag, so select the matching exported curve type explicitly when needed. Use a matching analysis CSV and result for C3/C4. The app imports these values without extracting photometry, normalizing or refitting.

## Optional synchronized shadow map

Below the job log, enable **Add synchronized map below video/GIF results**, then
open **Prediction elements**. Choose one `.occelmnt`/XML event or paste its full
XML. An example Altona prediction is included in `examples/`.

Choose **Map view**: **Full shadow path** (default) keeps the whole clip's path
and stations in view; **Follow asteroid** keeps the shadow center in the middle
as geography and stations move past. Follow mode uses a fixed zoom throughout
the clip. The choice is saved with the project and applies to MP4, GIF and PNG.

The exported video adds a full-width map below the curves/images. Geography
is reprojected along the shadow path so motion runs left to right. The viewport
zooms to the shadow corridor, and the dark circular silhouette moves at the
displayed UTC. Colored station dots and the compact legend match the curve rows;
there is no information sidebar. Major-city labels and a geographic north arrow follow the same rotated projection.
The two explanatory lines below the station rows are removed. The map renders
offline from bundled Natural Earth coastlines and cities.

`station_path_order.json` records north-positive nominal path offsets (km) and each station’s predicted closest-approach UTC. The calculation includes Earth rotation and does not use measured D/R to align stations.

`shadow_frame_positions.csv` gives positions for every verified original frame,
including corrected curve UTC and separate source UTC. `shadow_simulation.json`
records the prediction and model. Simulation does not change photometry, D/R,
clock corrections or playback UTC. Nominal coverage excludes prediction/shape
uncertainty; it is not an observed occultation classification.

## Noise diagnostics

**Noise diagnostics** reads saved curves without decoding images. It displays saved and guarded-baseline SNR separately, along with exposure, binning, camera evidence and available background/mask statistics.

Baseline SNR is `B / sigmaB`. Native TXT noise describes PyOTE fitted readings, which may be integrated; labels identify the fit and recorded integration size. It is not automatically the original camera-frame SNR. Curve diagnostics use the saved curve sampling. The diagnostic baseline excludes D−1 s through R+1 s by default; this guard is independent of video padding. Missing D/R leaves identified-baseline statistics unavailable.

Select two stations to compare their shared absolute UTC baseline. Recordings without overlap are marked unavailable. The spatial-background budget is approximate and does not isolate detector read noise; definitions and assumptions are saved in `quality_report.json`.

## Outputs and troubleshooting

Each run creates a new directory. Animation runs save MP4, GIF and PNG previews. Configuration runs also save `resolved_config.json`, `media_metadata.json`, `run_metadata.json`, source snapshots, input hashes and quality reports. Desktop jobs retain `run.log` and `result.json`, with results in the `media` subfolder.

| Problem | Check |
| --- | --- |
| Exposure not found | Original recording headers, matching CameraSettings, or the advanced override |
| UTC mismatch | Observation date, start/midpoint convention and already-applied camera offsets |
| PyOTE mode mismatch | Matching analysis curve and result file |
| Blank station image | Recording coverage and timestamp audit records |
| Wrong target marker | Target column, original tracking CSV or advanced target X/Y |
| Generation failed | The job's `run.log` and failed-run metadata |

See [supported fields and UTC conventions](docs/native_station_media.md) for detailed timing, source formats and result-file requirements.

## Run from source

Use Python 3.13 with Tk support. In the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python launch.py
```

On Windows, use `py -3.13 -m venv .venv` and `.venv\Scripts\activate` for the first two commands. Check Tk with `python -m tkinter`.

For a saved station configuration:

```bash
occultationvisualiser --media-config project.json
occultationvisualiser --media-config project.json --verify-only
occultationvisualiser --media-config project.json --quality-only
```

## Development

```bash
python -m unittest discover -s tests -v
python launch.py --self-test
python -m pip install -e ".[build]"
```

Run `Build-Windows.bat` or `Build-Mac.command` on the target platform. The Mac script builds for the running Python architecture (arm64 on M-series Macs). To explicitly build Intel, run `python3 build_tools/create_macos_env.py --architecture x86_64` with a universal2 Python. Apple Silicon builds compile the included, pinned ADVCore source and include its MPL notice; ADV2 support is native too. Source-only ARM runs can use `python build_tools/prepare_adv_bundle.py` followed by `PYTHONPATH=build_vendor python launch.py`. The supported build runtime is Python 3.13 with Tcl/Tk 8.6; the drag-and-drop dependency is pinned to its compatible version. Release tags trigger Windows/macOS packaging and frozen-app self-tests through GitHub Actions. Archives include both user guides, example configurations and artwork.

See [CHANGELOG.md](CHANGELOG.md) for releases and [THIRD_PARTY.md](THIRD_PARTY.md) for dependency licenses. The previous `occultation-media` commands and Python import `occultation_media` remain compatible.

### Input help / 输入提示

Hover over an input or its label for a moment (or focus it with Tab) to see supported formats, required/optional conditions and where to find the file. Help follows the UI language. Press Escape or move away to dismiss.

将鼠标停在输入框或标签上片刻（也可按 Tab 聚焦），即可查看支持格式、必填/可选条件以及文件所在位置。提示随界面中英文切换；移开鼠标或按 Esc 关闭。

The interface starts in English. Use the top-right language selector for Chinese; opening a saved project restores its saved interface language.
界面默认英文；右上角可切换中文，打开项目时恢复项目保存的界面语言。
