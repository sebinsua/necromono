"""NecroMono drawing kernel.

A `Pen` collects the shapes of one glyph and turns them into a clean outline.
The letters themselves are in textura.py; this module knows how to sweep a
broad nib along straight strokes, how to draw the thin lines that grow from
them, and how to merge everything into contours a font file can hold.
"""
import math
import random
from dataclasses import dataclass, replace

from fontTools.pens.recordingPen import RecordingPen
from pathops import Path

from . import textura

# ---------------------------------------------------------------- metrics
# Output metrics: what the font file says. Chosen so that at a given point size
# the text occupies an ordinary terminal cell: the row height of a regular
# monospace font, in a narrower cell (0.44 em), because black metal lettering
# is tall and tightly packed.
UPM = 1000
# All four are whole pixels at 13pt on a Retina display (26 px per em): a
# 12 x 33 px cell with a 15 px x-height. See textura.py for why.
ADVANCE = 462  # advance of every glyph
ASCENDER = 961  # line box; growth is free to leave it
DESCENDER = -307
XHEIGHT = 577

@dataclass(frozen=True)
class Cut:
    """One style of the family: how the same letters get inked."""

    name: str = "Regular"
    nib: float = 1.0  # width of the nib; the bold styles widen it
    grow: float = 1.0  # how much rises from the letters; the italics are the overgrown styles
    xshift: float = 0.0  # sideways nudge, to keep a different stem width on the pixel grid
    simplify: float = 1.0  # outline tolerance in font units


# Black metal lettering is dark. Measured against real logos (see texture.py),
# 2 px stems left the page no blacker than an ordinary code font, so the regular
# has 3 px stems. An odd width is nudged half a pixel sideways so that both
# edges of every stem still land on pixel boundaries.
REGULAR = Cut(nib=textura.nib_for(3), xshift=textura.PX / 2)
# A drawn bold, so terminals do not fake one by smearing the regular: 4 px stems.
BOLD = replace(REGULAR, name="Bold", nib=textura.nib_for(4), xshift=0.0)
# Italic is not slanted. Editors use italic for comments and emphasis, so that
# slot holds the same letters with more growing out of them.
ITALIC = replace(REGULAR, name="Italic", grow=1.6)
BOLD_ITALIC = replace(BOLD, name="Bold Italic", grow=1.6)
CUTS = (REGULAR, BOLD, ITALIC, BOLD_ITALIC)  # one font: NecroMono, in four styles


# ---------------------------------------------------------------- geometry
def hull(points):
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]


