"""Read event identity from supplied Occult elements for desktop form imports."""
from .read_occult_prediction import load_prediction


def prediction_event_fields(values):
    """Return asteroid, target and UTC date from one validated prediction.

    ``values`` supplies exactly one of ``shadow_prediction_file`` (UTF-8 XML
    path) and ``shadow_xml`` (complete XML text). The existing form date may be
    blank or stale: the imported epoch supplies an ISO YYYY-MM-DD UTC date.
    Names are copied from Object and Star. Missing identity raises ValueError.
    This read-only import works with the map disabled and changes no observation
    files, station inputs, measured times, display settings or map preference.
    """
    settings = dict(enabled=True)
    for key, source in (('prediction_file','shadow_prediction_file'), ('xml','shadow_xml')):
        if str(values.get(source, '')).strip():
            settings[key] = str(values[source]).strip()
    geometry, _, _ = load_prediction(settings)
    asteroid, target = geometry.object_name.strip(), geometry.star_name.strip()
    if not asteroid or not target:
        raise ValueError('Prediction has no asteroid or target name / 预测元素缺少小行星或目标星名称')
    return dict(event=asteroid, target=target,
                date_utc=str(geometry.epoch.astype('datetime64[D]')))
