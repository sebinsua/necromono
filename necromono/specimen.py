"""Draw the specimen sheet: `python -m necromono.specimen` writes docs/specimen.png.

Everything on it is set by the same renderer used to check the font (eyes.py),
so the sheet shows what a terminal shows, not an idealised drawing.
"""
import tempfile
from pathlib import Path

from PIL import Image

from .eyes import BG, ROOT, render

B, I, DIM, R = "\x1b[1m", "\x1b[3m", "\x1b[2m", "\x1b[0m"
KEY, STR, NUM, FN = "\x1b[38;5;110m", "\x1b[38;5;180m", "\x1b[38;5;174m", "\x1b[38;5;252m"

BLOCKS = [
    (96, "NecroMono"),
    (22, DIM + "the black metal monospace font" + R),
    (30, "abcdefghijklm nopqrstuvwxyz\nABCDEFGHIJKLM NOPQRSTUVWXYZ\n0123456789  (){}[]<>  !?&@#$%"),
    (
        17,
        f"{DIM}{I}// every word is drawn as a small logo{R}\n"
        f"{KEY}fn{R} {FN}summon{R}(name: &{KEY}str{R}) -> Rite {{\n"
        f"    {KEY}let mut{R} cold = {NUM}666{R};\n"
        f"    {KEY}if{R} name != {STR}\"frost\"{R} && cold >= {NUM}0{R} {{\n"
        f"        cold += veil[{NUM}0{R}] * {NUM}2{R};\n"
        f"    }}\n"
        f"    Rite::new(name, cold)\n"
        f"}}",
    ),
    (24, "-> <- => == === != !== <= >= :: ++ -- |>"),
    (24, "&& || >> << // ---   * + # 0   † ‡ ⛧"),
    (24, f"Regular  {B}Bold{R}  {I}Italic{R}  {B}{I}Bold Italic{R}"),
    (20, "Motörhead  Mötley Crüe  Mgła  Queensrÿche  Blue Öyster Cult"),
]


def main():
    fonts = ROOT / "fonts"
    tmp = Path(tempfile.gettempdir())
    images = []
    for i, (size, text) in enumerate(BLOCKS):
        out, _, _ = render(text + "\n", tmp / ("necromono-specimen-%d.png" % i), fonts / "NecroMono-Regular.ttf", fonts / "NecroMono-Bold.ttf", size=size, scale=2, pad=int(size * 1.1))  # room for what leaves the line
        images.append(Image.open(out).convert("RGB"))
    margin, gap = 40, 0
    width = max(im.width for im in images) + 2 * margin
    height = sum(im.height for im in images) + gap * (len(images) - 1) + 2 * margin
    sheet = Image.new("RGB", (width, height), BG)
    y = margin
    for im in images:
        sheet.paste(im, (margin, y))
        y += im.height + gap
    out = ROOT / "docs" / "specimen.png"
    out.parent.mkdir(exist_ok=True)
    sheet.save(out)
    print("%s  (%dx%d)" % (out.relative_to(ROOT), width, height))


if __name__ == "__main__":
    main()
