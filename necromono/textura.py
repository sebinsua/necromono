"""NecroMono's letters: constructed textura.

Every letter is assembled from the same few parts, drawn with a broad nib held
at a fixed angle: a straight stem with a diamond head and foot, six-sided
broken bowls, hairline joins. The black metal is in the rigidity and in what
grows off the parts: thin straight lines rising from free stem tops, a drip
falling from each foot, forked ascenders, descenders that end in daggers.

Drawn on its own grid (600 wide, x-height 540) and mapped to the font's
metrics by the pen, so the letters come out narrower and taller than drawn.
"""
import math

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
_r = math.radians(NIB_ANGLE)
HY = (NIB_W * math.sin(_r) + NIB_T * math.cos(_r)) / 2
YT, YB = X - HY, HY  # a stroke at YT has its top exactly on the x-height
AT, DB = ASC - HY, DESC + HY
L, R, M = col(2), col(8), col(5)
K, D = 44, 34  # run and drop of a diamond: drawn wide, so it is still a diamond once squeezed
UP, DOWN = 250, 95  # needle and drip lengths; the upward lines lead

# the broken bowl shared by o, b, d, p, q, c, e, g
TL, TP, TR = (L, YT - 60), (390, YT), (R, YT - 60)
BR, BP, BL = (R, YB + 60), (210, YB), (L, YB + 60)

TEXTURA = {}


def glyph(chars):
    def deco(fn):
        for ch in chars:
            TEXTURA[ch] = fn
        return fn

    return deco


# ---- zalgo
# Zalgo text is ordinary letters with small marks piled above and below them
# until the line looks possessed. Here the marks are part of the letter: where
# a line would rise from a stroke, sometimes a column of them climbs instead.
# Each is two or three pixels tall at terminal size, and the column wanders.
def z_dot(p, x, y):
    p.ts((x - 12, y + 44), (x + 12, y + 16), w=0.6)


def z_tick(p, x, y, s=1):
    p.tb((x - s * 22, y + 4), (x + s * 26, y + 78), w=0.42)


def z_chevron(p, x, y, s=1):
    lo, hi = (y + 8, y + 62) if s > 0 else (y + 62, y + 8)
    p.ts((x - 46, lo), (x, hi), (x + 46, lo), w=0.3, t=14)


def z_bar(p, x, y):
    p.ts((x - 44, y + 30), (x + 44, y + 30), w=0.32, t=14)


def z_cross(p, x, y):
    """An inverted cross: the bar sits low."""
    p.ts((x, y + 96), (x, y + 4), w=0.46, t=12)
    p.ts((x - 36, y + 30), (x + 36, y + 30), w=0.3, t=14)


def z_x(p, x, y):
    p.ts((x - 30, y + 66), (x + 30, y + 10), w=0.3, t=14)
    p.ts((x - 30, y + 10), (x + 30, y + 66), w=0.3, t=14)


def zalgo(p, pt, r, direction=1, count=3):
    """A wandering column of small marks leaving the stroke at pt."""
    marks = [z_dot, z_tick, lambda p, x, y: z_tick(p, x, y, -1), z_chevron, lambda p, x, y: z_chevron(p, x, y, -1), z_bar, z_cross, z_x]
    x = pt[0] + r.uniform(-14, 14)
    y = pt[1] + direction * (HY + 34)
    for _ in range(count):
        mark = r.choice(marks)
        mark(p, x, y if direction > 0 else y - 80)
        y += direction * r.uniform(88, 118)
        x += r.uniform(-30, 30)


def up(p, pt, ln=UP):
    """What rises from a stroke: usually thin straight lines, uneven with each
    other; sometimes a column of zalgo marks instead. The count per letter is
    fixed by the letter, so the texture never thickens into noise."""
    if getattr(p, "quiet", False):  # an accent is coming: leave the space above the letter to it
        return
    r = p.frng
    g = p.cut.grow
    p.tops.append(pt)
    if r.random() < 0.34 + (g - 1) * 0.3:
        zalgo(p, pt, r, count=r.randint(2, 3) + (2 if g > 1.3 else 0))
        return
    p.needle((pt[0], pt[1] + HY - 10), ln * r.uniform(1.2, 1.8) * (1 + (g - 1) * 0.5), w=38.0, jag=1.0)  # one pixel wide at the root
    if r.random() < 0.8 * g:
        p.needle((pt[0] + r.choice([-1, 1]) * r.uniform(30, 50), pt[1] + HY - 30), ln * r.uniform(0.5, 1.0) * g, w=30.0, jag=1.4)
    if g > 1.3:  # the overgrown styles: a third line, and it may lean hard
        p.needle((pt[0] + r.choice([-1, 1]) * r.uniform(50, 80), pt[1] + HY - 34), ln * r.uniform(0.7, 1.3), w=28.0, jag=2.2)


