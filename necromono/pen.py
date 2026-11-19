"""NecroMono drawing kernel.

The rules, arrived at over nine rounds of sketches:

* A letter is only the middle of its strokes. Each stroke leaves the letter at
  full weight and keeps going, thinning gradually. Nothing is attached.
* When a stroke forks it divides, like a vessel: two arms of similar weight
  at a shallow angle.
* The line work comes from a hard point, never a brush. A stroke is solid and
  ends in one sharp tip. Splinters leave its edge at an angle, and fine
  scratches are cut through the black. No bundles of parallel bristles.
* Ink may leave the cell. Only the advance is fixed.
"""
import math
import random
from dataclasses import dataclass, replace

from fontTools.pens.recordingPen import RecordingPen
from pathops import Path, PathOp, op

from . import textura

# ---------------------------------------------------------------- metrics
# Output metrics: what the font file says. Chosen so that at a given point size
# the text occupies an ordinary terminal cell: the row height of a regular
# monospace font, in a narrower cell (0.44 em), because black metal lettering
# is tall and tightly packed.
UPM = 1000
ADVANCE = 440  # advance of every glyph
ASCENDER = 950  # line box; growth is free to leave it
DESCENDER = -300
XHEIGHT = 576

# Design space: the grid the glyphs are drawn on. Skeleton points are mapped
# from here to output space; stroke weights are not, so weight is independent.
W = 420
X = 640
L, R, M = 92, 328, 210  # stem columns
SW = 128  # stem weight, before a cut's own weight factor
TALL = X + 170  # where an ascender's body stops and its spire begins
SX = ADVANCE / W
SY = XHEIGHT / X


@dataclass(frozen=True)
class Cut:
    """One cut of the family: how the same skeletons get inked."""

    name: str = "Regular"
    scratch: bool = True  # splinters, cut scratches and stray marks
    weight: float = 1.0  # multiplies every stroke weight
    nib: float = 1.0  # width of the textura nib; the bold cut widens it
    steady: bool = False  # no chance: every stem identical, strict verticals, even heights
    needle: float = 1.0  # weight of the growth relative to the stroke it leaves
    broken: bool = False  # blackletter: broad-nib contrast, every curve broken into straight strokes
    growth: float = 1.0  # how far strokes run on past the letter
    lines_per_unit: float = 1 / 24  # splinters per unit of stroke weight
    splinter_len: float = 1.0
    splinter_w: tuple = (7, 13)
    cuts: bool = True  # fine scratches cut through the black
    strays: tuple = (7, 11)  # loose hairlines per letter
    simplify: float = 1.0  # outline tolerance in font units


# The everyday cut: growth stays roughly inside the line, and the line work is
# sparse and thick enough to survive at terminal sizes.
REGULAR = Cut(name="Regular", weight=0.62, steady=True, needle=0.42, broken=True, growth=0.42, cuts=False, strays=(0, 0))
# The display cut: the full overgrowth. Unreadable at text sizes, on purpose.
# A drawn bold, so terminals do not fake one by smearing the regular.
BOLD = replace(REGULAR, name="Bold", nib=1.3)
KVLT = Cut(name="Kvlt")
CUTS = (REGULAR, BOLD, KVLT)


# ---------------------------------------------------------------- geometry
def smooth(pts, n=12):
    """Catmull-Rom through the points."""
    if len(pts) == 2:
        (x0, y0), (x1, y1) = pts
        return [(x0 + (x1 - x0) * i / (2 * n), y0 + (y1 - y0) * i / (2 * n)) for i in range(2 * n + 1)]
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            t = j / n
            out.append(
                tuple(
                    0.5
                    * (
                        2 * p1[k]
                        + (-p0[k] + p2[k]) * t
                        + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                        + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t**3
                    )
                    for k in (0, 1)
                )
            )
    out.append(P[-2])
    return out


NIB_ANGLE = math.radians(40)  # the broad pen is held at 40 degrees
NIB_THICK = 0.2  # its thin edge, as a share of its width


