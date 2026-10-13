"""Presentation-only fixed-scale camera for an overview or a following map."""
import numpy as np


def view_mode(value='full_path'):
    """Validate the stable JSON mode; old projects use a full-path overview."""
    if value not in ('full_path','follow_shadow'):
        raise ValueError('Map view must be full_path or follow_shadow / 请选择完整阴影路径或跟随小行星')
    return value


class ShadowMapView:
    """Keep projection/scale fixed, optionally translate to the physical center.

    Centers and rims are projected map km at densely sampled UTCs. Following
    uses three times the maximum footprint half-width/height over the whole
    clip, never a per-frame zoom. Geographic projection and scientific geometry
    are unchanged. If the center misses Earth, use the nearest valid sampled
    center; if none exists, retain the overview. This fallback is deterministic
    for preview/contact frames rendered out of order and does not invent UTCs.
    """
    def __init__(self, mode, times, centers, rims, diameter, size, midpoint, scale):
        self.mode=view_mode(mode)
        self.times=np.asarray(times)
        self.centers=np.asarray(centers,dtype=float)
        self.valid=np.isfinite(self.centers).all(axis=1)
        self.overview_midpoint=np.array(midpoint,copy=True)
        self.scale=scale
        if self.mode=='follow_shadow' and self.valid.any():
            half_extent=np.array([diameter/2,diameter/2],dtype=float)
            for center,rim,valid in zip(self.centers,rims,self.valid):
                if not valid:continue
                offsets=rim[np.isfinite(rim).all(axis=1)]-center
                if len(offsets):half_extent=np.maximum(half_extent,np.max(np.abs(offsets),axis=0))
            self.scale=float(np.min(np.asarray(size)/(6*half_extent)))

    def center(self, utc, position, projection):
        """Return map-km camera center; ``position`` is a real geographic center."""
        if self.mode=='full_path':return self.overview_midpoint.copy()
        if position is not None:
            return projection.project([position['latitude_deg'],position['longitude_deg']])
        if self.valid.any():
            index=np.argmin(abs(self.times[self.valid]-np.datetime64(utc,'ns')))
            return self.centers[self.valid][index].copy()
        return self.overview_midpoint.copy()
