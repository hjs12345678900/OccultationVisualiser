"""Read completed PyOTE log fit-metrics blocks and their local timing context."""
import re
from .read_pyote_result import clock_seconds

NUMBER = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'


def log_fits(text):
    """Return native fitted records in file order, including incomplete records.

    Each `fit metrics for <column>` identifies one result. Validity, block size,
    sampling cadence and 95% errors are scoped to its preceding report/session;
    newer incomplete results cannot silently select an earlier completed fit.
    Parse saved values only; never derive exposure from timeDelta.
    """
    fits = []
    markers = list(re.finditer(r'^fit metrics for (.+)$', text, re.M))
    for i, marker in enumerate(markers):
        end = markers[i+1].start() if i+1 < len(markers) else len(text)
        block = text[marker.end():end]
        prefix = text[:marker.start()]
        sessions = list(re.finditer(r'#+ PYOTE .*session started:', prefix))
        session_start = sessions[-1].start() if sessions else 0
        context_start = max(session_start, markers[i-1].end() if i else 0)
        context = text[context_start:marker.start()]
        session = prefix[session_start:]
        source = re.findall(r'^filename: (.+)$', session, re.M)
        valid = re.findall(r'Timestamps appear valid @ D and R|Times are invalid[^\n]*|! There is something wrong with timestamps[^\n]*', context)
        result = dict(target_column=marker.group(1).strip(),
                      source_curve=source[-1].strip() if source else None,
                      timesAreValid=bool(valid and valid[-1].startswith('Timestamps appear valid')),
                      validity_evidence='PyOTE log timestamp check')
        for key in ('B', 'A', 'sigmaB', 'sigmaA'):
            values = re.findall(r'fit metrics ===[^\n]*?\b'+key+r': ('+NUMBER+r')', block)
            if values:
                result[key] = float(values[0])
        for edge in ('D', 'R'):
            frames = re.findall(r'fit metrics === '+edge+r' frame number: ('+NUMBER+r')', block)
            clocks = re.findall(r'fit metrics === '+edge+r' time: (\[[^\]]+\])', block)
            if frames:
                result[edge+'frame'] = float(frames[0])
            if clocks:
                result[edge+'time'] = clock_seconds(clocks[0])
        sizes = re.findall(r'Block integration of size (\d+) has been applied', context)
        result['integration_readings'] = int(sizes[-1]) if sizes else (1 if 'has not been block integrated' in context else None)
        cadences = re.findall(r'timeDelta: ('+NUMBER+r') seconds per (?:reading|block)', session)
        result['fitted_cadence_s'] = float(cadences[-1]) if cadences else None
        result['timestamp_assumption'] = 'start' if 'assumption that timestamps are start-of-exposure times' in context else 'unrecorded'
        errors = {}
        for edge in ('D', 'R'):
            values = re.findall(edge+r': 0\.9500 containment intervals:  \{\+/- ('+NUMBER+r')\} seconds', context)
            errors[edge] = float(values[-1]) if values else None
        result['xlsxDict'] = {e+'err95': v for e,v in errors.items()}
        fits.append(result)
    return fits
