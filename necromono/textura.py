"""necromono's letters: constructed textura.

Every letter is assembled from the same few parts, drawn with a broad nib held
at a fixed angle: a straight stem with a diamond head and foot, six-sided
broken bowls, hairline joins. The black metal is in the rigidity and in what
grows off the parts: thin straight lines rising from free stem tops, a drip
falling from each foot, forked ascenders, descenders that end in daggers.

Drawn on its own grid (600 wide, x-height 540) and mapped to the font's
metrics by the pen, so the letters come out narrower and taller than drawn.
"""
import math
import random

W, X, ASC, DESC = 600, 540, 790, -220
# ---- the pixel grid
# macOS ignores font hinting, so the only way to get sharp stems is to draw the
# letters for the pixel grid they will actually land on. The target is 13pt on
# a Retina display: 26 pixels per em. At that size the cell is 12 px wide, a
# stem is exactly 2 px, and every stem is centred on a whole pixel, so both its
# edges fall on pixel boundaries. The layout of a two-stem letter is
#     1 px gap | 2 px stem | 4 px counter | 2 px stem | 3 px gap
# which makes the counter equal to the gap between letters: the even picket
# fence that textura depends on. The x-height is 15 px and capitals 20 px.
PX = 1000 / 26  # one pixel, in font units
CELL = 12  # cell width in pixels
XPP = (472 - 128) / 6  # drawing units per pixel


def col(n):
    """The drawing x whose stem is centred on pixel n of the cell."""
    return 300 + (n - 5) * XPP


SQUEEZE = PX / XPP  # letters are drawn wide and squeezed onto the grid
CENTRE = 5 * PX  # where drawing x = 300 lands

# a nib whose vertical stroke is exactly 2 px wide
NIB_ANGLE, NIB_T = 38.0, 20.0
NIB_W = (2 * PX - NIB_T * math.sin(math.radians(NIB_ANGLE))) / math.cos(math.radians(NIB_ANGLE))


def stem_px(nib, w=1.0, thick=1.0):
    """Width in pixels of a vertical stroke drawn with this nib."""
    r = math.radians(NIB_ANGLE)
    return (NIB_W * nib * w * math.cos(r) + NIB_T * (1 + (nib - 1) * 0.5) * thick * math.sin(r)) / PX


def nib_for(px, thick=1.0):
    """The nib factor whose vertical stroke is exactly px pixels wide."""
    lo, hi = 0.5, 4.0
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if stem_px(mid, thick=thick) < px else (lo, mid)
    return (lo + hi) / 2


def crowded(p):
    """For letters with three stems in one cell. Returns the stroke-width factor
    that makes their stems one pixel narrower than the style's own, and the
    sideways correction that keeps those narrower stems on the pixel grid."""
    nib = p.cut.nib
    px = 2  # always two pixels: three heavier stems would close the counters entirely
    lo, hi = 0.2, 1.2
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if stem_px(nib, mid, p.cut.thick) < px else (lo, mid)
    want = PX / 2 if px % 2 else 0.0
    return (lo + hi) / 2, (want - p.cut.xshift) / SQUEEZE
_r = math.radians(NIB_ANGLE)
HY = (NIB_W * math.sin(_r) + NIB_T * math.cos(_r)) / 2
YT, YB = X - HY, HY  # a stroke at YT has its top exactly on the x-height
AT, DB = ASC - HY, DESC + HY
L, R, M = col(2), col(8), col(5)
K, D = 66, 42  # run and drop of a diamond. Heads and feet are full lozenges: with the breaks, they are what makes the
# dark bands along the x-height and baseline that blackletter has and a row of bare stems does not.
UP, DOWN = 250, 95  # needle and drip lengths; the upward lines lead

# the broken bowl shared by o, b, d, p, q, c, e, g
# The broken bowl. Its top-left side climbs at the nib's own angle, so it is a
# hairline; at the peak the stroke breaks and falls into the right stem thick.
# The bottom is the same turned half round. Nothing in it is a curve.
RISE, PEAK, FALL = 150, 104, 92
RISE_T = 84  # arches rise on a stroke with some body, so n and u differ by more than a hairline
TL, TP, TR = (L, YT - RISE), (R - PEAK, YT + 4), (R, YT - FALL)
BR, BP, BL = (R, YB + RISE), (L + PEAK, YB - 4), (L, YB + FALL)

TEXTURA = {}


def glyph(chars):
    def deco(fn):
        for ch in chars:
            TEXTURA[ch] = fn
        return fn

    return deco


# ---- unruliness, and sigil endings
# Some lines do not end in a point. They end the way the strokes of a seal in a
# grimoire end: in a small crossbar, a fork, or an open lozenge. A line finished
# like that reads as a mark someone made on purpose, not as a thorn. Those
# lines carry no thorns, and the calm short ones are left plain.
ENDS = ["bar", "bar", "bar", "fork", "fork", "ring"]


# The growth is not handed out evenly. Most strokes get a line or two; some get
# almost nothing; now and then one is possessed and throws a cluster, with one
# line shooting far past the rest into the row above. That unevenness, not any
# particular ornament, is what stops the page looking tidy. Every line stays
# straight-edged and sharp, and some carry thorns.
def up(p, pt, ln=UP):
    if getattr(p, "quiet", False):  # an accent is coming: leave the space above the letter to it
        return
    r = p.frng
    g = p.cut.grow
    p.tops.append(pt)
    root = (pt[0], pt[1] + HY - 10)
    mood = r.random() - (g - 1) * 0.35  # the overgrown styles are possessed more often
    if mood > 0.74:  # calm: one short line
        p.needle(root, ln * r.uniform(0.5, 0.9), w=34.0, jag=0.8)
        return
    if mood < 0.2:  # possessed: a cluster, and one line that will not stop
        p.needle(root, ln * r.uniform(2.6, 3.8), w=40.0, jag=0.5, end=r.choice(ENDS))  # the tall one is always finished as a sigil
        for _ in range(r.randint(2, 3)):
            p.needle((pt[0] + r.uniform(-62, 62), pt[1] + HY - r.uniform(14, 36)), ln * r.uniform(0.5, 1.7), w=30.0, jag=2.0, barbs=r.randint(0, 1))
        return
    end = r.choice(ENDS) if r.random() < 0.45 else None
    p.needle(root, ln * r.uniform(1.3, 1.9) * (1 + (g - 1) * 0.5), w=38.0, jag=0.8 if end else 1.5, barbs=0 if end else r.choice([0, 1, 1, 2]), end=end)  # a sigil ending, or thorns: never both
    if r.random() < 0.8 * g:
        p.needle((pt[0] + r.choice([-1, 1]) * r.uniform(30, 50), pt[1] + HY - 30), ln * r.uniform(0.5, 1.0) * g, w=30.0, jag=1.4)
    if g > 1.3:  # the overgrown styles: a third line, and it may lean hard
        p.needle((pt[0] + r.choice([-1, 1]) * r.uniform(50, 80), pt[1] + HY - 34), ln * r.uniform(0.7, 1.3), w=28.0, jag=2.2, barbs=r.randint(0, 1))


def finish(p):
    """A letter that starts or ends a word throws one long line outward, so
    every word is bracketed the way a logo is."""
    if not p.edge or not p.tops:
        return
    # The same pair of horns on every word-start, mirrored on every word-end,
    # whatever the letters are: so a word's two ends answer each other, the way
    # a logo is drawn about its centre line.
    r = random.Random("word edge")
    side = -1 if p.edge == "init" else 1
    pt = min(p.tops, key=lambda q: q[0] * side * -1)
    for reach, lean, w in ((r.uniform(2.3, 2.7), r.uniform(0.2, 0.26), 40.0), (r.uniform(1.2, 1.5), r.uniform(0.42, 0.5), 32.0)):
        p.needle((pt[0] + side * 22, pt[1] + HY - 24), UP * reach, w=w, jag=0.0001, lean=side * lean)


def down(p, pt, ln=DOWN):
    """What falls from a foot: usually a short drip; now and then one that
    runs on well into the row below, sometimes with a thorn."""
    r = p.frng
    root = (pt[0], pt[1] - HY + 10)
    if r.random() < 0.16 + (p.cut.grow - 1) * 0.25:
        p.needle(root, -ln * r.uniform(2.4, 4.2), w=36.0, jag=0.6, barbs=r.randint(0, 2))
        return
    p.needle(root, -ln)


def stem(p, x, top=YT, bot=YB, head=True, foot=True, grow_up=True, grow_down=True, w=1.0):
    pts = [(x - K, top)] if head else []
    pts += [(x, top - D if head else top), (x, bot + D if foot else bot)]
    if foot:
        pts.append((x + K, bot))
    p.ts(*pts, w=w)
    if grow_up:
        up(p, pts[0])
    if grow_down:
        down(p, pts[-1])


