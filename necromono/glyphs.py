"""Glyph skeletons. Each function draws one character with a Pen.

Letters get `run_on()` and `strays()` applied afterwards; punctuation does
not, so the marks code depends on stay comparatively clean.
"""
from .pen import L, M, R, SW, TALL, W, X

GLYPHS = {}  # character -> drawing function


def glyph(chars):
    def deco(fn):
        for ch in chars:
            if ch in GLYPHS:
                raise ValueError("duplicate glyph %r" % ch)
            GLYPHS[ch] = fn
        return fn

    return deco


# ------------------------------------------------------------------ lowercase
@glyph("a")
def _(p):
    p.stem(R, top=X - 30)
    p.blade([(R, X - 40), (M, X + 16), (L + 20, X - 60), (L + 4, X - 160)], [SW * 0.9, SW * 0.7, SW * 0.5, 0])
    p.blade(
        [(R, X * 0.6), (L + 40, X * 0.52), (L - 6, X * 0.26), (L + 50, 0), (R, 100)],
        [SW * 0.3, SW * 0.7, SW, SW * 0.7, SW * 0.3],
    )


def _bowl_right(p, x=L):
    p.blade(
        [(x, X - 150), (M + 20, X + 10), (R + 6, X * 0.7), (R + 6, X * 0.3), (M + 10, -4), (x, 80)],
        [SW * 0.3, SW * 0.7, SW, SW, SW * 0.6, SW * 0.3],
    )


def _bowl_left(p, x=R):
    p.blade(
        [(x, X - 150), (M - 20, X + 10), (L - 6, X * 0.7), (L - 6, X * 0.3), (M - 10, -4), (x, 80)],
        [SW * 0.3, SW * 0.7, SW, SW, SW * 0.6, SW * 0.3],
    )


@glyph("b")
def _(p):
    p.stem(L, top=TALL, spire=p.rng.uniform(300, 400), hook=-1, drip=60)
    _bowl_right(p)


def _c(p, T=X):
    sp = p.rng.uniform(240, 380) * p.g
    p.blade(
        [(M + 30, T + sp), (L + 40, T + 20), (L - 6, T * 0.72), (L - 6, T * 0.3), (L + 46, 6), (M + 60, -10), (R + 30, 90)],
        [0, SW * 0.5, SW, SW, SW * 0.7, SW * 0.5, 0],
    )
    p.blade([(L + 30, T - 40), (M + 20, T + 16), (R + 10, T - 20), (R + 22, T - 130)], [SW * 0.3, SW * 0.7, SW * 0.8, 0])
    p.blade([(M + 40, -10), (M + 30, -120), (M + 60, -250)], [SW * 0.3, SW * 0.16, 0])


@glyph("c")
def _(p):
    _c(p)


@glyph("d")
def _(p):
    p.almond(spire=140)
    p.stem(R + 6, top=X + 150, spire=p.rng.uniform(330, 430), lean=-70)


@glyph("e")
def _(p):
    _c(p)
    p.blade([(R + 16, X - 110), (M + 20, X * 0.52), (L + 10, X * 0.4)], [SW * 0.5, SW * 0.34, SW * 0.2])


@glyph("f")
def _(p):
    p.blade(
        [(380, X + 210), (340, X + 300), (230, X + 290), (170, X + 120), (170, 200), (176, -60), (140, -330)],
        [0, SW * 0.5, SW * 0.8, SW, SW, SW * 0.6, 0],
    )
    p.blade([(226, X + 292), (200, X + 292 + 128 * p.g), (236, X + 292 + 268 * p.g)], [SW * 0.3, SW * 0.18, 0])
    p.blade([(30, X - 70), (150, X - 10), (290, X - 20), (390, X - 100)], [0, SW * 0.56, SW * 0.56, 0])


@glyph("g")
def _(p):
    p.almond(drip=20)
    p.blade(
        [(R + 4, X * 0.5), (R + 8, 0), (R - 10, -180), (M, -300), (L - 20, -250), (L - 50, -130)],
        [SW * 0.9, SW * 0.9, SW * 0.7, SW * 0.5, SW * 0.3, 0],
    )


