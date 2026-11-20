"""Build necromono: `python -m necromono.build` writes the four styles to fonts/."""
import sys
import time
from pathlib import Path

from fontTools.agl import UV2AGL
from fontTools.fontBuilder import FontBuilder
from fontTools.otlLib.builder import buildStatTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import newTable
from fontTools.ttLib.tables.ttProgram import Program
from fontTools.ttLib.tables.O_S_2f_2 import Panose

from . import textura
from .textura import LIGATURES, TEXTURA, finish, span
from .pen import ADVANCE as W
from .pen import ASCENDER, CUTS, DESCENDER, REGULAR, UPM, XHEIGHT, Pen
from .pen import XHEIGHT as X

FAMILY = "necromono"
# Clipping bounds, the same in every style and roomy enough for the longest
# line any letter throws. The build fails if a glyph ever exceeds them.
WIN_ASCENT, WIN_DESCENT = 1900, 1300
VERSION = "0.200"
COPYRIGHT = "Copyright 2026 Seb Insua"  # the first line of OFL.txt
ROOT = Path(__file__).resolve().parent.parent


def glyph_name(ch):
    cp = ord(ch)
    return UV2AGL.get(cp) or "uni%04X" % cp


def draw(ch, cut=REGULAR, seed=None, edge=None, bare=False):
    pen = Pen(ch, cut, seed=seed, edge=edge, bare=bare)
    TEXTURA[ch](pen)
    finish(pen)
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


# How tall a letter's growth is, by where it sits in its word. Tallest at the
# two ends and falling toward the middle, so a word has the outline a logo has.
REACH = {"": 0.7, "alt1": 0.7, "alt2": 0.7, "r2": 1.0, "r1": 1.3, "init": 1.6, "fina": 1.6}


def variants(cut, order, glyphs):
    """Extra drawings of every letter, and the rules that choose between them.

    init, fina: the first and last letter of a word of four letters or more.
        Tallest growth, and a pair of horns thrown outward.
    r1, r2: the letters next to those, and next to those again: stepping down.
    alt1, alt2: the same letter with different line work, for everything in
        between. The font cycles through them so a repeated letter is never a
        stamp.

    Letters do not join their neighbours. Two ways were tried and removed.
    Joining at the feet read as stray dashes on the baseline and made more
    pairs of letters look alike. Joining by arches above the x-height read as
    a zigzag ruled across the tops of the words.

    Returns OpenType feature code for `calt`."""

    def drawing(ch, kind):
        pen = Pen(ch, cut, seed=ch + "#" + kind[-1] if kind.startswith("alt") else None, edge=kind if kind in ("init", "fina") else None, reach=REACH[kind])
        TEXTURA[ch](pen)
        finish(pen)
        return tt_glyph(pen.contours())

    def name(ch, kind):
        return glyph_name(ch) + ("." + kind if kind else "")

    for ch in LETTERS:  # the plain letter is the mid-word one: its growth is the lowest
        glyphs[name(ch, "")] = drawing(ch, "")
    for kind in ("alt1", "alt2", "init", "fina", "r1", "r2"):
        for ch in LETTERS:
            glyphs[name(ch, kind)] = drawing(ch, kind)
            order.append(name(ch, kind))

    def cls(kind):
        return " ".join(name(ch, kind) for ch in LETTERS)

    return """
@L0 = [%s];
@L1 = [%s];
@L2 = [%s];
@LI = [%s];
@LF = [%s];
@R1 = [%s];
@R2 = [%s];
@ANY = [@L0 @L1 @L2 @LI @LF @R1 @R2];
feature calt {
    lookup word_start {  # only words of four letters or more: short words stay calm
        ignore sub @ANY @L0';
        sub @L0' @L0 @L0 @L0 by @LI;
    } word_start;
    lookup word_end {
        ignore sub @L0' @ANY;
        sub [@L0 @LI] @L0 @L0 @L0' by @LF;
    } word_end;
    lookup second {  # the letters next to the ends
        sub @LI @L0' by @R1;
        sub @L0' @LF by @R1;
    } second;
    lookup third {
        sub @LI @R1 @L0' by @R2;
        sub @L0' @R1 @LF by @R2;
    } third;
    lookup cycle {
        sub [@L0 @LI @R1 @R2] @L0' by @L1;
        sub @L1 @L0' by @L2;
    } cycle;
} calt;
""" % (cls(""), cls("alt1"), cls("alt2"), cls("init"), cls("fina"), cls("r1"), cls("r2"))


