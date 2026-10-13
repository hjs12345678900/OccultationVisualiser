"""Data I/O: validate one supplied Occult XML event for a shadow simulation."""
from pathlib import Path
import hashlib
import xml.etree.ElementTree as ET
import numpy as np
from .compute_shadow_geometry import ShadowGeometry, EARTH_A_KM, EARTH_B_KM
from .utc_conventions import utc_ns


def enabled(value):
    """Resolve boolean or stable checkbox strings; reject ambiguous values."""
    if isinstance(value, bool):
        return value
    if value in (0, 1, '0', '1', 'true', 'false', 'True', 'False'):
        return value in (1, '1', 'true', 'True')
    raise ValueError('shadow_enabled must be a boolean / 请勾选或关闭模拟')


def parse_prediction(xml):
    """Parse one Occultations/Event string; return validated ShadowGeometry.

    XML uses comma-separated Elements, Earth, Star and Object fields. Apparent
    star declination is Star[10]; Earth[0] is apparent RA minus GAST, in degrees.
    Input must contain exactly one event and all required finite coefficients.
    No catalog, network lookup, external entity or orbital integration is used.
    Malformed, ambiguous or incomplete input raises ValueError before rendering.
    """
    try:
        root = ET.fromstring(xml)
        events = root.findall('Event') if root.tag == 'Occultations' else []
        if len(events) != 1:
            raise ValueError('Supply exactly one Occultations/Event / 请提供一个事件的预测元素')
        node = events[0]
        el, earth, star, obj = (node.findtext(k, '').split(',') for k in ('Elements','Earth','Star','Object'))
        if len(el)<14 or len(earth)<2 or len(star)<11 or len(obj)<5:
            raise ValueError('Incomplete Occult prediction elements / 预测元素不完整')
        coefficients = np.array(el[6:14], dtype=float).reshape(4, 2)
        lon, dec, diameter = float(earth[0]), float(star[10]), float(obj[3])
        hour = float(el[5])
        if not np.isfinite(coefficients).all() or not np.isfinite([lon, dec, diameter, hour]).all():
            raise ValueError('Prediction elements must be finite')
        if abs(lon)>360 or abs(dec)>90 or diameter<=0 or not 0<=hour<24:
            raise ValueError('Invalid prediction angles, time or diameter')
        date = f'{int(el[2]):04d}-{int(el[3]):02d}-{int(el[4]):02d}'
        epoch = utc_ns(date+'T00:00:00') + np.timedelta64(round(hour*3.6e12), 'ns')
        return ShadowGeometry(epoch, coefficients, np.radians(lon), np.radians(dec),
                              diameter, obj[1], star[0], el[0])
    except (ET.ParseError, IndexError, TypeError) as exc:
        raise ValueError('Invalid Occult XML / 无效的 Occult XML') from exc


def load_prediction(settings, date_utc=None):
    """Return (geometry,evidence,paths) for enabled JSON simulation settings.

    settings has enabled=true plus exactly one of prediction_file or xml.
    Files are UTF-8/BOM text, read only. evidence contains the input SHA-256,
    provenance, epoch, units and explicit model limits. A disabled simulation
    returns (None,None,[]) and ignores stale optional inputs.
    """
    if not isinstance(settings, dict):
        raise ValueError('shadow_simulation must be a JSON object')
    if not enabled(settings.get('enabled', False)):
        return None, None, []
    from .plan_shadow_map_view import view_mode
    mode=view_mode(settings.get('view_mode','full_path'))
    file, inline = settings.get('prediction_file', ''), settings.get('xml', '')
    if bool(file) == bool(str(inline).strip()):
        raise ValueError('Choose a prediction file or paste XML / 选择预测文件或粘贴 XML')
    paths = []
    if file:
        path = Path(file).expanduser().resolve()
        raw = path.read_bytes()
        xml = raw.decode('utf-8-sig')
        paths = [path]
    else:
        xml = str(inline)
        raw = xml.encode('utf-8')
    if len(raw) > 1024*1024:
        raise ValueError('Prediction input exceeds 1 MiB; choose one event')
    geometry = parse_prediction(xml)
    if date_utc and str(geometry.epoch.astype('datetime64[D]')) != date_utc:
        raise ValueError('Prediction date differs from observation date / 预报日期与观测日期不一致')
    evidence = dict(enabled=True, view_mode=mode, input_sha256=hashlib.sha256(raw).hexdigest(),
                    prediction_file=str(paths[0]) if paths else None,
                    object=geometry.object_name, star=geometry.star_name,
                    epoch_utc=str(geometry.epoch), provenance=geometry.provenance,
                    diameter_km=geometry.diameter_km, earth_a_km=EARTH_A_KM, earth_b_km=EARTH_B_KM,
                    model='circular nominal shadow on rotating oblate ellipsoid',
                    uncertainty_included=False, timestamp_basis='corrected curve exposure midpoint UTC',
                    limits=['one hour around prediction epoch', 'no terrain or polar-motion correction',
                            'prediction only; measured D/R and photometry unchanged'])
    return geometry, evidence, paths


def form_settings(event, quality_only=False):
    """Build validated optional simulation JSON from saved desktop form values."""
    settings = {'enabled': False}
    if quality_only or not enabled(event.get('shadow_enabled', False)):
        return settings
    settings['enabled'] = True
    from .plan_shadow_map_view import view_mode
    settings['view_mode']=view_mode(event.get('shadow_view_mode','full_path'))
    if event.get('shadow_prediction_file', '').strip():
        settings['prediction_file'] = str(Path(event['shadow_prediction_file']).expanduser().resolve())
    if event.get('shadow_xml', '').strip():
        settings['xml'] = event['shadow_xml'].strip()
    load_prediction(settings, event['date_utc'].strip())
    return settings