def fork(p, x, y=AT):
    """Ascender head: a diamond, a horn torn off to the left, a needle."""
    p.ts((x - K, y), (x, y - D))
    p.tb((x - K, y), (x - K - 62, y + 92), w=0.68)
    up(p, (x, y - 6), ln=UP * 0.7)


def dagger(p, x, y_from):
    p.tb((x, y_from), (x - 14, DB - 62))


def rot(pts, cx=W / 2, cy=X / 2):
    return [(2 * cx - x, 2 * cy - y) for x, y in pts]


@glyph("a")
def _(p):
    p.ts((L + 30, YT - 118), TP, TR, (R, YB + D), (R + K, YB))
    p.tb((L + 30, YT - 118), (L + 6, YT - 210), w=0.6)
    p.ts((R, 318), (L + 10, 262), BL, BP, (R, YB + 165), t=58)
    up(p, TP)
    down(p, (R + K, YB))


@glyph("b")
def _(p):
    fork(p, L)
    p.ts((L, AT - D), BL, BP, BR, TR, TP, TL)
    down(p, BP)


@glyph("c")
def _(p):
    p.ts((R - 30, YT - 60), TP, TL, BL, BP)  # open on the right from top to bottom
    p.tb(BP, (R + 20, YB + 96))
    up(p, TP)
    down(p, BP)


@glyph("d")
def _(p):
    fork(p, R)
    p.ts((R, AT - D), (R, YB + D), (R + K, YB))
    p.ts(TR, TP, TL, BL, BP, (R, YB + 165), t=58)
    down(p, (R + K, YB))


@glyph("e")
def _(p):
    p.ts((R, YT - 150), TR, TP, TL, BL, BP)
    p.tb(BP, (R + 10, YB + 86))
    p.ts((R, YT - 150), (L, YT - 300), t=84)  # the eye closes with a stroke that has body
    up(p, TP)
    down(p, BP)


@glyph("f")
def _(p):
    # the long f: hooked above, and no foot: it stabs below the line
    x = col(4)
    p.ts((470, AT - 58), (400, AT), (x, AT - 62), (x, -40))
    p.tb((x, -40), (x - 24, DB - 20))
    p.ts((x - 60, YT), (440, YT), w=0.8)
    up(p, (400, AT), ln=UP * 0.7)


@glyph("g")
def _(p):
    p.ts(TL, TP, TR, (R, DB + RISE), (L + PEAK, DB - 4), (L + 6, DB + 80))
    p.ts(TL, BL, BP, (R, YB + 165), t=58)
    p.tb((R, YT - 60), (R + 96, YT + 30), w=0.7)  # the ear
    up(p, TP)
    down(p, (L + PEAK, DB), ln=DOWN * 0.6)


@glyph("h")
def _(p):
    fork(p, L)
    p.ts((L, AT - D), (L, YB + D), (L + K, YB))
    p.ts((L, YT - RISE), (R - PEAK, YT + 4), t=RISE_T)
    p.ts((R - PEAK, YT + 4), (R, YT - FALL), (R, YB + 70))
    p.tb((R, YB + 70), (R - 96, -200))
    down(p, (L + K, YB))


def _i_body(p):
    p.ts((196, YT - 82), (272, YT), (M, YT - D), (M, YB + D), (M + K, YB))
    p.tb((M + K, YB), (M + K + 104, YB + 84))
    down(p, (M + K, YB))


@glyph("i")
def _(p):
    _i_body(p)
    p.ts((M - 30, X + 168), (M - 8, X + 140))
    up(p, (M - 30, X + 168), ln=UP * 0.6)


@glyph("\u0131")  # dotless i
def _(p):
    _i_body(p)


@glyph("j")
def _(p):
    x = col(6)
    p.ts((x - 104, YT - 82), (x - 28, YT), (x, YT - D), (x, -40))
    p.tb((x, -40), (x - 150, DB - 40))
    p.ts((x - 30, X + 168), (x - 8, X + 140))
    up(p, (x - 30, X + 168), ln=UP * 0.6)


@glyph("k")
def _(p):
    fork(p, L)
    p.ts((L, AT - D), (L, YB + D), (L + K, YB))
    p.ts((L, YT - 215), (R - 110, YT - 20), (R - 16, YT - 104), (L + 80, 276), t=58)  # a small closed loop
    p.ts((L + 80, 276), (R, YB + D), (R + K, YB))
    down(p, (L + K, YB))
    down(p, (R + K, YB))


@glyph("l")
def _(p):
    fork(p, M)
    p.ts((M, AT - D), (M, YB + 80), (M + 100, YB), (M + 230, YB + 40))  # the foot turns out to the right
    p.tb((M + 230, YB + 40), (M + 280, YB + 150))


@glyph("m")
def _(p):
    w, dx = crowded(p)  # three stems in one cell: each a pixel narrower than usual
    a, b, c = col(1) + dx, col(5) + dx, col(9) + dx  # on even pixels, so the stems are whole pixels on a 1x display as well
    stem(p, a, w=w)
    for s, e in ((a, b), (b, c)):
        p.ts((s, YT - 110), (e - 84, YT + 4), w=w, t=RISE_T)
        p.ts((e - 84, YT + 4), (e, YT - 70), (e, YB + D), (e + K, YB), w=w)
    down(p, (b + K, YB))
    down(p, (c + K, YB))


N_LEFT = [(L - K, YT), (L, YT - D), (L, YB + D), (L + K, YB)]
N_RIGHT = [(L, YT - 205), (R - PEAK, YT + 4), (R, YT - FALL), (R, YB + D), (R + K, YB)]  # a pointed arch that leaves the stem low, so n and u differ by a visible diagonal


@glyph("n")
def _(p):
    p.ts(*N_LEFT)
    p.ts(*N_RIGHT[:2], t=RISE_T)
    p.ts(*N_RIGHT[1:])
    up(p, N_LEFT[0])  # one line: the stem under the arch grows none
    down(p, N_LEFT[-1])
    down(p, N_RIGHT[-1])


@glyph("u")
def _(p):
    a, b = rot(N_LEFT), rot(N_RIGHT)  # n turned half round: open at the top, closed below
    p.ts(*a)
    p.ts(*b[:2], t=RISE_T)
    p.ts(*b[1:])
    up(p, b[-1])  # two lines
    up(p, a[-1])
    down(p, a[0])


@glyph("o")
def _(p):
    p.ts(TL, TP, TR, BR, BP, BL, close=True)
    up(p, TP)
    down(p, BP)


@glyph("p")
def _(p):
    p.ts((L - K, YT), (L, YT - D), (L, DB + 96))
    dagger(p, L, DB + 96)
    p.ts(TL, TP, TR, BR, BP, BL)
    up(p, (L - K, YT))


@glyph("q")
def _(p):
    p.ts(TR, (R, DB + 96))
    dagger(p, R, DB + 96)
    p.ts(TR, TP, TL, BL, BP, (R, YB + 165), t=58)
    up(p, TP)


@glyph("r")
def _(p):
    x = col(3)
    stem(p, x)
    p.ts((x, YT - RISE), (x + 210, YT + 4), (x + 300, YT - FALL))
    p.tb((x + 300, YT - FALL), (x + 262, YT - 200), w=0.6)  # the flag ends in a flick
    p.tb((x + K, YB), (x + K + 104, YB + 62), w=0.6)


@glyph("s")
def _(p):
    p.ts((R - 6, YT - 86), TP, (L + 14, YT - 100), (L + 14, YT - 176), (R - 14, YB + 176), (R - 14, YB + 100), BP, (L + 6, YB + 86))
    up(p, TP)
    down(p, BP)


@glyph("t")
def _(p):
    x = col(4)
    p.ts((x, 652), (x, YB + 62), (x + 84, YB))
    p.tb((x + 84, YB), (500, YB + 128))
    p.ts((108, YT), (452, YT), w=0.8)
    up(p, (x, 652), ln=UP * 0.8)
    down(p, (x + 84, YB))


@glyph("v")
def _(p):
    p.ts((74, YT + 4), (112, YT - 20), (292, YB), (496, YT))
    up(p, (74, YT + 4))
    up(p, (496, YT))
    down(p, (292, YB))


@glyph("w")
def _(p):
    p.ts((48, YT + 4), (70, YT - 16), (176, YB), (300, YT - 90), (424, YB), (544, YT), w=0.82)
    up(p, (48, YT + 4))
    up(p, (544, YT))
    down(p, (176, YB))
    down(p, (424, YB))


