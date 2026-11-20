"""Draw the specimen sheet: `python -m necromono.specimen` writes docs/characters.png.

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
    (96, "necromono"),
    (22, DIM + "the black metal monospace font" + R),
    (30, "abcdefghijklm nopqrstuvwxyz\nABCDEFGHIJKLM NOPQRSTUVWXYZ\n0123456789  (){}[]<>  !?&@#$%"),
    (
        17,
        f"{DIM}{I}// count how often each word appears{R}\n"
        f"{KEY}fn{R} {FN}word_counts{R}(text: &{KEY}str{R}) -> HashMap<&{KEY}str{R}, {KEY}usize{R}> {{\n"
        f"    {KEY}let mut{R} counts = HashMap::new();\n"
        f"    {KEY}for{R} word {KEY}in{R} text.split_whitespace() {{\n"
        f"        *counts.entry(word).or_insert({NUM}0{R}) += {NUM}1{R};\n"
        f"    }}\n"
        f"    counts\n"
        f"}}",
    ),
    (24, "-> <- => == === != !== <= >= :: ++ -- |>"),
    (24, "&& || >> << // ---   * + # 0   † ‡ ⛧"),
    (24, f"Regular  {B}Bold{R}  {I}Italic{R}  {B}{I}Bold Italic{R}"),
    (20, "àéîõü ÀÉÎÕÜ  çñßøåł  café naïve señor fjörd"),
]


SCREEN = f"""{KEY}use{R} std::collections::HashMap;

{DIM}{I}// count how often each word appears{R}
{KEY}fn{R} {FN}word_counts{R}(text: &{KEY}str{R}) -> HashMap<&{KEY}str{R}, {KEY}usize{R}> {{
    {KEY}let mut{R} counts = HashMap::new();
    {KEY}for{R} word {KEY}in{R} text.split_whitespace() {{
        *counts.entry(word).or_insert({NUM}0{R}) += {NUM}1{R};
    }}
    counts
}}

{KEY}fn{R} {FN}main{R}() {{
    {KEY}let{R} counts = word_counts({STR}"the quick brown fox"{R});
    {KEY}if{R} counts.len() != {NUM}4{R} || counts[{STR}"fox"{R}] >= {NUM}2{R} {{
        eprintln!({STR}"unexpected: {{:?}}"{R}, counts);
    }}
}}
"""


def screenshot():
    """A plain source file, as an editor or terminal shows it."""
    fonts = ROOT / "fonts"
    tmp = Path(tempfile.gettempdir()) / "necromono-screen.png"
    # Drawn at twice the size it is shown at, so each font pixel is a whole number of
    # screen pixels on both Retina and ordinary displays. The README shows it at half its width.
    render(SCREEN, tmp, fonts / "necromono-Regular.ttf", fonts / "necromono-Bold.ttf", size=26, scale=2, pad=72)
    out = ROOT / "docs" / "code.png"
    out.parent.mkdir(exist_ok=True)
    Image.open(tmp).convert("RGB").save(out)
    print("%s  (%dx%d)" % ((out.relative_to(ROOT),) + Image.open(out).size))


def stamp_readme():
    """GitHub serves README images from a cache keyed on their address, and can
    go on showing an old picture after a new one is pushed. So the address
    carries a short fingerprint of the picture: a new picture is a new address."""
    import hashlib
    import re

    readme = ROOT / "README.md"
    text = readme.read_text()
    for name in ("code", "characters"):
        mark = hashlib.sha256((ROOT / "docs" / (name + ".png")).read_bytes()).hexdigest()[:8]
        text = re.sub(r"docs/%s\.png(\?v=[0-9a-f]+)?" % name, "docs/%s.png?v=%s" % (name, mark), text)
    readme.write_text(text)


def main():
    screenshot()
    fonts = ROOT / "fonts"
    tmp = Path(tempfile.gettempdir())
    images = []
    for i, (size, text) in enumerate(BLOCKS):
        out, _, _ = render(text + "\n", tmp / ("necromono-specimen-%d.png" % i), fonts / "necromono-Regular.ttf", fonts / "necromono-Bold.ttf", size=size, scale=2, pad=int(size * 1.1))  # room for what leaves the line
        images.append(Image.open(out).convert("RGB"))
    margin, gap = 40, 0
    width = max(im.width for im in images) + 2 * margin
    height = sum(im.height for im in images) + gap * (len(images) - 1) + 2 * margin
    sheet = Image.new("RGB", (width, height), BG)
    y = margin
    for im in images:
        sheet.paste(im, (margin, y))
        y += im.height + gap
    out = ROOT / "docs" / "characters.png"
    out.parent.mkdir(exist_ok=True)
    sheet.save(out)
    print("%s  (%dx%d)" % (out.relative_to(ROOT), width, height))
    stamp_readme()


if __name__ == "__main__":
    main()
