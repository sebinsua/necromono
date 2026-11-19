"""See the font the way a terminal draws it, without a terminal.

    python -m necromono.eyes                 # the preview sample plus a directory listing
    python -m necromono.eyes file.txt        # any text; ANSI colours are honoured
    some-command | python -m necromono.eyes -

Text is laid out on a cell grid and rasterised by Core Text, the engine Ghostty
uses on macOS, at the point size and pixel density of the real window. Fonts
are loaded straight from ./fonts, so nothing has to be installed first.

The grid follows Ghostty's rules: cell width is the advance rounded to whole
pixels, cell height is ascent + descent + line gap rounded, and every glyph is
drawn at a whole-pixel origin with greyscale antialiasing.
"""
import argparse
import math
import re
import sys
from pathlib import Path

import CoreText
import Quartz
from Foundation import NSURL, NSAttributedString

ROOT = Path(__file__).resolve().parent.parent

# The user's Ghostty theme (Abernathy), read from `ghostty +show-config`.
BG = "#111416"
FG = "#eeeeec"
PALETTE = [
    "#000000", "#cd0000", "#00cd00", "#cdcd00", "#1093f5", "#cd00cd", "#00cdcd", "#faebd7",
    "#404040", "#ff0000", "#00ff00", "#ffff00", "#11b5f6", "#ff00ff", "#00ffff", "#ffffff",
]  # fmt: skip

SGR = re.compile(r"\x1b\[([0-9;]*)m")
OTHER_ESCAPES = re.compile(r"\x1b\[[0-9;?]*[A-Za-ln-z]|\x1b\][^\x07]*\x07")


def rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def xterm(n):
    """Colour n of the 256-colour palette."""
    if n < 16:
        return rgb(PALETTE[n])
    if n < 232:
        n -= 16
        steps = [0, 95, 135, 175, 215, 255]
        return (steps[n // 36] / 255, steps[n // 6 % 6] / 255, steps[n % 6] / 255)
    v = (8 + (n - 232) * 10) / 255
    return (v, v, v)


def parse(text):
    """ANSI text -> rows of (char, colour, bold, dim, underline)."""
    text = OTHER_ESCAPES.sub("", text.replace("\r\n", "\n").expandtabs(8))
    rows, row = [], []
    fg, bold, dim, underline = rgb(FG), False, False, False
    pos = 0
    for m in list(SGR.finditer(text)) + [None]:
        chunk = text[pos : m.start() if m else len(text)]
        for ch in chunk:
            if ch == "\n":
                rows.append(row)
                row = []
            else:
                row.append((ch, fg, bold, dim, underline))
        if m is None:
            break
        pos = m.end()
        codes = [int(c) for c in m.group(1).split(";") if c] or [0]
        i = 0
        while i < len(codes):
            c = codes[i]
            if c == 0:
                fg, bold, dim, underline = rgb(FG), False, False, False
            elif c == 1:
                bold = True
            elif c == 2:
                dim = True
            elif c == 4:
                underline = True
            elif c == 22:
                bold = dim = False
            elif c == 24:
                underline = False
            elif 30 <= c <= 37:
                fg = rgb(PALETTE[c - 30])
            elif 90 <= c <= 97:
                fg = rgb(PALETTE[c - 90 + 8])
            elif c == 39:
                fg = rgb(FG)
            elif c == 38 and i + 2 < len(codes) and codes[i + 1] == 5:
                fg = xterm(codes[i + 2])
                i += 2
            elif c == 38 and i + 4 < len(codes) and codes[i + 1] == 2:
                fg = tuple(v / 255 for v in codes[i + 2 : i + 5])
                i += 4
            i += 1
    if row:
        rows.append(row)
    return rows


def load(path, px):
    descriptors = CoreText.CTFontManagerCreateFontDescriptorsFromURL(NSURL.fileURLWithPath_(str(path)))
    if not descriptors:
        raise SystemExit("could not load font: %s" % path)
    return CoreText.CTFontCreateWithFontDescriptor(descriptors[0], px, None)


def render(text, out, regular, bold=None, size=13.0, scale=2, zoom=1, pad=0):
    """Draw `text` as a terminal would. Returns (path, cell_w, cell_h)."""
    px = size * scale
    font_r = load(regular, px)
    font_b = load(bold, px) if bold and Path(bold).exists() else font_r
    ascent = CoreText.CTFontGetAscent(font_r)
    descent = CoreText.CTFontGetDescent(font_r)
    leading = CoreText.CTFontGetLeading(font_r)
    probe = CoreText.CTLineCreateWithAttributedString(NSAttributedString.alloc().initWithString_attributes_("0", {CoreText.kCTFontAttributeName: font_r}))
    advance = CoreText.CTLineGetTypographicBounds(probe, None, None, None)[0]
    cell_w = max(1, round(advance))
    cell_h = max(1, math.ceil(ascent + descent + leading))  # checked against a real Ghostty window: 33 px at 13pt x2
    baseline = round(descent + leading / 2)  # from the bottom of the cell

    rows = parse(text)
    cols = max((len(r) for r in rows), default=1)
    width, height = cols * cell_w + 2 * pad, len(rows) * cell_h + 2 * pad

    space = Quartz.CGColorSpaceCreateWithName(Quartz.kCGColorSpaceSRGB)
    ctx = Quartz.CGBitmapContextCreate(None, width, height, 8, width * 4, space, Quartz.kCGImageAlphaPremultipliedLast)
    Quartz.CGContextSetRGBFillColor(ctx, *rgb(BG), 1)
    Quartz.CGContextFillRect(ctx, Quartz.CGRectMake(0, 0, width, height))
    Quartz.CGContextSetShouldAntialias(ctx, True)
    Quartz.CGContextSetShouldSmoothFonts(ctx, False)  # greyscale, no LCD fattening
    Quartz.CGContextSetShouldSubpixelPositionFonts(ctx, False)
    Quartz.CGContextSetShouldSubpixelQuantizeFonts(ctx, False)

    for r, row in enumerate(rows):
        y = height - pad - (r + 1) * cell_h + baseline
        for c, (ch, fg, is_bold, is_dim, underline) in enumerate(row):
            if ch == " " and not underline:
                continue
            colour = Quartz.CGColorCreate(space, (*fg, 0.5 if is_dim else 1.0))
            attrs = {CoreText.kCTFontAttributeName: font_b if is_bold else font_r, CoreText.kCTForegroundColorAttributeName: colour}
            line = CoreText.CTLineCreateWithAttributedString(NSAttributedString.alloc().initWithString_attributes_(ch, attrs))
            x = pad + c * cell_w
            Quartz.CGContextSetTextPosition(ctx, x, y)
            CoreText.CTLineDraw(line, ctx)
            if underline:
                Quartz.CGContextSetRGBFillColor(ctx, *fg, 1)
                Quartz.CGContextFillRect(ctx, Quartz.CGRectMake(x, y - max(2, scale * 2), cell_w, max(1, scale)))

    image = Quartz.CGBitmapContextCreateImage(ctx)
    if zoom != 1:  # hard-edged enlargement, so individual pixels can be inspected
        zw, zh = width * zoom, height * zoom
        zctx = Quartz.CGBitmapContextCreate(None, zw, zh, 8, zw * 4, space, Quartz.kCGImageAlphaPremultipliedLast)
        Quartz.CGContextSetInterpolationQuality(zctx, Quartz.kCGInterpolationNone)
        Quartz.CGContextDrawImage(zctx, Quartz.CGRectMake(0, 0, zw, zh), image)
        image = Quartz.CGBitmapContextCreateImage(zctx)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dest = Quartz.CGImageDestinationCreateWithURL(NSURL.fileURLWithPath_(str(out)), "public.png", 1, None)
    Quartz.CGImageDestinationAddImage(dest, image, None)
    Quartz.CGImageDestinationFinalize(dest)
    return out, cell_w, cell_h


def listing(root=ROOT):
    """A directory listing coloured the way the user's `ls` (eza -al) colours
    it. Built here rather than by running eza, so the picture is reproducible
    and does not depend on what a subprocess is allowed to see."""
    import os
    import stat
    import time

    out = []
    for entry in sorted(os.scandir(root), key=lambda e: e.name.lstrip(".").lower()):
        st = entry.stat(follow_symlinks=False)
        mode = stat.filemode(st.st_mode)
        perms = "\x1b[1;%sm%s\x1b[0m" % ("34" if mode[0] == "d" else "37", mode[0] if mode[0] != "-" else ".")
        for ch in mode[1:]:
            perms += {"r": "\x1b[1;33mr", "w": "\x1b[1;31mw", "x": "\x1b[1;32mx"}.get(ch, "\x1b[2;37m-") + "\x1b[0m"
        size = "\x1b[2;37m  -\x1b[0m" if entry.is_dir() else "\x1b[1;32m%3d\x1b[0m" % min(st.st_size, 999)
        when = time.strftime("%d %b %H:%M", time.localtime(st.st_mtime))
        colour = "1;36" if entry.is_dir() else ("1;31" if st.st_mode & 0o111 else "0")
        out.append("%s@ %s \x1b[1;33m%s\x1b[0m \x1b[34m%s\x1b[0m \x1b[%sm%s\x1b[0m" % (perms, size, os.environ.get("USER", "user"), when, colour, entry.name))
    return "\n".join(out) + "\n"


def default_text():
    """The preview sample, then a prompt and a directory listing."""
    prompt = "\x1b[1;32m\u279c \x1b[0m \x1b[1;36mnecromono\x1b[0m "
    return (ROOT / "preview" / "sample.txt").read_text() + prompt + "\x1b[32mls\x1b[0m -al\n" + listing() + prompt + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source", nargs="?", help="text file, or - for stdin; default is the preview sample")
    ap.add_argument("--font", default="NecroMono-Regular", help="font file stem in ./fonts, or a path")
    ap.add_argument("--bold", default=None, help="bold font; default is the matching -Bold file")
    ap.add_argument("--size", type=float, default=13.0, help="point size (Ghostty's default is 13)")
    ap.add_argument("--scale", type=int, default=2, help="pixels per point: 2 on a Retina display")
    ap.add_argument("--zoom", type=int, default=1, help="enlarge the result N times with hard pixel edges")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    regular = Path(args.font) if "/" in args.font or args.font.endswith(".ttf") else ROOT / "fonts" / (args.font + ".ttf")
    bold = Path(args.bold) if args.bold else regular.with_name(regular.name.replace("-Regular", "-Bold"))
    if args.source == "-":
        text = sys.stdin.read()
    elif args.source:
        text = Path(args.source).read_text()
    else:
        text = default_text()
    out = args.out or ROOT / "proofs" / ("eyes-%s-%gpt.png" % (regular.stem, args.size))
    path, cw, ch = render(text, out, regular, bold if bold != regular else None, args.size, args.scale, args.zoom)
    print("%s  (cell %dx%d px at %gpt x%d)" % (path, cw, ch, args.size, args.scale))


if __name__ == "__main__":
    main()
