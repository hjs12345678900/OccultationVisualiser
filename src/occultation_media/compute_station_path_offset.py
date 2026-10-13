"""Scientific core: signed station chord offsets across a moving shadow path."""
import numpy as np
from .compute_shadow_geometry import EARTH_A_KM


def station_path_offset(geometry, station):
    """Return a nominal north-positive cross-track offset and approach UTC.

    ``geometry`` is ShadowGeometry; ``station`` supplies signed geodetic
    latitude/longitude degrees and optional ellipsoid altitude in metres.
    At each station's own predicted closest approach, minimize |r(t)|²,
    r=site_xy(t)-shadow_xy(t), including Earth's rotation. The tangent is the
    shadow's velocity relative to the station, v=-dr/dt. Its unit normal n
    is oriented so n·d(site_xy)/d(latitude)>0. The signed impact parameter is
    b=EARTH_A_KM*(r·n), in fundamental-plane km: north positive, south negative.
    Along-track longitude and measured D/R do not define the order.

    Search the prediction's ±1 h validity interval on a 30 s grid, then refine
    the best visible minimum by golden-section search to 0.1 ms. Time derivatives
    use symmetric 0.1 s differences; geographic north uses a 0.0001 degree
    tangent. No external solver, ephemeris, timing adjustment or fit is used.
    Return status/reason when coordinates, visible approach, a bounded minimum,
    motion, or a geographic north/south normal cannot be established. Unknown
    cases must not fall back to latitude sorting. Nominal model uncertainty is
    not propagated; this is a presentation coordinate, not an observed chord.
    """
    if 'latitude_deg' not in station or 'longitude_deg' not in station:
        return dict(status='unavailable',reason='missing_coordinates')
    lat,lon=station['latitude_deg'],station['longitude_deg']
    altitude=float(station.get('altitude_m',0))
    values=np.array([lat,lon,altitude],dtype=float)
    if not np.isfinite(values).all() or abs(lat)>90 or abs(lon)>180:
        raise ValueError('Invalid terrestrial coordinates for path station order')
    if abs(lat)==90:return dict(status='unavailable',reason='geographic_north_side_undefined')
    def at(seconds):
        utc=geometry.epoch+np.timedelta64(round(seconds*1e9),'ns')
        xyz=geometry.site_xyz(lat,lon,utc,altitude)
        return utc,xyz,xyz[:2]-geometry.center_xy(utc)
    def objective(seconds):
        utc,xyz,relative=at(seconds)
        return float(relative@relative) if geometry.site_star_sine(lat,lon,utc)>0 else np.inf
    grid=np.linspace(-3600,3600,241)
    distances=np.array([objective(s) for s in grid])
    i=int(np.argmin(distances))
    if not np.isfinite(distances[i]):
        return dict(status='unavailable',reason='star_below_horizon')
    if i in (0,len(grid)-1):
        return dict(status='unavailable',reason='closest_approach_outside_prediction_window')
    left,right=grid[i-1],grid[i+1]
    ratio=(np.sqrt(5)-1)/2
    a,b=right-ratio*(right-left),left+ratio*(right-left)
    fa,fb=objective(a),objective(b)
    while right-left>1e-4:
        if fa<fb:
            right,b,fb=b,a,fa;a=right-ratio*(right-left);fa=objective(a)
        else:
            left,a,fa=a,b,fb;b=left+ratio*(right-left);fb=objective(b)
    seconds=(left+right)/2
    utc,xyz,relative=at(seconds)
    if geometry.site_star_sine(lat,lon,utc)<=1e-8:return dict(status='unavailable',reason='closest_approach_at_visibility_boundary')
    velocity=-(at(seconds+.1)[2]-at(seconds-.1)[2])/.2
    speed=float(np.linalg.norm(velocity))
    if speed<1e-10:return dict(status='unavailable',reason='degenerate_relative_motion')
    normal=np.array([-velocity[1],velocity[0]])/speed
    # A centered geodetic tangent also works close to either geographic pole.
    lower=max(-90.,lat-.0001);upper=min(90.,lat+.0001)
    north=geometry.site_xyz(upper,lon,utc,altitude)[:2]-geometry.site_xyz(lower,lon,utc,altitude)[:2]
    length=float(np.linalg.norm(north))
    alignment=float(normal@north)/length if length else 0.
    if abs(alignment)<1e-8:
        return dict(status='unavailable',reason='geographic_north_side_undefined')
    if alignment<0:normal=-normal
    return dict(status='computed',closest_approach_utc=str(utc),
                cross_track_km=float(relative@normal*EARTH_A_KM),
                along_track_residual_km=float(relative@(velocity/speed)*EARTH_A_KM),
                closest_separation_fp_km=float(np.linalg.norm(relative)*EARTH_A_KM),
                relative_speed_km_s=speed*EARTH_A_KM,
                north_alignment=abs(alignment),normal_fp=normal.tolist())
