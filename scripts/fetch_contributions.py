#!/usr/bin/env python3
"""Fetch public GitHub contribution-calendar data without an API token."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
USERNAME = "vatistasdimitris01"
OUTPUT = ROOT / "data" / "contributions.json"
CONTRIBUTION_RE = re.compile(r"([\d,]+)\s+contribution")
SUMMARY_RE = re.compile(r"([\d,]+)\s+contributions?\s+in the last year")


def parse_count(text: str) -> int:
    match = CONTRIBUTION_RE.search(text)
    return int(match.group(1).replace(",", "")) if match else 0


def calculate_stats(days: list[dict[str, int | str]]) -> dict[str, int | str | None]:
    counts = {date.fromisoformat(str(day["date"])): int(day["count"]) for day in days}
    ordered_dates = sorted(counts)

    longest_streak = 0
    running_streak = 0
    for day_date in ordered_dates:
        if counts[day_date] > 0:
            running_streak += 1
            longest_streak = max(longest_streak, running_streak)
        else:
            running_streak = 0

    current_streak = 0
    cursor = min(datetime.now(timezone.utc).date(), ordered_dates[-1])
    if counts.get(cursor, 0) == 0:
        cursor -= timedelta(days=1)
    while counts.get(cursor, 0) > 0:
        current_streak += 1
        cursor -= timedelta(days=1)

    best = max(days, key=lambda day: int(day["count"]))
    return {
        "total": sum(int(day["count"]) for day in days),
        "active_days": sum(1 for day in days if int(day["count"]) > 0),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best["date"],
        "best_day_count": int(best["count"]),
    }


def main() -> None:
    url = f"https://github.com/users/{USERNAME}/contributions"
    response = requests.get(
        url,
        headers={"User-Agent": f"{USERNAME}-profile-readme"},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    tooltips = {
        tooltip.get("for"): tooltip.get_text(" ", strip=True)
        for tooltip in soup.select("tool-tip[for]")
    }
    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        cell_id = cell.get("id")
        if cell_id not in tooltips:
            raise RuntimeError(f"GitHub returned a contribution cell without a tooltip: {cell_id}")
        tooltip = tooltips[cell_id]
        days.append(
            {
                "date": cell["data-date"],
                "count": parse_count(tooltip),
                "level": int(cell.get("data-level", 0)),
            }
        )

    if not days:
        raise RuntimeError("GitHub returned no contribution-calendar cells")

    summary = soup.select_one("#js-contribution-activity-description")
    summary_match = SUMMARY_RE.search(summary.get_text(" ", strip=True)) if summary else None
    parsed_total = sum(int(day["count"]) for day in days)
    if summary_match:
        summary_total = int(summary_match.group(1).replace(",", ""))
        if parsed_total != summary_total:
            raise RuntimeError(
                f"Parsed {parsed_total:,} contributions but GitHub reports {summary_total:,}"
            )

    days.sort(key=lambda day: str(day["date"]))
    monthly_totals: defaultdict[str, int] = defaultdict(int)
    for day in days:
        monthly_totals[str(day["date"])[:7]] += int(day["count"])

    payload = {
        "username": USERNAME,
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "stats": calculate_stats(days),
        "monthly_totals": dict(sorted(monthly_totals.items())),
        "days": days,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(days)} days and {payload['stats']['total']:,} contributions")


if __name__ == "__main__":
    main()
