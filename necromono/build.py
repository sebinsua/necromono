"""Build NecroMono: `python -m necromono.build` writes fonts/NecroMono-Regular.ttf."""
import sys
import time
from pathlib import Path

from fontTools.agl import UV2AGL
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables.O_S_2f_2 import Panose

from .glyphs import GLYPHS, is_letter
from .textura import TEXTURA, finish
from .pen import ADVANCE as W
from .pen import ASCENDER, CUTS, DESCENDER, REGULAR, SY, UPM, Pen
from .pen import XHEIGHT as X

FAMILY = "NecroMono"
VERSION = "0.1"
ROOT = Path(__file__).resolve().parent.parent


def glyph_name(ch):
    cp = ord(ch)
    return UV2AGL.get(cp) or "uni%04X" % cp


def draw(ch, cut=REGULAR, seed=None, edge=None):
    pen = Pen(ch, cut, seed=seed, edge=edge)
    if cut.broken and ch in TEXTURA:  # the terminal cut's constructed letters
        TEXTURA[ch](pen)
        finish(pen)
        return pen.contours()
    GLYPHS[ch](pen)
    if is_letter(ch):
        pen.run_on()
        pen.strays()
    return pen.contours()


def tt_glyph(contours):
    pen = TTGlyphPen(None)
    for c in contours:
        pen.moveTo(c[0])
        for pt in c[1:]:
            pen.lineTo(pt)
        pen.closePath()
    return pen.glyph()


LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def variants(cut, order, glyphs):
    """Extra drawings of every letter, and the rules that choose between them.

    alt1, alt2: the same letter with different line work. The font cycles
        through them inside a word, so a repeated letter is never a stamp.
    init, fina: the letter at the start or end of a word, which throws one
        long line outward.

    Returns OpenType feature code. It lives in `calt`, which terminals and
    editors apply by default and which can be switched off like ligatures."""
    kinds = {"alt1": dict(seed="#1"), "alt2": dict(seed="#2"), "init": dict(edge="init"), "fina": dict(edge="fina")}
    for kind, kw in kinds.items():
        for ch in LETTERS:
            name = "%s.%s" % (glyph_name(ch), kind)
            contours = draw(ch, cut, seed=ch + kw["seed"] if "seed" in kw else None, edge=kw.get("edge"))
            glyphs[name] = tt_glyph(contours)
            order.append(name)

    def cls(kind):
        return " ".join(glyph_name(ch) + ("." + kind if kind else "") for ch in LETTERS)

    return """
@L0 = [%s];
@L1 = [%s];
@L2 = [%s];
@LI = [%s];
@LF = [%s];
@ANY = [@L0 @L1 @L2 @LI @LF];
feature calt {
    lookup word_start {
        ignore sub @ANY @L0';
        sub @L0' by @LI;
    } word_start;
    lookup word_end {
        ignore sub @L0' @ANY;
        sub @L0' by @LF;
    } word_end;
    lookup cycle {
        sub [@L0 @LI] @L0' by @L1;
        sub @L1 @L0' by @L2;
    } cycle;
} calt;
""" % (cls(""), cls("alt1"), cls("alt2"), cls("init"), cls("fina"))


def notdef():
    outer = [(60, 0), (60, X), (W - 60, X), (W - 60, 0)]
    inner = [(100, 40), (W - 100, 40), (W - 100, X - 40), (100, X - 40)]
    return [outer, inner]


def build(cut=REGULAR, out_dir=None):
    out_dir = Path(out_dir or ROOT / "fonts")
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()

    order = [".notdef", "space"]
    cmap = {0x20: "space", 0xA0: "space"}
    glyphs = {".notdef": tt_glyph(notdef()), "space": tt_glyph([])}
    points = 0
    chars = sorted(set(GLYPHS) | (set(TEXTURA) if cut.broken else set()))
    seen = {}  # several characters can share one drawing, e.g. the prompt arrows
    for ch in chars:
        fn = TEXTURA.get(ch) if cut.broken and ch in TEXTURA else GLYPHS[ch]
        if fn in seen and fn.__name__ == "_" and ch not in GLYPHS:
            cmap[ord(ch)] = seen[fn]
            continue
        name = glyph_name(ch)
        contours = draw(ch, cut)
        points += sum(len(c) for c in contours)
        glyphs[name] = tt_glyph(contours)
        order.append(name)
        cmap[ord(ch)] = name
        seen[fn] = name

    linked = cut.name in ("Regular", "Bold", "Italic", "Bold Italic")  # one family: nothing is faked by the terminal
    family = FAMILY if linked else "%s %s" % (FAMILY, cut.name)
    style = cut.name if linked else "Regular"
    is_bold, is_italic = linked and "Bold" in style, linked and "Italic" in style
    features = variants(cut, order, glyphs) if cut.broken else ""
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    glyf = fb.font["glyf"]
    metrics = {}
    for name in order:
        g = glyf[name]
        metrics[name] = (W, g.xMin if g.numberOfContours else 0)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENDER, descent=DESCENDER, lineGap=0)
    fb.setupNameTable(
        {
            # each cut is its own family, so an app's font list shows them separately
            "familyName": family,
            "styleName": style,
            "uniqueFontIdentifier": "%s %s %s" % (family, style, VERSION),
            "fullName": family if style == "Regular" else "%s %s" % (family, style),
            "psName": "%s-%s" % (FAMILY, cut.name.replace(" ", "")),
            "version": "Version %s" % VERSION,
        }
    )
    # growth leaves the line box on purpose; the win metrics cover it so
    # nothing is clipped where they are used as a clipping region
    y_max = max(glyf[n].yMax for n in order if glyf[n].numberOfContours)
    y_min = min(glyf[n].yMin for n in order if glyf[n].numberOfContours)
    panose = Panose()
    for field in ("bFamilyType", "bSerifStyle", "bWeight", "bProportion", "bContrast", "bStrokeVariation", "bArmStyle", "bLetterForm", "bMidline", "bXHeight"):
        setattr(panose, field, 0)
    panose.bFamilyType, panose.bProportion = 2, 9  # Latin text, monospaced
    fb.setupOS2(
        version=4,
        sTypoAscender=ASCENDER,
        sTypoDescender=DESCENDER,
        sTypoLineGap=0,
        usWinAscent=max(ASCENDER, y_max),
        usWinDescent=max(-DESCENDER, -y_min),
        sxHeight=X,
        sCapHeight=int(X + 150 * SY),
        xAvgCharWidth=W,
        fsSelection=((0x20 if is_bold else 0) | (0x01 if is_italic else 0) or 0x40) | 0x80,  # bold / italic / regular; use typo metrics
        usWeightClass=700 if is_bold else 400,
        panose=panose,
        achVendID="NCRO",
    )
    fb.setupPost(isFixedPitch=1, underlinePosition=-120, underlineThickness=50)
    fb.font["head"].macStyle |= (1 if is_bold else 0) | (2 if is_italic else 0)
    if features:
        fb.addOpenTypeFeatures(features)

    path = out_dir / ("%s-%s.ttf" % (FAMILY, cut.name.replace(" ", "")))
    fb.save(str(path))
    print(
        "%s: %d characters, %d outline points, %.0f KB, built in %.1fs"
        % (path.relative_to(ROOT), len(cmap) - 2, points, path.stat().st_size / 1024, time.time() - started)
    )
    return path


if __name__ == "__main__":
    for cut in CUTS:
        build(cut, out_dir=sys.argv[1] if len(sys.argv) > 1 else None)
