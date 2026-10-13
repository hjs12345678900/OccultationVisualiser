"""Label Natural Earth cities and geographic north in the oblique map view."""
from pathlib import Path
import json
from functools import lru_cache
import numpy as np
from PIL import ImageDraw
from .platform_runtime import load_font


def overlaps(a, b):
    return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]


@lru_cache(maxsize=1)
def city_records():
    """Load immutable offline city metadata once, including in follow mode."""
    cities=json.loads((Path(__file__).parent/'assets/maps/cities.json').read_text(encoding='utf-8'))
    return tuple(sorted(cities,key=lambda c:(c['rank'],-c['population'])))


class MapLandmarks:
    """Cache collision-aware city labels and a local, projected north arrow.

    City coordinates are geodetic degrees from Natural Earth populated places;
    their priority is ascending source scalerank then descending population.
    Only labels fully inside the existing viewport are drawn: cities never
    change the shadow-path framing. The compass differentiates geographic
    north through the same oblique projection at the arrow's map location.
    """
    def __init__(self, panel):
        self.font=load_font(20,'en')
        l,t,r,b=panel.rect
        self.origin=np.array([r-l-65.,65.])
        xy=(self.origin+[l,t]-[(l+r)/2,(t+b)/2])/[panel.scale,-panel.scale]+panel.midpoint
        self.reference=panel.projection.inverse(xy)
        delta=panel.projection.project(self.reference+[.001,0])-panel.projection.project(self.reference)
        delta*= [1,-1]
        self.north=delta/np.linalg.norm(delta)
        self.tip=self.origin+40*self.north
        self.labels=[]
        # Leave space around the compass and colored station markers.
        occupied=[(r-l-125,0,r-l,130)]
        for _,point in panel.station_points:
            x,y=panel.map_pixels(point)-[l,t]
            occupied.append((x-12,y-12,x+12,y+12))
        for city in city_records():
            x,y=panel.map_pixels(panel.projection.project([city['latitude'],city['longitude']]))-[l,t]
            if not (8<x<r-l-8 and 8<y<b-t-8):continue
            box=self.font.getbbox(city['name']);w,h=box[2]-box[0],box[3]-box[1]
            for dx,dy in ((18,-h-18),(18,18),(-w-18,-h-18),(-w-18,18)):
                label=(x+dx-3,y+dy-3,x+dx+w+3,y+dy+h+3)
                if label[0]<4 or label[1]<4 or label[2]>r-l-4 or label[3]>b-t-4:continue
                if any(overlaps(label,other) for other in occupied):continue
                self.labels.append((city['name'],(x,y),(x+dx,y+dy)))
                occupied.append(label);break
            if len(self.labels)>=10:break

    def draw(self, image):
        """Draw neutral cities and compass; station colors are drawn afterward."""
        draw=ImageDraw.Draw(image)
        for name,(x,y),position in self.labels:
            draw.ellipse((x-3,y-3,x+3,y+3),fill=(228,237,240),outline=(12,22,29))
            draw.text(position,name,font=self.font,anchor='lt',fill=(228,237,240),
                      stroke_width=2,stroke_fill=(13,25,33))
        tail=self.origin-15*self.north;tip=self.tip;side=np.array([-self.north[1],self.north[0]])
        draw.line([tuple(tail),tuple(tip)],fill=(235,241,244),width=3)
        draw.polygon([tuple(tip),tuple(tip-12*self.north+6*side),tuple(tip-12*self.north-6*side)],fill=(235,241,244))
        draw.text(tuple(tip+16*self.north),'N',font=self.font,anchor='mm',fill=(235,241,244),
                  stroke_width=2,stroke_fill=(13,25,33))