def finish(p):
    """A letter that starts or ends a word throws one long line outward, so
    every word is bracketed the way a logo is."""
    if not p.edge or not p.tops:
        return
    r = p.frng
    side = -1 if p.edge == "init" else 1
    pt = min(p.tops, key=lambda q: q[0] * side * -1)
    p.needle((pt[0] + side * 26, pt[1] + HY - 24), UP * r.uniform(1.7, 2.3), w=36.0, jag=1.0, lean=side * r.uniform(0.16, 0.3))


def down(p, pt, ln=DOWN):
    """What falls from a foot: a short drip, or now and then a zalgo mark or two."""
    r = p.frng
    if r.random() < 0.22 + (p.cut.grow - 1) * 0.3:
        zalgo(p, pt, r, direction=-1, count=r.randint(1, 2))
        return
    p.needle((pt[0], pt[1] - HY + 10), -ln)


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
    p.ts((160, YT - 62), TP, TR, (R, YB + D), (R + K, YB))
    p.ts((R, 322), (L, 238), BL, BP, (R, YB + 205))
    up(p, TP)
    down(p, (R + K, YB))


@glyph("b")
def _(p):
    fork(p, L)
    p.ts((L, AT - D), BL, BP, BR, TR, TP, TL)
    down(p, BP)


@glyph("c")
def _(p):
    p.ts((458, YT - 52), TP, TL, BL, BP)
    p.tb(BP, (492, YB + 128))
    up(p, TP)
    down(p, BP)


@glyph("d")
def _(p):
    fork(p, R)
    p.ts((R, AT - D), (R, YB + D), (R + K, YB))
    p.ts(TR, TP, TL, BL, BP, (R, YB + 205))
    down(p, (R + K, YB))


@glyph("e")
def _(p):
    p.ts((R, YT - 178), TR, TP, TL, BL, BP)
    p.tb(BP, (492, YB + 128))
    p.ts((R, YT - 178), (L, YT - 292))
    up(p, TP)
    down(p, BP)


@glyph("f")
def _(p):
    x = col(4)
    p.ts((470, AT - 58), (400, AT), (x, AT - 62), (x, YB + D), (x + K, YB))
    p.ts((112, YT), (440, YT), w=0.8)
    up(p, (400, AT), ln=UP * 0.7)
    down(p, (x + K, YB))


@glyph("g")
def _(p):
    p.ts(TL, TP, TR, (R, DB + 62), (220, DB), (142, DB + 56))
    p.ts(TL, BL, BP, (R, YB + 205))
    up(p, TP)
    down(p, (220, DB), ln=DOWN * 0.6)


@glyph("h")
def _(p):
    fork(p, L)
    p.ts((L, AT - D), (L, YB + D), (L + K, YB))
    p.ts((L, YT - 44), (408, YT), (R, YT - 62), (R, YB + 70))
    p.tb((R, YB + 70), (R - 74, -150))
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
    p.ts((L, 236), (452, YT - 6), w=0.64, t=46)
    p.ts((262, 340), (462, YB + D), (462 + K, YB))
    down(p, (L + K, YB))
    down(p, (462 + K, YB))


@glyph("l")
def _(p):
    p.ts((196, AT - 82), (272, AT), (M, AT - D), (M, YB + D), (M + K, YB))
    p.tb((272, AT), (272 - 58, AT + 88), w=0.64)
    p.ts((M, YB + 70), (M + 90, YB), (M + 200, YB + 30))  # l turns its foot out to the right
    p.tb((M + 200, YB + 30), (M + 250, YB + 120))
    up(p, (M - 10, AT), ln=UP * 0.7)
    down(p, (M + K, YB))


@glyph("m")
def _(p):
    w = 1.0
    a, b, c = col(2), col(6), col(10)  # three full stems with 2 px counters
    stem(p, a, w=w)
    p.ts((a, YT - 44), (b - 66, YT), (b, YT - 56), (b, YB + D), (b + K, YB), w=w)
    p.ts((b, YT - 44), (c - 66, YT), (c, YT - 56), (c, YB + D), (c + K, YB), w=w)
    down(p, (b + K, YB))
    down(p, (c + K, YB))


