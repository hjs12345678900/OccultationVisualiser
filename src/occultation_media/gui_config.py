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


def build_config(event, observers, quality_only=False):
    """Return JSON-safe configuration from shared fields and observer dicts.

    Exposure is read from metadata unless explicitly overridden in milliseconds;
    offsets/tolerances use seconds, detector coordinates zero-based pixels.
    Missing paths or unsupported values fail before
    a job is started. No source timestamps or photometry are changed here.
    """
    if not observers: raise ValueError('Add an observer / 请添加观测者')
    if len(observers)>8: raise ValueError('Maximum 8 observers / 最多 8 位观测者')
    if not event['event'].strip() or not event['target'].strip():
        raise ValueError('Enter event and target / 请填写事件及目标星')
    date = event['date_utc'].strip()
    window={'D/R 周围':'dr','手动 UTC':'manual','完整录制范围':'full'}.get(event.get('window_mode'),event.get('window_mode','manual'))
    playback={'真实时间':'real_time','指定时长':'fixed_duration'}.get(event.get('playback_mode'),event.get('playback_mode','real_time'))
    order={'路径北侧 → 南侧':'path_north_to_south','北 → 南':'north_to_south','输入顺序':'input'}.get(event.get('station_order'),event.get('station_order','input'))
    skip=event.get('skip_gaps',False)
    gap_mode={'加速空档':'accelerate','跳过':'skip','保留':'keep'}.get(skip,skip) if isinstance(skip,str) else ('skip' if skip else 'keep')
    if isinstance(skip,str):
        if gap_mode not in ('skip','keep','accelerate'): raise ValueError('Choose skip, keep or accelerate gaps')
        skip=skip in ('跳过','skip')
    start, stop = ((full_utc(date,event[k]) for k in ('start_utc','end_utc')) if window=='manual' and not quality_only else ('',''))
    step = number(event,'step_s')
    import numpy as np
    if window not in ('manual','dr','full') or playback not in ('real_time','fixed_duration'):
        raise ValueError('Choose window and playback mode')
    if step < .01 or (window=='manual' and not quality_only and utc_ns(stop)<=utc_ns(start)): raise ValueError('Check UTC window and display step')
    if window=='manual' and gap_mode=='keep' and not quality_only:
        count = int((utc_ns(stop)-utc_ns(start))/np.timedelta64(1,'ns'))//round(step*1e9)+1
        if not 2<=count<=2000: raise ValueError('Choose 2–2000 displayed frames / 调整时间范围或显示间隔')
    if not event['output_root'].strip(): raise ValueError('Choose output folder / 请选择输出目录')
    cfg = dict(event=re.sub(r'[^\w .()-]','_',event['event'].strip()),target=event['target'].strip(),
               date_utc=date,start_utc=start,end_utc=stop,step_s=step,language=event['language'],
               output_root=str(Path(event['output_root']).expanduser().resolve()),alignment='absolute_utc',stations=[])
    cfg.update(window_mode=window,event_padding_s=number(event,'event_padding_s',5),skip_gaps=skip,
               playback_mode=playback,station_order=order)
    cfg['gap_mode']=gap_mode
    if gap_mode=='accelerate':
        cfg['gap_speed']=number(event,'gap_speed',50)
        if cfg['gap_speed']<=1:raise ValueError('Gap acceleration must be greater than 1x')
    if cfg['event_padding_s']<0: raise ValueError('D/R padding must be nonnegative / 前后秒数不能为负')
    if playback=='fixed_duration':
        cfg['video_duration_s']=number(event,'video_duration_s')
        if cfg['video_duration_s']<.04: raise ValueError('Video duration must be >=0.04 seconds')
    for obs in observers:
        from .inspect_observer_metadata import resolve_exposure,resolve_native_mode
        station = dict(name=obs['name'].strip(),native_mode=resolve_native_mode(obs))
        if not station['name']: raise ValueError('Station name required / 请填写站点名称')
        if obs.get('pyote_fit_index','').strip():
            station['pyote_fit_index']=int(obs['pyote_fit_index'])
            if station['pyote_fit_index']<1:raise ValueError('PyOTE fit record must be >=1 / 拟合记录须从 1 开始')
        observer=obs.get('observer','').strip()
        if observer:station['observer']=observer
        from .resolve_station_colors import normalize_color
        color=normalize_color(obs.get('color'))
        if color:station['color']=color
        for key in ('curve','source','pyote_result','tracking_csv','timing_source_file','adv_python','camera_settings_file'):
            if obs.get(key,'').strip():
                path=Path(obs[key]).expanduser().resolve()
                if not path.exists(): raise ValueError(f'{station["name"]}: file not found: {path}')
                station[key]=str(path)
        required=('curve',) if quality_only else ('curve','source')
        if not all(k in station for k in required): raise ValueError('Choose curve and source / 请选择曲线及影像')
        kind = 'tangra_lc' if Path(station['curve']).suffix.lower()=='.lc' else ('tangra_csv' if obs['mode']=='Tangra' else 'pymovie_csv')
        source_path=Path(station.get('source',station['curve']))
        suffix = source_path.suffix.lower()
        exposure=resolve_exposure(obs)
        station.update(curve_format=kind,exposure_s=exposure['exposure_s'],exposure_evidence=exposure,
                       target_column=obs.get('target_column','signal-target').strip(),
                       source_first_frame=int(obs['source_first_frame']) if obs.get('source_first_frame') not in (None,'','auto') else 'auto',
                       timestamp_reference='midpoint' if kind.startswith('tangra') or suffix=='.adv' else 'start',
                       source_timestamp_reference='start',timing_policy=TIMING_NOTE,
                       mapping_tolerance_s=number(obs,'mapping_tolerance_s',.001),
                       source_minus_curve_s=number(obs,'source_minus_curve_s',0),
                       ser_byte_order=obs.get('ser_byte_order','header'))
        if suffix=='.avi':
            reference=obs.get('avi_timestamp_reference','auto')
            if kind=='tangra_lc':reference='midpoint'
            if reference not in ('start','midpoint','end'):
                raise ValueError('AVI: choose the saved curve timestamp convention / 请选择 AVI 曲线时标基准')
            station['timestamp_reference']=reference
            first=station['source_first_frame']
            if not quality_only and (not isinstance(first,int) or first<0):
                raise ValueError('AVI: supply curve frame ID at source index 0 / 请填写 AVI 第 0 帧对应的曲线帧号')
            if not quality_only and station['source_minus_curve_s']!=0:
                raise ValueError('AVI cannot independently verify a source clock offset; use zero')
            station['timing_policy']='AVI explicit frame identity; UTC from saved curve; no independent source clock'
        if kind=='pymovie_csv' and (source_path.is_dir() or suffix in ('.fits','.fit','.fts')):
            from astropy.io import fits
            source=source_path
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
        for key in ('latitude_deg','longitude_deg','altitude_m'):
            if str(obs.get(key,'')).strip(): station[key]=number(obs,key)
        if window=='dr' and not quality_only and 'pyote_result' not in station and 'D_utc' not in station:
            raise ValueError(f'{station["name"]}: D/R window requires PyOTE results or D/R')
        cfg['stations'].append(station)
    from .plan_station_timeline import order_stations
    from .read_occult_prediction import form_settings, load_prediction, enabled
    path_order=order=='path_north_to_south'
    settings=form_settings({**event,'shadow_enabled':'1'} if path_order else event,
                           quality_only and not path_order)
    geometry=load_prediction(settings,date)[0] if path_order else None
    if path_order:settings['enabled']=enabled(event.get('shadow_enabled',False))
    if settings['enabled'] or path_order:cfg['shadow_simulation']=settings
    cfg['stations']=[s['config'] for s in order_stations([dict(config=c) for c in cfg['stations']],order,geometry)]
    return cfg