@glyph("h")
def _(p):
    p.stem(L, top=TALL, spire=p.rng.uniform(300, 400))
    p.arch(L, R)
    p.stem(R, top=X - 30, vein=False, spire=0, hook=-1, drip=p.rng.uniform(260, 360))


@glyph("i")
def _(p):
    p.stem(M, spire=120, lean=-10, vein=False)
    p.blade([(M - 8, X + 150), (M + 14, X + 220), (M - 16, X + 290 + 140 * p.g)], [0, 76, 0])
    p.blade([(M - 70, X - 30), (M - 40, X + 10), (M - 6, X - 10)], [0, 34, 60])


@glyph("j")
def _(p):
    x = M + 30
    p.stem(x, spire=120, lean=-10, vein=False, bot=-150, hook=-1, drip=p.rng.uniform(200, 280))
    p.blade([(x + 4, -120), (x - 40, -250), (x - 130, -300), (x - 200, -220)], [SW * 0.8, SW * 0.6, SW * 0.34, 0])
    p.blade([(x - 8, X + 150), (x + 14, X + 220), (x - 16, X + 290 + 140 * p.g)], [0, 76, 0])
    p.blade([(x - 70, X - 30), (x - 40, X + 10), (x - 6, X - 10)], [0, 34, 60])


@glyph("k")
def _(p):
    p.stem(L, top=TALL, spire=p.rng.uniform(300, 400))
    p.blade([(L, X * 0.4), (M + 20, X * 0.78), (R + 30, X + 60), (R + 50, X + 260)], [SW * 0.3, SW * 0.6, SW * 0.4, 0])
    p.blade([(M - 30, X * 0.52), (R - 20, 150), (R + 20, 0), (R + 60, -220)], [SW * 0.4, SW * 0.9, SW * 0.7, 0])


@glyph("l")
def _(p):
    p.stem(M, top=TALL, spire=p.rng.uniform(300, 400), hook=1, drip=90)
    p.blade([(M + 4, 100), (M + 50, 6), (M + 150, 30), (M + 196, 130)], [SW * 0.8, SW * 0.5, SW * 0.3, 0])


@glyph("m")
def _(p):
    w = 82
    a, b, c = 66, 210, 354
    r = p.rng
    p.stem(a, w=w, spire=r.uniform(240, 320), lean=-30)
    p.arch(a, b, w=w)
    p.stem(b, top=X - 30, w=w, spire=0, lean=0, drip=r.uniform(260, 380), vein=False)
    p.arch(b, c, w=w)
    p.stem(c, top=X - 30, w=w, spire=0, lean=30, vein=False)


@glyph("n")
def _(p):
    p.stem(L)
    p.arch(L, R)
    p.stem(R, top=X - 30, vein=False, spire=0)  # under the arch: no spire, so n is not u


@glyph("o")
def _(p):
    p.almond()


@glyph("p")
def _(p):
    p.stem(L, bot=-230, hook=-1, drip=p.rng.uniform(120, 200))
    _bowl_right(p)


@glyph("q")
def _(p):
    p.stem(R, top=X - 30, bot=-230, hook=1, drip=p.rng.uniform(120, 200), vein=False)
    _bowl_left(p)


@glyph("r")
def _(p):
    p.stem(120)
    p.blade(
        [(120, X - 180), (230, X - 20), (330, X + 10), (372, X - 70), (350, X - 150)],
        [SW * 0.2, SW * 0.5, SW * 0.86, SW * 0.5, 0],
    )
    p.blade([(318, X + 10), (350, X + 160), (322, X + 330)], [SW * 0.4, SW * 0.24, 0])


def _s(p, T=X, k=1.0):
    w = SW * k
    p.blade(
        [(R + 14, T - 110), (M + 50, T + 6), (L + 6, T * 0.8), (M, T * 0.5), (R - 4, T * 0.22), (M - 40, -6), (L - 20, 100)],
        [0, w * 0.6, w * 0.9, w, w * 0.9, w * 0.6, 0],
    )
    p.up((M + 40, T - 20), w=w * 0.6)
    p.down((M - 30, 20), w=w * 0.6)


@glyph("s")
def _(p):
    _s(p)