def bare_set(cut, order, glyphs, cmap):
    """Stylistic set 1: the letters with nothing growing from them. It comes
    first in the font, so when it is on, the word shaping in calt finds no
    letters left to act on."""
    pairs = []
    done = set()
    for cp, name in sorted(cmap.items()):
        ch = chr(cp)
        if name in done or ch not in TEXTURA:
            continue
        done.add(name)
        plain = draw(ch, cut, bare=True)
        if plain != draw(ch, cut):
            glyphs[name + ".bare"] = tt_glyph(plain)
            order.append(name + ".bare")
            pairs.append(name)
    names = '    featureNames {\n        name 3 1 0x0409 "Bare letters";\n    };\n'  # so apps can show what the set does
    return "feature ss01 {\n%s    sub [%s] by [%s];\n} ss01;\n" % (names, " ".join(pairs), " ".join(n + ".bare" for n in pairs))


def ligatures(cut, order, glyphs):
    """Operator ligatures, the way programming fonts do them: the last
    character becomes one wide drawing reaching back over the others, and the
    others become an empty spacer, so the text keeps its cells."""
    glyphs["LIG"] = tt_glyph([])
    order.append("LIG")
    lookups = []
    for seq in sorted(LIGATURES, key=lambda s: (-len(s), s)):  # longest first
        names = [glyph_name(c) for c in seq]
        liga = "_".join(names) + ".liga"
        pen = Pen(liga, cut)
        LIGATURES[seq](pen, *span(len(seq)))
        glyphs[liga] = tt_glyph(pen.contours())
        order.append(liga)
        first, last = names[0], names[-1]
        rules = [
            "ignore sub %s %s' %s;" % (first, first, " ".join(names[1:])),  # not inside a longer run
            "ignore sub %s' %s %s;" % (first, " ".join(names[1:]), last),
            "sub %s %s' by %s;" % (" ".join(["LIG"] * (len(seq) - 1)), last, liga),
        ]
        for i in range(len(seq) - 2, -1, -1):
            rules.append("sub %s%s' %s by LIG;" % ("LIG " * i, names[i], " ".join(names[i + 1 :])))
        lookups.append("    lookup %s {\n        %s\n    } %s;" % (liga.replace(".", "_"), "\n        ".join(rules), liga.replace(".", "_")))
    return "feature liga {\n%s\n} liga;\n" % "\n".join(lookups)


def unhinted(font):
    """What an unhinted TrueType font should still carry: a `gasp` table asking
    for smooth rendering at every size, and a `prep` program that turns on
    dropout control, so thin lines are never lost on rasterisers that hint."""
    gasp = newTable("gasp")
    gasp.gaspRange = {0xFFFF: 15}
    font["gasp"] = gasp
    prep = newTable("prep")
    prep.program = Program()
    prep.program.fromAssembly(["PUSHW[]", "511", "SCANCTRL[]", "PUSHB[]", "4", "SCANTYPE[]"])
    font["prep"] = prep


