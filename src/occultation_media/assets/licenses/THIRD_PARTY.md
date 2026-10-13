# Third-party components

The application bundles or uses the following open-source projects; their
licenses continue to apply independently of this project's own source.

- Python / Tk: https://www.python.org/psf/license/ and https://www.tcl.tk/software/tcltk/license.html
- NumPy: https://github.com/numpy/numpy (BSD)
- Pillow: https://github.com/python-pillow/Pillow (HPND)
- Astropy / PyERFA: https://github.com/astropy/astropy (BSD) and https://github.com/liberfa/pyerfa
- Adv2: https://pypi.org/project/Adv2/1.2.0/ and https://github.com/AstroDigitalVideo/ADVlib
- ADVCore (MPL-2.0): https://github.com/AstroDigitalVideo/ADVCore/tree/bbcda85214540c2e8996b7715887c358f68141cd
  Apple Silicon builds use this unmodified revision. The complete `src/` and license
  are included in `assets/licenses/ADVCore/source.tar.gz`; its SHA-256 is
  `6f731f7ff558edb4daeb825fc16f8211e2e352f0c5c02b0a2127c1932769d02b`.
  A readable license and corresponding source travel with the frozen app.
- tkinterdnd2 / TkDND: https://github.com/pmgagne/tkinterdnd2 (MIT).
  Version 0.4.2 supplies a Tcl/Tk 8.6-compatible arm64 drag-and-drop binary.
- RAVF: https://github.com/ChasinSpin/ravf (MIT)
- OpenCV: https://github.com/opencv/opencv and https://github.com/opencv/opencv-python
- imageio-ffmpeg: https://github.com/imageio/imageio-ffmpeg (BSD); the supplied FFmpeg
  executable has its own license/configuration. Build scripts and corresponding
  upstream source references: https://github.com/imageio/imageio-binaries/tree/master/ffmpeg
  FFmpeg source: https://ffmpeg.org/download.html
- Noto Sans CJK: https://github.com/notofonts/noto-cjk (SIL Open Font License).
  Font and full OFL text are included in `src/occultation_media/assets/fonts/`.
- Natural Earth country polygons (public domain): https://www.naturalearthdata.com/about/terms-of-use/
  World outlines use 1:110m; Australia/New Zealand use 1:10m. Asset provenance is in `assets/maps/SOURCE.txt`.
- PyInstaller: https://pyinstaller.org/en/stable/license.html (GPL with the bundling exception).

The build records installed package license files alongside the bundled assets.
Before public redistribution, retain these notices and the relevant bundled
licenses. No observational data is included in the application package.

Natural Earth populated-place labels (public domain): cities.json is reduced from
[10m populated places](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-populated-places/)
using source names, latitude/longitude, scalerank and population; all 7,342 places are retained.