@glyph("t")
def _(p):
    p.stem(170, top=X + 40, spire=p.rng.uniform(330, 430), lean=-16, hook=1, drip=70)
    p.blade([(20, X - 60), (150, X - 6), (300, X - 16), (404, X - 90)], [0, SW * 0.6, SW * 0.6, 0])
    p.blade([(170, 110), (220, 10), (330, 10), (396, 120)], [SW * 0.8, SW * 0.6, SW * 0.34, 0])


@glyph("u")
def _(p):
    p.stem(L, drip=40, hook=1)
    p.stem(R)
    p.blade([(L, 150), (L + 60, 20), (M + 20, 0), (R, 110)], [SW * 0.9, SW * 0.8, SW * 0.42, SW * 0.2])


def _v(p, T=X):
    p.blade([(L - 30, T + 20), (L + 16, T * 0.5), (M, 10)], [SW * 0.7, SW, SW * 0.6])
    p.blade([(R + 30, T + 20), (R - 16, T * 0.5), (M, 10)], [SW * 0.5, SW * 0.8, SW * 0.6])
    p.up((L - 30, T - 40), w=SW * 0.7, lean=8)
    p.up((R + 30, T - 40), w=SW * 0.5, lean=-8)
    p.down((M, 60), w=SW * 0.7)


@glyph("v")
def _(p):
    _v(p)


def _w(p, T=X):
    w = 86
    p.blade([(40, T + 20), (80, T * 0.5), (130, 10)], [w * 0.7, w, w * 0.6])
    p.blade([(210, T * 0.86), (176, T * 0.45), (130, 10)], [w * 0.4, w * 0.7, w * 0.6])
    p.blade([(210, T * 0.86), (244, T * 0.45), (290, 10)], [w * 0.5, w * 0.9, w * 0.6])
    p.blade([(380, T + 20), (340, T * 0.5), (290, 10)], [w * 0.5, w * 0.7, w * 0.6])
    p.up((40, T - 40), w=w * 0.7, lean=8)
    p.up((210, T * 0.86 - 50), w=w * 0.6, ln=p.rng.uniform(500, 800))
    p.up((380, T - 40), w=w * 0.5, lean=-8)
    p.down((130, 60), w=w * 0.6)
    p.down((290, 60), w=w * 0.6)


@glyph("w")
def _(p):
    _w(p)


def _x(p, T=X):
    p.blade([(L - 24, T + 10), (M, T * 0.5), (R + 24, -10)], [SW * 0.6, SW, SW * 0.6])
    p.blade([(R + 24, T + 10), (M, T * 0.5), (L - 24, -10)], [SW * 0.4, SW * 0.64, SW * 0.4])
    p.up((L - 14, T - 40), w=SW * 0.6, lean=10)
    p.up((R + 14, T - 40), w=SW * 0.4, lean=-10)
    p.down((R + 14, 40), w=SW * 0.6, lean=6)
    p.down((L - 14, 40), w=SW * 0.4, lean=-6)


@glyph("x")
def _(p):
    _x(p)


@glyph("y")
def _(p):
    p.blade([(L - 30, X + 20), (L + 24, X * 0.5), (M + 10, 50)], [SW * 0.7, SW, SW * 0.5])
    p.blade([(R + 30, X + 20), (R - 30, X * 0.4), (M - 10, -120), (L, -300), (L - 70, -250)], [SW * 0.5, SW * 0.9, SW * 0.7, SW * 0.4, 0])
    p.up((L - 30, X - 40), w=SW * 0.7, lean=8)
    p.up((R + 30, X - 40), w=SW * 0.5, lean=-8)


def _z(p, T=X):
    p.blade([(L - 30, T - 90), (L + 20, T - 10), (M + 20, T + 6), (R + 14, T - 30)], [0, SW * 0.6, SW * 0.7, SW * 0.6])
    p.blade([(R + 14, T - 30), (M, T * 0.5), (L - 14, 30)], [SW * 0.5, SW * 0.9, SW * 0.6])
    p.blade([(L - 14, 30), (M - 20, -6), (R - 10, 10), (R + 40, 110)], [SW * 0.6, SW * 0.7, SW * 0.5, 0])
    p.up((R + 4, T - 60), w=SW * 0.5)
    p.down((L - 4, 60), w=SW * 0.5)