@glyph("x")
def _(p):
    p.ts((84, YT + 2), (124, YT - 20), (476, YB + 20), (516, YB - 2))
    p.ts((118, YB), (482, YT), w=0.66, t=44)
    up(p, (84, YT + 2))
    up(p, (482, YT))
    down(p, (516, YB - 2))
    down(p, (118, YB))


@glyph("y")
def _(p):
    p.ts((74, YT + 4), (112, YT - 20), (262, 180))  # the left arm joins high
    p.ts((496, YT), (270, -40), (230, DB + 20))  # the right stroke runs on deep below the line
    p.tb((230, DB + 20), (110, DB - 40))
    up(p, (74, YT + 4))
    up(p, (496, YT))


@glyph("z")
def _(p):
    p.ts((132, YT), (468, YT), w=0.75)
    p.ts((468, YT), (132, YB))
    p.ts((132, YB), (468, YB), w=0.75)
    up(p, (132, YT))
    down(p, (468, YB))


# ------------------------------------------------------------------ capitals
CAPH = 720
CT = CAPH - HY
CTL, CTP, CTR = (L, CT - RISE), (R - PEAK, CT + 4), (R, CT - FALL)
CUP = UP * 0.55  # capitals are already tall; their needles are shorter


def cstem(p, x, grow_up=True, grow_down=True, w=1.0, foot=True, head=True, double=False):
    # `double` is accepted and ignored: at the weight the font settled on, a hairline
    # inside a 3 px counter turned every capital into the same block.
    pts = [(x - K, CT)] if head else []
    pts += [(x, CT - D if head else CT), (x, YB + D if foot else YB)]
    if foot:
        pts.append((x + K, YB))
    p.ts(*pts, w=w)
    if grow_up:
        up(p, pts[0], ln=CUP)
    if grow_down:
        down(p, pts[-1])


def mirror(pts):
    return [(W - x, y) for x, y in pts]


@glyph("A")
def _(p):
    p.ts((250, CT), (R, CT - 80), (R, YB + D), (R + K, YB))
    p.ts((300, CT - 20), (L, YB + 50), (L - 20, YB))
    p.ts((196, 250), (R, 250), w=0.6)
    up(p, (250, CT), ln=CUP)
    down(p, (R + K, YB))
    down(p, (L - 20, YB))


@glyph("B")
def _(p):
    cstem(p, L)
    p.ts((L, CT), (320, CT), (380, CT - 70), (380, 450), (320, 390), w=1.0)  # upper bowl, the narrower
    p.ts((L, 380), (320, 380), w=1.3)  # a heavy waist
    p.ts((320, 380), (R + 16, 300), (R + 16, YB + RISE), (L + PEAK, YB - 4), (L + K, YB))


@glyph("C")
def _(p):
    p.ts((458, CT - 52), CTP, CTL, BL, BP)
    p.tb(BP, (492, YB + 128))
    up(p, CTP, ln=CUP)
    down(p, BP)


@glyph("D")
def _(p):
    # a shield: both right corners cut away hard
    cstem(p, L)
    p.ts((L, CT), (R - 150, CT), (R, CT - 210), (R, YB + 210), (R - 150, YB), (L + K, YB))


@glyph("E")
def _(p):
    # flat heavy arms top and bottom and a tongue between
    cstem(p, L, grow_down=False)
    p.ts((L, CT), (456, CT), w=1.15)
    p.tb((456, CT), (486, CT - 150), w=0.9)
    p.ts((L, 372), (420, 372), w=1.1)
    p.ts((L + K, YB), (460, YB), w=1.2)
    p.tb((460, YB), (500, YB + 150), w=0.9)


@glyph("F")
def _(p):
    # no foot: the stem runs on below the line as a dagger, as the long f does
    p.ts((L - K, CT), (L, CT - D), (L, -40))
    p.tb((L, -40), (L - 30, DB - 30))
    p.ts((L, CT), (456, CT), w=1.15)
    p.tb((456, CT), (486, CT - 150), w=0.9)
    p.ts((L, 372), (400, 372), w=1.0)
    up(p, (L - K, CT), ln=CUP)


@glyph("G")
def _(p):
    p.ts((458, CT - 52), CTP, CTL, BL, BP, (R, YB + 70), (R, 336))
    p.ts((R, 336), (320, 336), w=0.7)
    up(p, CTP, ln=CUP)
    down(p, BP)


@glyph("H")
def _(p):
    cstem(p, L)
    p.ts((L, 372), (R, 372), w=1.4)  # a heavy bar
    p.ts((R - K, CT), (R, CT - D), (R, YB + 60))
    p.tb((R, YB + 60), (R - 90, -240))  # and its right leg runs on well below the line
    up(p, (R - K, CT), ln=CUP)


@glyph("I")
def _(p):
    cstem(p, M, head=False, foot=False)
    p.ts((M - 190, CT), (M + 190, CT), w=1.0)
    p.ts((M - 190, YB), (M + 190, YB), w=1.0)


@glyph("J")
def _(p):
    # it hooks below the line
    p.ts((R - K, CT), (R, CT - D), (R, -60), (390, -160), (230, -160), (150, -80))
    p.ts((200, CT), (R, CT), w=1.0)
    up(p, (R - K, CT), ln=CUP)


@glyph("K")
def _(p):
    cstem(p, L)
    p.ts((L, 330), (R + 10, CT), w=0.8, t=40)  # an open arm to the top corner; R's bowl is closed
    p.ts((L + 90, 400), (R + 10, YB + D), (R + 10 + K, YB))
    down(p, (R + 10 + K, YB))


@glyph("L")
def _(p):
    fork(p, L, CT)
    p.ts((L, CT - D), (L, YB + 70), (L + 80, YB), (450, YB), w=1.0)
    p.tb((450, YB), (500, YB + 150), w=0.9)


@glyph("M")
def _(p):
    w, dx = crowded(p)
    a, b, c = col(1) + dx, col(5) + dx, col(9) + dx
    cstem(p, a, w=w)
    cstem(p, c, w=w)
    p.ts((a, CT - 20), (b, 300), (c, CT - 20), w=0.66, t=40)
    down(p, (b, 300), ln=DOWN * 0.8)


@glyph("N")
def _(p):
    # thin stems and a heavy diagonal: the diagonal is the letter
    p.ts((L - K, CT), (L, CT - D), (L, YB + D), (L + K, YB), w=0.72)
    p.ts((R - K, CT), (R, CT - D), (R, YB + D), (R + K, YB), w=0.72)
    p.ts((L, CT - 10), (R, YB + 10), w=1.15)
    up(p, (L - K, CT), ln=CUP)
    down(p, (R + K, YB))


@glyph("O")
def _(p):
    p.ts(CTL, CTP, CTR, BR, BP, BL, close=True)
    up(p, CTP, ln=CUP)
    down(p, BP)


@glyph("P")
def _(p):
    cstem(p, L)  # it stands on a foot; F is the one that runs on below the line
    p.ts((L, CT), (380, CT), (R, CT - 80), (R, 410), (390, 336), (L, 336))


@glyph("Q")
def _(p):
    p.ts(CTL, CTP, CTR, BR, BP, BL, close=True)
    p.ts((300, 150), (470, -40), w=1.0)  # a tail that cannot be missed
    p.tb((470, -40), (590, -190))
    up(p, CTP, ln=CUP)


@glyph("R")
def _(p):
    cstem(p, L, double=True)
    p.ts((L, CT), (380, CT), (R, CT - 80), (R, 410), (390, 336), (L, 336))
    p.ts((280, 336), (R + 20, YB + 30), w=1.1)  # a heavy leg kicked out past the bowl
    p.tb((R + 20, YB + 30), (R + 110, -150))


def _S(p, w=1.0):
    p.ts((458, CT - 56), (388, CT), (140, CT - 70), (140, CT - 200), (460, YB + 200), (460, YB + 66), (212, YB), (142, YB + 56), w=w)


@glyph("S")
def _(p):
    _S(p)
    up(p, (388, CT), ln=CUP)
    down(p, (212, YB))


@glyph("T")
def _(p):
    cstem(p, M, head=False)
    p.ts((40, CT), (560, CT), w=1.0)  # a wide heavy bar whose ends hang down
    p.tb((50, CT), (24, CT - 170), w=0.8)
    p.tb((550, CT), (576, CT - 170), w=0.8)


@glyph("U")
def _(p):
    p.ts((L - K, CT), (L, CT - D), (L, YB + 230), (L + PEAK + 40, YB - 4), (R, YB + 190))  # closed below by a deep heavy break
    cstem(p, R)
    up(p, (L - K, CT), ln=CUP)


