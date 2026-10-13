"""Sample retained event windows and continuous, faster UTC transit segments."""
import math
import numpy as np


def accelerated_samples(windows, step_ns, speed):
    """Return physical UTC samples, playback holds, intervals and audit data.

    Windows are merged increasing [start, stop) UTC[ns] pairs. Event windows
    retain the requested sampling step and 1x speed. Gaps use a UTC step of
    ``speed / 25`` seconds and holds of at most 40 ms, so shadow motion updates
    at the output video's 25 fps. No interpolation of photometry or detector
    frames occurs. The final hold ends exactly at each segment boundary.
    ``speed`` is a finite playback multiplier >1, never a clock correction.
    """
    speed = float(speed)
    if not math.isfinite(speed) or speed <= 1:
        raise ValueError('gap_speed must be finite and greater than 1')
    segments = []
    for i, (start, stop) in enumerate(windows):
        if i:
            segments.append((windows[i-1][1], start, speed, 'accelerated_gap'))
        segments.append((start, stop, 1., 'event'))
    times, holds, weights, gaps = [], [], [], []
    for start, stop, rate, kind in segments:
        stride = step_ns if kind == 'event' else max(1, round(rate * .04 * 1e9))
        span_ns = int((stop-start)/np.timedelta64(1, 'ns'))
        count = (span_ns+stride-1)//stride
        if len(times)+count > 2000:
            raise ValueError('Require 2–2000 displayed samples; adjust display step or gap speed')
        samples = start + np.arange(count)*np.timedelta64(stride, 'ns')
        times.extend(samples)
        holds.extend(np.minimum(stride, (stop-samples).astype('timedelta64[ns]').astype('int64'))/1e9/rate)
        weights.append(span_ns/1e9/rate)
        if kind == 'accelerated_gap':
            gaps.append(dict(start_utc=str(start), end_utc=str(stop), duration_s=span_ns/1e9,
                             speed=rate, presentation_duration_s=weights[-1]))
    if len(times) < 2:
        raise ValueError('Require at least two displayed samples')
    intervals = [(a,b) for a,b,_,_ in segments]
    audit = dict(gap_speed=speed, accelerated_gaps=gaps, axis_durations_s=weights,
                 event_intervals=[dict(start_utc=str(a),end_utc=str(b)) for a,b in windows],
                 segments=[dict(start_utc=str(a),end_utc=str(b),kind=k,speed=r) for a,b,r,k in segments])
    return times, np.asarray(holds), intervals, audit
