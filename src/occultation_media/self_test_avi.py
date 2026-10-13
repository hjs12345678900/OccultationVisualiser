"""Exercise AVI decoding, explicit identity and bilingual exports in the bundle."""
import json
from pathlib import Path
import subprocess
import numpy as np
from .platform_runtime import ffmpeg_executable, hidden_process_options
from .read_frame_sources import open_source


def write_fixture(path, codec='ffv1'):
    """Write six synthetic RGB8 frames with spatial and temporal identity.

    The AVI claims 25 fps while the companion curve uses irregular UTC near
    midnight. This intentionally prevents container cadence from validating UTC.
    Return uint8 (6,32,64,3) reference pixels. No observation data are used.
    """
    y,x=np.indices((32,64))
    cube=np.stack([np.stack(((x*3+i*20)%256,(y*5+i*17)%256,
                             ((x+y)*2+i*13)%256),axis=-1) for i in range(6)]).astype('uint8')
    command=[ffmpeg_executable(),'-hide_banner','-loglevel','error','-n',
             '-f','rawvideo','-pix_fmt','rgb24','-s','64x32','-r','25','-i','pipe:0',
             '-an','-c:v',codec]
    if codec=='rawvideo':command+=['-pix_fmt','bgr24']
    if codec=='mjpeg':command+=['-q:v','2','-pix_fmt','yuvj444p']
    subprocess.run(command+[str(path)],input=cube.tobytes(),check=True,**hidden_process_options())
    return cube


def verify(root):
    """Return evidence after real FFV1/raw/MJPEG reads and native AVI export."""
    from .gui_config import build_config
    from .gui_observer import DEFAULTS
    from .make_station_media import make_station_media
    root=Path(root)/'avi_validation';root.mkdir()
    errors={}
    for codec in ('rawvideo','ffv1','mjpeg'):
        path=root/f'{codec}.avi';expected=write_fixture(path,codec)
        source=open_source(path)
        if source.count!=6:raise AssertionError('AVI decoded count differs')
        decoded=source.read_many([5,0,3])
        error=max(float(np.abs(decoded[i][0].astype(float)-expected[i]).mean()) for i in decoded)
        if error>(4 if codec=='mjpeg' else 0):raise AssertionError('AVI pixel/frame identity differs')
        errors[codec]=error
    labels=['23:59:59.600','23:59:59.800','00:00:00.050','00:00:00.300','00:00:00.500','00:00:00.750']
    curve=root/'curve.csv'
    curve.write_text('FrameNum,timeInfo,signal-target,xcentroid-target,ycentroid-target\n'+'\n'.join(
        f'{100+i},[{clock}],{10 if i in (2,3) else 100},32,16' for i,clock in enumerate(labels)),encoding='utf-8')
    obs=dict(DEFAULTS,curve=str(curve),source=str(root/'ffv1.avi'),source_first_frame='100',
             exposure_mode='manual',exposure_ms='100',avi_timestamp_reference='midpoint')
    cfg=build_config(dict(event='AVI synthetic',target='Target',date_utc='2026-09-12',
        window_mode='full',step_s='.05',language='both',output_root=str(root)),[obs])
    config=root/'config.json';config.write_text(json.dumps(cfg),encoding='utf-8')
    out=make_station_media(config,root/'media')
    meta=json.loads((out/'media_metadata.json').read_text(encoding='utf-8'))
    station=meta['stations'][0]
    if station['matched_images']!=6 or station['residual_max_s'] is not None:
        raise AssertionError('AVI must map six frames without claiming source UTC agreement')
    records=station['frame_alignment']
    if records[2]['curve_midpoint_utc']!='2026-09-13T00:00:00.050000000':
        raise AssertionError('AVI ignored curve UTC midnight/irregular cadence')
    if any(r['source_midpoint_utc'] is not None for r in records):
        raise AssertionError('AVI invented independent source UTC')
    if not meta['warnings']:raise AssertionError('AVI timing limitation was not recorded')
    return dict(codecs=errors,mapped_frames=6,midnight=True,irregular_curve_utc=True,
                independent_source_utc=False,bilingual_export=True)
