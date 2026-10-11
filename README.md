# OccultationMedia

**English** | [简体中文](README.zh-CN.md)

A desktop tool for creating occultation animations. Synchronize recorded star fields with Tangra or saved PyMovie/PyOTE light curves and export GIF, PNG and MP4. Includes English and Chinese interfaces.

## Download and use

Download a package from [Releases](https://github.com/hjs12345678900/OccultationMedia/releases/latest):

- **Windows 10/11 x64:** extract the entire archive and open `OccultationMedia.exe`. Keep the `_internal` folder beside it.
- **macOS 14+:** extract and open `OccultationMedia.app`. Intel build; Apple Silicon requires Rosetta.

Select an observation file, a Tangra CSV and an output folder. Enter the date, exposure time and target names, then generate the animation. Predicted time and uncertainty are optional.

For native PyMovie/PyOTE or four observers, choose **PyMovie / four-station JSON…** and select a configuration based on [the examples](examples). [Configuration and UTC rules](docs/native_station_media.md) explain the required paths, exposures and saved D/R. Four curves appear on the left and matching full fields on the right. Every row uses the same absolute UTC; missing images stay blank.

## Features

- Inputs: ADV2, SER, FITS images / sequences / cubes, RAVF, and Tangra LC target cutouts.
- Uses Tangra CSV photometry and UTC. Set the CSV frame number corresponding to source frame 0 to align the data.
- Reads the initial target position from CSV, with a manual override. The marker has only right and lower arms; it does not track frame-by-frame motion.
- Fixes the display stretch using the first displayed frame's 0.5th and 99.95th percentiles throughout the animation.
- Native imports preserve saved net counts, per-frame tracking and raw/C3/C4 exports. Saved PyOTE D/R is displayed without fitting again or shifting by half an exposure.
- Configuration mode verifies original frame identity and exposure-midpoint timestamps before encoding, including SER 100-ns ticks, ADV acquisition-delay offsets, RAVF timing and partial FITS sequences. Metadata records every source/curve UTC residual and input hash.
- English and Chinese output; release packages include Python, Chinese fonts and FFmpeg.

For visualization, not formal occultation timing measurements. Desktop packages are unsigned / unnotarized. Build jobs run the test suite and frozen-application codec/font/native-timestamp self-tests; real Altona ADV/SER/FITS data are also verified locally.

## Run and build from source

Use Python 3.13 with Tk support. In a virtual environment:

```bash
python -m pip install -e ".[build]"
python launch.py
python launch.py --media-config examples/four_stations.json --verify-only
python launch.py --media-config examples/four_stations.json
```

Build entry points: `Build-Windows.bat` on Windows and `Build-Mac.command` on Mac. Both include tests.
For packaging only, use `python package_windows_only.py` on Windows or `python -m PyInstaller --noconfirm --clean OccultationMedia.spec` on Mac.
GitHub Actions builds are triggered manually or by release tags; verified packages are uploaded to the corresponding draft release. See [THIRD_PARTY.md](THIRD_PARTY.md) for third-party components and licenses.
