"""An outside judge of legibility: `python -m necromono.judge`.

It does not ask whether the letters look good. It asks one narrow question
that taste cannot answer: at the size the font is used, which characters could
be mistaken for each other?

Every character is drawn bare (no growth, which is decoration and differs
between alternates) and rasterised into its own 12 x 33 pixel cell, exactly as
at 13pt on a Retina display. Two characters are compared by how much of their
ink overlaps: 1.0 means the same picture, 0 means nothing in common. Pairs that
people really do confuse in code are always reported; any other pair above the
threshold is reported too.

The score that matters is the worst one. Run it before and after changing a
letter: a redesign that looks better but raises the worst score has made the
font harder to read.
"""
import sys

from PIL import Image, ImageDraw

from .pen import ADVANCE, ASCENDER, DESCENDER, REGULAR, Pen
from .textura import TEXTURA

PPEM = 26  # 13pt on a Retina display
SUPER = 8  # supersampling: draw at 8x, average down to real pixels
THRESHOLD = 0.72
MARGIN = 0.08  # how much more alike than the reference font a pair may be

# Pairs that are genuinely mistaken for each other in code and prose.
WATCH = [
    "nu", "nh", "hb", "ce", "co", "eo", "ao", "il", "l1", "lI", "I1", "i1", "O0", "o0", "OQ", "OD", "vy", "uv", "vw",
    "ft", "rn", "gq", "pq", "bd", "B8", "S5", "Z2", "G6", "g9", "q9", "z2", "sS", "cC", "xX", "vV", "wW", "zZ", "oO",
    ".,", ":;", "'`", "-_", "|l", "|I", "|1", "!i", "!l", "({", "[(", ")}", "])", "/|", "ij", "ae", "EF", "PR", "CG", "UV", "MN", "KX",
]  # fmt: skip


class Bare(Pen):
    """A pen that draws the letter and nothing that grows from it."""

    def needle(self, *args, **kwargs):
        pass