@glyph("z")
def _(p):
    _z(p)


# ------------------------------------------------------------------ capitals
CAP = X + 150
A0, B0 = 84, 336  # capital stem columns


def cap(p, x, lean=0, vein=True, **kw):
    kw.setdefault("spire", p.rng.uniform(330, 420))
    p.stem(x, top=CAP, lean=lean, vein=vein, **kw)


def _foot(p, x=A0):
    p.blade([(x, 30), (x + 136, -4), (x + 246, 20), (x + 296, 120)], [SW * 0.5, SW * 0.7, SW * 0.5, 0])


def _top_arm(p, x=A0):
    p.blade([(x, CAP - 30), (x + 136, CAP + 10), (x + 256, CAP - 30), (x + 272, CAP - 130)], [SW * 0.4, SW * 0.7, SW * 0.6, 0])


def _mid_arm(p, x=A0):
    p.blade([(x, CAP * 0.5), (x + 116, CAP * 0.52), (x + 216, CAP * 0.46)], [SW * 0.4, SW * 0.5, 0])


def _upper_bowl(p):
    p.blade(
        [(A0, CAP - 10), (236, CAP + 10), (336, CAP * 0.75), (236, CAP * 0.5), (A0 + 16, CAP * 0.46)],
        [SW * 0.3, SW * 0.7, SW * 0.9, SW * 0.6, SW * 0.3],
    )


def _leg(p):
    p.blade([(190, CAP * 0.5), (300, 150), (350, 0), (380, -200)], [SW * 0.4, SW * 0.9, SW * 0.7, 0])


@glyph("A")
def _(p):
    p.blade([(56, -10), (116, CAP * 0.5), (M, CAP + 40)], [SW * 0.7, SW * 0.9, SW * 0.6])
    p.blade([(364, -10), (304, CAP * 0.5), (M, CAP + 40)], [SW, SW, SW * 0.6])
    p.blade([(116, CAP * 0.36), (M, CAP * 0.4), (304, CAP * 0.34)], [SW * 0.3, SW * 0.45, SW * 0.3])
    p.up((M, CAP - 40), w=SW * 0.8, ln=p.rng.uniform(520, 820))
    p.down((60, 50), w=SW * 0.7, lean=-6)
    p.down((360, 50), w=SW * 0.9, lean=6)


@glyph("B")
def _(p):
    cap(p, A0)
    _upper_bowl(p)
    p.blade(
        [(A0 + 16, CAP * 0.5), (250, CAP * 0.5), (348, CAP * 0.26), (240, 0), (A0, 10)],
        [SW * 0.3, SW * 0.7, SW, SW * 0.7, SW * 0.3],
    )


@glyph("C")
def _(p):
    _c(p, CAP)


@glyph("D")
def _(p):
    cap(p, A0)
    p.blade(
        [(A0, CAP - 10), (240, CAP + 6), (348, CAP * 0.66), (348, CAP * 0.34), (240, -4), (A0, 10)],
        [SW * 0.3, SW * 0.7, SW, SW, SW * 0.7, SW * 0.3],
    )


@glyph("E")
def _(p):
    cap(p, A0, drip=60)
    _top_arm(p)
    _mid_arm(p)
    _foot(p)


@glyph("F")
def _(p):
    cap(p, A0)
    _top_arm(p)
    _mid_arm(p)


@glyph("G")
def _(p):
    _c(p, CAP)
    p.blade([(R + 24, CAP * 0.44), (R + 20, 200), (R + 10, 60)], [SW * 0.5, SW * 0.9, SW * 0.7])
    p.blade([(R + 30, CAP * 0.44), (M + 40, CAP * 0.46), (M - 10, CAP * 0.4)], [SW * 0.5, SW * 0.4, 0])


@glyph("H")
def _(p):
    cap(p, A0, lean=-30)
    cap(p, B0, lean=30, vein=False)
    p.blade([(A0, CAP * 0.5), (M, CAP * 0.55), (B0, CAP * 0.5)], [SW * 0.4, SW * 0.5, SW * 0.4])


