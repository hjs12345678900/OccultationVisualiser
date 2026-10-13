"""Preserve old scientific overrides while translating saved GUI choices."""
CHOICES={
 'window_mode':{'D/R 周围':'dr','手动 UTC':'manual','完整录制范围':'full'},
 'skip_gaps':{'跳过':'skip','保留':'keep','加速空档':'accelerate'},
 'playback_mode':{'真实时间':'real_time','指定时长':'fixed_duration'},
 'station_order':{'北 → 南':'north_to_south','输入顺序':'input'},
}


def migrate_project(data,defaults):
    """Return stable fields/observers; retain explicit exposure/frame overrides.

    gui_version=1 projects remain readable. Missing timeline fields in old
    files mean manual UTC/input order, rather than new full-range defaults.
    No curve, fit, UTC, coordinates or export-language values are recomputed.
    """
    if data.get('gui_version')!=1 or not isinstance(data.get('observers'),list) or len(data['observers'])>8:
        raise ValueError('Choose a saved GUI project')
    event=dict(data['event']);fallback=dict(window_mode='manual',station_order='input',skip_gaps='keep',playback_mode='real_time')
    for key,mapping in CHOICES.items():event[key]=mapping.get(event.get(key),event.get(key,fallback[key]))
    event.setdefault('gap_speed','50')
    event.setdefault('shadow_enabled','0')
    event.setdefault('shadow_view_mode','full_path')
    event.setdefault('shadow_prediction_file','')
    event.setdefault('shadow_xml','')
    if event['station_order']=='north_to_south' and event['shadow_enabled'] in (True,1,'1','True','true'):
        event['station_order']='path_north_to_south'
    observers=[]
    for original in data['observers']:
        o={k:str(original.get(k,v)) for k,v in defaults.items()}
        if 'exposure_mode' not in original:o['exposure_mode']='manual' if original.get('exposure_ms') else 'auto'
        observers.append(o)
    return event,observers
