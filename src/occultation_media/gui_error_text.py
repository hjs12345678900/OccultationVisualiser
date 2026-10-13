"""Localize known application diagnostics only at the desktop display boundary."""
import re
from .gui_error_catalog import ERRORS


def error_text(error, language):
    """Select the UI language without splitting paths, ratios or arbitrary text.

    Original exceptions and on-disk worker logs remain intact for diagnosis.
    Named application templates preserve dynamic field names and fit counts.
    """
    text = str(error)
    chinese = language in ('zh', '中文')
    for original, zh, en in ERRORS:
        selected = zh if chinese else en
        if '{value}' not in original:
            text = text.replace(original, selected)
        else:
            pattern = re.escape(original).replace(re.escape('{value}'), r'([^\n]+?)')
            def substitute(match):
                value = match.group(1)
                result = selected.replace('{value}', value)
                # Preserve the affected field/count even if older Chinese text omitted it.
                return result if '{value}' in selected else f'{value}: {result}'
            text = re.sub(pattern, substitute, text)
    return text
