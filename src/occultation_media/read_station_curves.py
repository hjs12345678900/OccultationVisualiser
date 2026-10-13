"""Read saved target-only CSV/LC curves for a common absolute UTC display.

Counts are never refitted or smoothed. Supported native PyMovie signals are
already net ADU; Tangra total/background values are subtracted once. LC binary
fields follow Tangra LCFile.cs, LCMeasurement v9 and LCFrameTiming v2:
https://github.com/hpavlov/tangra3/blob/master/Tangra%203/VideoOperations/LightCurves/LCFile.cs
"""
import csv
from dataclasses import replace
import io
from pathlib import Path
import struct
import zlib
import numpy as np
from .station_sample import MediaSample
from .utc_conventions import clock_sequence, midpoint
from .read_tangra_stamps import DotNetReader, skip_lc_header, read_measurement


def read_lc_curve(path):
    """Return target 0 net ADU/midpoints and recorded tracking coordinates.

    Require container v4, measurement v9, frame timing v2 and footer v14.
    Read the v14 footer's final digital-correction fields, applying a saved
    acquisition delay/reference offset once when explicitly enabled. Native
    midpoint ticks remain available separately for FITS identity verification.
    Flags use Tangra's IsSuccessfulReading list; no stamps or flux are estimated.
    """
    payload = zlib.decompress(Path(path).read_bytes(), -15)
    reader = DotNetReader(io.BytesIO(payload))
    objects, timing_type, count = skip_lc_header(reader)
    if timing_type == 0:
        raise ValueError('LC needs embedded frame times')
    samples, native = [], []
    good_flags = {0,1,2,6,9,14,17,22,25,30}
    for _ in range(count):
        if reader.i32() != 2:
            raise ValueError('Expected LC timing v2')
        utc = np.datetime64((reader.i64()-621355968000000000)*100, 'ns')
        exposure = reader.i32()/1000.
        width, height = reader.i32(), reader.i32()
        reader.read(width*height)
        if reader.boolean(): reader.read(24)
        for obj in range(objects):
            position = reader.stream.tell()
            if reader.i32() != 9: raise ValueError('Expected LC measurement v9')
            frame, target = reader.u32(), reader.u8()
            total, background = reader.u32(), reader.u32()
            reader.read(35*35*4)
            flag = reader.u8()
            xy = (reader.f32(), reader.f32())
            reader.read(8+8)
            flags_dword = reader.u32()
            effective_flag = flags_dword & 255 if flags_dword and flag == 0 else flag
            reader.stream.seek(position)
            read_measurement(reader, False)
            if obj == 0:
                if target != 0: raise ValueError('LC object order differs')
                samples.append(MediaSample(frame, utc, exposure, float(total)-background, (), (0.,0.),
                    0 if effective_flag in good_flags and not flags_dword & 256 else 2, 0, xy))
                native.append(utc)
    if reader.i32() != 14:
        raise ValueError('Expected LC footer v14')
    enabled, delay, offset = struct.unpack('<?dd', payload[-17:])
    correction = ((-delay if np.isfinite(delay) else 0.) + (offset if np.isfinite(offset) else 0.))/1000. if enabled else 0.
    if correction:
        from dataclasses import replace
        samples = [replace(r,utc=r.utc+np.timedelta64(round(correction*1e9),'ns')) for r in samples]
    return samples, native, dict(digital_corrections_enabled=enabled, applied_offset_s=correction)


