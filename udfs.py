"""Pixeltable UDFs for the climbing-route topo registry (module path e.g. `udfs.aspect_band`)."""
import PIL.Image

import pixeltable as pxt


@pxt.udf
def aspect_band(photo: PIL.Image.Image) -> str:
    """portrait / square / landscape from width / height."""
    w, h = photo.size
    r = w / h if h else 0
    if r < 0.85:
        return 'portrait'
    if r <= 1.15:
        return 'square'
    return 'landscape'


@pxt.udf
def dominant_channel(photo: PIL.Image.Image) -> str:
    """'red', 'green' or 'blue': channel with the highest mean on a tiny downscale."""
    small = photo.convert('RGB').resize((16, 16))
    sums = [0, 0, 0]
    for px in small.getdata():
        for i in range(3):
            sums[i] += px[i]
    return ('red', 'green', 'blue')[sums.index(max(sums))]


@pxt.udf
def topo_tag(aspect: str, channel: str, style: str) -> str:
    """Chained tag, e.g. 'portrait-warm-sport'."""
    tone = {'red': 'warm', 'green': 'verdant', 'blue': 'cool'}.get(channel, 'neutral')
    return f'{aspect}-{tone}-{style}'


@pxt.udf
def grade_band(grade: str) -> str:
    """Coarse YDS band from a grade string like '5.10a' / '5.12c'."""
    g = (grade or '').strip()
    if not g.startswith('5.'):
        return 'other'
    try:
        num = int(''.join(ch for ch in g[2:] if ch.isdigit())[:2] or '0')
    except ValueError:
        return 'other'
    if num < 9:
        return 'easy'
    if num < 11:
        return 'moderate'
    if num < 13:
        return 'hard'
    return 'elite'
