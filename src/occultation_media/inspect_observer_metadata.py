"""Read recorded exposure evidence for the desktop without estimating cadence."""
from pathlib import Path
import json
import re
import numpy as np


def positive(value):
    """Return positive finite seconds, rejecting absent/invalid exposure metadata."""
    value=float(value)
    if not np.isfinite(value) or value<=0:raise ValueError('Invalid recorded exposure')
    return value


def inspect_exposure(obs):
    """Return exposure seconds, evidence path and method, or None if unavailable.

    Actual source-frame exposure takes priority over command/settings metadata.
    SER has UTC cadence but no exposure-duration field: never equate those two.
    FITS uses EXPTIME seconds; ADV/RAVF use recorded nanoseconds; LC preserves
    recorded durations. Only one source frame is read for this input summary.
    All-frame UTC verification still runs separately before media generation.
    """
    source=Path(obs.get('source') or obs.get('curve') or '.').expanduser().resolve()
    curve=Path(obs.get('curve') or '.').expanduser().resolve()
    if source.exists():
        suffix=source.suffix.lower()
        if source.is_dir() or suffix in ('.fits','.fit','.fts'):
            from astropy.io import fits
            files=sorted([p for p in source.iterdir() if p.suffix.lower() in ('.fits','.fit','.fts')],key=lambda p:[int(v) if v.isdigit() else v for v in re.split(r'(\d+)',p.name)]) if source.is_dir() else [source]
            if files:
                header=fits.getheader(files[0],int(obs.get('fits_hdu') or 0))
                if 'EXPTIME' in header:return dict(exposure_s=positive(header['EXPTIME']),path=str(files[0]),method='FITS EXPTIME')
        elif suffix=='.lc':
            from .read_station_curves import read_lc_curve
            rows,_,_=read_lc_curve(source)
            return dict(exposure_s=positive(np.median([r.exposure_s for r in rows])),path=str(source),method='Tangra LC recorded exposure')
        elif suffix=='.adv':
            from .read_adv_frames import AdvSource
            reader=AdvSource(source,obs.get('adv_python') or None)
            record=reader._decode([0],None)['frames'][0]
            return dict(exposure_s=positive(record['exposure_ns']/1e9),path=str(source),method='ADV recorded exposure')
        elif suffix=='.ravf':
            from .read_ravf_frames import RavfSource
            reader=RavfSource(source)
            with source.open('rb') as stream:frame=reader.reader.frame_by_index(stream,0)
            return dict(exposure_s=positive(frame.exposure_duration/1e9),path=str(source),method='RAVF recorded exposure')
    if curve.is_file() and curve.suffix.lower()=='.csv':
        with curve.open(encoding='utf-8-sig') as stream:
            for line in stream:
                if line.startswith(('FrameNum,','FrameNo,')):break
                if line.startswith('#INSTRUMENT-SHUTTER:'):
                    return dict(exposure_s=positive(float(line.split(':',1)[1])/1e9),path=str(curve),method='PyMovie RAVF shutter metadata (ns)')
    settings=[Path(obs['camera_settings_file']).expanduser().resolve()] if obs.get('camera_settings_file') else [source.with_suffix('.CameraSettings.txt'),curve.with_suffix('.CameraSettings.txt')]
    for path in settings:
        if not path.is_file():continue
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            match=re.fullmatch(r'Exposure\s*=\s*([\d.eE+-]+)\s*(us|ms|s)',line.strip())
            if match:
                return dict(exposure_s=positive(float(match[1])*{'us':1e-6,'ms':1e-3,'s':1}[match[2]]),path=str(path),method='CameraSettings recorded setting')
    return None


def resolve_exposure(obs):
    """Resolve auto exposure or an explicit advanced override; retain evidence.

    Older projects with exposure_ms but no exposure_mode retain that explicit
    value. New projects default to auto and do not require a number to be typed.
    Failure identifies missing metadata rather than substituting frame cadence.
    """
    mode=obs.get('exposure_mode','manual' if obs.get('exposure_ms') else 'auto')
    if mode=='manual':return dict(exposure_s=positive(float(obs['exposure_ms'])/1000),method='explicit exposure override',path=None)
    result=inspect_exposure(obs)
    if result is None:raise ValueError('曝光记录缺失：请选择 CameraSettings 或在高级设置手动覆盖。 / No recorded exposure: select CameraSettings or use the advanced override.')
    return result


def resolve_native_mode(obs):
    """Read saved-result mode; raw/C3/C4 describe imported data, not new fitting."""
    chosen=obs.get('native_mode','auto')
    if chosen!='auto':
        if chosen not in ('raw','C3','C4'):raise ValueError('Unsupported saved curve mode')
        return chosen
    if obs.get('pyote_result'):
        result=json.loads(Path(obs['pyote_result']).expanduser().read_text(encoding='utf-8-sig'))
        mode=result.get('mode','raw')
        if mode not in ('raw','C3','C4'):raise ValueError('Unsupported saved curve mode')
        return mode
    return 'raw'