@glyph("V")
def _(p):
    p.ts((74, CT + 4), (112, CT - 20), (292, YB), (496, CT))
    up(p, (74, CT + 4), ln=CUP)
    up(p, (496, CT), ln=CUP)
    down(p, (292, YB))


@glyph("W")
def _(p):
    p.ts((48, CT + 4), (70, CT - 16), (176, YB), (300, CT - 130), (424, YB), (544, CT), w=0.82)
    up(p, (48, CT + 4), ln=CUP)
    up(p, (544, CT), ln=CUP)
    down(p, (176, YB))
    down(p, (424, YB))


@glyph("X")
def _(p):
    p.ts((84, CT + 2), (124, CT - 20), (476, YB + 20), (516, YB - 2))
    p.ts((118, YB), (482, CT), w=0.66, t=44)
    up(p, (84, CT + 2), ln=CUP)
    up(p, (482, CT), ln=CUP)
    down(p, (516, YB - 2))
    down(p, (118, YB))


@glyph("Y")
def _(p):
    p.ts((74, CT + 4), (112, CT - 20), (300, 340))
    p.ts((496, CT), (300, 340), w=0.8)
    p.ts((300, 340), (300, YB + D), (300 + K, YB))
    up(p, (74, CT + 4), ln=CUP)
    up(p, (496, CT), ln=CUP)
    down(p, (300 + K, YB))


@glyph("Z")
def _(p):
    p.ts((132, CT), (468, CT), w=0.75)
    p.ts((468, CT), (132, YB))
    p.ts((132, YB), (468, YB), w=0.75)
    up(p, (132, CT), ln=CUP)
    down(p, (468, YB))


# ------------------------------------------------------------------ digits
# Same construction and weight as the letters, but nothing grows off them:
# numbers have to be read exactly.
SIX = [(444, CT - 40), (380, CT), (210, CT), (L, CT - 80), (L, YB + 60), (210, YB), (390, YB), (R, YB + 62), (R, 330), (390, 400), (L, 356)]


@glyph("0")
def _(p):
    # narrower than O, with an eye at its centre
    a, b = col(3), col(7)
    p.ts((a, CT - RISE), (b - 70, CT + 4), (b, CT - FALL), (b, YB + RISE), (a + 70, YB - 4), (a, YB + FALL), close=True)
    c = (a + b) / 2
    p.ts((c - 16, CT / 2 + 58), (c + 16, CT / 2 + 14), w=0.62)


@glyph("1")
def _(p):
    x = col(5.5)
    p.ts((x, CT), (x, YB + D), (x + K, YB))
    p.ts((x, CT), (90, CT - 230), w=0.9)  # a long heavy flag: never an l or an I


@glyph("2")
def _(p):
    p.ts((140, CT - 96), (210, CT), (390, CT), (R, CT - 80), (R, CT - 210), (132, YB))
    p.ts((132, YB), (468, YB), w=0.75)


@glyph("3")
def _(p):
    p.ts((140, CT - 60), (210, CT), (390, CT), (R, CT - 70), (R, 430), (380, 366), (250, 366))
    p.ts((380, 366), (R, 300), (R, YB + 62), (390, YB), (210, YB), (140, YB + 60))


@glyph("4")
def _(p):
    x = col(7)
    p.ts((x, CT), (120, 250))
    p.ts((120, 250), (530, 250), w=0.7)
    p.ts((x, CT), (x, YB + D), (x + K, YB))


@glyph("5")
def _(p):
    p.ts((160, CT), (456, CT), w=0.75)
    p.ts((160, CT), (160, 410))
    p.ts((160, 410), (390, 410), (R, 336), (R, YB + 62), (390, YB), (210, YB), (140, YB + 60))


@glyph("6")
def _(p):
    p.ts(*SIX)


@glyph("7")
def _(p):
    p.ts((132, CT), (468, CT), w=0.75)
    p.ts((468, CT), (250, YB))


@glyph("8")
def _(p):
    p.ts((300, CT), (170, CT - 70), (170, 440), (300, 370), (R, 290), (R, YB + 62), (390, YB), (210, YB), (L, YB + 62), (L, 290), (300, 370), (430, 440), (430, CT - 70), (300, CT))


@glyph("9")
def _(p):
    p.ts(*rot(SIX, cy=(CT + YB) / 2))  # six turned half round


def pentagram(p, cx, cy, r, w=0.36, t=30):
    """A five-pointed star drawn as five crossing strokes, one point down."""
    pts = [(cx + r * 0.92 * math.cos(math.radians(-90 + 72 * k)), cy + r * math.sin(math.radians(-90 + 72 * k))) for k in range(5)]
    for k in range(5):
        p.ts(pts[k], pts[(k + 2) % 5], w=w, t=t)


# ------------------------------------------------------------------ punctuation
# A lighter nib and no growth: brackets and operators are what code hangs on.
PN = 0.86
MIDY = 270  # the height operators sit on
TOPY, BOTY = AT + 20, DB - 10  # brackets span the whole line


def dot(p, x=M, y=YB):
    p.ts((x - 20, y + 22), (x + 20, y - 22), w=1.15)


def comma(p, x=M, y=YB):
    dot(p, x, y)
    p.tb((x + 20, y - 22), (x - 60, y - 190), w=0.8)


@glyph(".")
def _(p):
    dot(p)


@glyph(",")
def _(p):
    comma(p)


@glyph(":")
def _(p):
    dot(p)
    dot(p, y=400)


@glyph(";")
def _(p):
    comma(p)
    dot(p, y=400)


@glyph("!")
def _(p):
    p.tb((300, CT + 20), (300, 170), w=1.1)
    dot(p)


@glyph("?")
def _(p):
    p.ts((150, CT - 90), (220, CT), (390, CT), (R, CT - 80), (R, CT - 200), (300, 310), (300, 200), w=0.8)
    dot(p)


@glyph("'")
def _(p):
    p.tb((300, AT + 10), (288, AT - 200), w=0.8)


@glyph('"')
def _(p):
    p.tb((210, AT + 10), (198, AT - 200), w=0.8)
    p.tb((390, AT + 10), (378, AT - 200), w=0.8)


@glyph("`")
def _(p):
    p.tb((220, AT + 30), (340, AT - 150), w=0.7)


@glyph("-")
def _(p):
    p.ts((110, MIDY), (490, MIDY), w=0.95)


@glyph("_")
def _(p):
    p.ts((-40, -120), (640, -120), w=0.5)


@glyph("=")
def _(p):
    p.ts((110, MIDY + 84), (490, MIDY + 84), w=0.85)
    p.ts((110, MIDY - 84), (490, MIDY - 84), w=0.85)


@glyph("+")
def _(p):
    # a cross with body, whose four arms end in points
    for inner, tip in (((300, MIDY + 130), (300, MIDY + 270)), ((300, MIDY - 130), (300, MIDY - 270)), ((170, MIDY), (50, MIDY)), ((430, MIDY), (550, MIDY))):
        p.ts((300, MIDY), inner, w=0.95)
        p.tb(inner, tip, w=0.95)


@glyph("*")
def _(p):
    pentagram(p, 300, MIDY + 50, 250, w=0.4, t=32)  # the asterisk is a pentagram


@glyph("/")
def _(p):
    p.ts((480, AT), (120, DB), w=PN, t=40)


@glyph("\\")
def _(p):
    p.ts((120, AT), (480, DB), w=PN)


@glyph("|")
def _(p):
    p.ts((300, TOPY + 20), (300, BOTY - 20), w=PN)


@glyph("<")
def _(p):
    p.ts((450, MIDY + 200), (140, MIDY), (450, MIDY - 200), w=0.9, t=46)


@glyph(">")
def _(p):
    p.ts(*mirror([(450, MIDY + 200), (140, MIDY), (450, MIDY - 200)]), w=0.9, t=46)


@glyph("^")
def _(p):
    p.ts((160, CT - 150), (300, CT + 30), (440, CT - 150), w=PN, t=36)


@glyph("~")
def _(p):
    p.ts((100, MIDY - 40), (220, MIDY + 60), (380, MIDY - 60), (500, MIDY + 40), w=PN)


PAREN = [(col(8), TOPY + 10), (col(4.5), TOPY - 250), (col(3.5), MIDY), (col(4.5), BOTY + 250), (col(8), BOTY - 10)]  # a bow
SQUARE = [(col(8.5), TOPY), (col(4), TOPY), (col(4), BOTY), (col(8.5), BOTY)]  # a post with long arms
CURLY = [(col(7.5), TOPY), (col(5), TOPY - 60), (col(5), MIDY + 90), (col(3), MIDY), (col(5), MIDY - 90), (col(5), BOTY + 60), (col(7.5), BOTY)]