N_LEFT = [(L - K, YT), (L, YT - D), (L, YB + D), (L + K, YB)]
N_RIGHT = [(L, YT - 44), (408, YT), (R, YT - 62), (R, YB + D), (R + K, YB)]


@glyph("n")
def _(p):
    p.ts(*N_LEFT)
    p.ts(*N_RIGHT)
    up(p, N_LEFT[0])  # one needle: the stem under the arch grows none
    down(p, N_LEFT[-1])
    down(p, N_RIGHT[-1])


@glyph("u")
def _(p):
    a, b = rot(N_LEFT), rot(N_RIGHT)  # n turned half round: open at the top
    p.ts(*a)
    p.ts(*b)
    up(p, b[-1])  # two needles
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
    p.ts(TR, TP, TL, BL, BP, (R, YB + 205))
    up(p, TP)


@glyph("r")
def _(p):
    x = col(3)
    stem(p, x)
    p.ts((x, YT - 52), (410, YT), (478, YT - 62))
    p.tb((x + K, YB), (x + K + 104, YB + 62), w=0.6)


@glyph("s")
def _(p):
    p.ts((458, YT - 56), (388, YT), (140, YT - 66), (140, YT - 150), (460, YB + 150), (460, YB + 66), (212, YB), (142, YB + 56))
    up(p, (388, YT))
    down(p, (212, YB))


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
    p.ts((74, YT + 4), (112, YT - 20), (300, YB + 10))
    p.ts((496, YT), (270, -40))
    p.tb((270, -40), (170, DB - 50))
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
CTL, CTP, CTR = (L, CT - 70), (390, CT), (R, CT - 70)
CUP = UP * 0.55  # capitals are already tall; their needles are shorter


def cstem(p, x, grow_up=True, grow_down=True, w=1.0, foot=True, head=True, double=False):
    if double:  # a one-pixel hairline, one pixel clear of the stem: the doubled stroke of a blackletter capital
        hx = x + 2.5 * XPP
        p.ts((hx, CT - 96), (hx, YB + 78), w=0.46, t=12)
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
    cstem(p, L, double=True)
    p.ts((L, CT), (370, CT), (440, CT - 64), (440, 420), (360, 366))
    p.ts((L, 366), (380, 366), (R, 300), (R, YB + 62), (390, YB), (L + K, YB))


@glyph("C")
def _(p):
    p.ts((458, CT - 52), CTP, CTL, BL, BP)
    p.tb(BP, (492, YB + 128))
    up(p, CTP, ln=CUP)
    down(p, BP)


@glyph("D")
def _(p):
    cstem(p, L, double=True)
    p.ts((L, CT), (380, CT), (R, CT - 90), (R, YB + 62), (390, YB), (L + K, YB))


@glyph("E")
def _(p):
    cstem(p, L, double=True, grow_down=False)
    p.ts((L, CT), (450, CT), w=0.8)
    p.ts((L, 366), (380, 366), w=0.7)
    p.ts((L + K, YB), (456, YB), w=0.8)


@glyph("F")
def _(p):
    cstem(p, L, double=True)
    p.ts((L, CT), (456, CT), w=0.8)
    p.ts((L, 366), (380, 366), w=0.7)


@glyph("G")
def _(p):
    p.ts((458, CT - 52), CTP, CTL, BL, BP, (R, YB + 70), (R, 336))
    p.ts((R, 336), (320, 336), w=0.7)
    up(p, CTP, ln=CUP)
    down(p, BP)


@glyph("H")
def _(p):
    cstem(p, L, double=True)
    cstem(p, R)
    p.ts((L, 366), (R, 366), w=0.7)


@glyph("I")
def _(p):
    cstem(p, M, head=False, foot=False)
    p.ts((120, CT), (480, CT), w=0.8)  # wide bars top and bottom: this is what makes it an I
    p.ts((120, YB), (480, YB), w=0.8)


@glyph("J")
def _(p):
    p.ts((R - K, CT), (R, CT - D), (R, YB + 70), (390, YB), (210, YB), (140, YB + 70))
    p.ts((300, CT), (R, CT), w=0.7)
    up(p, (R - K, CT), ln=CUP)
    down(p, (300, YB))


@glyph("K")
def _(p):
    cstem(p, L, double=True)
    p.ts((L, 300), (456, CT - 6), w=0.64, t=46)
    p.ts((250, 400), (462, YB + D), (462 + K, YB))
    down(p, (462 + K, YB))


