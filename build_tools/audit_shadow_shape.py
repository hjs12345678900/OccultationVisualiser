"""Reproduce footprint-shape diagnostics from an existing immutable media run."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from occultation_media.read_occult_prediction import parse_prediction
from occultation_media.plan_shadow_simulation import ShadowSimulation
from occultation_media.render_shadow_map import ShadowMapPanel
from occultation_media.compute_shadow_geometry import EARTH_A_KM, AXIS_RATIO
from occultation_media.record_media_run import snapshot_code, input_manifest, finish_record, write_json
from occultation_media.platform_runtime import load_font


def terrestrial_xyz(latlon):
    """Return geodetic surface coordinates as float64 (N,3) ECEF km."""
    lat,lon=np.radians(latlon).T
    n=EARTH_A_KM/np.sqrt(1-(1-AXIS_RATIO**2)*np.sin(lat)**2)
    return np.column_stack((n*np.cos(lat)*np.cos(lon),n*np.cos(lat)*np.sin(lon),
                            n*AXIS_RATIO**2*np.sin(lat)))


def diameters(points):
    """Return covariance-equivalent major/minor diameters in input units.

    Samples are uniform in fundamental-plane angle, not ground arclength.
    2*sqrt(2/N)*singular_values gives exact diameters for a sampled ellipse;
    the gently curved finite footprint is described approximately by these.
    """
    return (2*np.sqrt(2/len(points))*np.linalg.svd(points-points.mean(axis=0),compute_uv=False))[:2]


def audit(run, out):
    """Save fixed-scale map snapshots and FP/surface/map shape evidence."""
    out.mkdir(parents=True,exist_ok=False);snapshot_code(out)
    config=run/'resolved_config.json';metadata=run/'media_metadata.json';prediction=run/'shadow_prediction.occelmnt'
    inputs=input_manifest([config,metadata,prediction])
    cfg=json.loads(config.read_text());meta=json.loads(metadata.read_text())
    geometry=parse_prediction(prediction.read_text())
    times=np.array(meta['utc_timeline'],dtype='datetime64[ns]')
    stations=[dict(config=c) for c in cfg['stations']]
    panel=ShadowMapPanel(ShadowSimulation(geometry,{},stations,times),'en')
    chosen=times[np.unique(np.linspace(0,len(times)-1,5).round().astype(int))]
    canvas=Image.new('RGB',(1920,640*len(chosen)),(9,13,22));draw=ImageDraw.Draw(canvas)
    records=[]
    for k,utc in enumerate(chosen):
        rim=geometry.footprint(utc,512);center=geometry.project_surface(geometry.center_xy(utc),utc)
        fp=np.array([geometry.site_xyz(*p,utc)[:2] for p in rim])*EARTH_A_KM
        radii=np.linalg.norm(fp-geometry.center_xy(utc)*EARTH_A_KM,axis=1)
        ground=diameters(terrestrial_xyz(rim))
        projected=diameters(panel.projection.project(rim))
        pixels=diameters(panel.map_pixels(panel.projection.project(rim)))
        altitude=np.degrees(np.arcsin(geometry.site_star_sine(*center,utc)))
        row=dict(utc=str(utc),fundamental_radius_min_km=float(radii.min()),fundamental_radius_max_km=float(radii.max()),
                 ground_diameters_km=ground.tolist(),map_diameters_km=projected.tolist(),screen_diameters_px=pixels.tolist(),
                 ground_axis_ratio=float(ground[0]/ground[1]),map_axis_ratio=float(projected[0]/projected[1]),
                 star_altitude_deg=float(altitude),map_pixels_per_km=panel.scale)
        records.append(row);canvas.paste(panel.render(utc,[None]*len(stations)),(0,k*640))
        text=(f'FP diameter = {geometry.diameter_km:.3f} km (fixed) | ground ~ {ground[0]:.2f} x {ground[1]:.2f} km | '
              f'axis ratio {ground[0]/ground[1]:.4f} | star altitude {altitude:.2f} deg\n'
              f'Map axis ratio {projected[0]/projected[1]:.4f} | scale {panel.scale:.6f} px/km (fixed in both directions)')
        draw.text((36,k*640+545),text,font=load_font(23,'en'),fill=(232,239,249),spacing=10)
    canvas.save(out/'shadow_shape_comparison.png')
    write_json(out/'shape_metrics.json',dict(nominal_diameter_km=geometry.diameter_km,records=records,
        method='512 uniform FP-angle vertices; covariance-equivalent full diameters; ECEF surface versus fixed oblique map'))
    finish_record(out,inputs,'complete')
    print(json.dumps(records,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('run',type=Path);parser.add_argument('out',type=Path)
    args=parser.parse_args();audit(args.run,args.out)
