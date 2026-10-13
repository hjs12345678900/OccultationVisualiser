"""Scientific core: Occult shadow position and rotating terrestrial observers.

Field order and Earth constants are verified against Astrid/Steve Preston:
https://github.com/ChasinSpin/astrid/blob/11a3d320cc675567f1c28514585ff7a9c1a8cf28/app/pathcomputation.py
The independent ray/ellipsoid solution uses the supplied apparent star direction
and substellar longitude. There is no photometric fit or timing adjustment.
"""
from dataclasses import dataclass
import math
import numpy as np

EARTH_A_KM = 6378.14
EARTH_B_KM = 6356.755
AXIS_RATIO = EARTH_B_KM / EARTH_A_KM
ROTATION_RAD_H = 0.2625161


@dataclass(frozen=True)
class ShadowGeometry:
    """Cubic center trajectory in the Bessel fundamental plane.

    epoch is datetime64[ns] UTC; coefficients is float64 (4,2), storing
    constant, linear, quadratic and cubic terms in Earth radii and UT hours.
    Angles are radians. diameter_km describes a nominal circular silhouette;
    neither its uncertainty nor astrometric errors are propagated here.
    """
    epoch: np.datetime64
    coefficients: np.ndarray
    substar_lon_rad: float
    dec_rad: float
    diameter_km: float
    object_name: str
    star_name: str
    provenance: str

    def hours(self, utc):
        """Return scalar UT hours from epoch; reject NaT or >1 h extrapolation.

        The cubic is an event-local trajectory. The one-hour guard prevents a
        wrong recording/date from silently being presented as an event position.
        It is a display validation limit, not an ephemeris accuracy guarantee.
        """
        stamp = np.datetime64(utc, 'ns')
        if np.isnat(stamp):
            raise ValueError('Shadow simulation requires a valid UTC')
        hours = float((stamp-self.epoch)/np.timedelta64(1, 'h'))
        if abs(hours) > 1:
            raise ValueError('Frame UTC is more than one hour from the prediction epoch / 影像 UTC 与预报相差超过一小时')
        return hours

    def center_xy(self, utc):
        """Return (x,y) float64 (2,), in Earth radii at physical UTC."""
        h, c = self.hours(utc), self.coefficients
        return c[0] + h*(c[1] + h*(c[2] + h*c[3]))

    def project_surface(self, xy, utc):
        """Project fundamental-plane float64 (...,2) rays to geodetic degrees.

        Return float64 (...,2) [latitude, east longitude], NaN for rays missing
        the star-facing ellipsoid. In the star basis r=x*east+y*north+z*star;
        substitution into r_x²+r_y²+(r_z/q)²=1 gives a*z²+2*b*z+c=0.
        The larger root faces the star; geographic longitude wraps at ±180°.
        Surface height is zero and polar motion is omitted.
        """
        xy = np.asarray(xy, dtype=float)
        if xy.shape[-1] != 2:
            raise ValueError('Fundamental-plane coordinates require (...,2)')
        x, y = xy[..., 0], xy[..., 1]
        sd, cd, q = math.sin(self.dec_rad), math.cos(self.dec_rad), AXIS_RATIO
        a = cd*cd + sd*sd/q**2
        b = y*sd*cd*(1/q**2-1)
        c = x*x + y*y*(sd*sd+cd*cd/q**2)-1
        discriminant = b*b-a*c
        z = (-b+np.sqrt(np.maximum(0, discriminant)))/a
        u, vertical = z*cd-y*sd, z*sd+y*cd
        lat = np.degrees(np.arctan2(vertical, q*q*np.hypot(x, u)))
        lon = np.degrees(np.arctan2(x, u)+self.substar_lon_rad-ROTATION_RAD_H*self.hours(utc))
        result = np.stack((lat, (lon+180)%360-180), axis=-1)
        return np.where((discriminant >= 0)[..., None], result, np.nan)

    def site_xyz(self, latitude_deg, longitude_deg, utc, altitude_m=0):
        """Return site (x,y,z) (3,) in equatorial Earth radii at physical UTC.

        Latitude is geodetic, longitude east-positive, both signed degrees.
        altitude_m is height above the model ellipsoid, not a terrain/geoid
        correction. The positive z direction faces the star. The transform is
        the inverse of project_surface when altitude_m=0.
        """
        values = np.array([latitude_deg, longitude_deg, altitude_m], dtype=float)
        if not np.isfinite(values).all() or abs(latitude_deg)>90 or abs(longitude_deg)>180:
            raise ValueError('Invalid terrestrial coordinates for shadow simulation')
        lat, lon = np.radians(values[:2])
        height = altitude_m/(EARTH_A_KM*1000)
        n = 1/math.sqrt(1-(1-AXIS_RATIO**2)*math.sin(lat)**2)
        rho = (n+height)*math.cos(lat)
        vertical = (AXIS_RATIO**2*n+height)*math.sin(lat)
        theta = lon-self.substar_lon_rad+ROTATION_RAD_H*self.hours(utc)
        x, u = rho*math.sin(theta), rho*math.cos(theta)
        sd, cd = math.sin(self.dec_rad), math.cos(self.dec_rad)
        return np.array([x, vertical*cd-u*sd, vertical*sd+u*cd])

    def footprint(self, utc, vertices=128):
        """Return circular-shadow surface rim as (N,2) geodetic degrees.

        N defaults to 128 angular samples; NaN vertices mark nonintersecting
        horizon rays and must not be joined across the invisible arc. This is
        an instantaneous footprint, not the swept path boundary.
        """
        angles = np.linspace(0, 2*math.pi, vertices, endpoint=False)
        circle = np.column_stack((np.cos(angles), np.sin(angles)))
        return self.project_surface(self.center_xy(utc)+circle*self.diameter_km/(2*EARTH_A_KM), utc)

    def site_state(self, station, utc):
        """Return predicted FP separation km and circular coverage for a station.

        station has signed latitude_deg/longitude_deg and optional altitude_m.
        Absence of coordinates returns None; visibility uses the geodetic normal.
        This prediction is separate from measured D/R or actual light level.
        """
        if 'latitude_deg' not in station or 'longitude_deg' not in station:
            return None
        xyz = self.site_xyz(station['latitude_deg'], station['longitude_deg'], utc,
                            float(station.get('altitude_m', 0)))
        distance = float(np.linalg.norm(xyz[:2]-self.center_xy(utc))*EARTH_A_KM)
        visible = self.site_star_sine(station['latitude_deg'], station['longitude_deg'], utc)>0
        return dict(distance_fp_km=distance, star_above_horizon=bool(visible),
                    nominally_covered=bool(visible and distance<=self.diameter_km/2))

    def site_star_sine(self, latitude_deg, longitude_deg, utc):
        """Return sine of geometric star altitude above the geodetic horizon.

        Signed degree latitude/longitude specify the ellipsoid's local normal.
        n·s = sin(phi)sin(dec)+cos(phi)cos(dec)cos(H), where phi is geodetic
        latitude and H is longitude minus the rotating substellar longitude.
        The sign of geocentric fundamental-plane z is not this horizon test on
        an oblate Earth. Refraction and elevated-horizon dip are not modelled.
        """
        lat = math.radians(latitude_deg)
        hour_angle = math.radians(longitude_deg)-self.substar_lon_rad+ROTATION_RAD_H*self.hours(utc)
        return math.sin(lat)*math.sin(self.dec_rad)+math.cos(lat)*math.cos(self.dec_rad)*math.cos(hour_angle)
