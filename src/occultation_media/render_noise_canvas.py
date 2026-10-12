"""Draw saved baseline counts on shared UTC without interpolation or shifting."""
import numpy as np


def draw_pair(canvas,pair):
    """Plot B-normalized raw samples; never connect across rejected frame IDs.

    This interactive desktop preview is a descriptive count scatter plot.
    The exported JSON preserves all plotted UTC/frame/value arrays.
    """
    canvas.delete('all');w=max(canvas.winfo_width(),650);h=max(canvas.winfo_height(),180)
    if not pair.get('available'):
        canvas.create_text(w/2,h/2,text='没有共同 UTC 基线 / No comparable UTC baseline',fill='#666');return
    start=np.datetime64(pair['start_utc']);stop=np.datetime64(pair['end_utc'])
    duration=float((stop-start)/np.timedelta64(1,'s'))
    profiles=pair['profiles'];values=[v for p in profiles for v in p['normalized_counts']]
    lower,upper=min(values),max(values);padding=max((upper-lower)*.08,.02)
    lower-=padding;upper+=padding
    left,right,top,bottom=58,w-22,25,h-32
    for y in np.linspace(lower,upper,4):
        py=bottom-(y-lower)/(upper-lower)*(bottom-top)
        canvas.create_line(left,py,right,py,fill='#e5e5e5')
        canvas.create_text(left-5,py,text=f'{y:.2f}',anchor='e',fill='#555')
    for p,color in zip(profiles,('#2875b8','#d65b28')):
        for stamp,value in zip(p['utc'],p['normalized_counts']):
            seconds=float((np.datetime64(stamp)-start)/np.timedelta64(1,'s'))
            x=left+seconds/duration*(right-left);y=bottom-(value-lower)/(upper-lower)*(bottom-top)
            canvas.create_oval(x-1.5,y-1.5,x+1.5,y+1.5,fill=color,outline='')
    canvas.create_text(left,bottom+16,text=pair['start_utc'].split('T')[1],anchor='w')
    canvas.create_text(right,bottom+16,text=pair['end_utc'].split('T')[1]+' UTC',anchor='e')
    canvas.create_text(left,10,text='Raw counts / baseline mean',anchor='w')
    canvas.create_text(right,10,text='  ·  '.join(pair['names']),anchor='e')
