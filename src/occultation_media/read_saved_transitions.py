"""Use saved PyOTE D/R UTC without re-fitting or adding half an exposure."""
from pathlib import Path
import json
import numpy as np
from .utc_conventions import utc_ns


def saved_transitions(cfg, rows):
    """Return (D UTC[ns], R UTC[ns], provenance), or no overlay if absent.

    Native results require timesAreValid, integral-source frame identity and
    transition times agreeing with Dframe/Rframe within two exposures. Resolve
    each date independently near its original frame, including midnight.
    Explicit D_utc/R_utc are allowed only as a pair; supplied report values are
    retained without claiming native-fit precision or uncertainty.
    """
    if cfg.get('pyote_result'):
        path = Path(cfg['pyote_result'])
        result = json.loads(path.read_text())
        if result.get('timesAreValid') is not True: raise ValueError('Saved PyOTE times are invalid')
        if cfg.get('native_mode', 'raw') != result.get('mode', 'raw'):
            raise ValueError('Selected native curve mode differs from saved PyOTE result')
        times = []
        for edge in ('D', 'R'):
            frame, seconds = float(result[edge+'frame']), float(result[edge+'time'])
            if not np.isfinite([frame, seconds]).all() or not 0 <= seconds < 172800:
                raise ValueError('Invalid saved transition frame/time')
            row = min(rows, key=lambda r: abs(r.frame-frame))
            if not rows[0].frame <= frame <= rows[-1].frame:
                raise ValueError('Saved transition frame outside curve')
            day = row.utc.astype('datetime64[D]').astype('datetime64[ns]')
            value = day+np.timedelta64(round(seconds*1e9), 'ns')
            value = min((value+np.timedelta64(k,'D') for k in (-1,0,1)), key=lambda t:abs(t-row.utc))
            if abs(float((value-row.utc)/np.timedelta64(1,'s'))) > row.exposure_s*2:
                raise ValueError('Saved transition UTC disagrees with its curve frame')
            times.append(value)
        provenance = dict(method='saved native PyOTE D/R', path=str(path), mode=result.get('mode'),
                          errors95_s={e:result.get('xlsxDict',{}).get(e+'err95') for e in ('D','R')})
    elif cfg.get('D_utc') is not None or cfg.get('R_utc') is not None:
        times = [utc_ns(cfg[e+'_utc']) for e in ('D','R')]
        provenance = dict(method='supplied observation times', source=cfg.get('timing_source_file'))
    else: return None, None, dict(method='no saved D/R supplied')
    if not rows[0].utc < times[0] < times[1] < rows[-1].utc:
        raise ValueError('Saved D/R must be ordered inside the recording')
    return *times, provenance
