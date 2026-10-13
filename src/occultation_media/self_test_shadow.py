"""Check optional shadow-map resources and encoding inside the frozen package."""
import csv
import json
from pathlib import Path
import numpy as np
from astropy.io import fits
from PIL import Image
from .gui_config import build_config
from .gui_observer import DEFAULTS
from .make_station_media import make_station_media

XML='''<Occultations><Event>
<Elements>JPL#79,8.17,2026,9,12,9.8753005,-0.0949742,-0.1689929,4.5924730,-2.5776256,0.0053027,0.0003957,0.0000005,0.0000001</Elements>
<Earth>141.4193,-22.8036,30.95,4.09,False</Earth>
<Star>UCAC4 336-171713,18.70423466,-22.8294285,14.36,13.95,13.37,0,0,,18.73146372,-22.8036164</Star>
<Object>850,Altona,14.55,76.200,2.1756</Object>
</Event></Occultations>'''


def verify(root):
    """Render an opt-in job and verify original UTC and packaged coastlines."""
    observers=[]
    for k in range(2):
        source=root/f'shadow_fits_{k}';source.mkdir()
        lines=['FrameNum,timeInfo,signal-target,xcentroid-target,ycentroid-target']
        for i in range(3):
            utc=np.datetime64('2026-09-12T09:54:30','ns')+np.timedelta64(k*3000+i*200,'ms')
            lines.append(f'{i},[{str(utc).split("T")[1]}],100,8,8')
            fits.writeto(source/f'{i}.fits',np.arange(256,dtype=np.uint16).reshape(16,16),
                         fits.Header({'DATE-AVG':str(utc),'EXPTIME':.2}))
        curve=root/f'shadow_curve_{k}.csv';curve.write_text('\n'.join(lines),encoding='utf-8')
        observers.append({**DEFAULTS,'name':f'Station {k}','observer':'示例观测者 / Example Observer' if k==0 else '','curve':str(curve),'source':str(source),
                          'color':'#E65A8D' if k==0 else '', 'latitude_deg':str(-37.8136-k*.001),'longitude_deg':'144.9631'})
    cfg=build_config(dict(event='Altona',target='Star',date_utc='2026-09-12',step_s='.2',language='both',
                         window_mode='full',skip_gaps='accelerate',gap_speed='50',station_order='path_north_to_south',
                         output_root=str(root),shadow_enabled='1',shadow_xml=XML),observers)
    path=root/'shadow_config.json';path.write_text(json.dumps(cfg),encoding='utf-8')
    out=make_station_media(path,root/'shadow_media')
    meta=json.loads((out/'media_metadata.json').read_text(encoding='utf-8'))
    if not meta['shadow_simulation']['enabled']:raise AssertionError('Shadow simulation not enabled')
    if meta['outputs']['en']['mp4_shape']!=[1920,1258]:raise AssertionError('Missing shadow-map canvas')
    with (out/'shadow_frame_positions.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    if len(rows)!=6 or rows[0]['curve_midpoint_utc']!='2026-09-12T09:54:30.000000000':
        raise AssertionError('Shadow frame positions changed the physical UTC')
    if rows[0]['nominally_covered']!='True':raise AssertionError('Wrong nominal station coverage')
    ordering=json.loads((out/'station_path_order.json').read_text(encoding='utf-8'))
    offsets=[s['cross_track_km'] for s in ordering['stations']]
    if offsets!=sorted(offsets,reverse=True):raise AssertionError('Wrong north-positive path order')
    by_name={s['name']:s for s in meta['stations']}
    if by_name['Station 0'].get('observer')!='示例观测者 / Example Observer' or 'observer' in by_name['Station 1']:
        raise AssertionError('Optional observer attribution was lost or assigned to a different station')
    if by_name['Station 0']['display_color']!='#E65A8D' or by_name['Station 0']['color_mode']!='custom':
        raise AssertionError('Custom station color did not survive sorting/export')
    if by_name['Station 1']['color_mode']!='automatic':raise AssertionError('Blank color must remain automatic')
    for lang in ('en','zh'):
        with Image.open(meta['outputs'][lang]['preview']) as preview:
            pixels=np.asarray(preview.convert('RGB'))
        for region in (pixels[:718],pixels[718:]):
            if not (region==[230,90,141]).all(axis=2).any():
                raise AssertionError('Station panel and map must use the same selected color')
    plan=meta['timeline_plan']
    if len(plan['accelerated_gaps'])!=1 or plan['skipped_gaps']:
        raise AssertionError('Accelerated gap missing or incorrectly skipped')
    for lang in ('en','zh'):
        if meta['outputs'][lang]['gif_fps']!=25:raise AssertionError('Transit motion lost GIF update cadence')
        with Image.open(meta['outputs'][lang]['gif']) as gif:
            if gif.size!=(1280,838):raise AssertionError('Wrong scaled shadow-map GIF')
    # A second encoded job checks the following camera inside the frozen app.
    # Physical audit tables must be byte-identical across presentation modes.
    cfg['shadow_simulation']['view_mode']='follow_shadow'
    follow_path=root/'shadow_follow_config.json'
    follow_path.write_text(json.dumps(cfg),encoding='utf-8')
    follow=make_station_media(follow_path,root/'shadow_follow_media')
    follow_meta=json.loads((follow/'media_metadata.json').read_text(encoding='utf-8'))
    if follow_meta['shadow_simulation']['view_mode']!='follow_shadow':
        raise AssertionError('Following map selection was lost')
    for filename in ('shadow_frame_positions.csv','shadow_display_positions.csv'):
        if (out/filename).read_bytes()!=(follow/filename).read_bytes():
            raise AssertionError('Map camera changed physical frame positions or UTC')
    if meta['utc_timeline']!=follow_meta['utc_timeline'] or meta['timeline_plan']!=follow_meta['timeline_plan']:
        raise AssertionError('Map camera changed the timeline or accelerated gaps')
    return dict(ok=True,optional_observer=True,custom_station_colors=True,map_view_modes=True,verified_frame_positions=len(rows),offline_map=True,
                frame_utc_preserved=True,accelerated_gap=True,path_station_order=True,mp4_shape=[1920,1258],languages=['en','zh'])
