"""A second judge, for the look: `python -m necromono.texture`.

"Is it black metal?" cannot be computed. But some of what the eye is reacting
to can be measured, and measured on real logos as well as on the font. This
sets a line of text in each style and reports five properties of the result,
beside the range found across seven black metal logos (Behemoth, Mgla, the
Burzum demo logo, Immortal, Marduk, Gorgoroth, Darkthrone) and beside Menlo.

    density   how much of the band the letters sit in is ink. Black metal
              lettering is dark; a code font is mostly background.
    spill     the share of all ink that lies outside that band.
    reach     how far ink extends beyond the band, in band-heights.
    vertical  the share of all edges that are vertical. Too low and it is not
              blackletter; too high and it is a picket fence with nothing
              crossing it.
    stems     strokes crossed per band-height of width: how tightly packed.

These are proxies. A font can sit inside every range and still look wrong, so
this narrows the search and catches regressions; the eye still decides.
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .eyes import ROOT, render

# Measured from the logos listed above, with this same code.
LOGOS = {"density": (0.32, 0.60), "spill": (0.10, 0.30), "reach": (0.60, 2.02), "vertical": (0.59, 0.68), "stems": (1.64, 6.20)}
TEXT = "necromono behemoth darkthrone"


def measure(ink):
    """ink: 2-D array, 1 where there is ink. Returns the five properties."""
    ys, xs = np.where(ink > 0)
    ink = ink[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    rows = ink.mean(axis=1)
    core = np.where(rows >= 0.5 * np.percentile(rows, 90))[0]
    band = ink[core.min() : core.max() + 1]
    h = band.shape[0]
    gx = np.abs(np.diff(ink, axis=1)).sum()
    gy = np.abs(np.diff(ink, axis=0)).sum()
    mid = band[h // 2]
    return {
        "density": band.mean(),
        "spill": 1 - band.sum() / ink.sum(),
        "reach": (ink.shape[0] - h) / h,
        "vertical": gx / (gx + gy),
        "stems": (mid[1:] > mid[:-1]).sum() / (band.shape[1] / h),
    }


def of_font(style):
    out = Path(tempfile.gettempdir()) / ("necromono-texture-%s.png" % style)
    text = TEXT if "Bold" not in style else "\x1b[1m%s\x1b[0m" % TEXT
    render(text, out, ROOT / "fonts" / "NecroMono-Regular.ttf", ROOT / "fonts" / "NecroMono-Bold.ttf", size=60)
    grey = np.asarray(Image.open(out).convert("L"), dtype=float) / 255
    return measure((grey > 0.5).astype(float))


def of_menlo():
    font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 120)
    img = Image.new("L", (2600, 260), 0)
    ImageDraw.Draw(img).text((20, 20), TEXT, font=font, fill=255)
    return measure((np.asarray(img, dtype=float) / 255 > 0.5).astype(float))


def main():
    rows = [("NecroMono Regular", of_font("Regular")), ("NecroMono Bold", of_font("Bold")), ("Menlo", of_menlo())]
    keys = list(LOGOS)
    print("%-20s" % "" + "".join("%12s" % k for k in keys))
    print("%-20s" % "black metal logos" + "".join("%12s" % ("%.2f-%.2f" % LOGOS[k]) for k in keys))
    outside = []
    for name, m in rows:
        cells = []
        for k in keys:
            lo, hi = LOGOS[k]
            ok = lo <= m[k] <= hi
            if not ok and name.startswith("NecroMono"):
                outside.append("%s %s %.2f" % (name.split()[-1], k, m[k]))
            cells.append("%12s" % ("%.2f%s" % (m[k], "" if ok else (" low" if m[k] < lo else " high"))))
        print("%-20s" % name + "".join(cells))
    print("\n" + ("Inside the logos' range on every measure." if not outside else "Outside the logos' range: " + "; ".join(outside)))
    return 1 if outside else 0


if __name__ == "__main__":
    sys.exit(main())