@glyph("(")
def _(p):
    p.ts(*PAREN, w=PN * 0.7)


@glyph(")")
def _(p):
    p.ts(*mirror(PAREN), w=PN * 0.7)


@glyph("[")
def _(p):
    p.ts(*SQUARE, w=PN)


@glyph("]")
def _(p):
    p.ts(*mirror(SQUARE), w=PN)


@glyph("{")
def _(p):
    p.ts(*CURLY, w=PN)


@glyph("}")
def _(p):
    p.ts(*mirror(CURLY), w=PN)


@glyph("#")
def _(p):
    # still a hash, full size; each of its eight ends is drawn out to a point
    for x in (215, 385):
        p.ts((x + 22, CT - 90), (x - 22, YB + 90), w=0.62, t=40)
        p.tb((x + 22, CT - 90), (x + 40, CT + 60), w=0.62, t=40)
        p.tb((x - 22, YB + 90), (x - 40, YB - 60), w=0.62, t=40)
    for y in (480, 250):
        p.ts((150, y), (450, y), w=0.62)
        p.tb((150, y), (30, y), w=0.62)
        p.tb((450, y), (570, y), w=0.62)


@glyph("$")
def _(p):
    _S(p, 0.8)
    p.ts((300, CT + 110), (300, YB - 110), w=0.32, t=30)


@glyph("%")
def _(p):
    p.ts((160, CT), (100, CT - 110), (170, CT - 200), (230, CT - 90), w=0.45, close=True)
    p.ts((430, 230), (370, 120), (440, 30), (500, 140), w=0.45, close=True)
    p.ts((480, CT), (120, YB), w=0.45, t=36)


@glyph("&")
def _(p):
    p.ts((480, YB), (170, CT - 180), (170, CT - 60), (260, CT), (350, CT - 60), (350, CT - 180), (130, 190), (130, YB + 62), (210, YB), (340, YB), (480, 240), w=0.8)
    p.ts((420, 250), (540, 290), w=0.5, t=30)  # its last stroke is crossed, as a seal's strokes are


@glyph("@")
def _(p):
    # the ordinary at-sign: the eye belongs to the zero alone, or the two are mistaken for each other
    p.ts((440, 130), (390, YB), (210, YB), (L, YB + 62), (L, CT - 70), (210, CT), (390, CT), (R, CT - 70), (R, 210), (380, 210), w=PN)
    p.ts((380, 210), (380, 480), (250, 480), (250, 210), (380, 210), w=0.5)


# ------------------------------------------------------------------ beyond ASCII
# Symbols a shell prompt and everyday text actually use, so they do not fall
# back to another font and break the texture.
ARROW_HEAD = [(340, MIDY + 190), (530, MIDY), (340, MIDY - 190)]


@glyph("→")  # rightwards arrow
def _(p):
    p.ts((60, MIDY), (500, MIDY), w=0.9)
    p.ts(*ARROW_HEAD, w=0.9, t=46)


@glyph("←")  # leftwards arrow
def _(p):
    p.ts((100, MIDY), (540, MIDY), w=0.9)
    p.ts(*mirror(ARROW_HEAD), w=0.9, t=46)


@glyph("↑")  # upwards arrow
def _(p):
    p.ts((300, MIDY - 260), (300, MIDY + 250), w=0.9)
    p.ts((130, MIDY + 80), (300, MIDY + 280), (470, MIDY + 80), w=0.9, t=46)


@glyph("↓")  # downwards arrow
def _(p):
    p.ts((300, MIDY + 260), (300, MIDY - 250), w=0.9)
    p.ts((130, MIDY - 80), (300, MIDY - 280), (470, MIDY - 80), w=0.9, t=46)


@glyph("⇒")  # rightwards double arrow
def _(p):
    p.ts((80, MIDY + 70), (440, MIDY + 70), w=0.5)
    p.ts((80, MIDY - 70), (440, MIDY - 70), w=0.5)
    p.ts((350, MIDY + 190), (540, MIDY), (350, MIDY - 190), w=0.6, t=36)


@glyph("➜➤❯")  # the heavy arrows shell prompts use: drawn as a blade
def _(p):
    p.tb((440, MIDY), (60, MIDY + 6), w=1.5)
    p.ts((300, MIDY + 200), (540, MIDY), (300, MIDY - 200), w=1.0, t=40)


@glyph("✗✘")  # ballot x
def _(p):
    p.ts((140, MIDY + 190), (460, MIDY - 190), w=0.95)
    p.ts((140, MIDY - 190), (460, MIDY + 190), w=0.7, t=44)


@glyph("✓✔")  # check mark
def _(p):
    p.ts((110, MIDY + 10), (240, MIDY - 180), (500, MIDY + 230), w=0.85, t=44)


@glyph("•·")  # bullet, middle dot
def _(p):
    p.ts((M - 34, MIDY + 38), (M + 34, MIDY - 38), w=1.4)


@glyph("…")  # ellipsis
def _(p):
    for x in (90, 300, 510):
        p.ts((x - 12, YB + 14), (x + 12, YB - 14), w=0.8)


@glyph("–")  # en dash
def _(p):
    p.ts((70, MIDY), (530, MIDY), w=0.66)


@glyph("—")  # em dash: runs edge to edge, so a row of them joins
def _(p):
    p.ts((-40, MIDY), (640, MIDY), w=0.6)


@glyph("’")  # right single quote, apostrophe
def _(p):
    p.tb((310, AT + 10), (270, AT - 200), w=0.8)


@glyph("‘")  # left single quote
def _(p):
    p.tb((290, AT - 190), (330, AT + 20), w=0.8)


@glyph("”")
def _(p):
    p.tb((220, AT + 10), (180, AT - 200), w=0.8)
    p.tb((400, AT + 10), (360, AT - 200), w=0.8)


@glyph("“")
def _(p):
    p.tb((200, AT - 190), (240, AT + 20), w=0.8)
    p.tb((380, AT - 190), (420, AT + 20), w=0.8)


@glyph("«")  # left guillemet
def _(p):
    for dx in (-110, 110):
        p.ts((400 + dx, MIDY + 170), (220 + dx, MIDY), (400 + dx, MIDY - 170), w=0.6, t=36)


@glyph("»")
def _(p):
    for dx in (-110, 110):
        p.ts(*mirror([(400 + dx, MIDY + 170), (220 + dx, MIDY), (400 + dx, MIDY - 170)]), w=0.6, t=36)


@glyph("×")  # multiplication sign
def _(p):
    p.ts((170, MIDY + 140), (430, MIDY - 140), w=0.7)
    p.ts((170, MIDY - 140), (430, MIDY + 140), w=0.6, t=40)


@glyph("÷")  # division sign
def _(p):
    p.ts((130, MIDY), (470, MIDY), w=0.7)
    dot(p, y=MIDY + 150)
    dot(p, y=MIDY - 150)


@glyph("±")  # plus-minus
def _(p):
    p.ts((130, MIDY + 60), (470, MIDY + 60), w=0.7)
    p.ts((300, MIDY + 210), (300, MIDY - 80), w=0.7)
    p.ts((130, MIDY - 170), (470, MIDY - 170), w=0.6)


@glyph("°")  # degree
def _(p):
    p.ts((300, CT + 20), (220, CT - 70), (300, CT - 160), (380, CT - 70), w=0.45, close=True)


@glyph("≠")  # not equal
def _(p):
    p.ts((130, MIDY + 76), (470, MIDY + 76), w=0.6)
    p.ts((130, MIDY - 76), (470, MIDY - 76), w=0.6)
    p.ts((400, MIDY + 210), (200, MIDY - 210), w=0.5, t=36)


@glyph("≤")  # less-than or equal
def _(p):
    p.ts((450, MIDY + 230), (140, MIDY + 60), (450, MIDY - 110), w=0.66, t=36)
    p.ts((140, MIDY - 200), (450, MIDY - 200), w=0.6)


@glyph("≥")  # greater-than or equal
def _(p):
    p.ts(*mirror([(450, MIDY + 230), (140, MIDY + 60), (450, MIDY - 110)]), w=0.66, t=36)
    p.ts((150, MIDY - 200), (460, MIDY - 200), w=0.6)


@glyph("λ")  # lambda
def _(p):
    p.ts((150, AT), (230, AT - 30), (462, YB + D), (462 + K, YB))
    p.ts((300, YT - 60), (128, YB), w=0.8, t=40)


@glyph("ł")  # l with stroke
def _(p):
    TEXTURA["l"](p)
    p.ts((180, 330), (430, 470), w=0.5, t=36)


