"""Preserve native UTC precision and explicit exposure-time conventions."""
import numpy as np


def utc_ns(value):
    """Parse UTC ISO text as datetime64[ns]; reject non-UTC timezone offsets.

    A trailing Z or +00:00 is accepted. Bare ISO text means UTC by contract.
    Missing/NaT values fail rather than being replaced with inferred cadence.
    """
    text = str(value).strip()
    if text.endswith('+00:00'): text = text[:-6]
    if '+' in text[10:] or '-' in text[10:]:
        raise ValueError('Timestamps must be UTC, not a local timezone offset')
    value = np.datetime64(text.removesuffix('Z'), 'ns')
    if np.isnat(value): raise ValueError('Missing UTC timestamp')
    return value


def midpoint(stamp, exposure_s, reference):
    """Convert start/midpoint/end UTC[ns] using supplied positive exposure s.

    t_mid = t_recorded + f * exposure, f = +1/2, 0, -1/2 respectively.
    Round only the exposure correction to integer ns; retain native ticks.
    """
    if reference not in ('start', 'midpoint', 'end'):
        raise ValueError('Explicit timestamp_reference must be start/midpoint/end')
    if not np.isfinite(exposure_s) or exposure_s <= 0:
        raise ValueError('Exposure must be finite and positive')
    fraction = {'start': .5, 'midpoint': 0., 'end': -.5}[reference]
    return stamp + np.timedelta64(round(exposure_s*fraction*1e9), 'ns')


def clock_sequence(date, labels):
    """Resolve bracketed CSV UTC clock labels, retaining ns across midnight.

    event date is the first sample's UTC date. Only a backward jump >12 h is
    treated as midnight rollover; duplicates and small backward jumps fail.
    """
    day = utc_ns(date).astype('datetime64[D]')
    values = []
    for label in labels:
        stamp = utc_ns(str(day)+'T'+label.strip().strip('[]'))
        if values and stamp <= values[-1]:
            if values[-1]-stamp > np.timedelta64(12, 'h'):
                day += np.timedelta64(1, 'D')
                stamp += np.timedelta64(1, 'D')
            else: raise ValueError('CSV UTC must strictly increase')
        values.append(stamp)
    return values
