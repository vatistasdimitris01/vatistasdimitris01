#!/usr/bin/env python3
"""Render the fetched GitHub contribution data as an animated SVG."""

from __future__ import annotations

import html
import json
import os
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "contrib-heatmap.svg"
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
WIDTH, HEIGHT = 860, 240
GRID_X, GRID_Y = 52, 76
CELL, GAP = 11, 3
STEP = CELL + GAP


def cell_animation(delay: float) -> str:
    if os.getenv("STATIC") == "1":
        return ""

    reveal = 0.34
    if delay == 0:
        return (
            f'<animate attributeName="opacity" from="0" to="1" dur="{reveal:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 -8" to="0 0" '
            f'dur="{reveal:.2f}s" fill="freeze"/>'
        )

    total = delay + reveal
    hold = delay / total
    return (
        f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{hold:.4f};1" '
        f'dur="{total:.3f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 -8;0 -8;0 0" '
        f'keyTimes="0;{hold:.4f};1" dur="{total:.3f}s" fill="freeze"/>'
    )


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    days = sorted(payload["days"], key=lambda item: item["date"])
    if not days:
        raise RuntimeError("Contribution data contains no days")

    start = date.fromisoformat(days[0]["date"])
    stats = payload["stats"]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">'
        ),
        '<title id="title">Animated GitHub contribution heatmap for vatistasdimitris01</title>',
        (
            f'<desc id="desc">{stats["total"]:,} contributions in the last year, '
            f'with a longest streak of {stats["longest_streak"]} days.</desc>'
        ),
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        (
            '<text x="24" y="31" fill="#c9d1d9" font-size="14" font-weight="600" '
            'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">'
            '<tspan fill="#39d353">vatistasdimitris01</tspan><tspan fill="#8b949e"> / contribution activity</tspan></text>'
        ),
    ]

    month_positions: list[tuple[int, str]] = []
    seen_months: set[str] = set()
    for day in days:
        day_date = date.fromisoformat(day["date"])
        month_key = day_date.strftime("%Y-%m")
        if month_key in seen_months:
            continue
        seen_months.add(month_key)
        week = (day_date - start).days // 7
        month_positions.append((week, day_date.strftime("%b")))

    for week, label in month_positions:
        x = GRID_X + (week * STEP)
        if x < WIDTH - 28:
            parts.append(
                f'<text x="{x}" y="60" fill="#8b949e" font-size="10" '
                f'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">{label}</text>'
            )

    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = GRID_Y + (row * STEP) + 9
        parts.append(
            f'<text x="20" y="{y}" fill="#8b949e" font-size="9" '
            f'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">{label}</text>'
        )

    for day in days:
        day_date = date.fromisoformat(day["date"])
        week = (day_date - start).days // 7
        row = (day_date.weekday() + 1) % 7
        x = GRID_X + (week * STEP)
        y = GRID_Y + (row * STEP)
        level = max(0, min(int(day["level"]), len(PALETTE) - 1))
        delay = (week * 0.025) + (row * 0.035)
        count = int(day["count"])
        contribution_word = "contribution" if count == 1 else "contributions"
        tooltip = html.escape(f"{count} {contribution_word} on {day_date.isoformat()}")
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[level]}" opacity="1">{cell_animation(delay)}<title>{tooltip}</title></rect>'
        )

    parts.extend(
        [
            (
                f'<text x="24" y="203" fill="#c9d1d9" font-size="12" '
                f'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">'
                f'{stats["total"]:,} contributions in the last year</text>'
            ),
            (
                f'<text x="24" y="224" fill="#8b949e" font-size="10" '
                f'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">'
                f'Current streak {stats["current_streak"]}d  |  Longest {stats["longest_streak"]}d  |  '
                f'Best day {stats["best_day_count"]} on {stats["best_day"]}</text>'
            ),
            (
                '<text x="670" y="203" fill="#8b949e" font-size="10" '
                'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">Less</text>'
            ),
        ]
    )

    legend_x = 700
    for index, color in enumerate(PALETTE):
        parts.append(
            f'<rect x="{legend_x + (index * 17)}" y="193" width="11" height="11" rx="2.5" fill="{color}"/>'
        )
    parts.append(
        '<text x="790" y="203" fill="#8b949e" font-size="10" '
        'font-family="SFMono-Regular,Consolas,Liberation Mono,monospace">More</text>'
    )
    parts.append("</svg>")

    OUTPUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
