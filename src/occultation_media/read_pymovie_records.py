"""Read native PyMovie v1 binary aperture photometry without executing data.

The documented little-endian format is implemented from apertureRecord.py:
https://github.com/bob-anderson-ok/pymovie/blob/master/src/pymovie/apertureRecord.py
Only saved net signal, original integral frames and UTC are imported. Initial
header positions are static reference positions, not per-frame tracking.
"""
from pathlib import Path
import struct
import numpy as np
from .station_sample import MediaSample
from .utc_conventions import clock_sequence, midpoint


def record_header(path):
    """Return validated v1 sizes/date/source and static aperture coordinates.

    Fixed header: 1059 bytes; record prefix: 299 bytes followed by uint16 image
    and uint8 mask, each ROI². Added trailing fields are skipped by stored sizes.
    No exposure duration exists in this format; it must come from other evidence.
    """
    path = Path(path)
    size = path.stat().st_size
    with path.open('rb') as stream:
        data = stream.read(1059)
        if len(data)!=1059 or data[:8]!=b'PYMOVIE\x00':
            raise ValueError('Not a native PyMovie aperture file / 不是原生 PyMovie 测光文件')
        version, header_size, record_size, roi = struct.unpack_from('<HIIB',data,8)
        if version!=1 or not 1<=roi<=255 or not 1059<=header_size<=size or record_size<299+3*roi*roi:
            raise ValueError('Unsupported or damaged PyMovie v1 header / PyMovie 文件头损坏或版本不支持')
        date = data[19:35].rstrip(b'\x00').decode('ascii')
        source = data[35:1059].decode('utf-32-le').rstrip('\x00')
        positions = {}
        if header_size>=1065:
            width,height = struct.unpack('<HH',stream.read(4))
            table_start = 1059+4+3*width*height
            if table_start+2>header_size:
                raise ValueError('PyMovie initial frame exceeds header')
            stream.seek(table_start)
            count, = struct.unpack('<H',stream.read(2))
            if table_start+2+300*count>header_size:
                raise ValueError('PyMovie aperture table exceeds header')
            for _ in range(count):
                entry = stream.read(300)
                name = entry[:256].decode('utf-32-le').rstrip('\x00')
                x,y = struct.unpack_from('<dd',entry,284)
                if np.isfinite([x,y]).all():positions[name]=(x,y)
    return dict(header_size=header_size,record_size=record_size,roi_size=roi,
                obs_date=date,source=source,initial_positions=positions,
                records=(size-header_size)//record_size,trailing_bytes=(size-header_size)%record_size)


def aperture_names(path):
    """List names from header or the first 128 records, for target suggestions."""
    header = record_header(path)
    names = list(header['initial_positions'])
    if names:return names
    with Path(path).open('rb') as stream:
        for i in range(min(header['records'],128)):
            stream.seek(header['header_size']+i*header['record_size']+1)
            name = stream.read(256).decode('utf-32-le').rstrip('\x00')
            if name not in names:names.append(name)
    return names


def read_record_curve(cfg,date):
    """Return samples/native clocks, evidence and path for one saved aperture.

    Target column `signal-<name>` selects a binary aperture name. Intensities
    already subtract background and are never measured again from ROI pixels.
    Reject half-frame field mode because source mapping currently requires whole
    frames. Ignore a partial final record per the native format, recording its
    byte count. Static initial coordinates are used only without tracking/override.
    """
    path=Path(cfg['curve']).expanduser().resolve()
    header=record_header(path)
    if header['obs_date'] and header['obs_date']!=date:
        raise ValueError('PyMovie observation date differs from event UTC date / PyMovie 日期与事件 UTC 日期不符')
    target=cfg['target_column'].removeprefix('signal-')
    values=[]
    with path.open('rb') as stream:
        for i in range(header['records']):
            stream.seek(header['header_size']+i*header['record_size'])
            entry=stream.read(299)
            if entry[0]!=header['roi_size']:raise ValueError('PyMovie record ROI differs from header')
            name=entry[1:257].decode('utf-32-le').rstrip('\x00')
            if name!=target:continue
            signal,_,frame=struct.unpack_from('<ddd',entry,257)
            if not np.isfinite(frame) or frame<0 or int(frame)!=frame:
                raise ValueError('PyMovie field/half-frame mode is not supported; use whole-frame CSV / 暂不支持半帧场模式，请用整帧 CSV')
            clock=entry[281:297].rstrip(b'\x00').decode('ascii')
            if not clock:raise ValueError('PyMovie target has no saved UTC timestamp / 目标没有保存 UTC')
            values.append((int(frame),signal,clock))
    if not values:raise ValueError('PyMovie target aperture not found / 未找到目标孔径')
    times=clock_sequence(date,[v[2] for v in values])
    exposure=cfg['exposure_s']
    xy=tuple(cfg['target_xy']) if cfg.get('target_xy') else header['initial_positions'].get(target)
    rows=[MediaSample(frame,midpoint(t,exposure,cfg['timestamp_reference']),exposure,signal,target_xy=xy)
          for (frame,signal,_),t in zip(values,times)]
    return rows,times,dict(format='PyMovie aperture records v1',source=header['source'],
        flux_convention='Saved background-subtracted intensity',timestamp_reference=cfg['timestamp_reference'],
        coordinate_basis='explicit override' if cfg.get('target_xy') else 'static initial aperture position',
        partial_final_record_bytes_ignored=header['trailing_bytes']),[path]