@glyph("L")
def _(p):
    cstem(p, L, double=True, grow_down=False)
    p.ts((L + K, YB), (456, YB), w=0.8)
    p.tb((456, YB), (500, YB + 120), w=0.8)


@glyph("M")
def _(p):
    a, b, c = col(2), col(6), col(10)
    cstem(p, a)
    cstem(p, c)
    p.ts((a, CT - 20), (b, 300), (c, CT - 20), w=0.66, t=40)
    down(p, (b, 300), ln=DOWN * 0.8)


@glyph("N")
def _(p):
    cstem(p, L, double=True)
    cstem(p, R)
    p.ts((L, CT - 20), (R, YB + 20), w=0.8)


@glyph("O")
def _(p):
    p.ts(CTL, CTP, CTR, BR, BP, BL, close=True)
    up(p, CTP, ln=CUP)
    down(p, BP)


@glyph("P")
def _(p):
    cstem(p, L, double=True)
    p.ts((L, CT), (380, CT), (R, CT - 80), (R, 410), (390, 336), (L, 336))


@glyph("Q")
def _(p):
    p.ts(CTL, CTP, CTR, BR, BP, BL, close=True)
    p.tb((330, 110), (530, -120))
    up(p, CTP, ln=CUP)


@glyph("R")
def _(p):
    cstem(p, L, double=True)
    p.ts((L, CT), (380, CT), (R, CT - 80), (R, 410), (390, 336), (L, 336))
    p.ts((300, 336), (462, YB + D), (462 + K, YB))
    down(p, (462 + K, YB))


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
    p.ts((110, CT), (490, CT), w=0.8)


@glyph("U")
def _(p):
    p.ts((L - K, CT), (L, CT - D), (L, YB + 60), (210, YB), (R, YB + 90))
    p.ts((L + 2.5 * XPP, CT - 96), (L + 2.5 * XPP, YB + 110), w=0.46, t=12)
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
    p.ts(CTL, CTP, CTR, BR, BP, BL, close=True)
    p.ts((220, 200), (380, CT - 160), w=0.6, t=40)  # a slash heavy enough to survive


@glyph("1")
def _(p):
    x = col(5)
    p.ts((x - K, CT), (x, CT - D), (x, YB))
    p.tb((x - K, CT), (110, CT - 190), w=1.0)  # a long flag, and a base
    p.ts((150, YB), (480, YB), w=0.8)


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
    p.ts((110, MIDY), (490, MIDY), w=0.95)
    p.ts((300, MIDY + 190), (300, MIDY - 190), w=0.95)


@glyph("*")
def _(p):
    cy = MIDY + 40
    p.ts((300, cy + 180), (300, cy - 180), w=0.7)
    p.ts((120, cy + 100), (480, cy - 100), w=0.7, t=50)
    p.ts((120, cy - 100), (480, cy + 100), w=0.7, t=50)


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


PAREN = [(col(7), TOPY + 10), (col(4), TOPY - 150), (col(4), BOTY + 150), (col(7), BOTY - 10)]
SQUARE = [(col(7.5), TOPY), (col(4), TOPY), (col(4), BOTY), (col(7.5), BOTY)]
CURLY = [(col(7.5), TOPY), (col(5), TOPY - 60), (col(5), MIDY + 90), (col(3), MIDY), (col(5), MIDY - 90), (col(5), BOTY + 60), (col(7.5), BOTY)]


@glyph("(")
def _(p):
    p.ts(*PAREN, w=PN)


@glyph(")")
def _(p):
    p.ts(*mirror(PAREN), w=PN)


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
    p.ts((240, CT), (190, YB), w=0.5, t=40)
    p.ts((420, CT), (370, YB), w=0.5, t=40)
    p.ts((90, 470), (510, 470), w=0.5)
    p.ts((90, 240), (510, 240), w=0.5)


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


@glyph("@")
def _(p):
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


@glyph("—─")  # em dash: runs edge to edge, so a row of them joins
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
    p.ts((470, YT + 30), (130, YB - 30), w=0.4, t=34)


@glyph("Ø")
def _(p):
    TEXTURA["O"](p)
    p.ts((480, CT + 30), (120, YB - 30), w=0.4, t=34)


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
    p.ts((x - 120, y - 30), (x, y + 90), (x + 120, y - 30), w=0.5, t=34)


def m_caron(p, y, x=M):
    p.ts((x - 120, y + 90), (x, y - 30), (x + 120, y + 90), w=0.5, t=34)


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
