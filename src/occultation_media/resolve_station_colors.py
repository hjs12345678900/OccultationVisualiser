"""Resolve optional display colors consistently across station and map views."""
import re

PALETTE = ('#5CAAFF', '#64D7AB', '#F9CF6F', '#C695F6',
           '#FF9866', '#5DDCE5', '#F28EBD', '#D5DCE8')


def normalize_color(value):
    """Return uppercase #RRGGBB, or an empty string for automatic selection.

    Missing/null/blank values preserve old projects. Reject other formats so
    Tk and Pillow receive identical RGB values, independent of named colors.
    """
    if value is None:
        return ''
    if not isinstance(value, str):
        raise ValueError('Color must be #RRGGBB or blank / 颜色须为 #RRGGBB 或留空')
    value = value.strip()
    if value and not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        raise ValueError('Color must be #RRGGBB or blank / 颜色须为 #RRGGBB 或留空')
    return value.upper()


def station_colors(configs):
    """Return RGB integer tuples in final display order for up to eight stations.

    Explicit choices follow their station through sorting, including intentional
    duplicates. Automatic choices prefer the corresponding palette slot and
    avoid all explicitly reserved colors and earlier automatic assignments.
    No configuration is mutated; automatic fields stay blank when saved.
    """
    choices = [normalize_color(c.get('color')) for c in configs]
    if len(choices)>len(PALETTE):
        raise ValueError('Colors support at most eight stations')
    used = set(filter(None, choices))
    result = []
    for i, choice in enumerate(choices):
        if not choice:
            choice = next(c for c in PALETTE[i:]+PALETTE[:i] if c not in used)
            used.add(choice)
        result.append(tuple(int(choice[j:j+2],16) for j in (1,3,5)))
    return result


def color_hex(rgb):
    """Serialize an RGB byte tuple for export metadata."""
    return '#%02X%02X%02X' % tuple(rgb)
