"""Plan display-only UTC cuts and playback durations; never alter measured times."""
import math
import numpy as np
from .utc_conventions import utc_ns


def order_stations(stations, mode='input'):
    """Validate terrestrial degrees and optionally sort latitude descending.

    Coordinates are signed geographic degrees: north/east positive. Both
    latitude and longitude are required for north-to-south order; unknown
    locations are never inferred from observer names or star coordinates.
    Stable sorting preserves input order for equal latitudes.
    """
    if mode not in ('input', 'north_to_south'):
        raise ValueError('station_order must be input or north_to_south')
    for station in stations:
        c = station['config']
        provided = [k in c for k in ('latitude_deg', 'longitude_deg')]
        if any(provided) and not all(provided):
            raise ValueError(f'{c["name"]}: supply both latitude and longitude')
        if all(provided):
            for key, limit in (('latitude_deg', 90), ('longitude_deg', 180)):
                value = float(c[key])
                if not math.isfinite(value) or abs(value) > limit:
                    raise ValueError(f'{c["name"]}: invalid {key}')
                c[key] = value
        elif mode == 'north_to_south':
            raise ValueError(f'{c["name"]}: coordinates required for north-to-south order')
    return sorted(stations, key=lambda s: -s['config']['latitude_deg']) if mode == 'north_to_south' else stations


def merged_intervals(intervals):
    """Return sorted non-overlapping [start, stop) UTC[ns] pairs; merge touches."""
    result = []
    for start, stop in sorted(intervals):
        if start >= stop:
            continue
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(stop, result[-1][1]))
        else:
            result.append((start, stop))
    return result


def plan_timeline(cfg, stations):
    """Return UTC samples, per-sample presentation seconds and auditable cuts.

    ``dr`` keeps [D-padding, R+padding) for each station; every station must
    have saved/supplied D/R. ``manual`` uses explicit UTC limits. Skipping gaps
    merges D/R windows, or station curve-coverage intervals in manual mode;
    missing images inside a retained interval remain blank. The last display
    hold of each cut is shortened to end exactly at its boundary.

    Fixed playback rescales only presentation durations by target/sum(holds).
    All curve, source, D/R and displayed clock timestamps remain absolute UTC.
    Legacy manual/no-gap configurations retain their inclusive endpoint hold.
    At most 2,000 display samples are allowed after cutting.
    """
    step = float(cfg['step_s'])
    if not math.isfinite(step) or step < .01:
        raise ValueError('Display step must be finite and >= 0.01 s')
    step_ns = round(step * 1e9)
    mode = cfg.get('window_mode', 'manual')
    skip = cfg.get('skip_gaps', False)
    if not isinstance(skip, bool):
        raise ValueError('skip_gaps must be a JSON boolean')
    if mode == 'dr':
        padding = float(cfg.get('event_padding_s', 10))
        if not math.isfinite(padding) or padding < 0:
            raise ValueError('D/R padding must be finite and nonnegative seconds')
        pad = np.timedelta64(round(padding * 1e9), 'ns')
        windows = []
        for station in stations:
            if station['D'] is None or station['R'] is None:
                raise ValueError(f'{station["config"]["name"]}: D/R required for event windows')
            windows.append((station['D'] - pad, station['R'] + pad))
        windows = merged_intervals(windows)
    elif mode == 'manual':
        start, stop = (utc_ns(cfg[k]) for k in ('start_utc', 'end_utc'))
        if start >= stop:
            raise ValueError('Require increasing manual UTC limits')
        windows = [(start, stop)]
        if skip:
            windows = merged_intervals([(max(start, s['rows'][0].utc), min(stop, s['rows'][-1].utc)) for s in stations])
    else:
        raise ValueError('window_mode must be manual or dr')
    if not windows:
        raise ValueError('No station coverage inside the requested window')
    if not skip:
        windows = [(windows[0][0], windows[-1][1])]
    legacy = mode == 'manual' and not skip
    counts = [int((b-a).astype('timedelta64[ns]').astype('int64')) for a, b in windows]
    lengths = [ns//step_ns+1 if legacy else (ns+step_ns-1)//step_ns for ns in counts]
    if not 2 <= sum(lengths) <= 2000:
        raise ValueError('Require 2–2000 displayed samples after cuts; adjust display step')
    times, holds = [], []
    for (start, stop), length in zip(windows, lengths):
        segment = start + np.arange(length) * np.timedelta64(step_ns, 'ns')
        times.extend(segment)
        holds.extend([step if legacy else min(step, float((stop-t)/np.timedelta64(1, 's'))) for t in segment])
    holds = np.array(holds, dtype=float)
    real_duration = float(holds.sum())
    playback = cfg.get('playback_mode', 'real_time')
    if playback == 'fixed_duration':
        duration = float(cfg['video_duration_s'])
        if not math.isfinite(duration) or duration < .04:
            raise ValueError('Video duration must be finite and >=0.04 s')
        holds *= duration / real_duration
    elif playback != 'real_time':
        raise ValueError('playback_mode must be real_time or fixed_duration')
    gaps = [dict(start_utc=str(a[1]), end_utc=str(b[0]), duration_s=float((b[0]-a[1])/np.timedelta64(1, 's')))
            for a, b in zip(windows, windows[1:])]
    info = dict(window_mode=mode, skip_gaps=skip, event_padding_s=cfg.get('event_padding_s', 10) if mode=='dr' else None,
                intervals=[dict(start_utc=str(a), end_utc=str(b)) for a, b in windows], skipped_gaps=gaps,
                retained_utc_span_s=sum(counts)/1e9, real_time_duration_s=real_duration,
                playback_mode=playback, requested_video_duration_s=float(holds.sum()),
                presentation_durations_s=holds.tolist())
    return np.array(times, dtype='datetime64[ns]'), holds, windows, info