@glyph("I")
def _(p):
    cap(p, M)
    p.blade([(90, CAP - 60), (M, CAP - 6), (330, CAP - 60)], [0, SW * 0.5, 0])
    p.blade([(90, 60), (M, 6), (330, 60)], [0, SW * 0.5, 0])


@glyph("J")
def _(p):
    p.blade([(290, CAP), (290, 220), (250, 30), (150, -10), (70, 120)], [SW, SW, SW * 0.8, SW * 0.5, 0])
    p.blade([(130, CAP - 60), (250, CAP - 6), (370, CAP - 60)], [0, SW * 0.5, 0])
    p.up((290, CAP - 40), w=SW)


@glyph("K")
def _(p):
    cap(p, A0)
    p.blade([(A0, CAP * 0.42), (230, CAP * 0.75), (346, CAP + 40), (366, CAP + 260)], [SW * 0.3, SW * 0.6, SW * 0.4, 0])
    _leg(p)


@glyph("L")
def _(p):
    cap(p, A0, drip=60, hook=1)
    _foot(p)


@glyph("M")
def _(p):
    w = 98
    cap(p, 62, lean=-40, w=w)
    cap(p, 358, lean=40, w=w, vein=False)
    p.blade([(62, CAP - 10), (130, CAP * 0.6), (M, CAP * 0.28)], [w * 0.5, w * 0.7, w * 0.5])
    p.blade([(358, CAP - 10), (290, CAP * 0.6), (M, CAP * 0.28)], [w * 0.4, w * 0.6, w * 0.5])
    p.down((M, CAP * 0.28 + 50), w=w * 0.6)


@glyph("N")
def _(p):
    r = p.rng
    p.stem(84, top=X + 150, spire=r.uniform(330, 420), lean=-50)
    p.blade([(84, X + 110), (210, X * 0.55), (336, 30)], [SW * 0.4, SW * 0.74, SW * 0.5])
    p.stem(336, top=X + 150, spire=r.uniform(330, 420), lean=50, vein=False)


@glyph("O")
def _(p):
    p.almond(top=CAP)


@glyph("P")
def _(p):
    cap(p, A0)
    _upper_bowl(p)


@glyph("Q")
def _(p):
    p.almond(top=CAP)
    p.blade([(230, 150), (320, -40), (410, -210)], [SW * 0.5, SW * 0.6, 0])


@glyph("R")
def _(p):
    cap(p, A0)
    _upper_bowl(p)
    _leg(p)


@glyph("S")
def _(p):
    _s(p, CAP)


@glyph("T")
def _(p):
    cap(p, M)
    p.blade([(24, CAP - 80), (150, CAP - 6), (280, CAP - 16), (400, CAP - 100)], [0, SW * 0.6, SW * 0.6, 0])


@glyph("U")
def _(p):
    cap(p, A0, drip=40, hook=1)
    cap(p, B0, vein=False)
    p.blade([(A0, 150), (A0 + 60, 20), (M + 20, 0), (B0, 110)], [SW * 0.9, SW * 0.8, SW * 0.42, SW * 0.2])


@glyph("V")
def _(p):
    _v(p, CAP)


@glyph("W")
def _(p):
    _w(p, CAP)


@glyph("X")
def _(p):
    _x(p, CAP)


@glyph("Y")
def _(p):
    p.blade([(60, CAP + 20), (130, CAP * 0.7), (M, CAP * 0.42)], [SW * 0.7, SW * 0.9, SW * 0.7])
    p.blade([(360, CAP + 20), (290, CAP * 0.7), (M, CAP * 0.42)], [SW * 0.5, SW * 0.7, SW * 0.6])
    p.blade([(M, CAP * 0.46), (M, CAP * 0.2), (M, 10)], [SW * 0.8, SW, SW])
    p.up((60, CAP - 40), w=SW * 0.7, lean=8)
    p.up((360, CAP - 40), w=SW * 0.5, lean=-8)
    p.down((M, 50), w=SW)


@glyph("Z")
def _(p):
    _z(p, CAP)


# ------------------------------------------------------------------ digits
@glyph("0")
def _(p):
    p.almond(top=CAP)
    p.blade([(150, CAP * 0.26), (M, CAP * 0.5), (270, CAP * 0.74)], [0, 34, 0])


