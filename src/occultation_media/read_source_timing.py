"""Read original source exposure midpoints without implicit clock corrections."""
from pathlib import Path
import numpy as np
from .utc_conventions import utc_ns, midpoint


def source_timing(source, cfg, indices):
    """Return index -> (UTC[ns] midpoint, original metadata) for real frames.

    ADV is intrinsically midpoint; RAVF stores start/exposure ns since 2010.
    SER requires explicit start/midpoint/end convention and exposure seconds.
    FITS DATE-AVG is intrinsically midpoint; other date fields require an
    explicit convention. Multi-plane FITS without per-plane timing fails.
    TIMEsys other than UTC fails. No cadence or missing timestamps are invented.
    """
    kind = source.metadata['format']
    epoch = np.datetime64('2010-01-01', 'ns')
    values = {}
    if kind == 'ADV2':
        records = source._decode(indices, None)['frames']
    elif kind == 'SER':
        records = list(source.timing_records(indices).values())
    elif kind == 'FITS':
        from astropy.io import fits
        records = []
        for index in indices:
            file, hdu, plane = source.entries[index]
            header = fits.getheader(file, hdu)
            if header.get('NAXIS') == 3:
                raise ValueError('Strict UTC mapping requires per-plane FITS timing; export a timed sequence')
            if header.get('TIMESYS', 'UTC').upper() != 'UTC':
                raise ValueError('FITS TIMESYS must be UTC')
            exposure = float(header['EXPTIME'])
            label = next((header[k] for k in ('DATE-AVG','DATE-OBS','DATE-BEG') if k in header), None)
            if label is None: raise ValueError('FITS has no recorded UTC')
            ref = 'midpoint' if 'DATE-AVG' in header else cfg['source_timestamp_reference']
            time = midpoint(utc_ns(label), exposure, ref)
            records.append(dict(source_index=index, file=str(Path(file)), utc_ns=int(time.astype('int64')),
                                exposure_s=exposure, timestamp_reference=ref))
    elif kind == 'RAVF':
        records = [source.read(i)[1] for i in indices]
    else: raise ValueError('Unsupported timestamped source')
    for record in records:
        if kind == 'ADV2':
            time = epoch+np.timedelta64(record['midpoint_timestamp_ns'], 'ns')
        elif kind == 'RAVF':
            time = epoch+np.timedelta64(record['start_timestamp_ns']+round(record['exposure_ns']/2), 'ns')
        else:
            time = np.datetime64(record['utc_ns'], 'ns')
            if kind == 'SER':
                time = midpoint(time, cfg['exposure_s'], cfg['source_timestamp_reference'])
        if np.isnat(time): raise ValueError('Missing source UTC')
        values[record['source_index']] = (time, record)
    return values