@glyph("Ł")
def _(p):
    TEXTURA["L"](p)
    p.ts((40, 300), (290, 440), w=0.5, t=36)


@glyph("Λ")  # capital lambda, so the small one has its partner
def _(p):
    p.ts((L - 20, YB), (L, YB + 50), (300, CT), (R, YB + 50), (R + 20, YB))
    up(p, (300, CT), ln=CUP)
    down(p, (L - 20, YB))
    down(p, (R + 20, YB))


@glyph("ø")  # o with stroke
def _(p):
    TEXTURA["o"](p)
    p.ts((470, YT + 30), (130, YB - 30), w=0.4, t=58)


@glyph("Ø")
def _(p):
    TEXTURA["O"](p)
    p.ts((480, CT + 30), (120, YB - 30), w=0.4, t=58)


@glyph("ß")  # sharp s
def _(p):
    p.ts((L - K, YB), (L, YB + D), (L, AT - 90), (230, AT), (370, AT), (440, AT - 80), (440, 470), (330, 400))
    p.ts((330, 400), (R, 320), (R, YB + 62), (390, YB), (250, YB), (210, YB + 50))
    up(p, (300, AT), ln=UP * 0.6)


# ---- accented letters: the base letter plus a mark. Metal umlauts included.
def m_dieresis(p, y, x=M):
    p.ts((x - 108, y + 22), (x - 68, y - 22), w=1.05)
    p.ts((x + 68, y + 22), (x + 108, y - 22), w=1.05)


def m_acute(p, y, x=M):
    p.tb((x - 50, y - 40), (x + 90, y + 130), w=0.9)


def m_grave(p, y, x=M):
    p.tb((x + 50, y - 40), (x - 90, y + 130), w=0.9)


def m_circumflex(p, y, x=M):
    p.ts((x - 120, y - 30), (x, y + 90), (x + 120, y - 30), w=0.5, t=58)


def m_caron(p, y, x=M):
    p.ts((x - 120, y + 90), (x, y - 30), (x + 120, y + 90), w=0.5, t=58)


def m_tilde(p, y, x=M):
    p.ts((x - 150, y - 10), (x - 60, y + 60), (x + 60, y - 10), (x + 150, y + 60), w=0.5)


def m_ring(p, y, x=M):
    p.ts((x, y + 110), (x - 70, y + 30), (x, y - 50), (x + 70, y + 30), w=0.42, close=True)


def m_cedilla(p, y, x=M):
    p.tb((x + 20, YB - 20), (x - 70, YB - 220), w=0.8)


def accented(ch, base, mark):
    below = mark is m_cedilla
    body = "ı" if base == "i" else base
    y = (X if base.islower() else CAPH) + 110

    @glyph(ch)
    def _(p):
        p.quiet = not below
        TEXTURA[body](p)
        mark(p, 0 if below else y)


for _marks, _fn in (
    ("äëïöüÿÄËÏÖÜ", m_dieresis),
    ("áéíóúýÁÉÍÓÚÝ", m_acute),
    ("àèìòùÀÈÌÒÙ", m_grave),
    ("âêîôûÂÊÎÔÛ", m_circumflex),
    ("ãñõÃÑÕ", m_tilde),
    ("åÅ", m_ring),
    ("çÇ", m_cedilla),
    ("šžčŠŽČ", m_caron),
):
    import unicodedata

    for _ch in _marks:
        accented(_ch, unicodedata.normalize("NFD", _ch)[0], _fn)


# ------------------------------------------------------------------ iconography
# Marks that cost code nothing, because code does not use them.
def inverted_cross(p, bars=(250,)):
    p.ts((300, CT + 60), (300, YB - 40), w=0.9)
    for y in bars:
        p.ts((150, y), (450, y), w=0.9)


@glyph("\u2020\u271d\u271e\u271f\u2e38")  # dagger and the Latin crosses: the bar sits low
def _(p):
    inverted_cross(p)


@glyph("\u2021")  # double dagger
def _(p):
    inverted_cross(p, bars=(330, 170))


@glyph("\u26e7\u26e5\u2606\u2605")  # the pentagram, and the plain stars: one point down
def _(p):
    pentagram(p, 300, MIDY + 80, 300)


# ------------------------------------------------------------------ ligatures
# Operator pairs drawn as one mark across their cells. The text still occupies
# the same cells, so columns never move. They live in the `liga` feature, which
# can be turned off without losing the alternates in `calt`.
CELLW = CELL * XPP  # one cell, in drawing units
LIGATURES = {}


def ligature(seq):
    def deco(fn):
        LIGATURES[seq] = fn
        return fn

    return deco


def span(n):
    """Left and right edge, in drawing units, of the n cells a ligature covers.
    The glyph sits in the last cell and reaches back over the others."""
    return col(0) - (n - 1) * CELLW, col(CELL)


def flip(pts, x0, x1):
    return [(x0 + x1 - x, y) for x, y in pts]


def bars(p, x0, x1, ys, inset=80, w=0.85):
    for y in ys:
        p.ts((x0 + inset, MIDY + y), (x1 - inset, MIDY + y), w=w)


def slash_through(p, x0, x1):
    mid = (x0 + x1) / 2
    p.ts((mid + 190, MIDY + 300), (mid - 190, MIDY - 300), w=0.7, t=44)


ARROW = lambda x0, x1: ([(x0 + 90, MIDY), (x1 - 150, MIDY)], [(x1 - 280, MIDY + 200), (x1 - 70, MIDY), (x1 - 280, MIDY - 200)])


@ligature("->")
def _(p, x0, x1):
    shaft, head = ARROW(x0, x1)
    p.ts(*shaft, w=0.9)
    p.ts(*head, w=0.9, t=46)


@ligature("<-")
def _(p, x0, x1):
    shaft, head = ARROW(x0, x1)
    p.ts(*flip(shaft, x0, x1), w=0.9)
    p.ts(*flip(head, x0, x1), w=0.9, t=46)


@ligature("=>")
def _(p, x0, x1):
    for y in (84, -84):
        p.ts((x0 + 90, MIDY + y), (x1 - 250, MIDY + y), w=0.85)
    p.ts((x1 - 310, MIDY + 250), (x1 - 70, MIDY), (x1 - 310, MIDY - 250), w=0.9, t=46)


@ligature("==")
def _(p, x0, x1):
    bars(p, x0, x1, (84, -84))


@ligature("===")
def _(p, x0, x1):
    bars(p, x0, x1, (150, 0, -150))


@ligature("!=")
def _(p, x0, x1):
    bars(p, x0, x1, (84, -84))
    slash_through(p, x0, x1)


@ligature("!==")
def _(p, x0, x1):
    bars(p, x0, x1, (150, 0, -150))
    slash_through(p, x0, x1)


LESS_EQ = lambda x0, x1: ([(x1 - 110, MIDY + 270), (x0 + 110, MIDY + 80), (x1 - 110, MIDY - 110)], [(x0 + 110, MIDY - 240), (x1 - 110, MIDY - 240)])


@ligature("<=")
def _(p, x0, x1):
    wedge, bar = LESS_EQ(x0, x1)
    p.ts(*wedge, w=0.9, t=46)
    p.ts(*bar, w=0.85)


@ligature(">=")
def _(p, x0, x1):
    wedge, bar = LESS_EQ(x0, x1)
    p.ts(*flip(wedge, x0, x1), w=0.9, t=46)
    p.ts(*flip(bar, x0, x1), w=0.85)


@ligature("::")
def _(p, x0, x1):
    mid = (x0 + x1) / 2
    for x in (mid - 170, mid + 170):
        dot(p, x)
        dot(p, x, y=400)


@ligature("++")
def _(p, x0, x1):
    bars(p, x0, x1, (0,), w=0.95)
    for x in (x0 + col(5) - col(0), x1 - (col(CELL) - col(5))):
        p.ts((x, MIDY + 190), (x, MIDY - 190), w=0.95)


@ligature("--")
def _(p, x0, x1):
    bars(p, x0, x1, (0,), inset=70, w=0.95)


@ligature("|>")
def _(p, x0, x1):
    x = x0 + col(5) - col(0)
    p.ts((x, TOPY - 60), (x, BOTY + 60), w=PN)
    p.ts((x + 230, MIDY + 210), (x1 - 80, MIDY), (x + 230, MIDY - 210), w=0.9, t=46)


AMP = [(480, YB), (170, CT - 180), (170, CT - 60), (260, CT), (350, CT - 60), (350, CT - 180), (130, 190), (130, YB + 62), (210, YB), (340, YB), (480, 240)]


