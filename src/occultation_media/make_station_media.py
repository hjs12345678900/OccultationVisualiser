"""Compose saved native/Tangra curves and verified images on absolute UTC."""
from datetime import datetime, timezone
from pathlib import Path
import json
import numpy as np
from .read_station_curves import read_station_curve
from .prepare_station_frames import StationFrames, nearest_sample
from .prepare_lc_frames import LCFrames
from .read_saved_transitions import saved_transitions
from .record_media_run import write_json, input_manifest, finish_record, sha256, snapshot_code
from .utc_conventions import utc_ns
from .render_station_panels import StationPanels
from .encode_station_media import encode_station_language


def load_config(path):
    """Resolve user-supplied JSON file paths relative to its location.

    One to eight stations, explicit absolute UTC window and timestamp rules.
    Relative files make shareable examples possible without embedding local data.
    """
    path = Path(path).expanduser().resolve()
    cfg = json.loads(path.read_text(encoding='utf-8'))
    if cfg.get('alignment') != 'absolute_utc' or not 1 <= len(cfg.get('stations',[])) <= 8:
        raise ValueError('Require one to eight stations and alignment=absolute_utc')
    for values in [cfg, *cfg['stations']]:
        for key in ('curve','source','output_root','pyote_result','tracking_csv','timing_source_file','adv_python'):
            if values.get(key):
                file = Path(values[key]).expanduser()
                values[key] = str((path.parent/file).resolve() if not file.is_absolute() else file.resolve())
    if cfg['language'] not in ('en','zh','both'): raise ValueError('Unsupported output language')
    return cfg


def make_station_media(config_path, output_dir=None, verify_only=False):
    """Return a new immutable run; verify_only audits every time without encoding.

    Missing real images remain blank. Native net ADU and saved PyOTE D/R remain
    unchanged. Explicit source offset validates already-corrected curve UTC.
    Hash original inputs and record all actual source/curve UTC residuals.
    """
    cfg = load_config(config_path)
    start, stop = (utc_ns(cfg[k]) for k in ('start_utc','end_utc'))
    step = float(cfg['step_s'])
    if not np.isfinite(step) or step<.01 or start>=stop:
        raise ValueError('Require increasing UTC window and display step >=10 ms')
    step_ns = round(step*1e9)
    count = int((stop-start).astype('timedelta64[ns]').astype('int64'))//step_ns+1
    if not 2<=count<=2000: raise ValueError('Require 2..2000 displayed frames; adjust step_s')
    timeline = start+np.arange(count)*np.timedelta64(step_ns,'ns')
    identifier = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    out = Path(output_dir).expanduser().resolve() if output_dir else Path(cfg['output_root'])/identifier
    out.mkdir(parents=True, exist_ok=False)
    snapshot_code(out)
    print(f'UTC-verified media: {out}', flush=True)
    stations, inputs, paths = [], [], [config_path]
    status, error = 'failed', None
    try:
        write_json(out/'resolved_config.json', cfg)
        write_json(out/'status.json', dict(status='running'))
        coverage = []
        for c in cfg['stations']:
            rows, native, info, curve_paths = read_station_curve(c, cfg['date_utc'])
            if c.get('source_sha256') and sha256(c['source']) != c['source_sha256']:
                raise ValueError('Source hash differs from saved photometry recording')
            frames = (LCFrames if Path(c['source']).suffix.lower()=='.lc' else StationFrames)(c, rows, native)
            station = dict(config=c, rows=rows, frames=frames, D=None, R=None, curve_info=info)
            stations.append(station)
            station['D'], station['R'], station['timing'] = saved_transitions(c, rows)
            paths += curve_paths+frames.paths
            paths += [c[k] for k in ('pyote_result','tracking_csv','timing_source_file') if c.get(k)]
            residuals = [record['residual_s'] for record in frames.records.values()]
            coverage.append(dict(name=c['name'], samples=len(rows), matched_images=len(frames.mapping),
                curve_start_utc=str(rows[0].utc), curve_end_utc=str(rows[-1].utc),
                image_start_utc=frames.records[min(frames.mapping)]['source_midpoint_utc'] if frames.mapping else None,
                image_end_utc=frames.records[max(frames.mapping)]['source_midpoint_utc'] if frames.mapping else None,
                residual_min_s=min(residuals) if residuals else None,
                residual_max_s=max(residuals) if residuals else None))
            print(f'{c["name"]}: {len(rows)} samples; {len(frames.mapping)} verified real images', flush=True)
        inputs = input_manifest(paths)
        selections = [[nearest_sample(s['rows'], t) for s in stations] for t in timeline]
        partial = [c for c in coverage if c['matched_images']<c['samples']]
        warnings = [f'{c["name"]}: {c["matched_images"]}/{c["samples"]} source images; missing times stay blank' for c in partial]
        context = dict(event=cfg['event'].replace('_',' '), target=cfg['target'], date_utc=cfg['date_utc'], step_s=step,
            coverage_note=dict(en=' · '.join(warnings) if warnings else 'All source timestamps verified',
                              zh=' · '.join(f'{c["name"]}：{c["matched_images"]}/{c["samples"]} 帧；缺失时无画面' for c in partial) if partial else '所有原始帧时间戳均已核对'))
        outputs = {}
        if not verify_only:
            for k, s in enumerate(stations): s['frames'].prepare([indices[k] for indices in selections])
            contacts = [start, start+(stop-start)//2, stop]
            first_event = next((s for s in stations if s['D'] is not None), None)
            if first_event:
                contacts[1] = first_event['D']+(first_event['R']-first_event['D'])//2
            for s in stations:
                if s['D'] is not None:
                    contacts += [s['D']-np.timedelta64(2,'s'), s['D']+(s['R']-s['D'])//2, s['R']+np.timedelta64(2,'s')]
            for lang in ('en','zh') if cfg['language']=='both' else (cfg['language'],):
                panels = StationPanels(stations, start, stop, lang, context)
                outputs[lang] = encode_station_language(panels,timeline,selections,out/f'{cfg["event"]}_stations_{lang}.mp4',contacts)
        metadata = []
        for s, cov in zip(stations, coverage):
            f = s['frames']
            metadata.append(dict(**cov, curve_info=s['curve_info'], timing=s['timing'],
                D_utc=str(s['D']) if s['D'] is not None else None, R_utc=str(s['R']) if s['R'] is not None else None,
                stretch=f.limits, frame_alignment=[f.records[i] for i in sorted(f.records)]))
        write_json(out/'media_metadata.json', dict(alignment='absolute_utc', no_event_time_shift=True,
            verified_only=verify_only, utc_timeline=[str(t) for t in timeline], step_s=step, warnings=warnings,
            stations=metadata, outputs=outputs, display_selection=[dict(utc=str(t), frames=[s['rows'][i].frame if i is not None and i in s['frames'].mapping else None for s,i in zip(stations,indices)]) for t,indices in zip(timeline,selections)]))
        status = 'complete_with_warnings' if warnings else 'complete'
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        for s in stations: s['frames'].close()
        finish_record(out, inputs, status, error)
    return out
