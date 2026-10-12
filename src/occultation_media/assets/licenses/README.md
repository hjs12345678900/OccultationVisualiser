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
| Tangra CSV | ADV2, SER, RAVF, timed FITS sequence, or matching Tangra LC target stamps |
| Tangra LC with recorded times | Original recording, or the target stamps embedded in the LC file |
| PyMovie CSV | Original ADV2, SER, RAVF or timed FITS sequence |
| Saved C3/C4 analysis CSV | Original recording; optionally the original tracking CSV if positions are absent |

Tangra CSV uses target object 1. PyMovie uses the selected `signal-<target>` column. LC stamps contain the recorded 35×35 target cutout; choose the original recording for a full-field view.

AVI/MP4 are not supported as observation inputs. FITS sequences need per-frame UTC records. Compatible saved PyOTE result JSON can supply D/R; the supported schema is described in the [configuration reference](docs/native_station_media.md).

## Make your first video

1. Enter the asteroid name, target star and observation date in UTC. Choose an output folder.
2. Click **Add station** and select its curve and images. Check the suggested target column. Exposure is read automatically from recorded metadata.
3. Choose the time range and playback settings below.
4. Click **Verify timestamps** to check agreement between the recorded image and curve times.
5. Click **Generate**, then **Open output folder** to view the MP4, GIF and PNG previews.

Use **Save project / Open project** to reuse inputs. The top-right **中文 / English** selector changes the interface language; **Export language** independently chooses Chinese, English or both for the media.

### Time range and playback

| Setting | Meaning |
| --- | --- |
| Full recording coverage | Use the saved curves' recording range. No typed start/end UTC or D/R is required. |
| D/R event windows | Keep a selected number of seconds before disappearance D and after reappearance R. Default padding is 10 seconds. Each station needs saved or supplied D/R. |
| Custom start/end UTC | Crop the displayed video, for example 09:54:20–09:54:45 UTC. Across midnight, include the end date: `2026-09-13T00:00:10`. |
| Skip gaps | Omit gaps between retained recording/event windows. The clock still shows absolute UTC; axis breaks mark the jump. |
| Real event speed | Play retained intervals at their recorded time scale. |
| Set total video duration | Rescale playback to the chosen length, such as 20 seconds. Recorded UTC and D/R remain unchanged. |

Stations are synchronized by absolute UTC. A station without an image at the displayed time stays blank. MP4 duration is quantized to 25 fps; GIF duration uses centiseconds.

### Optional inputs

Coordinates, altitude and prediction are optional for one or several stations. **North → south** sorts known locations and places unknown locations last. Supply latitude and longitude together if used.

PyOTE results are optional for full-recording media. D/R can instead be entered in **Advanced**. Prediction is a separate label and is not a measured event boundary.

The first-frame field is an optional **Advanced** mapping override for cropped recordings. By default, original UTC matches images to curve samples. It does not set the video's displayed start time.

Exposure comes from FITS/ADV/RAVF/LC, PyMovie shutter metadata or CameraSettings. SER timestamps describe cadence, not exposure. If no exposure record exists, select CameraSettings or use the advanced exposure override. Older projects retain their explicit overrides.

**Curve type** describes already-exported data: `raw` means original target counts; supported `C3/C4` exports were normalized using the corresponding reference star. Auto reads the saved result's mode, otherwise uses raw. Use a matching analysis CSV and result for C3/C4. The app imports these values without extracting photometry, normalizing or refitting.

## Noise diagnostics

**Noise diagnostics** reads saved curves without decoding images. It displays saved and guarded-baseline SNR separately, along with exposure, binning, camera evidence and available background/mask statistics.

Baseline SNR is `B / sigmaB`, using per-exposure scatter. The diagnostic baseline excludes D−1 s through R+1 s by default; this guard is independent of video padding. Missing D/R leaves identified-baseline statistics unavailable.

Select two stations to compare their shared absolute UTC baseline. Recordings without overlap are marked unavailable. The spatial-background budget is approximate and does not isolate detector read noise; definitions and assumptions are saved in `quality_report.json`.

## Outputs and troubleshooting

Each run creates a new directory. Animation runs save MP4, GIF and PNG previews. Configuration runs also save `resolved_config.json`, `media_metadata.json`, `run_metadata.json`, source snapshots, input hashes and quality reports. Desktop jobs retain `run.log` and `result.json`, with results in the `media` subfolder.

| Problem | Check |
| --- | --- |
| Exposure not found | Original recording headers, matching CameraSettings, or the advanced override |
| UTC mismatch | Observation date, start/midpoint convention and already-applied camera offsets |
| PyOTE mode mismatch | Matching analysis curve and compatible result JSON |
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
