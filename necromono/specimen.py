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


SCREEN = f"""{B}\x1b[32m\u279c{R}  {B}\x1b[36mwordcount{R} cat src/main.rs
{KEY}use{R} std::collections::HashMap;

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

{B}\x1b[32m\u279c{R}  {B}\x1b[36mwordcount{R} cargo test
{DIM}running 3 tests{R}
test counts_repeated_words ... \x1b[32mok{R}
test ignores_extra_whitespace ... \x1b[32mok{R}
test empty_input ... \x1b[31m{B}FAILED{R}
"""


def screenshot():
    """A terminal window's worth of real use, at real size."""
    fonts = ROOT / "fonts"
    tmp = Path(tempfile.gettempdir()) / "necromono-screen.png"
    # Drawn at twice the size it is shown at, so each font pixel is a whole number of
    # screen pixels on both Retina and ordinary displays. The README shows it at half its width.
    render(SCREEN, tmp, fonts / "necromono-Regular.ttf", fonts / "necromono-Bold.ttf", size=26, scale=2, pad=72)
    out = ROOT / "docs" / "screenshot.png"
    out.parent.mkdir(exist_ok=True)
    Image.open(tmp).convert("RGB").save(out)
    print("%s  (%dx%d)" % ((out.relative_to(ROOT),) + Image.open(out).size))


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
    out = ROOT / "docs" / "specimen.png"
    out.parent.mkdir(exist_ok=True)
    sheet.save(out)
    print("%s  (%dx%d)" % (out.relative_to(ROOT), width, height))


if __name__ == "__main__":
    main()
