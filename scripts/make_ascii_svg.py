#!/usr/bin/env python3
"""Convert Dimitris's GitHub avatar into an animated ASCII portrait SVG."""

from __future__ import annotations

import argparse
import html
import os
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = "https://github.com/vatistasdimitris01.png?size=1000"
RAMP = "@%#*+=-:. "


def load_image(source: str) -> Image.Image:
    if source.startswith(("https://", "http://")):
        response = requests.get(
            source,
            headers={"User-Agent": "vatistasdimitris01-profile-readme"},
            timeout=30,
        )
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")

    return Image.open(source).convert("RGBA")


def isolate_subject(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    if alpha.getextrema()[0] < 250:
        canvas = Image.new("RGBA", image.size, "white")
        canvas.alpha_composite(image)
        rgb = canvas.convert("RGB")
    else:
        rgb = image.convert("RGB")
        corners = [
            rgb.getpixel((0, 0)),
            rgb.getpixel((rgb.width - 1, 0)),
            rgb.getpixel((0, rgb.height - 1)),
            rgb.getpixel((rgb.width - 1, rgb.height - 1)),
        ]
        corner_brightness = sum(sum(color) for color in corners) / (len(corners) * 3)
        if corner_brightness < 96:
            for point in (
                (0, 0),
                (rgb.width - 1, 0),
                (0, rgb.height - 1),
                (rgb.width - 1, rgb.height - 1),
            ):
                ImageDraw.floodfill(rgb, point, (255, 255, 255), thresh=24)

    white = Image.new("RGB", rgb.size, "white")
    difference = ImageChops.difference(rgb, white).convert("L")
    subject_mask = difference.point(lambda value: 255 if value > 12 else 0)
    bounds = subject_mask.getbbox()
    if not bounds:
        raise ValueError("The source image does not contain a visible subject")

    left, top, right, bottom = bounds
    padding = max(8, int(max(right - left, bottom - top) * 0.035))
    crop = (
        max(0, left - padding),
        max(0, top - padding),
        min(rgb.width, right + padding),
        min(rgb.height, bottom + padding),
    )
    return rgb.crop(crop)


def to_ascii_rows(image: Image.Image, columns: int) -> list[str]:
    grayscale = ImageOps.grayscale(image)
    grayscale = ImageOps.autocontrast(grayscale, cutoff=1)
    grayscale = ImageEnhance.Contrast(grayscale).enhance(1.25)

    rows = max(1, round((grayscale.height / grayscale.width) * columns * 0.5))
    sample = grayscale.resize((columns, rows), Image.Resampling.LANCZOS)

    output: list[str] = []
    for y in range(rows):
        chars = []
        for x in range(columns):
            brightness = sample.getpixel((x, y))
            index = round((brightness / 255) * (len(RAMP) - 1))
            chars.append(RAMP[index])
        output.append("".join(chars))
    return output


def render_svg(rows: list[str], output: Path, static: bool) -> None:
    width, height = 370, 430
    left, right = 18, 18
    content_top, content_bottom = 54, 18
    usable_width = width - left - right
    usable_height = height - content_top - content_bottom
    columns = max(len(row) for row in rows)
    font_size = min(usable_width / (columns * 0.61), usable_height / len(rows))
    line_height = font_size * 1.02
    art_height = line_height * len(rows)
    first_baseline = content_top + ((usable_height - art_height) / 2) + font_size
    wipe_width = usable_width + 4

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        ),
        "<title id=\"title\">Animated ASCII portrait of Dimitris Vatistas</title>",
        "<desc id=\"desc\">A terminal-style portrait that types itself from top to bottom.</desc>",
        '<rect x="0.5" y="0.5" width="369" height="429" rx="12" fill="#0d1117" stroke="#30363d"/>',
        '<circle cx="18" cy="20" r="4" fill="#ff5f56"/>',
        '<circle cx="32" cy="20" r="4" fill="#ffbd2e"/>',
        '<circle cx="46" cy="20" r="4" fill="#27c93f"/>',
        (
            '<text x="62" y="24" fill="#8b949e" font-size="11" '
            'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">avatar.png -&gt; ascii.svg</text>'
        ),
        "<defs>",
    ]

    for index, _ in enumerate(rows):
        y = first_baseline + (index * line_height)
        parts.append(f'<clipPath id="row-{index}"><rect x="{left}" y="{y - font_size:.2f}" width="{wipe_width:.2f}" height="{line_height + 2:.2f}">')
        if not static:
            delay = index * 0.045
            duration = 0.30
            total = delay + duration
            if delay == 0:
                parts.append(
                    f'<animate attributeName="width" from="0" to="{wipe_width:.2f}" dur="{duration:.2f}s" fill="freeze"/>'
                )
            else:
                hold = delay / total
                parts.append(
                    f'<animate attributeName="width" values="0;0;{wipe_width:.2f}" '
                    f'keyTimes="0;{hold:.4f};1" dur="{total:.3f}s" fill="freeze"/>'
                )
        parts.append("</rect></clipPath>")
    parts.append("</defs>")

    for index, row in enumerate(rows):
        y = first_baseline + (index * line_height)
        escaped_row = html.escape(row)
        parts.append(
            f'<text x="{left}" y="{y:.2f}" fill="#c9d1d9" font-size="{font_size:.2f}" '
            'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace" '
            f'xml:space="preserve" clip-path="url(#row-{index})">{escaped_row}</text>'
        )
        if not static:
            delay = index * 0.045
            duration = 0.30
            parts.append(
                f'<rect x="{left}" y="{y - font_size + 1:.2f}" width="3" height="{font_size:.2f}" fill="#39d353" opacity="0">'
                f'<animate attributeName="x" from="{left}" to="{left + wipe_width - 3:.2f}" begin="{delay:.3f}s" dur="{duration:.2f}s" fill="freeze"/>'
                f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.08;0.88;1" begin="{delay:.3f}s" dur="{duration:.2f}s" fill="freeze"/>'
                "</rect>"
            )

    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Local image path or image URL")
    parser.add_argument("--columns", type=int, default=72, help="Number of ASCII columns")
    parser.add_argument("--output", type=Path, default=ROOT / "ascii-portrait.svg")
    args = parser.parse_args()

    if args.columns < 20:
        parser.error("--columns must be at least 20")

    image = isolate_subject(load_image(args.source))
    rows = to_ascii_rows(image, args.columns)
    render_svg(rows, args.output, static=os.getenv("STATIC") == "1")
    print(f"Wrote {args.output} ({len(rows)} rows x {args.columns} columns)")


if __name__ == "__main__":
    main()