@glyph("1")
def _(p):
    cap(p, M + 20)
    p.blade([(M + 20, CAP - 20), (130, CAP - 120), (66, CAP - 210)], [SW * 0.6, SW * 0.4, 0])
    p.blade([(100, 60), (M + 20, 6), (350, 60)], [0, SW * 0.5, 0])


@glyph("2")
def _(p):
    p.blade(
        [(66, CAP - 180), (150, CAP), (290, CAP - 20), (334, CAP * 0.68), (200, CAP * 0.34), (70, 10)],
        [0, SW * 0.6, SW * 0.9, SW * 0.9, SW * 0.7, SW * 0.5],
    )
    p.blade([(70, 20), (M, -4), (330, 20), (384, 116)], [SW * 0.6, SW * 0.7, SW * 0.5, 0])
    p.up((200, CAP - 40), w=SW * 0.6)


@glyph("3")
def _(p):
    p.blade([(66, CAP - 90), (200, CAP + 6), (324, CAP * 0.78), (M, CAP * 0.54)], [0, SW * 0.7, SW * 0.9, SW * 0.4])
    p.blade([(M, CAP * 0.54), (344, CAP * 0.3), (220, -6), (56, 96)], [SW * 0.4, SW, SW * 0.7, 0])
    p.up((220, CAP - 40), w=SW * 0.6)
    p.down((230, 40), w=SW * 0.6)


@glyph("4")
def _(p):
    p.blade([(270, CAP + 20), (160, CAP * 0.66), (60, CAP * 0.32)], [SW * 0.5, SW * 0.7, SW * 0.8])
    p.blade([(60, CAP * 0.32), (200, CAP * 0.3), (396, CAP * 0.35)], [SW * 0.6, SW * 0.5, 0])
    cap(p, 284, vein=False)


@glyph("5")
def _(p):
    p.blade([(340, CAP - 50), (M, CAP), (100, CAP - 30)], [0, SW * 0.6, SW * 0.5])
    p.blade([(100, CAP - 10), (98, CAP * 0.78), (96, CAP * 0.55)], [SW * 0.6, SW * 0.6, SW * 0.6])
    p.blade([(96, CAP * 0.55), (240, CAP * 0.6), (344, CAP * 0.32), (220, -6), (56, 96)], [SW * 0.4, SW * 0.8, SW, SW * 0.7, 0])
    p.up((104, CAP - 50), w=SW * 0.6)
    p.down((230, 40), w=SW * 0.6)


@glyph("6")
def _(p):
    p.blade(
        [(314, CAP + 80), (150, CAP * 0.7), (A0, CAP * 0.3), (M, -6), (B0, CAP * 0.24), (230, CAP * 0.52), (100, CAP * 0.4)],
        [0, SW * 0.7, SW, SW * 0.8, SW, SW * 0.6, SW * 0.3],
    )


@glyph("7")
def _(p):
    p.blade([(46, CAP - 70), (200, CAP), (354, CAP - 20)], [0, SW * 0.7, SW * 0.7])
    p.blade([(354, CAP - 20), (230, CAP * 0.45), (170, 0)], [SW * 0.6, SW * 0.9, SW])
    p.up((330, CAP - 60), w=SW * 0.6)


@glyph("8")
def _(p):
    p.blade(
        [(M, CAP), (110, CAP * 0.78), (M, CAP * 0.52), (324, CAP * 0.26), (M, 0), (96, CAP * 0.26), (M, CAP * 0.52), (310, CAP * 0.78), (M, CAP)],
        [SW * 0.5, SW * 0.9, SW * 0.6, SW, SW * 0.6, SW, SW * 0.6, SW * 0.9, SW * 0.5],
    )


@glyph("9")
def _(p):
    p.blade(
        [(106, -80), (270, CAP * 0.3), (B0, CAP * 0.7), (M, CAP + 6), (A0, CAP * 0.76), (190, CAP * 0.48), (320, CAP * 0.6)],
        [0, SW * 0.7, SW, SW * 0.8, SW, SW * 0.6, SW * 0.3],
    )


