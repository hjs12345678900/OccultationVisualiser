"""Cache projected offline geography and corridor, then draw a moving viewport."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from .compute_shadow_geometry import EARTH_A_KM


class ShadowBackground:
    """Retain map-km vectors, not a giant raster or repeatedly reloaded assets."""
    def __init__(self, panel):
        self.coasts=[]
        asset=Path(__file__).parent/'assets/maps/countries.geojson'
        for feature in json.loads(asset.read_text(encoding='utf-8'))['features']:
            geom=feature['geometry']
            polygons=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
            for polygon in polygons:
                points=panel.projection.project(np.asarray(polygon[0])[:,::-1])
                # A projection seam is geographic, independent of camera zoom.
                if not np.isfinite(points).all() or (abs(np.diff(points[:,0]))>np.pi*EARTH_A_KM).any():continue
                self.coasts.append(points)
        self.rims=[rim for rim in panel.rims if np.isfinite(rim).all()]
        self.coast_bounds=self.bounds(self.coasts)
        self.rim_bounds=self.bounds(self.rims)

    @staticmethod
    def bounds(polygons):
        """Return (N,2,2) map-km min/max boxes, including an empty layer."""
        return np.array([[p.min(axis=0),p.max(axis=0)] for p in polygons]).reshape(-1,2,2)

    @staticmethod
    def visible(bounds, low, high):
        """Return polygon indices whose bounding boxes intersect the viewport."""
        return np.flatnonzero((bounds[:,1]>=low).all(axis=1)&(bounds[:,0]<=high).all(axis=1))

    def render(self, panel):
        """Draw offline terrain/path at the camera's current translation."""
        l,t,r,b=panel.rect
        size=(r-l,b-t);half=np.asarray(size)/(2*panel.scale)
        low,high=panel.midpoint-half,panel.midpoint+half
        viewport=Image.new('RGB',size,(19,35,51));draw=ImageDraw.Draw(viewport)
        for i in self.visible(self.coast_bounds,low,high):
            points=panel.map_pixels(self.coasts[i])-[l,t]
            draw.polygon([tuple(p) for p in points],fill=(46,61,61),outline=(93,116,122))
        mask=Image.new('L',size);sweep=ImageDraw.Draw(mask)
        for i in self.visible(self.rim_bounds,low,high):
            points=panel.map_pixels(self.rims[i])-[l,t]
            sweep.polygon([tuple(p) for p in points],fill=34)
        viewport.paste(Image.new('RGB',size,(146,169,166)),(0,0),mask)
        if panel.has_shadow_path and len(panel.path)>1:
            path=panel.map_pixels(panel.path)-[l,t]
            ImageDraw.Draw(viewport).line([tuple(p) for p in path],fill=(147,164,176),width=2)
        return viewport
