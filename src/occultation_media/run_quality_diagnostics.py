"""Create an immutable curve-only noise report without decoding video frames."""
from datetime import datetime, timezone
from pathlib import Path
import csv
from .make_station_media import load_config
from .read_station_curves import read_station_curve
from .read_saved_transitions import saved_transitions
from .read_saved_snr import station_snr
from .resolve_station_order import resolve_station_order
from .diagnose_noise_quality import diagnose_stations
from .record_media_run import snapshot_code, input_manifest, finish_record, write_json


def save_quality_report(out, stations, margin_s=1):
    """Save full JSON and compact CSV; return capture evidence paths for hashing.

    The summary keeps saved-fit SNR separate from the explicitly guarded curve
    baseline. Count units and background assumptions remain in the full JSON.
    """
    report,paths=diagnose_stations(stations,margin_s)
    write_json(out/'quality_report.json',report)
    columns=['station','saved_snr','guarded_baseline_snr','baseline_scatter_percent',
             'exposure_s','camera','binning','baseline_samples','aperture_noise_estimate']
    with (out/'quality_summary.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for s in report['stations']:
            p=s['baseline'];c=s['context']
            writer.writerow(dict(station=s['name'],saved_snr=s['saved_snr'].get('snr'),
                guarded_baseline_snr=p.get('snr'),baseline_scatter_percent=p.get('scatter_percent'),
                exposure_s=s['exposure_s'],camera=c.get('camera'),binning=c.get('binning'),
                baseline_samples=p['samples'],aperture_noise_estimate=s['pixel_budget'].get('aperture_sigma_estimate')))
    return paths


def run_quality_diagnostics(config_path, output_dir=None):
    """Read saved curves/D/R only and record source hashes and executing code.

    No image alignment is audited in this mode. UTC comparisons use the saved
    midpoint conventions; source frames are verified by the separate Verify
    action. Neither source photometry nor saved D/R is modified or re-fitted.
    """
    cfg=load_config(config_path)
    identifier=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    out=Path(output_dir).expanduser().resolve() if output_dir else Path(cfg['output_root'])/identifier
    out.mkdir(parents=True,exist_ok=False);snapshot_code(out)
    inputs=[];status='failed';error=None;stations=[];paths=[config_path]
    try:
        write_json(out/'resolved_config.json',cfg)
        for c in cfg['stations']:
            rows,_,_,files=read_station_curve(c,cfg['date_utc']);paths+=files
            paths += [c[k] for k in ('pyote_result','tracking_csv','timing_source_file','snr_source_file','coordinate_source_file') if c.get(k)]
            if c.get('exposure_evidence',{}).get('path'):paths.append(c['exposure_evidence']['path'])
            d,r,timing=saved_transitions(c,rows)
            stations.append(dict(config=c,rows=rows,D=d,R=r,timing=timing,snr=station_snr(c,rows,d,r)))
        stations,ordering_paths=resolve_station_order(cfg,stations,out)
        paths+=ordering_paths
        paths+=save_quality_report(out,stations,float(cfg.get('diagnostic_margin_s',1)))
        inputs=input_manifest(paths);status='complete'
        print(f'Noise diagnostics: {out}',flush=True)
    except BaseException as exc:
        error=f'{type(exc).__name__}: {exc}';raise
    finally: finish_record(out,inputs,status,error)
    return out
