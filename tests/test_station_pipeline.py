"""Exercise the standalone native/four-station CLI with real FITS and codecs."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np
from astropy.io import fits
from PIL import Image
from occultation_media.make_station_media import make_station_media
from occultation_media.record_media_run import version


class StationPipelineTests(unittest.TestCase):
    def test_four_stations_absolute_utc_missing_frames_and_bilingual_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stations=[]
            base=np.datetime64('2026-09-12T09:54:20','ns')
            for k in range(4):
                directory=root/f'station{k}';directory.mkdir()
                # Fourth station truly records four minutes later, never shifted.
                epoch=base+np.timedelta64(240 if k==3 else 0,'s')
                lines=['FrameNum,timeInfo,signal-target,xcentroid-target,ycentroid-target']
                for i in range(6):
                    utc=epoch+np.timedelta64(i*200,'ms')
                    clock=str(utc).split('T')[1]
                    lines.append(f'{i},[{clock}],{10 if i in (2,3) else 100},16,16')
                    if k==2 and i>1:continue  # Partial sequence: no event images.
                    pixels=np.arange(1024,dtype=np.uint16).reshape(32,32)+100
                    pixels[15:18,15:18]=5000 if i not in (2,3) else 100
                    fits.writeto(directory/f'frame{i}.fits',pixels,fits.Header({'DATE-OBS':str(utc),'EXPTIME':.2}))
                (root/f'curve{k}.csv').write_text('\n'.join(lines))
                stations.append(dict(name=f'Station {k}',curve_format='pymovie_csv',curve=f'curve{k}.csv',source=f'station{k}',
                    target_column='signal-target',exposure_s=.2,timestamp_reference='start',source_timestamp_reference='start',mapping_tolerance_s=1e-9))
            cfg=dict(event='Synthetic',target='Target',date_utc='2026-09-12',alignment='absolute_utc',
                start_utc=str(base),end_utc=str(base+np.timedelta64(1200,'ms')),step_s=.2,language='both',stations=stations)
            path=root/'config.json';path.write_text(json.dumps(cfg));out=root/'media'
            command=[sys.executable,str(Path(__file__).resolve().parents[1]/'launch.py'),'--media-config',str(path),'--output-dir',str(out)]
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            meta=json.loads((out/'media_metadata.json').read_text())
            self.assertTrue(meta['no_event_time_shift'])
            self.assertEqual([s['matched_images'] for s in meta['stations']],[6,6,2,6])
            self.assertTrue(all(s['frames'][3] is None for s in meta['display_selection']))
            self.assertIn('09:58:',meta['stations'][3]['curve_start_utc'])
            run=json.loads((out/'run_metadata.json').read_text())
            self.assertEqual(run['version'],version());self.assertTrue(run['input_integrity_verified'])
            self.assertEqual(run['status'],'complete_with_warnings')
            for lang in ('en','zh'):
                with Image.open(meta['outputs'][lang]['gif']) as image:
                    self.assertEqual(image.size,(1280,960));self.assertEqual(image.n_frames,7)
                    duration=0
                    for i in range(image.n_frames):image.seek(i);duration+=image.info['duration']
                    self.assertEqual(duration,1400)
                self.assertGreater(Path(meta['outputs'][lang]['mp4']).stat().st_size,100)
            with self.assertRaises(FileExistsError):make_station_media(path,out,verify_only=True)


if __name__=='__main__':unittest.main()
