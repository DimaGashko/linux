#!/usr/bin/env python3
"""Build the panel font from editable, rounded-stroke SVG sources."""

import html
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import SVGPath
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parent
FAMILY = "Custom System Icons"
EM = 1000
SCALE = EM / 24


def main():
    entries = json.loads((ROOT / "manifest.json").read_text())
    build = ROOT / "build"
    dist = ROOT / "dist"
    build.mkdir(exist_ok=True)
    dist.mkdir(exist_ok=True)
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    cmap = {}

    for entry in entries:
        name = entry["name"]
        codepoint = int(entry["codepoint"], 16)

        if name in glyphs or codepoint in cmap:
            raise ValueError(f"Duplicate icon: {entry}")

        source = ROOT / entry["source"]
        outline = build / f"{name}.svg"
        actions = (
            "select-all:all;object-stroke-to-path;"
            f"export-filename:{outline};export-plain-svg;export-do"
        )
        result = subprocess.run(
            ["inkscape", str(source), "--batch-process", f"--actions={actions}"],
            capture_output=True, text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Inkscape failed for {name}: {result.stderr}")

        pen = TTGlyphPen(None)
        quadratic = Cu2QuPen(pen, max_err=0.5, reverse_direction=True)
        transformed = TransformPen(quadratic, (SCALE, 0, 0, -SCALE, 0, 800))
        SVGPath(str(outline)).draw(transformed)
        glyphs[name] = pen.glyph()
        cmap[codepoint] = name

    builder = FontBuilder(EM, isTTF=True)
    builder.setupGlyphOrder(list(glyphs))
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    # Keep the SVG origin: the badge's left bearing positions it over the icon.
    builder.setupHorizontalMetrics({
        name: (EM, getattr(glyph, "xMin", 0)) for name, glyph in glyphs.items()
    })
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({
        "familyName": FAMILY,
        "styleName": "Regular",
        "uniqueFontIdentifier": "CustomSystemIcons-Regular-1.0",
        "fullName": f"{FAMILY} Regular",
        "psName": "CustomSystemIcons-Regular",
        "version": "Version 1.000",
        "copyright": "Original artwork MIT; OpenAI and @ glyphs Fonticons CC BY 4.0. See icons/NOTICE.md.",
    })
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    builder.setupPost()
    builder.setupMaxp()
    builder.font["head"].created = 3786912000
    builder.font["head"].modified = 3786912000
    font_path = dist / "CustomSystemIcons.ttf"
    builder.save(font_path)

    with TTFont(font_path) as font:
        assert font.getBestCmap() == cmap
        glyph_set = font.getGlyphSet()

        for name in cmap.values():
            bounds = BoundsPen(glyph_set)
            glyph_set[name].draw(bounds)
            assert bounds.bounds is not None, f"Empty glyph: {name}"
            x0, y0, x1, y1 = bounds.bounds
            assert 0 <= x0 < x1 <= EM and -200 <= y0 < y1 <= 800, (name, bounds.bounds)

    make_preview(entries, dist)
    print(f"Built and validated {len(cmap)} glyphs: {font_path}")


def make_preview(entries, dist):
    columns = 5
    rows = (len(entries) + columns - 1) // columns
    width, height = 1000, 80 + rows * 106
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#101619"/>',
        '<text x="24" y="36" font-family="sans-serif" font-size="22" fill="#edf4f6">Custom System Icons</text>',
    ]

    for index, entry in enumerate(entries):
        x, y = 24 + index % columns * 195, 65 + index // columns * 106
        root = ET.parse(ROOT / entry["source"]).getroot()
        body = "".join(ET.tostring(child, encoding="unicode") for child in root)
        body = body.replace("#000", "#edf4f6")
        style = " ".join(
            f'{key}="{html.escape(value.replace("#000", "#edf4f6"), quote=True)}"'
            for key, value in root.attrib.items()
            if key in ("fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin")
        )
        svg.append(f'<g transform="translate({x},{y}) scale(1.5)" {style}>{body}</g>')
        svg.append(f'<text x="{x}" y="{y+61}" font-family="sans-serif" font-size="13" fill="#edf4f6">{html.escape(entry["name"])}</text>')
        svg.append(f'<text x="{x}" y="{y+80}" font-family="monospace" font-size="11" fill="#91a5ad">U+{entry["codepoint"]}</text>')

    svg.append('</svg>')
    (dist / "preview.svg").write_text("\n".join(svg) + "\n")


if __name__ == "__main__":
    main()
