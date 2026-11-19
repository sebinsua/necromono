"""Validate the built fonts with Font Bakery: `python -m necromono.validate`.

The four linked styles are checked together as one family and the display cut
on its own. Failures that are deliberate are listed in WAIVED with the reason,
and reported separately, so a real regression cannot hide among them.
"""
import collections
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAMILIES = {
    "NecroMono": ["Regular", "Bold", "Italic", "BoldItalic"],
    "NecroMono Display": ["Display"],
}
WAIVED = {
    "opentype/italic_angle": "The italics are deliberately upright: they are the overgrown cuts, not slanted ones.",
    "typoascender_exceeds_Agrave": "The line box is set to exactly 33 px at 13pt; accents and growth are meant to leave it.",
    "caps_vertically_centered": "Follows from the same pixel-fitted line box.",
    "contour_count": "The letters carry extra lines by design, so contour counts differ from ordinary fonts.",
    "opentype/monospace": "fontTools writes a compact hmtx (one metric) for a font whose advances are all equal.",
    "overlapping_path_segments": "Display cut only: an artefact of simplifying very dense outlines; it does not affect rendering.",
}


def run(family, styles):
    out = ROOT / "proofs" / ("fontbakery-%s.json" % family.replace(" ", ""))
    out.parent.mkdir(exist_ok=True)
    fonts = [str(ROOT / "fonts" / ("NecroMono-%s.ttf" % s)) for s in styles]
    subprocess.run([str(Path(sys.executable).parent / "fontbakery"), "check-universal", "--json", str(out), "-q", "-n", *fonts], capture_output=True)
    data = json.loads(out.read_text())
    found = collections.defaultdict(list)
    for section in data["sections"]:
        for check in section["checks"]:
            if check["result"] in ("FAIL", "ERROR", "FATAL", "WARN"):
                key = check["key"][1].split(":")[-1].rstrip(">")
                text = "; ".join(str(log["message"].get("message") if isinstance(log["message"], dict) else log["message"]).replace("\n", " ")[:200] for log in check["logs"] if log["status"] != "PASS")
                found[(check["result"], key)].append(((check.get("filename") or "").split("/")[-1], text))
    return data["result"], found


def main():
    bad = 0
    for family, styles in FAMILIES.items():
        totals, found = run(family, styles)
        print("\n%s: %d passed, %d failed, %d warnings" % (family, totals.get("PASS", 0), totals.get("FAIL", 0) + totals.get("ERROR", 0), totals.get("WARN", 0)))
        for (result, key), items in sorted(found.items()):
            waived = key in WAIVED
            bad += 0 if waived else (result != "WARN")
            files = ", ".join(sorted({f.replace("NecroMono-", "").replace(".ttf", "") for f, _ in items if f})) or "family"
            print("  [%s%s] %s (%s)" % (result, ", waived" if waived else "", key, files))
            print("      %s" % (WAIVED[key] if waived else items[0][1]))
    print("\n%s" % ("No unwaived failures." if not bad else "%d unwaived failure(s)." % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