def area(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return s / 2


def _inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def _rdp(pts, tol):
    """Ramer-Douglas-Peucker on an open run of points."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = pts[a], pts[b]
        dx, dy = bx - ax, by - ay
        d = math.hypot(dx, dy) or 1e-9
        worst, at = 0.0, -1
        for i in range(a + 1, b):
            dist = abs((pts[i][0] - ax) * dy - (pts[i][1] - ay) * dx) / d
            if dist > worst:
                worst, at = dist, i
        if worst > tol:
            keep[at] = True
            stack.append((a, at))
            stack.append((at, b))
    return [p for p, k in zip(pts, keep) if k]


def _simplify_closed(poly, tol):
    if len(poly) < 8 or tol <= 0:
        return poly
    # split at the two extreme points so the closed loop becomes two open runs
    i0 = min(range(len(poly)), key=lambda i: poly[i])
    i1 = max(range(len(poly)), key=lambda i: poly[i])
    a, b = sorted((i0, i1))
    one = _rdp(poly[a : b + 1], tol)
    two = _rdp(poly[b:] + poly[: a + 1], tol)
    return one[:-1] + two[:-1]


def _dedupe(pts):
    out = []
    for p in pts:
        if not out or p != out[-1]:
            out.append(p)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    return out


class Pen:
    """Collects the shapes of one glyph and turns them into an outline."""

    def __init__(self, name, cut=REGULAR, seed=None, edge=None, bare=False):
        self.name = name
        self.bare = bare  # draw the letter and nothing that grows from it
        self.cut = cut
        self.edge = edge  # "init" or "fina": this drawing starts or ends a word
        self.tops = []  # where upward lines were rooted, for word-edge growth
        self.polys = []
        self.frng = random.Random("f" + (seed or name))  # the fine line work; alternates differ only here

    # ------------------------------------------------------------ strokes
    # Points arrive on textura.py's drawing grid and are mapped to the font's
    # metrics; the nib is not, so stroke weight does not stretch with the letters.
    def _tmap(self, p):
        return ((p[0] - textura.W / 2) * textura.SQUEEZE + textura.CENTRE + self.cut.xshift, p[1] * (XHEIGHT / textura.X))

    @staticmethod
    def _nib(p, w, t):
        r = math.radians(textura.NIB_ANGLE)
        ux, uy = math.cos(r) * w / 2, math.sin(r) * w / 2
        vx, vy = -math.sin(r) * t / 2, math.cos(r) * t / 2
        x, y = p
        return [(x + ux + vx, y + uy + vy), (x - ux + vx, y - uy + vy), (x - ux - vx, y - uy - vy), (x + ux - vx, y + uy - vy)]

    def ts(self, *pts, w=1.0, t=None, close=False):
        """Sweep the nib along a polyline of straight strokes."""
        pts = [self._tmap(p) for p in pts]
        if close:
            pts.append(pts[0])
        nw = textura.NIB_W * w * self.cut.nib
        nt = (textura.NIB_T if t is None else t) * (1 + (self.cut.nib - 1) * 0.5)
        for a, b in zip(pts, pts[1:]):
            self.polys.append(hull(self._nib(a, nw, nt) + self._nib(b, nw, nt)))

    def tb(self, p, q, w=1.0, t=None):
        """A blade: the full nib at p, tapering to a point at q."""
        nt = (textura.NIB_T if t is None else t) * (1 + (self.cut.nib - 1) * 0.5)
        self.polys.append(hull(self._nib(self._tmap(p), textura.NIB_W * w * self.cut.nib, nt) + [self._tmap(q)]))

    def tpoly(self, *pts):
        """A filled shape given on the drawing grid."""
        self.polys.append([self._tmap(q) for q in pts])

    def rect(self, x0, y0, x1, y1):
        """A filled rectangle in font units, for the characters that must meet
        their neighbours exactly: box drawing, blocks, braille."""
        self.polys.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def _spike(self, a, b, wa, wb):
        """A dead-straight tapering line from a to b. Below one unit wide the
        far end is a single point, so rounding cannot fold it back on itself."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        near = [(a[0] + nx * wa / 2, a[1] + ny * wa / 2), (a[0] - nx * wa / 2, a[1] - ny * wa / 2)]
        far = [b] if wb < 1 else [(b[0] - nx * wb / 2, b[1] - ny * wb / 2), (b[0] + nx * wb / 2, b[1] + ny * wb / 2)]
        self.polys.append([near[0], *far[::-1], near[1]] if len(far) == 2 else [near[0], far[0], near[1]])

    def _sigil_end(self, a, tip, w, kind):
        """Finish a line that runs from a to tip."""
        dx, dy = tip[0] - a[0], tip[1] - a[1]
        d = math.hypot(dx, dy) or 1
        ux, uy = dx / d, dy / d
        nx, ny = -uy, ux
        t = max(22.0, w * 0.62)  # stroke weight of the ending
        if kind == "bar":  # a crossbar just below the tip: the line becomes a small cross
            cx, cy = tip[0] - ux * 62, tip[1] - uy * 62
            self._spike((cx - nx * 52, cy - ny * 52), (cx + nx * 52, cy + ny * 52), t, t)
        elif kind == "fork":  # two tines leaving below the tip: a trident
            fx, fy = tip[0] - ux * 84, tip[1] - uy * 84
            for s in (-1, 1):
                ang = math.atan2(uy, ux) + s * math.radians(34)
                self._spike((fx, fy), (fx + math.cos(ang) * 96, fy + math.sin(ang) * 96), t, 0.6)
        elif kind == "ring":  # an open lozenge standing on the tip
            r = 46
            cx, cy = tip[0] + ux * (r - 6), tip[1] + uy * (r - 6)
            corners = [(cx + ux * r, cy + uy * r), (cx + nx * r * 0.8, cy + ny * r * 0.8), (cx - ux * r, cy - uy * r), (cx - nx * r * 0.8, cy - ny * r * 0.8)]
            for i in range(4):
                self._spike(corners[i], corners[(i + 1) % 4], t * 0.8, t * 0.8)

    def needle(self, p, ln, w=38.0, jag=0.0, lean=None, barbs=0, end=None):
        """A thin line growing from p: up if ln > 0, down if not.

        With `jag` the line is still perfectly straight-edged, but it leaves at
        a slight angle and may break once at a hard corner. Never a curve and
        never a zigzag: at small sizes those blur into flames. `barbs` adds
        short thorns that leave the line at a sharp angle. `end` finishes the
        line the way a sigil's strokes are finished, instead of in a point:
        "bar" (a small cross), "fork" (a trident) or "ring" (an open lozenge)."""
        if self.bare:
            return
        x, y = self._tmap(p)
        ln *= XHEIGHT / textura.X
        w *= 1 + (self.cut.nib - 1) * 0.6
        if not jag:
            self.polys.append([(x - w / 2, y), (x + w / 2, y), (x, y + ln)])
            return
        rnd = self.frng
        sgn = 1 if ln > 0 else -1
        root = (x, y - sgn * 24)  # rooted inside the stroke, so it never floats
        lean_given = lean
        drift = rnd.uniform(-0.13, 0.13) * jag  # sideways drift as a share of length
        lean = drift if lean is None else lean
        tip = (x + ln * lean * sgn, y + ln)
        if lean_given is None and rnd.random() < 0.4:  # one hard break
            t = rnd.uniform(0.4, 0.68)
            turn = rnd.choice([-1, 1]) * rnd.uniform(0.1, 0.2) * abs(ln)
            knee = (x + (tip[0] - x) * t + turn * 0.5, y + ln * t)
            tip = (tip[0] - turn * 0.5, tip[1])
            self._spike(root, knee, w, w * 0.6)
            self._spike(knee, tip, w * 0.6, 0.6 if not end else w * 0.5)
            trunk, last = (root, knee), (knee, tip)
        else:
            self._spike(root, tip, w, 0.6 if not end else w * 0.5)
            trunk = last = (root, tip)
        if end:
            self._sigil_end(last[0], last[1], w, end)
        for _ in range(barbs):  # thorns: short, straight, raked toward the tip
            t = rnd.uniform(0.3, 0.8)
            bx = trunk[0][0] + (trunk[1][0] - trunk[0][0]) * t
            by = trunk[0][1] + (trunk[1][1] - trunk[0][1]) * t
            ang = math.atan2(trunk[1][1] - trunk[0][1], trunk[1][0] - trunk[0][0]) + rnd.choice([-1, 1]) * math.radians(rnd.uniform(32, 58))
            bl = rnd.uniform(46, 96)
            self._spike((bx, by), (bx + math.cos(ang) * bl, by + math.sin(ang) * bl), w * 0.62, 0.6)

    # ------------------------------------------------------------ outline
    @staticmethod
    def _union(polys):
        path = Path()
        pen = path.getPen()
        for poly in polys:
            if len(poly) < 3:
                continue
            if area(poly) < 0:
                poly = poly[::-1]
            pen.moveTo(poly[0])
            for pt in poly[1:]:
                pen.lineTo(pt)
            pen.closePath()
        path.simplify(fix_winding=True, keep_starting_points=False)
        return path

    def contours(self):
        """The union of everything drawn: outer contours clockwise, holes
        counter-clockwise, integer coordinates."""
        path = self._union(self.polys)
        rec = RecordingPen()
        path.draw(rec)
        loops, cur = [], []
        for verb, args in rec.value:
            if verb == "moveTo":
                cur = [args[0]]
            elif verb == "lineTo":
                cur.append(args[0])
            else:
                if cur:
                    loops.append(cur)
                cur = []
        polys = []
        for loop in loops:
            loop = _simplify_closed(loop, self.cut.simplify)
            loop = _dedupe([(int(round(x)), int(round(y))) for x, y in loop])
            if len(loop) >= 3 and abs(area(loop)) >= 30:
                polys.append(loop)
        out = []
        for i, c in enumerate(polys):
            depth = sum(1 for j, o in enumerate(polys) if j != i and _inside(c[0], o))
            want_cw = depth % 2 == 0
            if (area(c) < 0) != want_cw:
                c = c[::-1]
            out.append(c)
        return out