def bitmap(ch, cut=REGULAR):
    """The character in its cell, as rows of grey levels 0..1."""
    pen = Bare(ch, cut)
    pen.quiet = True
    TEXTURA[ch](pen)
    scale = PPEM / 1000 * SUPER
    w = round(ADVANCE * scale)
    h = round((ASCENDER - DESCENDER) * scale)
    img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(img)
    for i, contour in enumerate(pen.contours()):
        from .pen import area

        pts = [(x * scale, (ASCENDER - y) * scale) for x, y in contour]
        draw.polygon(pts, fill=255 if area(contour) < 0 else 0)  # clockwise = ink, counter-clockwise = hole
    small = img.resize((w // SUPER, h // SUPER), Image.BOX)
    return [v / 255 for v in small.tobytes()]


REFERENCE = "/System/Library/Fonts/Menlo.ttc"  # an ordinary, well-regarded code font


def reference_bitmap(ch, _cache={}):
    """The same character in the reference font, drawn the same way, so there
    is a yardstick: a pair is only a problem if it is more alike here than in
    a font nobody finds hard to read."""
    from PIL import ImageFont

    if "font" not in _cache:
        _cache["font"] = ImageFont.truetype(REFERENCE, PPEM * SUPER)
    font = _cache["font"]
    w = round(font.getlength("0"))
    asc, desc = font.getmetrics()
    img = Image.new("L", (w, asc + desc), 0)
    ImageDraw.Draw(img).text((0, 0), ch, font=font, fill=255)
    small = img.resize((max(1, w // SUPER), max(1, (asc + desc) // SUPER)), Image.BOX)
    return [v / 255 for v in small.tobytes()]


def similarity(a, b):
    """Shared ink over total ink."""
    shared = sum(min(x, y) for x, y in zip(a, b))
    total = sum(max(x, y) for x, y in zip(a, b))
    return shared / total if total else 1.0


def measure(chars=None):
    chars = chars or [chr(c) for c in range(33, 127)]
    maps = {ch: bitmap(ch) for ch in chars if ch in TEXTURA}
    watched = []
    for pair in WATCH:
        a, b = pair[0], pair[1]
        if a in maps and b in maps:
            watched.append((similarity(maps[a], maps[b]), a, b))
    seen = {frozenset(p) for p in WATCH}
    others = []
    keys = sorted(maps)
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            if frozenset((a, b)) in seen:
                continue
            s = similarity(maps[a], maps[b])
            if s >= THRESHOLD:
                others.append((s, a, b))
    return sorted(watched, reverse=True), sorted(others, reverse=True)


MINIMS = "inumlad"  # the letters blackletter is notorious for running together


def pair_bitmap(a, b, arched=False, cut=REGULAR):
    """Two letters side by side as they sit inside a word, growth removed."""
    from .textura import finish

    width = round(ADVANCE * PPEM / 1000 * SUPER)
    height = round((ASCENDER - DESCENDER) * PPEM / 1000 * SUPER)
    scale = PPEM / 1000 * SUPER
    img = Image.new("L", (2 * width, height), 0)
    draw = ImageDraw.Draw(img)
    for i, ch in enumerate((a, b)):
        pen = Bare(ch, cut, link=("R" if i == 0 else "L") if arched else "")
        pen.quiet = True
        TEXTURA[ch](pen)
        finish(pen)
        for contour in pen.contours():
            from .pen import area

            pts = [((x + i * ADVANCE) * scale, (ASCENDER - y) * scale) for x, y in contour]
            draw.polygon(pts, fill=255 if area(contour) < 0 else 0)
    small = img.resize((2 * width // SUPER, height // SUPER), Image.BOX)
    return [v / 255 for v in small.tobytes()]


def minims(arched=False):
    """How alike the worst two different pairs of minim letters are."""
    pairs = [a + b for a in MINIMS for b in MINIMS]
    maps = {s: pair_bitmap(s[0], s[1], arched) for s in pairs}
    scores = sorted(((similarity(maps[x], maps[y]), x, y) for i, x in enumerate(pairs) for y in pairs[i + 1 :]), reverse=True)
    return scores


def main():
    watched, others = measure()
    rows = []
    for s, a, b in watched + others:
        try:
            ref = similarity(reference_bitmap(a), reference_bitmap(b))
        except OSError:
            ref = float("nan")
        rows.append((s - ref, s, ref, a, b))
    print("How alike two characters are at 13pt (1.00 = identical), beside the same pair in Menlo.")
    print("A pair is a problem when it is both alike in absolute terms and clearly more alike than in Menlo.\n")
    rows.sort(key=lambda r: -r[1])
    problems = []
    line = []
    for excess, s, ref, a, b in rows:
        bad = s >= THRESHOLD and excess > MARGIN
        if bad:
            problems.append((s, ref, a, b))
        line.append("%s %s %.2f (%.2f)%s" % (a, b, s, ref, " !" if bad else "  "))
    for i in range(0, min(len(line), 40), 5):
        print("   " + "   ".join(line[i : i + 5]))
    print("\n%d pair(s) both at or above %.2f and more than %.2f worse than Menlo%s" % (
        len(problems), THRESHOLD, MARGIN, ": " + ", ".join("%s/%s" % (a, b) for _, _, a, b in problems) if problems else "."))
    apart, joined = minims(), minims(arched=True)
    print("\nLetters in a row (%s), where blackletter runs together. Most alike two-letter pairs:" % ", ".join(MINIMS))
    print("   apart:  " + "   ".join("%s/%s %.2f" % (x, y, s) for s, x, y in apart[:5]) + "   | %d at or above 0.85" % sum(s >= 0.85 for s, _, _ in apart))
    print("   arched: " + "   ".join("%s/%s %.2f" % (x, y, s) for s, x, y in joined[:5]) + "   | %d at or above 0.85" % sum(s >= 0.85 for s, _, _ in joined))
    return problems


if __name__ == "__main__":
    sys.exit(0 if not main() else 1)
