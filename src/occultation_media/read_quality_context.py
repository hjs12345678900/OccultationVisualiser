"""Read capture/photometry evidence and optional CSV pixel-noise columns."""
import csv
from pathlib import Path


def read_quality_context(cfg):
    """Return context, frame-keyed auxiliaries and every evidence file read.

    Native PyMovie header fields and Tangra export tables are interpreted only
    where their labels are explicit. Nearby SharpCap CameraSettings files or an
    explicitly supplied file provide binning/gain. Recorded gain units are not
    assumed comparable across cameras. Missing metadata stays unknown; no
    camera specification or photon/electron conversion is invented.
    """
    path=Path(cfg.get('tracking_csv') or cfg['curve'])
    context=dict(curve_format=cfg['curve_format'],native_mode=cfg.get('native_mode','raw'))
    aux={};paths=[]
    if path.suffix.lower()=='.csv':
        paths.append(path);lines=path.read_text(encoding='utf-8-sig').splitlines()
        name=(cfg.get('tracking_target_column') or cfg.get('target_column','signal-target'))[7:]
        active=False
        for line in lines:
            if line.startswith('# aperture name:'): active=line.split(':',1)[1].strip()==name
            if active and 'def mask radius:' in line: context['aperture_radius_pixels']=line.split(':',1)[1].strip()
            if active and 'aperture size:' in line: context['background_thumbnail_size']=line.split(':',1)[1].strip()
            for label,key in [('INSTRUMENT-SENSOR','camera'),('INSTRUMENT-GAIN','recorded_gain'),
                              ('IMAGE-BINNING-X','binning_x'),('IMAGE-BINNING-Y','binning_y'),('TELESCOPE','recorded_telescope')]:
                if line.startswith('#'+label+':'): context[key]=line.split(':',1)[1].strip()
            if 'Aperture photometry was used' in line: context['photometry']='PyMovie aperture photometry'
        for i,line in enumerate(lines[:-1]):
            if line.startswith('Reversed Gamma,'):
                params=dict(zip([v.strip() for v in next(csv.reader([line]))],next(csv.reader([lines[i+1]]))))
                context.update(camera=params.get('Camera'),photometry=params.get('Signal Method'))
            if line.startswith('Object, Type, Aperture,'):
                fields=[v.strip() for v in next(csv.reader([line]))]
                values=next(csv.reader([lines[i+1]]));obj=dict(zip(fields,values))
                context.update(aperture_radius_pixels=obj.get('Aperture'),recorded_fwhm_pixels=obj.get('FWHM'))
        header=next((i for i,l in enumerate(lines) if l.startswith(('FrameNum,','FrameNo,'))),None)
        if header is not None:
            table=csv.DictReader(lines[header:])
            for item in table:
                item={k.strip():v for k,v in item.items()}
                frame=int(float(item.get('FrameNum',item.get('FrameNo'))))
                columns=dict(background_std=f'stdbkg-{name}',mask_pixels=f'nmaskpx-{name}')
                record={}
                for key,col in columns.items():
                    if col in item:
                        try: record[key]=float(item[col])
                        except (ValueError,TypeError): pass
                aux[frame]=record
    source=Path(cfg.get('source') or cfg['curve'])
    explicit=cfg.get('camera_settings_file')
    candidates=[Path(explicit)] if explicit else [source.with_suffix('.CameraSettings.txt'),Path(cfg['curve']).with_suffix('.CameraSettings.txt')]
    settings=next((p for p in candidates if p.is_file()),None)
    if explicit and settings is None: raise FileNotFoundError(explicit)
    if settings:
        paths.append(settings);values={}
        for line in settings.read_text(encoding='utf-8-sig').splitlines():
            if line.startswith('[') and line.endswith(']'): context['camera']=line[1:-1]
            if '=' in line:
                key,value=line.split('=',1);values[key.strip()]=value.strip()
        context.update({key:values[src] for src,key in [('Binning','binning'),('Gain','recorded_gain'),('Exposure','recorded_exposure')] if src in values})
        context['camera_settings_source']=str(settings)
    if not context.get('binning') and context.get('binning_x') and context.get('binning_y'):
        context['binning']=f'{context["binning_x"]}x{context["binning_y"]}'
    context['gain_note']='Recorded gain; cross-camera units/conversion are not assumed'
    return context,aux,paths
