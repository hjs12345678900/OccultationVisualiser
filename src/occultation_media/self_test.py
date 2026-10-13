"""Exercise shipped codecs, fonts and exports inside a frozen application."""
import contextlib
from datetime import datetime,timedelta
import io
import json
from pathlib import Path
import platform
import struct
import tempfile
import numpy as np
from PIL import Image
from astropy.io import fits
from .make_tangra_occultation_media import main as generate
from .platform_runtime import load_font,ffmpeg_executable


def run():
    """Return test results; raise on missing bundled resources or wrong outputs."""
    from ravf import RavfWriter,RavfFrameType
    from .verify_adv_fixture import verify
    adv=verify()
    from .gui_branding import branding_asset
    for name in ('cover.png','icon.png','app.ico','app.icns'):
        with Image.open(branding_asset(name)) as artwork:artwork.verify()
    load_font(20,'en');load_font(20,'zh')
    with tempfile.TemporaryDirectory(prefix='occultation-self-test-') as tmp:
        root=Path(tmp);base=np.arange(2048,dtype='<u2').reshape(32,64)+1000
        cube=np.stack([base if i not in (2,3) else base//2 for i in range(6)])
        csv=['FrameNo,Time (UT),Signal (1),Background (1)']
        for i in range(6):
            t=datetime(2026,1,1)+timedelta(seconds=i*.3)
            csv.append(f"{i},{t.strftime('%H:%M:%S.%f')},{10000 if i in (2,3) else 120000},1000")
        (root/'curve.csv').write_text('\n'.join(csv), encoding='utf-8')
        fits.writeto(root/'cube.fits',cube)
        h=bytearray(178);h[:14]=b'LUCAM-RECORDER';struct.pack_into('<7I',h,14,0,0,1,64,32,16,6)
        (root/'frames.ser').write_bytes(h+cube.tobytes())
        with contextlib.redirect_stdout(io.StringIO()),(root/'frames.ravf').open('wb') as stream:
            writer=RavfWriter(stream,[('COLOR-TYPE',0),('IMAGE-ENDIANESS',1),('IMAGE-WIDTH',64),('IMAGE-HEIGHT',32),
                 ('IMAGE-ROW-STRIDE',128),('IMAGE-FORMAT',1),('FRAME-TIMING-ACCURACY',1000)],[])
            for i,pixels in enumerate(cube):writer.write_frame(stream,RavfFrameType.LIGHT,pixels.tobytes(),i*300000000,300000000,7,0,0,0,i)
            writer.finish(stream)
        summaries=[]
        for source in ['cube.fits','frames.ser','frames.ravf']:
            output=root/source.replace('.','_')
            argv=[str(root),'--source',str(root/source),'--source-first-frame','0',
                  '--event-date','2026-01-01','--asteroid','Self test','--star','Target',
                  '--predicted-time','00:00:00.750','--prediction-error-sec','.2','--exposure-ms','300',
                  '--event-frames','2','3','--language','both','--output-dir',str(output),'--basename','test']
            if source == 'frames.ravf':
                for flag in ('--predicted-time','--prediction-error-sec'):
                    index=argv.index(flag);del argv[index:index+2]
            with contextlib.redirect_stdout(io.StringIO()):generate(argv)
            for lang in ['en','zh']:
                gif=output/f'test_occultation_{lang}.gif'
                with Image.open(gif) as image:
                    if image.n_frames!=6 or image.size!=(1260,540):raise AssertionError('Invalid GIF')
                if (output/f'test_occultation_{lang}.mp4').stat().st_size<100:raise AssertionError('Empty MP4')
            manifest=json.loads((output/'test_metadata.json').read_text(encoding='utf-8-sig'))
            if source=='frames.ravf' and manifest['prediction'] is not None:
                raise AssertionError('Missing prediction must remain null')
            summaries.append(manifest['outputs']['en'])
        if len({s['black_adu'] for s in summaries})!=1:raise AssertionError('Stretch differs between source formats')
        # Exercise strict native timing and metadata inside the frozen app too.
        from .make_station_media import make_station_media
        start=np.datetime64('2026-01-01','ns')
        ticks=int(start.astype('int64'))//100+621355968000000000
        with (root/'frames.ser').open('ab') as stream:
            stream.write(struct.pack('<6Q',*(ticks+i*3000000 for i in range(6))))
        native=['FrameNum,timeInfo,signal-target,xcentroid-target,ycentroid-target']
        for i in range(6):
            clock=str(start+np.timedelta64(i*300,'ms')).split('T')[1]
            native.append(f'{i},[{clock}],{10 if i in (2,3) else 100},32,16')
        (root/'native.csv').write_text('\n'.join(native), encoding='utf-8')
        cfg=dict(event='Native',target='Target',date_utc='2026-01-01',alignment='absolute_utc',
            start_utc=str(start),end_utc=str(start+np.timedelta64(1500,'ms')),step_s=.3,language='both',
            stations=[dict(name='Observer',curve_format='pymovie_csv',curve='native.csv',target_column='signal-target',
                source='frames.ser',source_first_frame=0,exposure_s=.3,timestamp_reference='start',source_timestamp_reference='start',mapping_tolerance_s=1e-9)])
        config=root/'native.json';config.write_text(json.dumps(cfg), encoding='utf-8')
        # Build the same native job through new automatic desktop defaults.
        from .gui_config import build_config
        from .gui_observer import DEFAULTS
        (root/'frames.CameraSettings.txt').write_text('Exposure=300ms\n', encoding='utf-8')
        automatic=build_config(dict(event='Native',target='Target',date_utc='2026-01-01',step_s='.3',language='both',window_mode='full',skip_gaps='skip',output_root=str(root)),
            [dict(DEFAULTS,curve=str(root/'native.csv'),source=str(root/'frames.ser'))])
        config.write_text(json.dumps(automatic), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):make_station_media(config,root/'native_media')
        record=json.loads((root/'native_media/run_metadata.json').read_text(encoding='utf-8-sig'))
        if not record['input_integrity_verified']:raise AssertionError('Native input integrity failed')
        if not {'read_avi_frames.py','compute_shadow_geometry.py','make_station_media.py'}.issubset(record['source_sha256']):
            raise AssertionError('Frozen export lacks reproducible Python source hashes')
        meta=json.loads((root/'native_media/media_metadata.json').read_text(encoding='utf-8-sig'))
        if not (root/'native_media/quality_report.json').is_file():raise AssertionError('Missing automatic quality report')
        from .station_cli import main as station_cli
        with contextlib.redirect_stdout(io.StringIO()):
            station_cli([str(config),'--quality-only','--output-dir',str(root/'quality_only')])
        quality=json.loads((root/'quality_only/quality_report.json').read_text(encoding='utf-8-sig'))
        if quality['stations'][0]['baseline']['available']:raise AssertionError('Baseline needs saved D/R')
        if meta['stations'][0]['residual_max_s']!=0:raise AssertionError('Native source/curve UTC differs')
        for lang in ('en','zh'):
            with Image.open(meta['outputs'][lang]['gif']) as image:
                if image.n_frames!=6:raise AssertionError('Native GIF elapsed timeline differs')
        from .self_test_avi import verify as verify_avi
        with contextlib.redirect_stdout(io.StringIO()):avi_job=verify_avi(root)
        from .self_test_unicode import verify as verify_unicode
        unicode_job=verify_unicode(root)
        from .self_test_pyote_native import verify as verify_native_pyote
        native_pyote_job=verify_native_pyote(root)
        from .self_test_shadow import verify as verify_shadow
        with contextlib.redirect_stdout(io.StringIO()):shadow_job=verify_shadow(root)
    return {'ok':True,'system':platform.system(),'architecture':platform.machine(),
            'version':__import__('occultation_media.record_media_run',fromlist=['version']).version(),
            'avi':avi_job,'exports':['AVI','SER','FITS','RAVF','native PyMovie SER'],'languages':['en','zh'],'outputs':['GIF','PNG','MP4'],
            'branding_resources':True,'noise_diagnostics':True,'automatic_metadata_and_utc':True,'source_snapshot_hashes':True,
            'ffmpeg':ffmpeg_executable(),'adv':adv,'unicode_inputs':unicode_job,'native_pyote':native_pyote_job,'shadow_simulation':shadow_job}
