"""Check native v1 schema, Unicode names, original UTC and source mapping."""
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np
from occultation_media.read_station_curves import read_station_curve
from occultation_media.read_pymovie_records import record_header,aperture_names
from occultation_media.read_pyote_result import curve_basename
from occultation_media.gui_config import build_config
from occultation_media.gui_observer import DEFAULTS


def make_binary(path, frames=(0,1,2,3), extension=b''):
    """Build an independent schema fixture with two apertures per frame."""
    source='原始录像.avi'.encode('utf-32-le').ljust(1024,b'\0')
    header=b'PYMOVIE\0'+struct.pack('<HIIB',1,1065+len(extension),311+len(extension),2)
    header+=b'2026-09-12'.ljust(16,b'\0')+source+struct.pack('<HHH',0,0,0)+extension
    records=[]
    for frame in frames:
        for name,counts in (('目标 ñ',100.5-frame),('ref',200)):
            records.append(bytes([2])+name.encode('utf-32-le').ljust(256,b'\0')
                +struct.pack('<ddd',counts,counts+20,frame)
                +f'09:54:{frame*.2:010.7f}'.encode('ascii').ljust(16,b'\0')
                +struct.pack('<H',255)+np.zeros((2,2),dtype='<u2').tobytes()+bytes(4)+extension)
    path.write_bytes(header+b''.join(records))


class BinaryPyMovieTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'curve.pymovie'
        self.cfg=dict(curve=str(self.path),curve_format='pymovie_records',target_column='signal-目标 ñ',
                      exposure_s=.2,timestamp_reference='start',target_xy=[10,20])

    def test_native_counts_unicode_target_and_utc_are_retained(self):
        make_binary(self.path)
        self.assertEqual(aperture_names(self.path),['目标 ñ','ref'])
        rows,native,info,paths=read_station_curve(self.cfg,'2026-09-12')
        self.assertEqual([r.counts for r in rows],[100.5,99.5,98.5,97.5])
        self.assertEqual(rows[0].utc,np.datetime64('2026-09-12T09:54:00.100','ns'))
        self.assertEqual(rows[0].target_xy,(10,20))
        self.assertEqual(info['source'],'原始录像.avi')
        self.assertEqual(curve_basename(self.path),'curve.csv')
        self.assertEqual(curve_basename('curve.csv.pymovie'),'curve.csv')

    def test_extended_records_and_partial_tail_are_explicit(self):
        make_binary(self.path,extension=b'extra')
        with self.path.open('ab') as stream:stream.write(b'partial')
        rows,_,info,_=read_station_curve(self.cfg,'2026-09-12')
        self.assertEqual(len(rows),4)
        self.assertEqual(info['partial_final_record_bytes_ignored'],7)

    def test_bad_magic_date_target_and_half_frame_fail_clearly(self):
        make_binary(self.path)
        with self.assertRaisesRegex(ValueError,'date differs'):read_station_curve(self.cfg,'2026-09-13')
        with self.assertRaisesRegex(ValueError,'aperture not found'):read_station_curve(dict(self.cfg,target_column='signal-missing'),'2026-09-12')
        make_binary(self.path,frames=(0,.5,1))
        with self.assertRaisesRegex(ValueError,'half-frame'):read_station_curve(self.cfg,'2026-09-12')
        self.path.write_bytes(b'not binary')
        with self.assertRaisesRegex(ValueError,'Not a native'):record_header(self.path)

    def test_desktop_resolves_native_file_and_manual_stretch(self):
        make_binary(self.path)
        source=Path(self.temp.name)/'frames.avi';source.touch()
        cfg=build_config(dict(event='Test',target='Star',date_utc='2026-09-12',step_s='.2',language='en',
            window_mode='full',output_root=self.temp.name),[dict(DEFAULTS,curve=str(self.path),source=str(source),
            target_column='signal-目标 ñ',exposure_mode='manual',exposure_ms='200',source_first_frame='0',
            avi_timestamp_reference='start',image_stretch_mode='manual',image_black='10',image_white='100')])
        station=cfg['stations'][0]
        self.assertEqual(station['curve_format'],'pymovie_records')
        self.assertEqual(station['image_stretch'],dict(mode='manual',strength=8,black=10,white=100))


if __name__=='__main__':unittest.main()
