"""Lay out a common piecewise UTC axis, explicitly marking omitted intervals."""
import numpy as np


class UtcAxis:
    """Map retained UTC intervals proportionally to pixels, with visible breaks.

    Optional durations in playback seconds compress accelerated transit while
    preserving a continuous UTC axis. Optional relative speeds identify
    accelerated intervals with shaded bands and double-slash compression marks;
    actual omissions retain their existing breaks.
    Input intervals are increasing datetime64[ns] pairs in UTC; positions are
    canvas pixels. Omitted times return None. Curves must reset across segments
    so a line cannot bridge a cut. The axis changes display only, never UTC.
    """
    def __init__(self, intervals, left=116, right=898, durations=None, speeds=None):
        durations = durations if durations is not None else [float((b-a)/np.timedelta64(1, 's')) for a,b in intervals]
        if len(durations)!=len(intervals) or not np.isfinite(durations).all() or min(durations)<=0:
            raise ValueError('Positive finite axis duration required for each interval')
        self.speeds = speeds if speeds is not None else [1.]*len(intervals)
        if len(self.speeds)!=len(intervals) or not np.isfinite(self.speeds).all() or min(self.speeds)<1:
            raise ValueError('One finite relative speed >=1 per UTC interval is required')
        breaks = [a[1] < b[0] for a,b in zip(intervals,intervals[1:])]
        total = sum(durations)
        gap = min(22., (right-left)/(2*len(intervals)))
        width = right-left-gap*sum(breaks)
        self.segments = []
        cursor = left
        for i, ((start, stop), duration) in enumerate(zip(intervals, durations)):
            end = cursor+width*duration/total
            self.segments.append((start,stop,cursor,end))
            cursor = end+(gap if i<len(breaks) and breaks[i] else 0)

    def position(self, utc):
        for start, stop, left, right in self.segments:
            if start <= utc <= stop:
                return left+float((utc-start)/(stop-start))*(right-left)
        return None

    def segment_id(self, utc):
        return next((i for i,(a,b,_,_) in enumerate(self.segments) if a<=utc<=b), None)

    def spans(self, start, stop):
        """Yield pixel spans for interval intersections; omitted gaps are empty."""
        for a,b,_,_ in self.segments:
            lo,hi=max(a,start),min(b,stop)
            if lo < hi:
                yield self.position(lo),self.position(hi)

    def draw(self, draw, y, font, format_clock, gap_label='Gap'):
        """Draw UTC ticks and distinguish both compressed and omitted time.

        ``gap_label`` is localized display text. Compression annotations use
        relative gap/event speed, independent of any final playback rescaling.
        Marking compression changes no pixel-to-UTC mapping or frame selection.
        """
        from .render_utc_compression import draw_compression
        labels=draw_compression(draw,self.segments,self.speeds,y,font,gap_label)
        ticks=[]
        for (a,b,left,right),speed in zip(self.segments,self.speeds):
            if speed>1:continue
            span=float((b-a)/np.timedelta64(1, 's'))
            target=max(2., (right-left)/112)
            tick=next((s for s in (1,2,5,10,30,60,300,600,3600) if s>=span/target),3600)
            seconds=int(a.astype('datetime64[s]').astype('int64'))
            time=np.datetime64((seconds//tick+1)*tick,'s').astype('datetime64[ns]')
            while time<b:
                px=self.position(time)
                draw.line((px,y+68,px,y+244),fill=(32,45,67))
                ticks.append((px,format_clock(time)[:8]))
                time+=np.timedelta64(tick,'s')
        last_right=self.segments[0][2]
        for px,text in sorted(ticks):
            bounds=font.getbbox(text);half=(bounds[2]-bounds[0])/2
            if px-half<last_right+8 or px+half>self.segments[-1][3]:continue
            if any(px+half+8>left and px-half-8<right for left,right in labels):continue
            draw.text((px,y+253),text,font=font,fill=(189,200,217),anchor='mt')
            last_right=px+half
        for previous,following in zip(self.segments,self.segments[1:]):
            if previous[1] == following[0]:continue
            center=(previous[3]+following[2])/2
            draw.rectangle((previous[3]+2,y+66,following[2]-2,y+246),fill=(9,13,22))
            for offset in (-4,3):
                draw.line((center+offset-3,y+249,center+offset+3,y+239),fill=(249,236,181),width=2)


def coordinate_label(cfg):
    """Return signed terrestrial degrees as cardinal labels; empty if unknown."""
    if 'latitude_deg' not in cfg:
        return ''
    lat,lon=cfg['latitude_deg'],cfg['longitude_deg']
    return f'{abs(lat):.5f}° {"N" if lat>=0 else "S"} · {abs(lon):.5f}° {"E" if lon>=0 else "W"}'