def style_attributes(font, is_bold, is_italic):
    """A STAT table, so apps can tell how the four styles relate."""
    weight = dict(value=700, name="Bold") if is_bold else dict(value=400, name="Regular", flags=0x2, linkedValue=700)
    italic = dict(value=1, name="Italic") if is_italic else dict(value=0, name="Roman", flags=0x2, linkedValue=1)
    buildStatTable(font, [dict(tag="wght", name="Weight", values=[weight]), dict(tag="ital", name="Italic", values=[italic])], macNames=False)


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
    seen = {}  # several characters can share one drawing, e.g. the prompt arrows
    for ch in sorted(TEXTURA):
        fn = TEXTURA[ch]
        if fn in seen:
            cmap[ord(ch)] = seen[fn]
            continue
        name = glyph_name(ch)
        contours = draw(ch, cut)
        points += sum(len(c) for c in contours)
        glyphs[name] = tt_glyph(contours)
        order.append(name)
        cmap[ord(ch)] = name
        seen[fn] = name

    style = cut.name  # Regular, Bold, Italic, Bold Italic: one family, so nothing is faked by the terminal
    is_bold, is_italic = "Bold" in style, "Italic" in style
    features = bare_set(cut, order, glyphs, cmap) + variants(cut, order, glyphs) + ligatures(cut, order, glyphs)
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
            "familyName": FAMILY,
            "styleName": style,
            "uniqueFontIdentifier": "%s %s %s" % (FAMILY, style, VERSION),
            "fullName": FAMILY if style == "Regular" else "%s %s" % (FAMILY, style),
            "psName": "%s-%s" % (FAMILY, cut.name.replace(" ", "")),
            "version": "Version %s" % VERSION,
            "copyright": COPYRIGHT,
            "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org",
            "licenseInfoURL": "https://openfontlicense.org",
        },
        mac=False,
    )
    # growth leaves the line box on purpose; the win metrics cover it so
    # nothing is clipped where they are used as a clipping region
    y_max = max(glyf[n].yMax for n in order if glyf[n].numberOfContours)
    y_min = min(glyf[n].yMin for n in order if glyf[n].numberOfContours)
    if y_max > WIN_ASCENT or -y_min > WIN_DESCENT:
        raise SystemExit("growth reaches %d / %d, beyond the clipping bounds %d / -%d" % (y_max, y_min, WIN_ASCENT, WIN_DESCENT))
    panose = Panose()
    for field in ("bFamilyType", "bSerifStyle", "bWeight", "bProportion", "bContrast", "bStrokeVariation", "bArmStyle", "bLetterForm", "bMidline", "bXHeight"):
        setattr(panose, field, 0)
    panose.bFamilyType, panose.bProportion = 2, 9  # Latin text, monospaced
    fb.setupOS2(
        version=4,
        sTypoAscender=ASCENDER,
        sTypoDescender=DESCENDER,
        sTypoLineGap=0,
        # one value for the whole family, generous enough to cover every cut's growth
        usWinAscent=WIN_ASCENT,
        usWinDescent=WIN_DESCENT,
        ulCodePageRange1=1,  # Latin 1
        sxHeight=X,
        sCapHeight=round(textura.CAPH * XHEIGHT / textura.X),
        xAvgCharWidth=W,
        fsSelection=((0x20 if is_bold else 0) | (0x01 if is_italic else 0) or 0x40) | 0x80,  # bold / italic / regular; use typo metrics
        usWeightClass=700 if is_bold else 400,
        panose=panose,
        achVendID="NCRO",
    )
    px = textura.PX
    # a clean 2 px underline, one pixel clear of the baseline; strikethrough through the middle of the x-height
    fb.setupPost(isFixedPitch=1, underlinePosition=-round(px), underlineThickness=round(2 * px))
    fb.font["OS/2"].yStrikeoutSize = round(2 * px)
    fb.font["OS/2"].yStrikeoutPosition = round(9 * px)
    fb.font["head"].macStyle |= (1 if is_bold else 0) | (2 if is_italic else 0)
    fb.font["head"].fontRevision = float(VERSION)
    unhinted(fb.font)
    style_attributes(fb.font, is_bold, is_italic)
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
