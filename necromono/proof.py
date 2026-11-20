"""Render proof sheets from the built font: `python -m necromono.proof`.

Text is set by a real text engine (FreeType via Pillow) from the .ttf, so what
the sheet shows is what an editor will draw, overflow included.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BG, INK = "#0a0b0c", "#e7e3da"

SAMPLE = [
    "abcdefghijklm",
    "nopqrstuvwxyz",
    "ABCDEFGHIJKLM",
    "NOPQRSTUVWXYZ",
    "0123456789",
    "(){}[]<>/\\|!?",
    ".,:;'\"`-_=+*~^",
    "#$%&@",
]

CODE = [
    'fn word_counts(text: &str) -> HashMap<&str, usize> {',
    '    let mut counts = HashMap::new();',
    '    for word in text.split_whitespace() {',
    '        *counts.entry(word).or_insert(0) += 1;',
    '    }',
    '    counts',
    '}',
]


def sheet(font_path, out_path, sizes=(96, 40, 24, 16), lines=SAMPLE, line_height=1.5):
    pad = 90
    blocks = []
    width = 0
    for size in sizes:
        font = ImageFont.truetype(str(font_path), size)
        advance = font.getlength("n")
        h = int(len(lines) * size * line_height)
        blocks.append((size, font, h))
        width = max(width, int(advance * max(len(l) for l in lines)))
    img = Image.new("RGB", (width + 2 * pad, sum(h for _, _, h in blocks) + pad * (len(blocks) + 1)), BG)
    d = ImageDraw.Draw(img)
    y = pad
    for size, font, h in blocks:
        for i, line in enumerate(lines):
            d.text((pad, y + i * size * line_height), line, font=font, fill=INK)
        y += h + pad
    img.save(out_path)
    return out_path


if __name__ == "__main__":
    out = ROOT / "proofs"
    out.mkdir(exist_ok=True)
    fonts = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / "fonts").glob("necromono-*.ttf"))
    for font in fonts:
        print(sheet(font, out / (font.stem + "-glyphs.png"), sizes=(72,), line_height=1.5))
        # 1.45 is the font's own line height, i.e. what a terminal uses
        print(sheet(font, out / (font.stem + "-code.png"), sizes=(44, 24, 16, 13), lines=CODE, line_height=1.45))
