"""Exercise binary PyMovie records and display controls in packaged exports."""
from pathlib import Path
import contextlib
import io
import json
import struct
import numpy as np
from .make_station_media import make_station_media
from .gui_config import build_config
from .gui_observer import DEFAULTS


def verify(root):
    """Verify six saved signals/UTCs without CSV decoding or pixel photometry."""
    root=Path(root)
    path=root/'native.pymovie'
    source='运行.ser'.encode('utf-32-le').ljust(1024,b'\0')
    prefix=b'PYMOVIE\0'+struct.pack('<HIIB',1,1065,326,3)+b'2026-01-01'.ljust(16,b'\0')+source
    data=prefix+struct.pack('<HHH',0,0,0)
    for frame in range(6):
        counts=10 if frame in (2,3) else 100
        data+=bytes([3])+'target'.encode('utf-32-le').ljust(256,b'\0')+struct.pack('<ddd',counts,counts+10,frame)
        data+=f'00:00:{frame*.3:010.7f}'.encode('ascii').ljust(16,b'\0')+struct.pack('<H',65535)+bytes(27)
    path.write_bytes(data)
    cfg=build_config(dict(event='Binary PyMovie',target='Target',date_utc='2026-01-01',step_s='.3',
        language='both',window_mode='full',skip_gaps='skip',output_root=str(root)),
        [dict(DEFAULTS,curve=str(path),source=str(root/'frames.ser'),target_xy='32 16',
              image_stretch_mode='manual',image_black='1000',image_white='2000',image_strength='0')])
    config=root/'binary-config.json';config.write_text(json.dumps(cfg),encoding='utf-8')
    with contextlib.redirect_stdout(io.StringIO()):make_station_media(config,root/'binary-media')
    meta=json.loads((root/'binary-media/media_metadata.json').read_text(encoding='utf-8'))
    station=meta['stations'][0]
    if station['samples']!=6 or station['matched_images']!=6 or station['displayed_images']!=6 or station['residual_max_s']!=0:
        raise AssertionError('Native binary source/curve frame UTC differs')
    if station['stretch']!=[1000,2000] or station['stretch_info']['strength']!=0:
        raise AssertionError('Manual display settings changed')
    record=json.loads((root/'binary-media/run_metadata.json').read_text(encoding='utf-8'))
    if not record['input_integrity_verified']:raise AssertionError('Binary PyMovie inputs changed')
    return dict(format='PyMovie aperture records v1',frame_matches=6,displayed_images=6,
                binary_unicode_header=True,manual_fixed_levels=True,source_and_curve_utc_unchanged=True)
