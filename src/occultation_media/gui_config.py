"""Translate desktop values into a reproducible station configuration.

SharpCap SER and FITS DATE-OBS use estimated exposure start; DATE-AVG is
midpoint. ADV/RAVF retain native conventions. See SharpCap's author statement:
https://forums.sharpcap.co.uk/viewtopic.php?t=9540
Tangra exported times are treated as midpoints; PyMovie follows the source.
All assumptions are saved and source/curve agreement is still verified.
"""
from pathlib import Path
import math
import re
from .utc_conventions import utc_ns

TIMING_NOTE = ('SharpCap SER / FITS DATE-OBS: exposure start → display +½ exposure. '
               'FITS DATE-AVG / ADV: midpoint; RAVF: start. '
               'Tangra CSV: exported midpoint; PyMovie: source convention. '
               'Saved PyOTE D/R unchanged. 原始时标仍须通过核验。')


def number(values, key, default=None):
    """Read a finite numeric form field; blanks use only an explicit default."""
    value = values.get(key, '')
    result = float(value if str(value).strip() else default)
    if not math.isfinite(result):
        raise ValueError(f'{key}: requires a finite number / 需要有限数值')
    return result


def full_utc(date, value):
    """Validate UTC date-time, accepting a clock appended to the event date."""
    value = value.strip()
    if not value: raise ValueError('UTC time is required / 请填写 UTC 时刻')
    if 'T' not in value: value = date + 'T' + value
    return str(utc_ns(value))


def build_config(event, observers):
    """Return JSON-safe configuration from shared fields and observer dicts.

    Exposure inputs are milliseconds, offsets/tolerances seconds, coordinates
    zero-based detector pixels. Missing paths or unsupported values fail before
    a job is started. No source timestamps or photometry are changed here.
    """
    if not observers: raise ValueError('Add an observer / 请添加观测者')
    if len(observers)>8: raise ValueError('Maximum 8 observers / 最多 8 位观测者')
    if not event['event'].strip() or not event['target'].strip():
        raise ValueError('Enter event and target / 请填写事件及目标星')
    date = event['date_utc'].strip()
    start, stop = (full_utc(date,event[k]) for k in ('start_utc','end_utc'))
    step = number(event,'step_s')
    import numpy as np
    if step < .01 or utc_ns(stop)<=utc_ns(start): raise ValueError('Check UTC window and display step')
    count = int((utc_ns(stop)-utc_ns(start))/np.timedelta64(1,'ns'))//round(step*1e9)+1
    if not 2<=count<=2000: raise ValueError('Choose 2–2000 displayed frames / 调整时间范围或显示间隔')
    if not event['output_root'].strip(): raise ValueError('Choose output folder / 请选择输出目录')
    cfg = dict(event=re.sub(r'[^\w .()-]','_',event['event'].strip()),target=event['target'].strip(),
               date_utc=date,start_utc=start,end_utc=stop,step_s=step,language=event['language'],
               output_root=str(Path(event['output_root']).expanduser().resolve()),alignment='absolute_utc',stations=[])
    for obs in observers:
        station = dict(name=obs['name'].strip(),native_mode=obs.get('native_mode','raw'))
        if not station['name']: raise ValueError('Observer name required / 请填写观测者姓名')
        for key in ('curve','source','pyote_result','tracking_csv','timing_source_file','adv_python'):
            if obs.get(key,'').strip():
                path=Path(obs[key]).expanduser().resolve()
                if not path.exists(): raise ValueError(f'{station["name"]}: file not found: {path}')
                station[key]=str(path)
        if not all(k in station for k in ('curve','source')): raise ValueError('Choose curve and source / 请选择曲线及影像')
        kind = 'tangra_lc' if Path(station['curve']).suffix.lower()=='.lc' else ('tangra_csv' if obs['mode']=='Tangra' else 'pymovie_csv')
        suffix = Path(station['source']).suffix.lower()
        station.update(curve_format=kind,exposure_s=number(obs,'exposure_ms')/1000,
                       target_column=obs.get('target_column','signal-target').strip(),
                       source_first_frame=int(obs.get('source_first_frame','0')),
                       timestamp_reference='midpoint' if kind.startswith('tangra') or suffix=='.adv' else 'start',
                       source_timestamp_reference='start',timing_policy=TIMING_NOTE,
                       mapping_tolerance_s=number(obs,'mapping_tolerance_s',.001),
                       source_minus_curve_s=number(obs,'source_minus_curve_s',0),
                       ser_byte_order=obs.get('ser_byte_order','header'))
        if kind=='pymovie_csv' and (Path(station['source']).is_dir() or suffix in ('.fits','.fit','.fts')):
            from astropy.io import fits
            source=Path(station['source'])
            files=sorted(p for p in source.iterdir() if p.suffix.lower() in ('.fits','.fit','.fts')) if source.is_dir() else [source]
            if files:
                header=fits.getheader(files[0],int(obs.get('fits_hdu') or 0))
                if 'DATE-AVG' in header: station['timestamp_reference']='midpoint'
        if station['exposure_s']<=0 or station['mapping_tolerance_s']<0: raise ValueError('Check exposure/tolerance')
        for key in ('predicted_utc','D_utc','R_utc'):
            if obs.get(key,'').strip(): station[key]=full_utc(date,obs[key])
        if ('D_utc' in station)!=('R_utc' in station): raise ValueError('Supply both D and R / D 与 R 须同时填写')
        if obs.get('target_xy','').strip():
            xy=obs['target_xy'].replace(',',' ').split()
            if len(xy)!=2: raise ValueError('Target X Y requires two numbers')
            station['target_xy']=[float(v) for v in xy]
            if not all(math.isfinite(v) for v in station['target_xy']): raise ValueError('Invalid target X Y')
        if obs.get('fits_hdu','').strip(): station['fits_hdu']=int(obs['fits_hdu'])
        cfg['stations'].append(station)
    return cfg