def nib(p, w):
    """The four corners of the pen's footprint at p."""
    if w <= 0.5:
        return [p]
    ux, uy = math.cos(NIB_ANGLE) * w / 2, math.sin(NIB_ANGLE) * w / 2
    t = max(9.0, w * NIB_THICK)
    vx, vy = -math.sin(NIB_ANGLE) * t / 2, math.cos(NIB_ANGLE) * t / 2
    x, y = p
    return [(x + ux + vx, y + uy + vy), (x - ux + vx, y - uy + vy), (x - ux - vx, y - uy - vy), (x + ux - vx, y + uy - vy)]


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


class Steady(random.Random):
    """A source of chance with the chance removed: always the middle value.
    Used by cuts that must be rigid, so the same drawing code serves both."""

    def uniform(self, a, b):
        return (a + b) / 2

    def choice(self, seq):
        return seq[0]

    def random(self):
        return 0.5

    def randint(self, a, b):
        return (a + b) // 2


class Pen:
    """Collects the shapes of one glyph and turns them into an outline."""

    def __init__(self, name, cut=REGULAR):
        self.name = name
        self.cut = cut
        self.g = cut.growth
        self.polys = []
        self.cuts = []
        # separate streams, so changing how strokes are inked never moves them
        self.rng = Steady() if cut.steady else random.Random("v9" + name)  # structure: lengths, leans, forks
        self.frng = random.Random("f" + name)  # the scratched lines
        self.srng = random.Random("s" + name)  # stray marks

    # ------------------------------------------------------------ strokes
    def raw(self, centres, halves, cut=False):
        """A ribbon along `centres` with a half-width at each point. With
        `cut`, the ribbon is removed from the glyph instead of added."""
        left, right = [], []
        N = len(centres) - 1
        for i, (x, y) in enumerate(centres):
            a = centres[max(0, i - 1)]
            b = centres[min(N, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            d = math.hypot(dx, dy) or 1
            h = halves[i]
            left.append((x - dy / d * h, y + dx / d * h))
            right.append((x + dy / d * h, y - dx / d * h))
        (self.cuts if cut else self.polys).append(left + right[::-1])

    def blade(self, pts, ws, n=12):
        """A stroke through `pts` with a weight at each point."""
        ws = [x * self.cut.weight for x in ws]
        if self.cut.broken:
            # Blackletter: no curve survives. The pen moves in straight strokes
            # from point to point, and its angle decides thick and thin.
            out = [(p[0] * SX, p[1] * SY) for p in pts]
            for i in range(len(out) - 1):
                poly = hull(nib(out[i], ws[i] * 1.18) + nib(out[i + 1], ws[i + 1] * 1.18))
                if len(poly) >= 3:
                    self.polys.append(poly)
            return
        sp = smooth([(p[0] * SX, p[1] * SY) for p in pts], n)  # design space -> output space
        segs = len(pts) - 1
        N = len(sp) - 1
        w, nrm = [], []
        for i in range(N + 1):
            u = i / N * segs
            k = min(segs - 1, int(u))
            f = u - k
            f = f * f * (3 - 2 * f)
            w.append(ws[k] + (ws[k + 1] - ws[k]) * f)
            a = sp[max(0, i - 1)]
            b = sp[min(N, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            d = math.hypot(dx, dy) or 1
            nrm.append((-dy / d, dx / d))
        if not self.cut.scratch:
            self.raw(sp, [x / 2 for x in w])
            return
        # A hard point, not a brush: the stroke itself is solid and ends in one
        # sharp tip. The scratchiness is separate line work laid over it.
        self.raw(sp, [x / 2 for x in w])
        rnd = self.frng
        wmax = max(ws) or 1
        if wmax < 26:
            return
        thin_end = 1 if w[N] <= w[0] else -1  # splinters rake toward the thinner end
        # splinters: hard hairlines that leave the stroke's edge at an angle
        for _ in range(int(1 + wmax * self.cut.lines_per_unit)):
            i = int(rnd.uniform(0.08, 0.92) * N)
            side = rnd.choice([-1, 1])
            a = sp[max(0, i - 1)]
            b = sp[min(N, i + 1)]
            ang = math.atan2((b[1] - a[1]) * thin_end, (b[0] - a[0]) * thin_end) + side * thin_end * math.radians(rnd.uniform(7, 30))
            ln = rnd.uniform(70, 260) * (0.45 + wmax / 230) * self.cut.splinter_len
            x0 = sp[i][0] + nrm[i][0] * side * w[i] * 0.3
            y0 = sp[i][1] + nrm[i][1] * side * w[i] * 0.3
            kink = rnd.uniform(-0.06, 0.06) * ln
            mid = (x0 + math.cos(ang) * ln * 0.5 - math.sin(ang) * kink, y0 + math.sin(ang) * ln * 0.5 + math.cos(ang) * kink)
            end = (x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln)
            bw = rnd.uniform(*self.cut.splinter_w)
            self.raw([(x0, y0), mid, end], [bw / 2, bw / 3.2, 0.4])
        # scratches: fine lines cut through the black, slightly off the stroke's axis
        if self.cut.cuts and wmax >= 60:
            for _ in range(rnd.randint(1, 3)):
                i = int(rnd.uniform(0.1, 0.8) * N)
                a = sp[max(0, i - 1)]
                b = sp[min(N, i + 1)]
                ang = math.atan2(b[1] - a[1], b[0] - a[0]) + math.radians(rnd.choice([-1, 1]) * rnd.uniform(3, 16))
                ln = rnd.uniform(120, 380)
                off = rnd.uniform(-0.3, 0.3) * w[i]
                x0 = sp[i][0] + nrm[i][0] * off - math.cos(ang) * ln * 0.3
                y0 = sp[i][1] + nrm[i][1] * off - math.sin(ang) * ln * 0.3
                end = (x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln)
                mid = ((x0 + end[0]) / 2, (y0 + end[1]) / 2)
                cw = rnd.uniform(5, 9)
                self.raw([(x0, y0), mid, end], [0.4, cw / 2, 0.4], cut=True)

    # ------------------------------------------------------------ textura
    # The constructed letters of the terminal cut (see textura.py). Points
    # arrive on that module's own grid and are mapped to the font's metrics;
    # the nib is not, so stroke weight does not stretch with the letters.
    @staticmethod
    def _tmap(p):
        return ((p[0] - textura.W / 2) * textura.SQUEEZE + ADVANCE / 2, p[1] * (XHEIGHT / textura.X))

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

    def _spike(self, a, b, wa, wb):
        """A dead-straight tapering line from a to b."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        self.polys.append(
            [(a[0] + nx * wa / 2, a[1] + ny * wa / 2), (b[0] + nx * wb / 2, b[1] + ny * wb / 2), (b[0] - nx * wb / 2, b[1] - ny * wb / 2), (a[0] - nx * wa / 2, a[1] - ny * wa / 2)]
        )

    def needle(self, p, ln, w=24.0, jag=0.0):
        """A thin line growing from p: up if ln > 0, down if not.

        With `jag` the line is still perfectly straight-edged, but it leaves at
        a slight angle and may break once at a hard corner. Never a curve and
        never a zigzag: at small sizes those blur into flames."""
        x, y = self._tmap(p)
        ln *= XHEIGHT / textura.X
        w *= 1 + (self.cut.nib - 1) * 0.6
        if not jag:
            self.polys.append([(x - w / 2, y), (x + w / 2, y), (x, y + ln)])
            return
        rnd = self.frng
        sgn = 1 if ln > 0 else -1
        root = (x, y - sgn * 24)  # rooted inside the stroke, so it never floats
        lean = rnd.uniform(-0.13, 0.13) * jag  # sideways drift as a share of length
        tip = (x + ln * lean * sgn, y + ln)
        if rnd.random() < 0.4:  # one hard break
            t = rnd.uniform(0.4, 0.68)
            turn = rnd.choice([-1, 1]) * rnd.uniform(0.1, 0.2) * abs(ln)
            knee = (x + (tip[0] - x) * t + turn * 0.5, y + ln * t)
            tip = (tip[0] - turn * 0.5, tip[1])
            self._spike(root, knee, w, w * 0.6)
            self._spike(knee, tip, w * 0.6, 0.6)
        else:
            self._spike(root, tip, w, 0.6)

    def limb(self, p, ang, ln, w, depth):
        """A stroke that keeps going: thins along its whole length, hooks at
        the tip, and divides into arms of similar weight."""
        rng = self.rng
        r = math.radians(ang)
        ux, uy = math.cos(r), math.sin(r)
        nx, ny = -uy, ux
        bend = rng.uniform(-0.22, 0.22)
        hook = bend + (0 if self.cut.steady else rng.choice([-1, 1]) * rng.uniform(0.05, 0.22))
        if self.cut.steady:
            depth = 0  # a rigid cut grows straight needles, unforked

        def at(t, o):
            return (p[0] + ux * ln * t + nx * ln * o, p[1] + uy * ln * t + ny * ln * o)

        self.blade([p, at(0.3, bend * 0.25), at(0.7, bend * 0.85), at(1.0, hook)], [w, w * 0.72, w * 0.36, 0])
        if depth > 0:
            t = rng.uniform(0.28, 0.5)
            wt = w * (1 - 0.7 * t)  # the parent's own weight where it divides
            s = -1 if hook > bend else 1  # the new arm leaves on the outside of the bend
            base = at(t - 0.06, bend * t * 0.8)
            self.limb(base, ang + s * rng.uniform(12, 26), ln * (1 - t) * rng.uniform(0.75, 1.05), wt * 0.92, depth - 1)

    def up(self, p, w=SW * 0.75, ln=None, lean=0.0, depth=2):
        """Let a stroke end run on upward."""
        ln = (self.rng.uniform(380, 720) if ln is None else ln) * self.g
        self.limb(p, 90 + lean + self.rng.uniform(-10, 10), ln, w * self.cut.needle, depth)

    def down(self, p, w=SW * 0.7, ln=None, lean=0.0, depth=1):
        """Let a stroke end run on downward."""
        ln = (self.rng.uniform(240, 520) if ln is None else ln) * self.g
        self.limb(p, 270 + lean + self.rng.uniform(-9, 9), ln, w * self.cut.needle, depth)

    # ------------------------------------------------------------ parts
    def stem(self, x, top=X, spire=None, lean=None, drip=None, w=SW, hook=None, bot=0, vein=True):
        rng = self.rng
        spire = (rng.uniform(520, 980) if spire is None else spire * 1.5) * self.g
        lean = rng.uniform(-14, 14) if lean is None else lean * 0.25
        drip = (rng.uniform(260, 640) if drip is None else drip * 1.4) * self.g
        hook = rng.choice([-1, 1]) if hook is None else hook
        # the body is only the middle of the stroke
        self.blade([(x, top + 10), (x, top * 0.5 + bot * 0.5), (x, bot - 10)], [w, w * 0.84, w])
        # blackletter breaks: a thorn off the shoulder, a barb off the foot
        self.blade(
            [(x - 4, top - 70), (x - w * 0.5, top + 10), (x - w * 0.7 - rng.uniform(10, 50), top + rng.uniform(100, 200))],
            [w * 0.8, w * 0.5, 0],
        )
        self.blade(
            [(x + 4, bot + 70), (x + w * 0.5, bot - 10), (x + w * 0.7 + rng.uniform(10, 50), bot - rng.uniform(90, 180))],
            [w * 0.8, w * 0.5, 0],
        )
        # ...and it keeps going, at full weight, up and down
        k = self.cut.needle
        self.limb((x, top - 30), 90 + lean + rng.uniform(-6, 6), spire + 30, w * k, 2)
        self.limb((x, bot + 30), 270 + rng.uniform(-7, 7) + (0 if self.cut.steady else 5 * hook), drip + 30, w * 0.96 * k, 1)
        if vein:  # a hair-thin echo beside the stroke
            s = rng.choice([-1, 1])
            self.blade(
                [
                    (x + s * w * 0.2, bot + (top - bot) * 0.4),
                    (x + s * (w * 0.7 + 30), bot + (top - bot) * 0.95),
                    (x + s * 70, top + spire * 0.5),
                    (x - s * 20, top + spire * 0.95),
                ],
                [16, 21, 15, 0],
            )

    def arch(self, x0, x1, y0=X - 190, peak=X + 30, w=SW):
        self.blade(
            [(x0, y0), (x0 + (x1 - x0) * 0.45, peak - 60), (x1 - 34, peak), (x1 + 2, peak - 80)],
            [w * 0.2, w * 0.42, w * 0.8, w * 0.95],
        )

    def almond(self, x0=L, x1=R, top=X, bot=0, w=SW, spire=None, drip=None):
        """Two facing blades meeting in a point above and below: the lancet bowl."""
        rng = self.rng
        spire = max(70, (rng.uniform(320, 560) if spire is None else spire) * self.g)
        drip = max(20, (rng.uniform(160, 340) if drip is None else drip) * self.g)
        m = (x0 + x1) / 2 + rng.uniform(-14, 14)
        for x, s in ((x0, -1), (x1, 1)):
            self.blade(
                [
                    (m + s * rng.uniform(4, 20), top + spire),
                    (x - s * 40, top + 20),
                    (x + s * 6, bot + (top - bot) * 0.72),
                    (x + s * 6, bot + (top - bot) * 0.3),
                    (x - s * 40, bot),
                    (m - s * rng.uniform(4, 20), bot - drip),
                ],
                [0, w * 0.5, w, w, w * 0.5, 0],
            )
        self.limb((m, top + spire * 0.35), 90 + rng.uniform(-10, 10), rng.uniform(420, 760) * self.g, w * 0.8, 2)
        self.limb((m, bot - drip * 0.3), 270 + rng.uniform(-8, 8), rng.uniform(240, 520) * self.g, w * 0.7, 1)
        self.blade(
            [(m - 70, top * 0.2), (m - 104, top * 0.6), (m - 40, top + spire * 0.6), (m + 20, top + spire * 1.3)],
            [16, 21, 15, 0],
        )

    # ------------------------------------------------------------ finishing
    def run_on(self):
        """A letter whose highest or lowest point is not already a spire or a
        drip still runs on from there, at stroke weight, so there is no seam."""
        rng = self.rng
        pts = [(p[0] / SX, p[1] / SY) for poly in self.polys for p in poly]  # back to design space
        hi = max(pts, key=lambda p: p[1])
        lo = min(pts, key=lambda p: p[1])
        if hi[1] < X + 420 * self.g:
            self.limb((hi[0], hi[1] - 90), 90 + rng.uniform(-12, 12), rng.uniform(420, 720) * self.g, SW * 0.8, 2)
        if lo[1] > -220 * self.g:
            self.limb((lo[0], lo[1] + 90), 270 + rng.uniform(-10, 10), rng.uniform(280, 520) * self.g, SW * 0.7, 1)

    def strays(self):
        """Stray marks: the pen skipping, dragging, going over the letter again."""
        if not self.cut.scratch:
            return
        rng = self.srng
        pts = [p for poly in self.polys for p in poly]
        x0 = max(min(p[0] for p in pts), -60)
        x1 = min(max(p[0] for p in pts), ADVANCE + 60)
        for _ in range(rng.randint(*self.cut.strays)):
            x = rng.uniform(x0, x1)
            y = rng.uniform(-260, XHEIGHT + 200)
            ang = 90 + (rng.uniform(-10, 10) if rng.random() < 0.7 else rng.choice([-1, 1]) * rng.uniform(28, 60))
            ln = rng.uniform(180, 620)
            r = math.radians(ang)
            n = 14
            ph = rng.uniform(0, 6.28)
            cs = [
                (x + math.cos(r) * ln * i / n + 4 * math.sin(i * 0.8 + ph), y + math.sin(r) * ln * i / n + rng.uniform(-2, 2))
                for i in range(n + 1)
            ]
            self.raw(cs, [rng.uniform(4, 7.5) * math.sin(math.pi * i / n) ** 0.4 for i in range(n + 1)])

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
        if self.cuts:
            path = op(path, self._union(self.cuts), PathOp.DIFFERENCE, fix_winding=True)
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
