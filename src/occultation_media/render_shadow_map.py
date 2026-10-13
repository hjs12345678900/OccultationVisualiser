"""Draw a full-width, path-aligned map and moving nominal asteroid shadow.

The same oblique geographic projection applies to country polygons, stations,
path and instantaneous shadow. The viewport fits the full corridor or follows
the shadow center at a fixed scale,
and uses equal map-km pixel scales. Station colors match the light-curve rows.
"""
import numpy as np
from PIL import Image, ImageDraw
from .platform_runtime import load_font
from .project_shadow_path_map import PathMapProjection

from .resolve_station_colors import station_colors


class ShadowMapPanel:
    """Cache a tightly framed path map, then move the silhouette by true UTC.

    size is even RGB pixels. Unknown stations have no invented map coordinates.
    Coastlines are bundled Natural Earth vectors. The sweep is a display-only
    union of instantaneous footprints, sampled densely enough to overlap;
    input frame clocks, positions, and station coverage are not modified.
    """
    def __init__(self, simulation, language, size=(1920,540)):
        self.simulation,self.language,self.size=simulation,language,size
        self.colors=station_colors([s['config'] for s in simulation.stations])
        self.small=load_font(17,language)
        self.rect=(36,58,size[0]-36,size[1]-52)
        start,end=simulation.timeline[0],simulation.timeline[-1]
        seconds=float((end-start)/np.timedelta64(1,'s'))
        geometry=simulation.geometry
        speed=np.linalg.norm(geometry.coefficients[1])*6378.14/3600
        step=min(1.,geometry.diameter_km/max(speed*8,1))
        count=min(5000,max(2,int(np.ceil(seconds/step))+1))
        offsets=np.rint(np.linspace(0,seconds*1e9,count)).astype('int64')
        self.times=start+offsets.astype('timedelta64[ns]')
        centers=[simulation.position(t) for t in self.times]
        geographic=[(p['latitude_deg'],p['longitude_deg']) for p in centers if p is not None]
        self.has_shadow_path=bool(geographic)
        known=[s['config'] for s in simulation.stations if 'latitude_deg' in s['config']]
        if not geographic:geographic=[(c['latitude_deg'],c['longitude_deg']) for c in known] or [(0,0)]
        if len(geographic)==1:
            p=simulation.position(start+np.timedelta64(1,'s'))
            if p is not None:geographic.append((p['latitude_deg'],p['longitude_deg']))
        self.projection=PathMapProjection(geographic[0],geographic[-1])
        self.path=self.projection.project(geographic)
        self.rims=[self.projection.project(geometry.footprint(t,64)) for t in self.times]
        positions=[self.path,*[p[np.isfinite(p).all(axis=1)] for p in self.rims]]
        self.station_points=[]
        for k,c in enumerate(s['config'] for s in simulation.stations):
            if 'latitude_deg' not in c:continue
            point=self.projection.project([c['latitude_deg'],c['longitude_deg']])
            self.station_points.append((k,point));positions.append(point[None,:])
        points=np.concatenate(positions)
        low,high=np.min(points,axis=0),np.max(points,axis=0)
        midpoint=(low+high)/2
        extent=np.maximum(high-low+geometry.diameter_km*.9,geometry.diameter_km*2.5)
        width,height=self.rect[2]-self.rect[0],self.rect[3]-self.rect[1]
        self.scale=min(width/extent[0],height/extent[1])
        from .plan_shadow_map_view import ShadowMapView
        center_points=self.projection.project([[p['latitude_deg'],p['longitude_deg']] if p else [np.nan,np.nan] for p in centers])
        self.camera=ShadowMapView(simulation.evidence.get('view_mode','full_path'),self.times,
            center_points,self.rims,geometry.diameter_km,(width,height),midpoint,self.scale)
        self.scale=self.camera.scale
        self.midpoint=self.camera.center(start,simulation.position(start),self.projection)
        from .render_shadow_background import ShadowBackground
        self.background=ShadowBackground(self)
        from .render_map_landmarks import MapLandmarks
        self.landmarks=MapLandmarks(self)
        self.template=self._template()

    def map_pixels(self, xy):
        """Map float64 (...,2) projected km to floating screen (...,2) pixels."""
        l,t,r,b=self.rect
        pixels=(np.asarray(xy)-self.midpoint)*[self.scale,-self.scale]
        return pixels+[(l+r)/2,(t+b)/2]

    def screen(self, lat, lon):
        """Return integer map pixels for signed geodetic degree coordinates."""
        return tuple(np.rint(self.map_pixels(self.projection.project([lat,lon]))).astype(int))

    def _template(self):
        image=Image.new('RGB',self.size,(9,13,22));draw=ImageDraw.Draw(image)
        title='小行星阴影移动' if self.language=='zh' else 'Asteroid shadow motion'
        if self.camera.mode=='follow_shadow':title+=' · 跟随' if self.language=='zh' else ' · Follow'
        draw.text((36,12),title,font=load_font(23,self.language,True),fill=(231,240,251))
        l,t,r,b=self.rect
        viewport=self.background.render(self)
        image.paste(viewport,(l,t));draw.rectangle(self.rect,outline=(59,78,99),width=1)
        x=36
        for k,s in enumerate(self.simulation.stations):
            text=s['config']['name'];color=self.colors[k]
            draw.ellipse((x,b+17,x+10,b+27),fill=color)
            draw.text((x+17,b+12),text,font=self.small,fill=color)
            x+=draw.textbbox((0,0),text,font=self.small)[2]+42
        draw.text((r,b+15),'Natural Earth',font=load_font(13,'en'),fill=(110,132,151),anchor='ra')
        return image

    def render(self, utc, indices):
        """Return RGB map only, with an actual nominal silhouette at global UTC.

        indices are accepted for the shared renderer API; no frame-information
        sidebar or repeated coordinate/status text is drawn. Colored stations
        remain visible over the silhouette to identify chord positions.
        """
        if self.camera.mode=='follow_shadow':
            center=self.camera.center(utc,self.simulation.position(utc),self.projection)
            if not np.array_equal(center,self.midpoint):
                self.midpoint=center
                from .render_map_landmarks import MapLandmarks
                self.landmarks=MapLandmarks(self)
                self.template=self._template()
        image=self.template.copy();l,t,r,b=self.rect
        viewport=image.crop(self.rect);draw=ImageDraw.Draw(viewport,'RGBA')
        rim=self.projection.project(self.simulation.geometry.footprint(utc))
        pixels=self.map_pixels(rim)-[l,t];valid=np.isfinite(pixels).all(axis=1)
        if valid.all():
            points=[tuple(p) for p in pixels]
            draw.polygon(points,fill=(5,8,12,225))
            draw.line(points+[points[0]],fill=(246,221,156),width=3)
        else:
            for a,c,ok in zip(pixels,np.roll(pixels,-1,axis=0),valid & np.roll(valid,-1)):
                if ok:draw.line([tuple(a),tuple(c)],fill=(246,221,156),width=3)
        self.landmarks.draw(viewport)
        draw=ImageDraw.Draw(viewport,'RGBA')
        for k,point in self.station_points:
            x,y=self.map_pixels(point)-[l,t]
            color=self.colors[k]
            draw.ellipse((x-7,y-7,x+7,y+7),fill=color,outline=(8,12,19),width=2)
        image.paste(viewport,(l,t))
        draw=ImageDraw.Draw(image)
        stamp=str(np.datetime64(utc,'ms')).split('T')[1]
        draw.text((r,14),stamp+' UTC',font=load_font(21,self.language),fill=(239,224,184),anchor='ra')
        return image