# ------------------------------------------------------------------ punctuation
# No growth, no stray marks: the marks code depends on stay comparatively clean.
PW = 62
OW = 92  # operators and dots are heavier than brackets, or they vanish beside the letters
MID = X * 0.5  # the height operators sit on


def _dot(p, x=M, y=0):
    p.blade([(x, y - 20), (x + 16, y + 70), (x - 8, y + 190)], [0, 112, 0])


def _tail(p, x=M, y=0):
    p.blade([(x + 6, y + 190), (x + 16, y + 70), (x - 20, y - 90), (x - 80, y - 270)], [0, 112, 50, 0])


def _tick(p, x=M):
    p.blade([(x, CAP + 60), (x + 8, CAP - 20), (x - 10, CAP - 170)], [PW, PW * 0.8, 0])


def _dash(p, y=MID, x0=30, x1=390):
    p.blade([(x0, y), ((x0 + x1) / 2, y + 8), (x1, y)], [0, OW, 0])


@glyph(".")
def _(p):
    _dot(p)


@glyph(",")
def _(p):
    _tail(p)


@glyph(":")
def _(p):
    _dot(p)
    _dot(p, y=X - 230)


@glyph(";")
def _(p):
    _dot(p, y=X - 230)
    _tail(p)


@glyph("!")
def _(p):
    p.blade([(M, CAP + 80), (M + 8, CAP * 0.62), (M, CAP * 0.28)], [PW * 1.4, PW, 0])
    _dot(p)


@glyph("?")
def _(p):
    p.blade([(96, CAP - 120), (200, CAP + 6), (324, CAP * 0.76), (226, CAP * 0.46), (M, CAP * 0.28)], [0, PW, PW * 1.2, PW * 0.8, 0])
    _dot(p)


@glyph("'")
def _(p):
    _tick(p)


@glyph('"')
def _(p):
    _tick(p, M - 70)
    _tick(p, M + 70)


@glyph("`")
def _(p):
    p.blade([(140, CAP + 90), (190, CAP + 20), (250, CAP - 80)], [PW, PW * 0.6, 0])


@glyph("-")
def _(p):
    _dash(p)


@glyph("_")
def _(p):
    p.blade([(4, -110), (M, -100), (W - 4, -110)], [PW * 0.5, PW * 0.7, PW * 0.5])


@glyph("=")
def _(p):
    _dash(p, MID + 105)
    _dash(p, MID - 105)


@glyph("+")
def _(p):
    _dash(p)
    p.blade([(M, MID + 220), (M + 6, MID), (M, MID - 220)], [0, OW, 0])


@glyph("*")
def _(p):
    import math

    cy = X * 0.62
    for a in (90, 30, -30):
        dx, dy = math.cos(math.radians(a)) * 210, math.sin(math.radians(a)) * 210
        p.blade([(M - dx, cy - dy), (M, cy), (M + dx, cy + dy)], [0, OW * 0.8, 0])


@glyph("/")
def _(p):
    p.blade([(344, CAP + 130), (M, CAP * 0.45), (76, -210)], [0, PW, 0])


@glyph("\\")
def _(p):
    p.blade([(76, CAP + 130), (M, CAP * 0.45), (344, -210)], [0, PW, 0])


@glyph("|")
def _(p):
    p.blade([(M, CAP + 210), (M, CAP * 0.45), (M, -290)], [0, PW * 0.9, 0])


@glyph("<")
def _(p):
    p.blade([(350, X + 70), (210, MID + 170), (70, MID)], [0, OW * 0.7, OW])
    p.blade([(70, MID), (210, MID - 170), (350, -70)], [OW, OW * 0.7, 0])


@glyph(">")
def _(p):
    p.blade([(70, X + 70), (210, MID + 170), (350, MID)], [0, OW * 0.7, OW])
    p.blade([(350, MID), (210, MID - 170), (70, -70)], [OW, OW * 0.7, 0])


@glyph("^")
def _(p):
    p.blade([(84, CAP - 150), (150, CAP - 40), (M, CAP + 70)], [0, PW * 0.7, PW * 0.9])
    p.blade([(M, CAP + 70), (270, CAP - 40), (336, CAP - 150)], [PW * 0.9, PW * 0.7, 0])


