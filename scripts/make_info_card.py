#!/usr/bin/env python3
"""Generate Dimitris's animated terminal-style profile card."""

from __future__ import annotations

import html
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "info-card.svg"

ROWS = [
    ("Name", "Dimitris Vatistas"),
    ("Role", "Full Stack Developer & UI Designer"),
    ("Builds", "Web apps, mobile apps & product prototypes"),
    ("Stack", "TypeScript / React / Node / Express"),
    ("AI", "Python / Ollama / computer vision"),
    ("Mobile", "Swift / iOS / Kotlin / Android"),
    ("Focus", "Cipher / search / developer utilities"),
    ("Status", "Freelance / full-time / collaborations"),
    ("Site", "dvatistas.vercel.app"),
]


def animation(index: int) -> str:
    if os.getenv("STATIC") == "1":
        return ""

    delay = 0.12 + (index * 0.12)
    reveal = 0.36
    total = delay + reveal
    hold = delay / total
    return (
        f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{hold:.4f};1" '
        f'dur="{total:.3f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" values="-8 0;-8 0;0 0" '
        f'keyTimes="0;{hold:.4f};1" dur="{total:.3f}s" fill="freeze"/>'
    )


def main() -> None:
    width, height = 490, 430
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        ),
        '<title id="title">Terminal profile card for Dimitris Vatistas</title>',
        '<desc id="desc">Animated lines describe Dimitris as a full stack developer and UI designer.</desc>',
        '<rect x="0.5" y="0.5" width="489" height="429" rx="12" fill="#0d1117" stroke="#30363d"/>',
        '<circle cx="18" cy="20" r="4" fill="#ff5f56"/>',
        '<circle cx="32" cy="20" r="4" fill="#ffbd2e"/>',
        '<circle cx="46" cy="20" r="4" fill="#27c93f"/>',
        (
            '<text x="62" y="24" fill="#8b949e" font-size="11" '
            'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">vatistasdimitris01@github:~</text>'
        ),
        '<line x1="18" y1="42" x2="472" y2="42" stroke="#21262d"/>',
    ]

    for index, (label, value) in enumerate(ROWS):
        y = 72 + (index * 32)
        parts.append(f'<g opacity="1">{animation(index)}')
        parts.append(
            f'<text x="24" y="{y}" fill="#39d353" font-size="12" font-weight="600" '
            f'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">{html.escape(label)}</text>'
        )
        parts.append(
            f'<text x="112" y="{y}" fill="#c9d1d9" font-size="12" '
            f'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">{html.escape(value)}</text>'
        )
        parts.append("</g>")

    parts.extend(
        [
            '<line x1="18" y1="372" x2="472" y2="372" stroke="#21262d"/>',
            '<g opacity="1">',
            animation(len(ROWS)),
            (
                '<text x="24" y="398" fill="#8b949e" font-size="11" '
                'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">$ build --useful --polished --human</text>'
            ),
            (
                '<rect x="314" y="388" width="7" height="13" fill="#39d353">'
                '<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>'
                "</rect>"
                if os.getenv("STATIC") != "1"
                else '<rect x="314" y="388" width="7" height="13" fill="#39d353"/>'
            ),
            "</g>",
            "</svg>",
        ]
    )

    OUTPUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
