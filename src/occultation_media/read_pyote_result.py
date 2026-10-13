"""Import native PyOTE fit_metrics/log exports or the legacy adapter JSON.

Native export fields follow PyOTE updateFitMetricTxtFile and printFitMetrics:
https://github.com/bob-anderson-ok/py-ote/blob/master/src/pyoteapp/pyote.py
This reader preserves fitted values; it does not apply camera corrections.
"""
import csv
import json
import math
from pathlib import Path, PureWindowsPath
import re


def clock_seconds(value):
    """Parse a saved [HH:MM:SS.s] UTC clock into seconds since midnight."""
    match = re.fullmatch(r'\[?(\d{1,2}):(\d{2}):(\d{1,2}(?:\.\d+)?)\]?', value.strip())
    if not match:
        raise ValueError('PyOTE: invalid saved UTC clock / 结果 UTC 格式无效')
    h, m, s = map(float, match.groups())
    if not (0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60):
        raise ValueError('PyOTE: saved UTC clock outside range')
    return h*3600+m*60+s


def read_result_text(path):
    """Read UTF-8/BOM or Windows CP1252 text, rejecting binary/wrong inputs."""
    if path.stat().st_size > 10*1024*1024:
        raise ValueError('PyOTE: result file exceeds 10 MiB; choose a text export')
    data = path.read_bytes()
    try:
        text, encoding = data.decode('utf-8-sig'), 'utf-8-sig'
    except UnicodeDecodeError:
        try:
            text, encoding = data.decode('cp1252'), 'cp1252'
        except UnicodeDecodeError as exc:
            raise ValueError('PyOTE: unreadable text; export as UTF-8 / 请使用 UTF-8 文本') from exc
    if any(ord(c) < 32 and c not in '\r\n\t' for c in text):
        raise ValueError('PyOTE: binary input; choose fit_metrics.txt or .pyote_log.txt / 请选择原生结果文本')
    return text, encoding


def curve_basename(value):
    """Compare moved Windows/macOS source names, allowing .pyote.csv exports."""
    name=PureWindowsPath(str(value).replace('/', '\\')).name.replace('.pyote.csv', '.csv')
    if name.endswith('.pymovie'):
        name=name[:-8]
        if not name.endswith('.csv'):name+='.csv'
    return name


def select_fit(candidates, cfg):
    """Select one matching aperture/source or an explicit one-based fit index.

    Repeated distinct fits are ambiguous even if the final record is newer.
    Identical repeats are collapsed only when the user supplies no index.
    """
    target = cfg.get('target_column')
    selected = [r for r in candidates if not target or r.get('target_column') == target]
    if cfg.get('curve'):
        name = curve_basename(cfg['curve'])
        selected = [r for r in selected if not r.get('source_curve') or curve_basename(r['source_curve']) == name]
    if not selected:
        raise ValueError('PyOTE: no fit matches target column/source curve / 无匹配目标列或曲线的拟合结果')
    index = cfg.get('pyote_fit_index')
    if index not in (None, ''):
        try:
            index = int(str(index))
        except ValueError as exc:
            raise ValueError('PyOTE: fit record must be a positive integer / 拟合记录须为正整数') from exc
        if not 1 <= index <= len(selected):
            raise ValueError(f'PyOTE: fit record outside 1–{len(selected)}')
        result = dict(selected[index-1], fit_record=index)
    else:
        unique = {json.dumps(r, sort_keys=True): r for r in selected}
        if len(unique) != 1:
            raise ValueError(f'PyOTE: {len(selected)} matching fits; choose Fit record in Advanced / 多条结果，请在高级设置选拟合记录')
        result = dict(next(iter(unique.values())))
    if any(k not in result for k in ('Dtime', 'Rtime', 'Dframe', 'Rframe')):
        raise ValueError('PyOTE: incomplete D/R fit; export a complete D and R result / 缺少完整 D/R 结果')
    for key in ('Dframe', 'Rframe', 'B', 'A', 'sigmaB'):
        if key in result and not math.isfinite(float(result[key])):
            raise ValueError(f'PyOTE: nonfinite {key}')
    return result


def metric_fits(text):
    """Read CSV-formatted fit_metrics.txt with interspersed Source file lines."""
    header, source, results = None, None, []
    for line in text.splitlines():
        if line.startswith('Source file is '):
            source = line[len('Source file is '):].strip()
            continue
        if not line.strip():
            continue
        fields = next(csv.reader([line]))
        if fields[0].strip() == 'aperture name':
            header = [s.strip() for s in fields]
            continue
        if header is None:
            raise ValueError('PyOTE: expected fit_metrics header')
        if len(fields) != len(header):
            raise ValueError('PyOTE: malformed fit_metrics row')
        record = dict(zip(header, fields))
        result = dict(target_column=record['aperture name'].strip(), source_curve=source,
                      timesAreValid=True, validity_evidence='frame/UTC checked by importer; metrics has no validity flag')
        try:
            for edge in ('D', 'R'):
                result[edge+'frame'] = float(record[edge+' frame'])
                result[edge+'time'] = clock_seconds(record[edge+' time'])
            for key in ('B', 'A', 'sigmaB', 'sigmaA'):
                result[key] = float(record[key])
            result['reported_time_error_s'] = float(record['time err +/-secs'])
        except (KeyError, ValueError) as exc:
            raise ValueError('PyOTE: incomplete or invalid fit_metrics values') from exc
        results.append(result)
    return results


def read_pyote_result(cfg):
    """Return saved numeric fields plus provenance; None when no result supplied.

    Accept native TXT exports and legacy UTF-8 adapter JSON by content. Native
    D/R clocks are seconds since midnight; fractional frames remain source IDs.
    Native sigmaB describes fitted readings, possibly block integrated, rather
    than guaranteed single camera exposures. No native raw/C3/C4 flag exists.
    """
    if not cfg.get('pyote_result'):
        return None
    path = Path(cfg['pyote_result']).expanduser().resolve()
    if path.suffix.lower() not in ('.txt', '.json'):
        raise ValueError('PyOTE: choose fit_metrics.txt / .pyote_log.txt; put .pyote.csv in Light curve / 光变 CSV 请放曲线栏')
    text, encoding = read_result_text(path)
    if text.lstrip().startswith('{'):
        try:
            result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError('PyOTE: invalid legacy adapter JSON') from exc
        if not isinstance(result, dict):
            raise ValueError('PyOTE: adapter JSON must be an object')
        return dict(result, result_format='adapter_json', result_encoding=encoding)
    if 'aperture name,time err' in text:
        result, kind = select_fit(metric_fits(text), cfg), 'pyote_fit_metrics'
    elif 'fit metrics for ' in text:
        from .read_pyote_log import log_fits
        result, kind = select_fit(log_fits(text), cfg), 'pyote_log'
    else:
        raise ValueError('PyOTE: unrecognized result text; choose fit_metrics.txt or .pyote_log.txt / 不是 PyOTE 拟合结果')
    if cfg.get('native_mode', 'auto') not in ('auto', 'raw', 'C3', 'C4'):
        raise ValueError('Unsupported saved curve mode')
    return dict(result, result_format=kind, result_encoding=encoding,
                mode=cfg.get('native_mode') if cfg.get('native_mode') not in (None, 'auto') else 'raw',
                noise_scope='PyOTE fitted readings', camera_corrections_applied_by_importer=False)
