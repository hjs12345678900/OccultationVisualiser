"""Draw four target curves and their actual detector fields on one UTC axis."""
import numpy as np
from PIL import Image, ImageDraw
from .platform_runtime import load_font
from .render_utc_axis import UtcAxis, coordinate_label
from .read_saved_snr import snr_label


def format_counts(value):
    return f'{value/1e6:.2g}M' if abs(value)>=1e6 else f'{value/1e3:.3g}K' if abs(value)>=1e3 else f'{value:.3g}'

SIZE = (1920,1440)
from .resolve_station_colors import station_colors


def clock(utc):
    """Format true UTC[ns] to milliseconds for an image label."""
    return utc.astype('datetime64[us]').item().strftime('%H:%M:%S.%f')[:-3]


class StationPanels:
    """Render original-cadence net ADU and nearest actual frames at global UTC.

    Rows have independent ADU scales and an identical absolute UTC x axis.
    No inter-station time shift, curve normalization, smoothing or interpolation
    is applied. Red D/R reveals only after the relevant station's transition.
    Full fields retain aspect/orientation; adjacent target details use real
    detector crops with the identical fixed whole-field stretch.
    """
    def __init__(self,stations,start,stop,language,context):
        self.stations,self.start,self.stop,self.language = stations,start,stop,language
        self.colors=station_colors([s['config'] for s in stations])
        self.span = float((stop-start)/np.timedelta64(1,'s'))
        self.timeline_plan = context.get('timeline_plan', {})
        segment_plan=self.timeline_plan.get('segments')
        self.axis = UtcAxis(context.get('intervals', [(start,stop)]),
                            durations=self.timeline_plan.get('axis_durations_s'),
                            speeds=[s['speed'] for s in segment_plan] if segment_plan else None)
        self.font = load_font(21,language)
        self.small = load_font(17,language)
        self.size = (1920, max(526, (220 + 305*len(stations) + 1)//2*2))
        self.base_size=self.size
        self.shadow_panel=None
        if context.get('shadow_simulation') is not None:
            from .render_shadow_map import ShadowMapPanel
            self.base_size=(1920,(108+305*len(stations))//2*2)
            self.size=self.base_size
            self.shadow_panel=ShadowMapPanel(context['shadow_simulation'],language)
            self.size=(self.size[0],self.size[1]+self.shadow_panel.size[1])
        self.template = Image.new('RGB',self.size,(9,13,22))
        draw = ImageDraw.Draw(self.template)
        draw.text((28,22),f"{context['event']} · {context['target']} · {context['date_utc']}",
                  font=load_font(32,language,True),fill=(241,246,255))
        title = '目标光变（净计数 ADU）                  原始影像 + 目标细节' if language=='zh' else 'Target light curves (net ADU)                   Recorded images + target details'
        draw.text((28,64),title,font=self.font,fill=(184,198,220))
        for k,station in enumerate(stations):
            y = 105+k*305
            draw.rounded_rectangle((24,y,920,y+295),radius=12,fill=(12,20,34),outline=(40,57,82))
            draw.rounded_rectangle((944,y,1896,y+295),radius=12,fill=(12,20,34),outline=(40,57,82))
            color = self.colors[k]
            draw.text((42,y+10),station['config']['name'],font=load_font(24,language,True),fill=color)
            draw.text((965,y+10),station['config']['name'],font=load_font(24,language,True),fill=color)
            details=' · '.join(v for v in (coordinate_label(station['config']),snr_label(station.get('snr',{}),language)) if v)
            observer=station['config'].get('observer','').strip()
            font=load_font(15,language)
            if observer:
                credit=('观测者：' if language=='zh' else 'Observer: ')+' '.join(observer.split())
                details=' · '.join(v for v in (details,credit) if v)
                # Fit attribution on the existing metadata line, clear of the plot ticks.
                # Full supplied text is retained in the saved configuration and metadata.
                if draw.textlength(details,font=font)>856:
                    while details and draw.textlength(details+'…',font=font)>856:details=details[:-1]
                    details+='…'
            draw.text((42,y+34),details,font=font,fill=(189,200,217))
            values = [r.counts for r in station['rows'] if r.valid and self.sx(r.utc) is not None]
            if not values: values = [r.counts for r in station['rows'] if r.valid]
            lo,hi = min(0.,min(values)),max(0.,max(values))
            pad = max(hi-lo,1.)*.1
            station['plot_limits'] = (lo-pad if lo<0 else 0.,hi+pad)
            for value in np.linspace(*station['plot_limits'],4):
                py = self.sy(k,value)
                draw.line((116,py,898,py),fill=(32,45,67))
                draw.text((103,py),format_counts(value),font=self.small,fill=(189,200,217),anchor='rm')
            draw.rectangle((116,y+68,898,y+244),outline=(64,79,103),width=2)
            self.axis.draw(draw,y,self.small,clock,gap_label='空档' if language=='zh' else 'Gap')
    def sx(self,utc):
        return self.axis.position(utc)

    def sy(self,k,counts):
        lo,hi = self.stations[k]['plot_limits']
        return 105+k*305+244-(counts-lo)/(hi-lo)*176

    def render(self,utc,indices):
        """Return a RGB canvas; each image retains its own recorded UTC label."""
        image = self.template.copy()
        draw = ImageDraw.Draw(image,'RGBA')
        draw.text((1896,30),str(utc.astype('datetime64[D]'))+' '+clock(utc)+' UTC',font=load_font(32,self.language,True),fill=(249,236,181),anchor='ra')
        for k,(station,index) in enumerate(zip(self.stations,indices)):
            rows = station['rows']; y = 105+k*305
            d,r = station['D'],station['R']
            if d is not None and utc>=d:
                for x1,x2 in self.axis.spans(d,min(utc,r)):
                    draw.rectangle((x1,y+68,x2,y+244),fill=(255,73,98,32))
                for boundary in (d,r):
                    px=self.sx(boundary)
                    if px is not None and boundary<=utc:
                        draw.line((px,y+68,px,y+244),fill=(255,73,98),width=2)
                note=f'D {clock(d)}'
                if utc>=r: note+=f' · R {clock(r)}'
                draw.text((898,y+13),note+' UTC',font=self.small,fill=(219,163,170),anchor='ra')
            predicted = station['config'].get('predicted_utc')
            if predicted and self.sx(np.datetime64(predicted,'ns')) is not None:
                px = self.sx(np.datetime64(predicted,'ns'))
                draw.line((px,y+68,px,y+244),fill=(117,170,224),width=2)
            previous=None
            for row in rows:
                if row.utc>utc: break
                x=self.sx(row.utc)
                if x is None or not row.valid:
                    previous=None;continue
                point=(x,self.sy(k,row.counts))
                segment=self.axis.segment_id(row.utc)
                if previous is not None and previous_segment==segment: draw.line((*previous,*point),fill=self.colors[k],width=2)
                draw.ellipse((point[0]-2,point[1]-2,point[0]+2,point[1]+2),fill=self.colors[k])
                previous=point;previous_segment=segment
            px = self.sx(utc)
            draw.line((px,y+68,px,y+244),fill=(249,236,181,120),width=2)
            field = station['frames']
            if index is None or index not in field.prepared:
                msg='无画面：此 UTC 没有对应原始帧' if self.language=='zh' else 'No image at this UTC'
                draw.text((1420,y+145),msg,font=load_font(24,self.language),fill=(154,169,192),anchor='mm')
                continue
            row=rows[index]
            record = field.records[index]
            source_utc = np.datetime64(record['source_midpoint_utc'], 'ns') if record['source_midpoint_utc'] else None
            label = f'{clock(row.utc)} UTC · frame {row.frame}'
            draw.text((1876,y+16),label,font=self.small,fill=(198,208,224),anchor='ra')
            if source_utc is None:
                note = 'AVI 帧号对应 · UTC 来自曲线' if self.language=='zh' else 'AVI frame mapping · UTC from curve'
                draw.text((1876,y+42),note,font=self.small,fill=(154,169,192),anchor='ra')
            elif source_utc != row.utc:
                draw.text((1876,y+42),f'Source {clock(source_utc)} UTC; curve above',font=self.small,fill=(154,169,192),anchor='ra')
            if field.cfg.get('source','').lower().endswith('.lc'):
                draw.text((965,y+40),'LC target cutout (35 × 35)',font=self.small,fill=(198,208,224))
            gray = field.prepared[index]
            frame=Image.fromarray(gray).convert('RGB')
            scale=min(620/frame.width,232/frame.height)
            w,h=round(frame.width*scale),round(frame.height*scale)
            left,top=962+(620-w)//2,y+48+(232-h)//2
            image.paste(frame.resize((w,h),Image.Resampling.LANCZOS),(left,top))
            xy=(17.,17.) if field.cfg.get('source','').lower().endswith('.lc') else row.target_xy
            if xy is not None and np.isfinite(xy).all() and 0<=xy[0]<gray.shape[1] and 0<=xy[1]<gray.shape[0]:
                x,z=left+(xy[0]+.5)*scale,top+(xy[1]+.5)*scale
                draw.line((x+7,z-7,x+23,z-23),fill=(255,239,109),width=3)
                cx,cy=round(xy[0]),round(xy[1])
                crop=frame.crop((max(0,cx-18),max(0,cy-18),min(frame.width,cx+19),min(frame.height,cy+19)))
                image.paste(crop.resize((196,196),Image.Resampling.NEAREST),(1650,y+72))
                low=d is not None and d<=row.utc<r and utc>=d
                draw.rectangle((1647,y+69,1849,y+271),outline=(255,73,98) if low else self.colors[k],width=3)
        if self.shadow_panel is not None:
            image.paste(self.shadow_panel.render(utc,indices),(0,self.base_size[1]))
        return image