def read_station_curve(cfg, date):
    """Return one station's full-cadence MediaSamples, native UTC and provenance.

    Explicit cfg selects pymovie_csv, binary pymovie_records, tangra_csv or
    tangra_lc. CSV
    start timestamps receive half the supplied exposure only for midpoint
    display; midpoint CSV values retain already-applied clock corrections.
    Reject unordered frames/times; native input paths are returned for hashing.
    """
    kind = cfg['curve_format']
    if kind not in ('pymovie_csv','pymovie_records','tangra_csv','tangra_lc'):
        raise ValueError('Unsupported curve_format')
    path = Path(cfg['curve']).expanduser().resolve()
    if kind == 'pymovie_records':
        from .read_pymovie_records import read_record_curve
        rows,native,info,_ = read_record_curve(cfg,date)
    elif kind == 'tangra_lc':
        rows, native, info = read_lc_curve(path)
    else:
        if path.suffix.lower() not in ('.csv','.txt'):
            raise ValueError('Choose an exported CSV, native .pymovie or Tangra LC curve / 请选择导出 CSV、原生 .pymovie 或 Tangra LC')
        try:lines = path.read_text(encoding='utf-8-sig').splitlines()
        except UnicodeDecodeError as exc:
            raise ValueError('Curve is not UTF-8 CSV text; choose .pymovie as a native curve / 该曲线不是 CSV 文本') from exc
        header = 'FrameNum,' if kind == 'pymovie_csv' else 'FrameNo,'
        start = next((i for i,line in enumerate(lines) if line.startswith(header)),None)
        if start is None:raise ValueError('Curve header missing; choose matching PyMovie/Tangra export / 未找到曲线表头，请选正确导出文件')
        table = [{k.strip():v for k,v in row.items()} for row in csv.DictReader(lines[start:])]
        exposure = cfg['exposure_s']
        labels = [r['timeInfo'] if kind == 'pymovie_csv' else r['Time (UT)'] for r in table]
        times = clock_sequence(date, labels)
        rows, native = [], []
        for r, utc in zip(table, times):
            if kind == 'pymovie_csv':
                frame = float(r['FrameNum'])
                if not np.isfinite(frame) or int(frame) != frame: raise ValueError('Integrated/fractional CSV frame unsupported')
                flux = float(r[cfg['target_column']])
                name = cfg['target_column'][7:]
                xy = tuple(float(r[k] or 'nan') for k in (f'xcentroid-{name}',f'ycentroid-{name}')) if f'xcentroid-{name}' in r else (tuple(cfg['target_xy']) if cfg.get('target_xy') else None)
                defect = int(r.get(f'hit-defect-{name}', 0) or 0)
            elif kind == 'tangra_csv':
                frame = int(r['FrameNo'])
                defect = 0
                flux = float(r['Signal (1)'])-float(r['Background (1)'])
                from .read_tangra_photometry import read_target_position
                xy = tuple(cfg['target_xy']) if cfg.get('target_xy') else read_target_position(path, 1)
            else:
                raise ValueError('Unknown curve format')
            rows.append(MediaSample(int(frame),midpoint(utc,exposure,cfg['timestamp_reference']),exposure,flux,(),(0.,0.),2 if defect else 0,0,xy))
            native.append(utc)
        info = dict(flux_convention='Saved native net counts' if kind == 'pymovie_csv' else 'Tangra Signal(1)-Background(1)',
                    timestamp_reference=cfg['timestamp_reference'])
    if any(r.frame < 0 or np.isnat(r.utc) or not np.isfinite(r.exposure_s) or r.exposure_s <= 0 for r in rows):
        raise ValueError('Invalid station frame, UTC or exposure')
    if len(rows)<3 or any(b.frame<=a.frame or b.utc<=a.utc for a,b in zip(rows,rows[1:])):
        raise ValueError('Station frames and UTC must strictly increase')
    if not any(r.valid for r in rows): raise ValueError('Station has no valid target counts')
    if cfg.get('tracking_csv'):
        tracking_cfg = dict(cfg, curve=cfg['tracking_csv'])
        tracking_cfg.pop('tracking_csv')
        if kind=='pymovie_records':tracking_cfg['curve_format']='pymovie_csv'
        tracking_cfg['target_column'] = cfg.get('tracking_target_column', cfg['target_column'])
        tracking, track_native, _, _ = read_station_curve(tracking_cfg, date)
        by_frame = {r.frame:r for r in tracking}
        matched = [by_frame.get(r.frame) for r in rows]
        if any(b is None or a.utc!=b.utc for a,b in zip(rows,matched)):
            raise ValueError('Tracking CSV and processed curve frame/UTC differ')
        # PyOTE block exports retain source frame IDs but omit intermediate rows.
        # Coordinates come from those exact saved frames, without interpolation.
        rows = [replace(a,target_xy=b.target_xy,tracking_flag=max(a.tracking_flag,b.tracking_flag)) for a,b in zip(rows,matched)]
        info['tracking_source'] = cfg['tracking_csv']
    return rows, native, info, [path]
