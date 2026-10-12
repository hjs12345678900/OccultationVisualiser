"""Stream multi-station RGB frames to H.264 and make memory-bounded GIFs."""
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image
from .platform_runtime import ffmpeg_executable, hidden_process_options


def encode_station_language(panels,timeline,selections,output,contacts,durations=None):
    """Encode positive presentation holds in seconds, independent of UTC cuts.

    Original-curve cadence is unaffected. Stream RGB24 instead of accumulating
    a long animation in RAM. H.264/yuv420p at 25 fps quantizes cumulative hold
    boundaries to nearest 40 ms (not each hold independently). A UTC jump adds
    no unwanted playback time. Fixed duration changes these holds only.
    GIF downscales to 1280×960 at display cadence, capped at 50 fps;
    palette generation runs separately to avoid buffering the entire video.
    """
    output = Path(output)
    size = panels.size
    gif_height = round(size[1]*1280/size[0]/2)*2
    contact_height = round(size[1]*640/size[0])
    step = float((timeline[1]-timeline[0]).astype('timedelta64[ns]').astype('int64'))/1e9
    durations=np.array(durations if durations is not None else [step]*len(timeline),dtype=float)
    if len(durations)!=len(timeline) or not np.isfinite(durations).all() or (durations<=0).any():
        raise ValueError('One positive finite presentation duration per UTC sample is required')
    boundaries=np.rint(np.cumsum(durations)*25).astype('int64')
    boundaries[-1]=max(1,boundaries[-1])
    repeats=np.diff(np.r_[0,boundaries])
    gif_fps=min(50.,1/float(np.median(durations)))
    executable = ffmpeg_executable()
    cmd=[executable,'-hide_banner','-loglevel','error','-n','-f','rawvideo','-pixel_format','rgb24',
         '-video_size',f'{size[0]}x{size[1]}','-framerate','25','-i','pipe:0',
         '-vf','format=yuv420p','-c:v','libx264','-preset','fast','-crf','20',
         '-movflags','+faststart','-an',str(output)]
    chosen = {int(abs(timeline-t).argmin()) for t in contacts}
    contact_images=[]
    log = output.with_suffix('.ffmpeg.log')
    with log.open('w', encoding='utf-8') as handle:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=handle,**hidden_process_options())
        try:
            for k,utc in enumerate(timeline):
                image=panels.render(utc,selections[k])
                pixels=image.tobytes()
                for _ in range(repeats[k]): process.stdin.write(pixels)
                if k in chosen:
                    image.save(output.with_name(output.stem+f'_stage_{k:04d}.png'))
                    contact_images.append(image.resize((640,contact_height),Image.Resampling.LANCZOS))
                if k%100==0: print(f'{panels.language}: {k+1}/{len(timeline)} UTC {utc}',flush=True)
            process.stdin.close()
            if process.wait(): raise RuntimeError(f'Video encoding failed; inspect {log}')
        except BaseException:
            process.stdin.close()
            process.terminate();process.wait()
            raise
    sheet=Image.new('RGB',(1280,contact_height*((len(contact_images)+1)//2)),(9,13,22))
    for i,image in enumerate(contact_images): sheet.paste(image,((i%2)*640,(i//2)*contact_height))
    contact=output.with_name(output.stem+'_contact.png');sheet.save(contact)
    preview_index=int(abs(timeline-contacts[1]).argmin())
    preview=output.with_name(output.stem+'_preview.png')
    panels.render(timeline[preview_index],selections[preview_index]).save(preview)
    palette=output.with_name(output.stem+'_palette.png')
    subprocess.run([executable,'-hide_banner','-loglevel','error','-n','-i',str(output),
        '-vf',f'fps={gif_fps},scale=1280:{gif_height}:flags=lanczos,palettegen=max_colors=128:stats_mode=diff',
        '-frames:v','1',str(palette)],check=True,**hidden_process_options())
    gif=output.with_suffix('.gif')
    subprocess.run([executable,'-hide_banner','-loglevel','error','-n','-i',str(output),'-i',str(palette),
        '-lavfi',f'fps={gif_fps},scale=1280:{gif_height}:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5',
        '-loop','0',str(gif)],check=True,**hidden_process_options())
    with Image.open(gif) as animation:
        gif_frames=animation.n_frames
        gif_duration_ms=0
        for index in range(gif_frames):
            animation.seek(index);gif_duration_ms+=animation.info.get('duration',0)
    return dict(mp4=str(output),gif=str(gif),preview=str(preview),contact_sheet=str(contact),
                frames=len(timeline),duration_s=float(durations.sum()),mp4_duration_s=int(boundaries[-1])/25,
                mp4_frames=int(boundaries[-1]),gif_fps=gif_fps,gif_frames=gif_frames,gif_duration_s=gif_duration_ms/1000,
                mp4_shape=list(size),gif_shape=[1280,gif_height])
