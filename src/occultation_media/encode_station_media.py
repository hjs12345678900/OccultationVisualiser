"""Stream multi-station RGB frames to H.264 and make memory-bounded GIFs."""
from pathlib import Path
import subprocess
from PIL import Image
from .platform_runtime import ffmpeg_executable, hidden_process_options


def encode_station_language(panels,timeline,selections,output,contacts):
    """Encode at actual elapsed time; images update once per configured step.

    Original-curve cadence is unaffected. Stream RGB24 instead of accumulating
    a long animation in RAM. H.264/yuv420p at 25 fps holds each display image for
    the requested real-time step. GIF downscales to 1280×960 at display cadence;
    palette generation runs separately to avoid buffering the entire video.
    """
    output = Path(output)
    size = panels.size
    gif_height = round(size[1]*1280/size[0]/2)*2
    contact_height = round(size[1]*640/size[0])
    step = float((timeline[1]-timeline[0]).astype('timedelta64[ns]').astype('int64'))/1e9
    executable = ffmpeg_executable()
    cmd=[executable,'-hide_banner','-loglevel','error','-n','-f','rawvideo','-pixel_format','rgb24',
         '-video_size',f'{size[0]}x{size[1]}','-framerate',str(1/step),'-i','pipe:0',
         '-vf','fps=25,format=yuv420p','-c:v','libx264','-preset','fast','-crf','20',
         '-movflags','+faststart','-an',str(output)]
    chosen = {int(abs(timeline-t).argmin()) for t in contacts}
    contact_images=[]
    log = output.with_suffix('.ffmpeg.log')
    with log.open('w') as handle:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=handle,**hidden_process_options())
        try:
            for k,utc in enumerate(timeline):
                image=panels.render(utc,selections[k])
                process.stdin.write(image.tobytes())
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
        '-vf',f'fps={1/step},scale=1280:{gif_height}:flags=lanczos,palettegen=max_colors=128:stats_mode=diff',
        '-frames:v','1',str(palette)],check=True,**hidden_process_options())
    gif=output.with_suffix('.gif')
    subprocess.run([executable,'-hide_banner','-loglevel','error','-n','-i',str(output),'-i',str(palette),
        '-lavfi',f'fps={1/step},scale=1280:{gif_height}:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5',
        '-loop','0',str(gif)],check=True,**hidden_process_options())
    return dict(mp4=str(output),gif=str(gif),preview=str(preview),contact_sheet=str(contact),
                frames=len(timeline),duration_s=len(timeline)*step,mp4_shape=list(size),gif_shape=[1280,gif_height])
