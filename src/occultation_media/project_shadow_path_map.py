"""Scientific drawing geometry: a spherical oblique Mercator along the path.

The geographic grid is rotated BEFORE projection, together with coastlines,
stations and the geodetic shadow rim. This is not an image rotation/stretch.
Projection references: PROJ, General Oblique Transformation (new equator points)
and Mercator, Mathematical definition / Spherical form:
https://proj.org/en/stable/operations/projections/ob_tran.html
https://proj.org/en/stable/operations/projections/merc.html
The drawing sphere uses the model equatorial radius; physical shadow positions
remain those calculated on the oblate ellipsoid by ShadowGeometry.
"""
import numpy as np
from .compute_shadow_geometry import EARTH_A_KM


def geographic_vectors(latlon):
    """Map float64 (...,2) [latitude, east longitude] degrees to unit (...,3)."""
    values = np.radians(np.asarray(latlon, dtype=float))
    lat, lon = values[...,0], values[...,1]
    return np.stack((np.cos(lat)*np.cos(lon), np.cos(lat)*np.sin(lon), np.sin(lat)), axis=-1)


class PathMapProjection:
    """Project a fixed Earth map with event motion directed left to right.

    start/end are geodetic [latitude,longitude] degrees along increasing UTC.
    Their great circle defines the new equator. A degenerate/single-position
    path uses the geographic east tangent as a deterministic fallback.
    """
    def __init__(self, start, end):
        a,b = geographic_vectors([start,end])
        pole = np.cross(a,b)
        if np.linalg.norm(pole)<1e-10:
            east = np.array([-a[1],a[0],0.])
            if np.linalg.norm(east)<1e-10:east=np.array([0.,1.,0.])
            pole = np.cross(a,east)
        pole /= np.linalg.norm(pole)
        origin = a+b
        if np.linalg.norm(origin)<1e-10:origin=a.copy()
        origin /= np.linalg.norm(origin)
        along = np.cross(pole,origin)
        self.basis = np.array([origin,along,pole])

    def project(self, latlon):
        """Return float64 (...,2) [along,across] map km, retaining input NaNs.

        With rotated unit vector (u,v,w), lambda'=atan2(v,u), phi'=asin(w),
        X=R*lambda', Y=R*atanh(w). R is EARTH_A_KM. Draw latitude is clamped
        at the rotated poles to keep remote coastline vertices finite. This
        projection does not change physical UTC, Earth coordinates or coverage.
        """
        rotated = geographic_vectors(latlon)@self.basis.T
        x = np.arctan2(rotated[...,1],rotated[...,0])
        y = np.arctanh(np.clip(rotated[...,2],-1+1e-12,1-1e-12))
        return EARTH_A_KM*np.stack((x,y),axis=-1)

    def inverse(self, xy):
        """Return geodetic draw-sphere degrees for (...,2) projected map km.

        This inverse locates a compass reference on the rotated map. It is a
        drawing operation, not an inverse of the physical ellipsoid shadow.
        """
        values = np.asarray(xy, dtype=float)/EARTH_A_KM
        lam, height = values[...,0], values[...,1]
        phi = np.arctan(np.sinh(height))
        rotated = np.stack((np.cos(phi)*np.cos(lam),np.cos(phi)*np.sin(lam),np.sin(phi)),axis=-1)
        geographic = rotated@self.basis
        return np.degrees(np.stack((np.arcsin(np.clip(geographic[...,2],-1,1)),
                                   np.arctan2(geographic[...,1],geographic[...,0])),axis=-1))