@glyph("~")
def _(p):
    p.blade([(30, MID - 50), (130, MID + 70), (290, MID - 60), (390, MID + 56)], [0, OW, OW, 0])


@glyph("(")
def _(p):
    p.blade([(330, X + 330), (190, X - 40), (190, 100), (330, -300)], [0, PW, PW, 0])


@glyph(")")
def _(p):
    p.blade([(90, X + 330), (230, X - 40), (230, 100), (90, -300)], [0, PW, PW, 0])


@glyph("[")
def _(p):
    p.blade([(170, CAP + 200), (170, CAP * 0.45), (170, -290)], [PW, PW * 0.9, PW])
    p.blade([(170, CAP + 190), (260, CAP + 196), (340, CAP + 210)], [PW, PW * 0.7, 0])
    p.blade([(170, -280), (260, -286), (340, -300)], [PW, PW * 0.7, 0])


@glyph("]")
def _(p):
    p.blade([(250, CAP + 200), (250, CAP * 0.45), (250, -290)], [PW, PW * 0.9, PW])
    p.blade([(250, CAP + 190), (160, CAP + 196), (80, CAP + 210)], [PW, PW * 0.7, 0])
    p.blade([(250, -280), (160, -286), (80, -300)], [PW, PW * 0.7, 0])


@glyph("{")
def _(p):
    p.blade([(340, X + 320), (240, X + 200), (240, X - 180), (110, X * 0.5 - 6)], [0, PW, PW, 0])
    p.blade([(110, X * 0.5 + 6), (240, 150), (240, -180), (340, -300)], [0, PW, PW, 0])


@glyph("}")
def _(p):
    p.blade([(80, X + 320), (180, X + 200), (180, X - 180), (310, X * 0.5 - 6)], [0, PW, PW, 0])
    p.blade([(310, X * 0.5 + 6), (180, 150), (180, -180), (80, -300)], [0, PW, PW, 0])


@glyph("#")
def _(p):
    for x in (150, 280):
        p.blade([(x + 30, CAP + 60), (x, CAP * 0.5), (x - 30, -60)], [0, PW * 0.7, 0])
    for y in (CAP * 0.68, CAP * 0.32):
        p.blade([(40, y - 6), (M, y + 6), (380, y - 6)], [0, PW * 0.7, 0])


@glyph("$")
def _(p):
    _s(p, CAP, 0.7)
    p.blade([(M + 10, CAP + 190), (M, CAP * 0.5), (M - 10, -190)], [0, 34, 0])


@glyph("%")
def _(p):
    for cx, cy in ((116, CAP - 110), (304, 110)):
        p.blade([(cx, cy + 100), (cx - 60, cy), (cx, cy - 100), (cx + 60, cy), (cx, cy + 100)], [PW * 0.4, PW * 0.7, PW * 0.4, PW * 0.7, PW * 0.4])
    p.blade([(350, CAP + 60), (M, CAP * 0.5), (70, -60)], [0, PW * 0.8, 0])


@glyph("&")
def _(p):
    p.blade(
        [(366, 30), (250, CAP * 0.3), (124, CAP * 0.72), (204, CAP + 10), (284, CAP * 0.76), (84, CAP * 0.24), (190, -6), (300, 60), (372, CAP * 0.42)],
        [0, PW * 0.9, PW, PW, PW, PW * 1.3, PW, PW * 0.8, 0],
    )


@glyph("@")
def _(p):
    p.blade(
        [(310, 20), (M, -50), (64, CAP * 0.3), (64, CAP * 0.8), (M, CAP + 70), (356, CAP * 0.8), (356, CAP * 0.36), (290, CAP * 0.26), (262, CAP * 0.62)],
        [0, PW * 0.8, PW, PW, PW * 0.8, PW, PW * 0.8, PW * 0.6, PW * 0.5],
    )
    p.blade([(262, CAP * 0.62), (196, CAP * 0.68), (150, CAP * 0.48), (196, CAP * 0.3), (262, CAP * 0.4)], [PW * 0.4, PW * 0.7, PW * 0.8, PW * 0.7, PW * 0.4])


def is_letter(ch):
    return ch.isalnum()


__all__ = ["GLYPHS", "is_letter", "W"]
