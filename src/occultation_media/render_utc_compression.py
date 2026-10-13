"""Mark accelerated UTC bands without introducing a discontinuity in motion."""
import math


def draw_compression(draw, segments, speeds, y, font, gap_label):
    """Shade compressed time and return reserved axis-label pixel intervals.

    ``segments`` contain (UTC start, UTC stop, left px, right px); ``speeds``
    are dimensionless playback multipliers relative to event windows. Only
    speeds >1 are annotated. Double slashes identify a scale change, while a
    localized caption states the multiplier. Narrow bands use a shorter caption
    and a second line so ordinary UTC ticks remain legible. The UTC axis itself
    remains continuous, and the renderer writes no timing or measurement data.
    """
    reserved=[]
    ink=(249,218,156)
    for (_,_,left,right),speed in zip(segments,speeds):
        if speed<=1:continue
        if right-left>=2:
            draw.rectangle((left+1,y+69,right-1,y+243),fill=(36,31,29))
        for edge in (left,right):
            for top in range(y+70,y+242,12):
                draw.line((edge,top,edge,top+5),fill=(134,111,81),width=1)
        centers=(left,right) if right-left>=24 else ((left+right)/2,)
        for center in centers:
            for offset in (-4,3):
                draw.line((center+offset-3,y+249,center+offset+3,y+239),fill=ink,width=2)
        caption=f'{gap_label} ×{speed:g}'
        box=font.getbbox(caption);width=box[2]-box[0]
        label_y=y+253
        if right-left<width+12:
            caption=f'×{speed:g}';box=font.getbbox(caption);width=box[2]-box[0]
            label_y=y+276
        half=math.ceil(width/2)
        center=max(segments[0][2]+half,min((left+right)/2,segments[-1][3]-half))
        draw.text((center,label_y),caption,font=font,fill=ink,anchor='mt')
        if label_y==y+253:reserved.append((center-half,center+half))
    return reserved
