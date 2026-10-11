"""Draw four target curves and their actual detector fields on one UTC axis."""
import numpy as np
from PIL import Image, ImageDraw
from .platform_runtime import load_font


def format_counts(value):
    return f'{value/1e6:.2g}M' if abs(value)>=1e6 else f'{value/1e3:.3g}K' if abs(value)>=1e3 else f'{value:.3g}'

SIZE = (1920,1440)
COLORS = [(92,170,255),(100,215,171),(249,207,111),(198,149,246)]


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
        self.span = float((stop-start)/np.timedelta64(1,'s'))
        self.font = load_font(21,language)
        self.small = load_font(17,language)
        self.size = (1920, 1440 if len(stations)==4 else 526)
        self.template = Image.new('RGB',self.size,(9,13,22))
        draw = ImageDraw.Draw(self.template)
        draw.text((28,22),f"{context['event']} · {context['target']} · {context['date_utc']}",
                  font=load_font(32,language,True),fill=(241,246,255))
        title = '目标光变（净计数 ADU）                  原始完整星场 + 目标细节' if language=='zh' else 'Target light curves (net ADU)                   Full recorded fields + target details'
        draw.text((28,64),title,font=self.font,fill=(184,198,220))
        for k,station in enumerate(stations):
            y = 105+k*305
            draw.rounded_rectangle((24,y,920,y+295),radius=12,fill=(12,20,34),outline=(40,57,82))
            draw.rounded_rectangle((944,y,1896,y+295),radius=12,fill=(12,20,34),outline=(40,57,82))
            color = COLORS[k]
            draw.text((42,y+10),station['config']['name'],font=load_font(24,language,True),fill=color)
            draw.text((965,y+10),station['config']['name'],font=load_font(24,language,True),fill=color)
            values = [r.counts for r in station['rows'] if r.valid and start<=r.utc<=stop]
            if not values: values = [r.counts for r in station['rows'] if r.valid]
            lo,hi = min(0.,min(values)),max(0.,max(values))
            pad = max(hi-lo,1.)*.1
            station['plot_limits'] = (lo-pad if lo<0 else 0.,hi+pad)
            for value in np.linspace(*station['plot_limits'],4):
                py = self.sy(k,value)
                draw.line((116,py,898,py),fill=(32,45,67))
                draw.text((103,py),format_counts(value),font=self.small,fill=(189,200,217),anchor='rm')
            tick_s = next((s for s in (1,2,5,10,30,60,300,600,3600) if s>=self.span/7),3600)
            seconds = int(start.astype('datetime64[s]').astype('int64'))
            minute = np.datetime64((seconds//tick_s+1)*tick_s,'s').astype('datetime64[ns]')
            while minute < stop:
                px = self.sx(minute)
                draw.line((px,y+52,px,y+244),fill=(32,45,67))
                draw.text((px,y+253),clock(minute)[:8],font=self.small,fill=(189,200,217),anchor='mt')
                minute += np.timedelta64(tick_s,'s')
            draw.rectangle((116,y+52,898,y+244),outline=(64,79,103),width=2)
        step=context['step_s']
        footer = f'统一绝对 UTC · 原始光变采样 · 无画面不补帧 · 展示间隔 {step:g} 秒（实时速度）' if language=='zh' else f'Shared absolute UTC · original curve cadence · no missing images synthesized · {step:g} s display steps (real time)'
        draw.text((28,self.size[1]-84),footer,font=self.font,fill=(188,203,222))
        self.footer = context['coverage_note'][language]

    def sx(self,utc):
        return 116+float((utc-self.start)/np.timedelta64(1,'s'))/self.span*782

    def sy(self,k,counts):
        lo,hi = self.stations[k]['plot_limits']
        return 105+k*305+244-(counts-lo)/(hi-lo)*192

    def render(self,utc,indices):
        """Return a RGB canvas; each image retains its own recorded UTC label."""
        image = self.template.copy()
        draw = ImageDraw.Draw(image,'RGBA')
        draw.text((1896,30),str(utc.astype('datetime64[D]'))+' '+clock(utc)+' UTC',font=load_font(32,self.language,True),fill=(249,236,181),anchor='ra')
        for k,(station,index) in enumerate(zip(self.stations,indices)):
            rows = station['rows']; y = 105+k*305
            d,r = station['D'],station['R']
            if d is not None and utc>=d:
                x = self.sx(d)
                draw.rectangle((max(116,x),y+52,min(898,self.sx(min(utc,r))),y+244),fill=(255,73,98,32))
                for boundary in (d,r):
                    if self.start<=boundary<=min(utc,self.stop):
                        px=self.sx(boundary);draw.line((px,y+52,px,y+244),fill=(255,73,98),width=2)
                note=f'D {clock(d)}'
                if utc>=r: note+=f' · R {clock(r)}'
                draw.text((898,y+13),note+' UTC',font=self.small,fill=(219,163,170),anchor='ra')
            predicted = station['config'].get('predicted_utc')
            if predicted and self.start<=np.datetime64(predicted,'ns')<=self.stop:
                px = self.sx(np.datetime64(predicted,'ns'))
                draw.line((px,y+52,px,y+244),fill=(117,170,224),width=2)
            previous=None
            for row in rows:
                if row.utc>utc: break
                if row.utc<self.start or not row.valid:
                    previous=None;continue
                point=(self.sx(row.utc),self.sy(k,row.counts))
                if previous is not None: draw.line((*previous,*point),fill=COLORS[k],width=2)
                draw.ellipse((point[0]-2,point[1]-2,point[0]+2,point[1]+2),fill=COLORS[k])
                previous=point
            px = self.sx(utc)
            draw.line((px,y+52,px,y+244),fill=(249,236,181,120),width=2)
            field = station['frames']
            if index is None or index not in field.prepared:
                msg='无画面：此 UTC 没有对应原始帧' if self.language=='zh' else 'No image at this UTC'
                draw.text((1420,y+145),msg,font=load_font(24,self.language),fill=(154,169,192),anchor='mm')
                continue
            row=rows[index]
            record = field.records[index]
            source_utc = np.datetime64(record['source_midpoint_utc'], 'ns')
            label = f'{clock(row.utc)} UTC · frame {row.frame}'
            draw.text((1876,y+16),label,font=self.small,fill=(198,208,224),anchor='ra')
            if source_utc != row.utc:
                draw.text((1876,y+42),f'Source {clock(source_utc)} UTC; curve above',font=self.small,fill=(154,169,192),anchor='ra')
            gray = field.prepared[index]
            frame=Image.fromarray(gray).convert('RGB')
            scale=min(620/frame.width,232/frame.height)
            w,h=round(frame.width*scale),round(frame.height*scale)
            left,top=962+(620-w)//2,y+48+(232-h)//2
            image.paste(frame.resize((w,h),Image.Resampling.LANCZOS),(left,top))
            xy=row.target_xy
            if xy is not None and np.isfinite(xy).all() and 0<=xy[0]<gray.shape[1] and 0<=xy[1]<gray.shape[0]:
                x,z=left+(xy[0]+.5)*scale,top+(xy[1]+.5)*scale
                draw.line((x+7,z-7,x+23,z-23),fill=(255,239,109),width=3)
                cx,cy=round(xy[0]),round(xy[1])
                crop=frame.crop((max(0,cx-18),max(0,cy-18),min(frame.width,cx+19),min(frame.height,cy+19)))
                image.paste(crop.resize((196,196),Image.Resampling.NEAREST),(1650,y+72))
                low=d is not None and d<=row.utc<r and utc>=d
                draw.rectangle((1647,y+69,1849,y+271),outline=(255,73,98) if low else COLORS[k],width=3)
        draw.text((28,self.size[1]-42),self.footer,font=self.small,fill=(168,183,204))
        return image