@ligature("&&")
def _(p, x0, x1):
    for dx in (x0 - col(0) + 130, x1 - col(CELL) - 130):  # two ampersands drawn close enough to lock together
        p.ts(*[(x + dx, y) for x, y in AMP], w=0.8)


@ligature("||")
def _(p, x0, x1):
    mid = (x0 + x1) / 2
    for x in (mid - 160, mid + 160):
        p.ts((x, TOPY - 60), (x, BOTY + 60), w=PN)


CHEVRONS = lambda x0: [[(x0 + 170 + dx, MIDY + 220), (x0 + 520 + dx, MIDY), (x0 + 170 + dx, MIDY - 220)] for dx in (0, 500)]


@ligature(">>")
def _(p, x0, x1):
    for pts in CHEVRONS(x0):
        p.ts(*pts, w=0.9, t=46)


@ligature("<<")
def _(p, x0, x1):
    for pts in CHEVRONS(x0):
        p.ts(*flip(pts, x0, x1), w=0.9, t=46)


@ligature("//")
def _(p, x0, x1):
    mid = (x0 + x1) / 2
    for c in (mid - 240, mid + 240):
        p.ts((c + 190, AT), (c - 190, DB), w=PN, t=40)


@ligature("---")
def _(p, x0, x1):
    p.ts((x0 + 190, MIDY), (x1 - 190, MIDY), w=0.95)  # a rule, drawn out to a point at each end
    p.tb((x0 + 190, MIDY), (x0 + 40, MIDY), w=0.95)
    p.tb((x1 - 190, MIDY), (x1 - 40, MIDY), w=0.95)


# ------------------------------------------------------------------ interface marks
# What a terminal agent's interface prints around the text: bullets, selection
# marks, pointers, checkboxes, extra arrows. Drawn with the same pen, so they
# stop falling back to a system font.
def ngon(cx, cy, rx, ry, n=8, turn=22.5):
    return [(cx + rx * math.cos(math.radians(turn + 360 * k / n)), cy + ry * math.sin(math.radians(turn + 360 * k / n))) for k in range(n)]


DOT_C = (300, MIDY + 40)


@glyph("●⏺⬤")  # black circle, record
def _(p):
    p.tpoly(*ngon(*DOT_C, 250, 190))


@glyph("○◯")  # white circle
def _(p):
    p.ts(*ngon(*DOT_C, 230, 180), w=0.5, close=True)


@glyph("◉◎")  # fisheye: the selected one
def _(p):
    p.ts(*ngon(*DOT_C, 230, 180), w=0.5, close=True)
    p.tpoly(*ngon(*DOT_C, 110, 84))


DIAMOND = [(300, MIDY + 260), (520, MIDY + 40), (300, MIDY - 180), (80, MIDY + 40)]


@glyph("◆")
def _(p):
    p.tpoly(*DIAMOND)


@glyph("◇")
def _(p):
    p.ts(*DIAMOND, w=0.5, close=True)


def square(r=190, cy=MIDY + 40, rx=None):
    rx = rx or r * 1.25
    return [(300 - rx, cy + r), (300 + rx, cy + r), (300 + rx, cy - r), (300 - rx, cy - r)]


@glyph("■")
def _(p):
    p.tpoly(*square())


@glyph("□☐")  # white square, ballot box
def _(p):
    p.ts(*square(), w=0.5, close=True)


@glyph("▪")
def _(p):
    p.tpoly(*square(100))


@glyph("▫")
def _(p):
    p.ts(*square(110), w=0.4, close=True)


@glyph("☑")  # ballot box with check
def _(p):
    p.ts(*square(), w=0.5, close=True)
    p.ts((170, MIDY + 40), (270, MIDY - 70), (440, MIDY + 170), w=0.6, t=40)


@glyph("☒")  # ballot box with x
def _(p):
    p.ts(*square(), w=0.5, close=True)
    p.ts((160, MIDY + 170), (440, MIDY - 90), w=0.5, t=36)
    p.ts((160, MIDY - 90), (440, MIDY + 170), w=0.5, t=36)


TRI_UP = [(300, MIDY + 260), (540, MIDY - 150), (60, MIDY - 150)]
TRI_RIGHT = [(110, MIDY + 260), (540, MIDY + 40), (110, MIDY - 180)]


def flip_v(pts, cy=MIDY + 55):
    return [(x, 2 * cy - y) for x, y in pts]


for _chars, _pts, _fill in (
    ("▲▴", TRI_UP, True), ("▼▾", flip_v(TRI_UP), True), ("▶►▸", TRI_RIGHT, True), ("◀◄◂", mirror(TRI_RIGHT), True),
    ("△▵", TRI_UP, False), ("▽▿", flip_v(TRI_UP), False), ("▷▹", TRI_RIGHT, False), ("◁◃", mirror(TRI_RIGHT), False),
):  # fmt: skip
    def _triangle(p, pts=_pts, fill=_fill):
        p.tpoly(*pts) if fill else p.ts(*pts, w=0.5, close=True)

    glyph(_chars)(_triangle)


ANGLE = [(200, MIDY + 200), (420, MIDY), (200, MIDY - 200)]


@glyph("›")  # single right angle quote: pi's pointer
def _(p):
    p.ts(*ANGLE, w=0.9, t=46)


@glyph("‹")
def _(p):
    p.ts(*mirror(ANGLE), w=0.9, t=46)


@glyph("❮")  # heavy left angle: the prompt blade, turned round
def _(p):
    p.tb((160, MIDY), (540, MIDY + 6), w=1.5)
    p.ts(*mirror([(300, MIDY + 200), (540, MIDY), (300, MIDY - 200)]), w=1.0, t=40)


@glyph("↔")  # left right arrow
def _(p):
    p.ts((90, MIDY), (510, MIDY), w=0.8)
    p.ts((400, MIDY + 150), (540, MIDY), (400, MIDY - 150), w=0.8, t=44)
    p.ts(*mirror([(400, MIDY + 150), (540, MIDY), (400, MIDY - 150)]), w=0.8, t=44)


@glyph("↕")  # up down arrow
def _(p):
    p.ts((300, MIDY - 240), (300, MIDY + 260), w=0.8)
    p.ts((170, MIDY + 130), (300, MIDY + 290), (430, MIDY + 130), w=0.8, t=44)
    p.ts((170, MIDY - 110), (300, MIDY - 270), (430, MIDY - 110), w=0.8, t=44)


DOUBLE_ARROW = [[(80, MIDY + 70), (440, MIDY + 70)], [(80, MIDY - 70), (440, MIDY - 70)], [(350, MIDY + 190), (540, MIDY), (350, MIDY - 190)]]


@glyph("⇐")  # leftwards double arrow
def _(p):
    for pts, kw in zip(DOUBLE_ARROW, (dict(w=0.5), dict(w=0.5), dict(w=0.6, t=36))):
        p.ts(*mirror(pts), **kw)


@glyph("⇔")  # left right double arrow
def _(p):
    p.ts((160, MIDY + 70), (440, MIDY + 70), w=0.5)
    p.ts((160, MIDY - 70), (440, MIDY - 70), w=0.5)
    p.ts(*DOUBLE_ARROW[2], w=0.6, t=36)
    p.ts(*mirror(DOUBLE_ARROW[2]), w=0.6, t=36)


@glyph("↵⏎↩")  # return
def _(p):
    p.ts((470, MIDY + 250), (470, MIDY), (120, MIDY), w=0.8)
    p.ts((240, MIDY + 140), (90, MIDY), (240, MIDY - 140), w=0.8, t=44)


@glyph("⇧")  # shift: the up arrow
def _(p):
    TEXTURA["↑"](p)


@glyph("⌃")  # control: a caret
def _(p):
    TEXTURA["^"](p)


@glyph("‖∥")  # double vertical line
def _(p):
    for x in (220, 380):
        p.ts((x, TOPY - 60), (x, BOTY + 60), w=PN * 0.8)


@glyph("≈")  # almost equal
def _(p):
    for dy in (80, -80):
        p.ts((100, MIDY - 40 + dy), (220, MIDY + 50 + dy), (380, MIDY - 50 + dy), (500, MIDY + 40 + dy), w=PN * 0.8)


@glyph("≡")  # identical to
def _(p):
    for dy in (150, 0, -150):
        p.ts((110, MIDY + dy), (490, MIDY + dy), w=0.8)


@glyph("¬")  # not sign
def _(p):
    p.ts((100, MIDY + 60), (480, MIDY + 60), (480, MIDY - 110), w=0.85)


@glyph("√")  # square root
def _(p):
    p.ts((70, MIDY), (150, MIDY + 20), (240, YB), (350, CT), (560, CT), w=0.7, t=40)


@glyph("⚠")  # warning
def _(p):
    p.ts((300, CT - 20), (560, YB + 20), (40, YB + 20), w=0.5, close=True)
    p.tb((300, 430), (300, 220), w=0.7)
    p.ts((300 - 14, 150), (300 + 14, 118), w=0.6)


@glyph("⎿")  # the corner that hangs a result under a call
def _(p):
    p.ts((210, TOPY - 220), (210, MIDY - 60), (540, MIDY - 60), w=0.6)


@glyph("✻✽✶✳✢✦✧✱✲✴✵")  # the star marks agents use: all the pentagram
def _(p):
    pentagram(p, 300, MIDY + 50, 250, w=0.4, t=32)


# ------------------------------------------------------------------ box drawing, blocks, braille
# These must meet their neighbours exactly, so they are plain rectangles on the
# pixel grid, not pen strokes. Ghostty draws its own; other terminals do not.
ADV = round(CELL * PX)  # the cell: 12 x 33 px
LINE_TOP, LINE_BOTTOM = 961, -307
CX, CY = 6 * PX, 9 * PX  # where lines cross: whole pixels, mid-cell
HALF = {1: PX, 2: 2 * PX}  # half-thickness of a light and a heavy line


def _arm(p, direction, weight):
    if not weight:
        return
    if weight == 3:  # double: two one-pixel lines, a pixel and a half either side
        for off in (-1.5 * PX, 1.5 * PX):
            _bar(p, direction, PX / 2, off, 2 * PX)
    else:
        _bar(p, direction, HALF[weight], 0.0, HALF[weight])


def _bar(p, direction, h, off, past):
    """One line from the cell edge to just past the crossing point."""
    if direction == "up":
        p.rect(CX + off - h, CY - past, CX + off + h, LINE_TOP)
    elif direction == "down":
        p.rect(CX + off - h, LINE_BOTTOM, CX + off + h, CY + past)
    elif direction == "left":
        p.rect(0, CY + off - h, CX + past, CY + off + h)
    else:
        p.rect(CX - past, CY + off - h, ADV, CY + off + h)


BOX = {  # up, right, down, left: 1 light, 2 heavy, 3 double
    "─": (0, 1, 0, 1), "━": (0, 2, 0, 2), "│": (1, 0, 1, 0), "┃": (2, 0, 2, 0),
    "┌": (0, 1, 1, 0), "┐": (0, 0, 1, 1), "└": (1, 1, 0, 0), "┘": (1, 0, 0, 1),
    "╭": (0, 1, 1, 0), "╮": (0, 0, 1, 1), "╰": (1, 1, 0, 0), "╯": (1, 0, 0, 1),
    "├": (1, 1, 1, 0), "┤": (1, 0, 1, 1), "┬": (0, 1, 1, 1), "┴": (1, 1, 0, 1), "┼": (1, 1, 1, 1),
    "┏": (0, 2, 2, 0), "┓": (0, 0, 2, 2), "┗": (2, 2, 0, 0), "┛": (2, 0, 0, 2),
    "┣": (2, 2, 2, 0), "┫": (2, 0, 2, 2), "┳": (0, 2, 2, 2), "┻": (2, 2, 0, 2), "╋": (2, 2, 2, 2),
    "═": (0, 3, 0, 3), "║": (3, 0, 3, 0), "╔": (0, 3, 3, 0), "╗": (0, 0, 3, 3), "╚": (3, 3, 0, 0), "╝": (3, 0, 0, 3),
    "╠": (3, 3, 3, 0), "╣": (3, 0, 3, 3), "╦": (0, 3, 3, 3), "╩": (3, 3, 0, 3), "╬": (3, 3, 3, 3),
    "╤": (0, 3, 1, 3), "╧": (1, 3, 0, 3), "╟": (3, 1, 3, 0), "╢": (3, 0, 3, 1), "╪": (1, 3, 1, 3), "╫": (3, 1, 3, 1),
    "╿": (2, 0, 1, 0), "╴": (0, 0, 0, 1), "╵": (1, 0, 0, 0), "╶": (0, 1, 0, 0), "╷": (0, 0, 1, 0),
}  # fmt: skip
def _chamfer(sx, sy):
    """A rounded corner, drawn the way this font draws every curve: broken.
    sx is +1 for an arm to the right, sy is +1 for an arm upward."""

    def draw(p):
        c = 3 * PX
        if sx > 0:
            p.rect(CX + c, CY - PX, ADV, CY + PX)
        else:
            p.rect(0, CY - PX, CX - c, CY + PX)
        if sy > 0:
            p.rect(CX - PX, CY + c, CX + PX, LINE_TOP)
        else:
            p.rect(CX - PX, LINE_BOTTOM, CX + PX, CY - c)
        p.polys.append([(CX - PX, CY + sy * c), (CX + PX, CY + sy * c), (CX + sx * c, CY + PX), (CX + sx * c, CY - PX)] if sx * sy > 0 else [(CX + PX, CY + sy * c), (CX - PX, CY + sy * c), (CX + sx * c, CY + PX), (CX + sx * c, CY - PX)])

    return draw


for _ch, _arms in BOX.items():
    def _box(p, arms=_arms):
        for direction, weight in zip(("up", "right", "down", "left"), arms):
            _arm(p, direction, weight)

    TEXTURA[_ch] = _box


def _dashed_h(p):
    for a, b in ((0.5, 5), (6.5, 11.5)):
        p.rect(a * PX, CY - PX, b * PX, CY + PX)


def _dashed_v(p):
    total = LINE_TOP - LINE_BOTTOM
    for a, b in ((0.04, 0.46), (0.54, 0.96)):
        p.rect(CX - PX, LINE_BOTTOM + a * total, CX + PX, LINE_BOTTOM + b * total)


for _ch, _sx, _sy in (("╭", 1, -1), ("╮", -1, -1), ("╰", 1, 1), ("╯", -1, 1)):
    TEXTURA[_ch] = _chamfer(_sx, _sy)
TEXTURA["╌"] = TEXTURA["┄"] = _dashed_h
TEXTURA["╎"] = TEXTURA["┆"] = _dashed_v


def _block(x0, y0, x1, y1):
    """A block element: fractions of the cell, from its bottom-left corner."""
    h = LINE_TOP - LINE_BOTTOM

    def draw(p):
        p.rect(x0 * ADV, LINE_BOTTOM + y0 * h, x1 * ADV, LINE_BOTTOM + y1 * h)

    return draw


TEXTURA["█"] = _block(0, 0, 1, 1)
TEXTURA["▀"] = _block(0, 0.5, 1, 1)
TEXTURA["▄"] = _block(0, 0, 1, 0.5)
TEXTURA["▌"] = _block(0, 0, 0.5, 1)
TEXTURA["▐"] = _block(0.5, 0, 1, 1)
for _i, _ch in enumerate("▏▎▍▌▋▊▉"):
    TEXTURA[_ch] = _block(0, 0, (_i + 1) / 8, 1)
for _i, _ch in enumerate("▁▂▃▄▅▆▇"):
    TEXTURA[_ch] = _block(0, 0, 1, (_i + 1) / 8)


def _shade(keep):
    """A shade: single pixels, kept where keep(column, row) says so."""

    def draw(p):
        for cx in range(CELL):
            for cy in range(33):
                if keep(cx, cy):
                    p.rect(cx * PX, LINE_BOTTOM + cy * PX, (cx + 1) * PX, LINE_BOTTOM + (cy + 1) * PX)

    return draw


TEXTURA["░"] = _shade(lambda x, y: x % 2 == 0 and y % 2 == 0)
TEXTURA["▒"] = _shade(lambda x, y: (x + y) % 2 == 0)
TEXTURA["▓"] = _shade(lambda x, y: not (x % 2 == 1 and y % 2 == 1))

# Braille: pi's spinner. Two columns of four dots; each dot a lozenge, as every
# dot in this font is.
BRAILLE_X = (3.5 * PX, 8.5 * PX)
BRAILLE_Y = (19 * PX, 13.5 * PX, 8 * PX, 2.5 * PX)
BRAILLE_BITS = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (0, 3), (1, 3))


def _braille(code):
    def draw(p):
        for bit, (c, r) in enumerate(BRAILLE_BITS):
            if code >> bit & 1:
                x, y, d = BRAILLE_X[c], BRAILLE_Y[r], 1.5 * PX
                p.polys.append([(x, y + d), (x + d, y), (x, y - d), (x - d, y)])

    return draw


for _code in range(1, 256):
    TEXTURA[chr(0x2800 + _code)] = _braille(_code)
TEXTURA[chr(0x2800)] = lambda p: None  # the blank pattern
