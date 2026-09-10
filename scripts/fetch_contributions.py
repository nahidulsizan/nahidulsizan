#!/usr/bin/env python3
"""
fetch_contributions.py
------------------------
Scrapes the public GitHub contribution calendar for a given username
(no API key / auth required — uses the same HTML fragment endpoint
GitHub profile pages use internally) and computes:
  - total contributions (last 12 months)
  - current streak
  - longest streak
  - best single day

Saves everything to data/contributions.json.

Usage:
    python scripts/fetch_contributions.py [username]
"""

import sys
import os
import json
import datetime

import requests
from bs4 import BeautifulSoup

GITHUB_USERNAME_DEFAULT = "nahidulsizan"
CALENDAR_URL = "https://github.com/users/{username}/contributions"
OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "contributions.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ProfileHeatmapBot/1.0; +https://github.com)"
}


def fetch_calendar_html(username: str) -> str:
    url = CALENDAR_URL.format(username=username)
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_calendar(html: str):
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub renders each day as <td class="ContributionCalendar-day" data-date="YYYY-MM-DD" data-level="N">
    cells = soup.select("td.ContributionCalendar-day")
    if cells:
        for td in cells:
            date_str = td.get("data-date")
            level = td.get("data-level")
            if date_str is None:
                continue
            count = 0
            tool_tip_id = td.get("id")
            days.append({
                "date": date_str,
                "level": int(level) if level is not None else 0,
                "_tooltip_id": tool_tip_id,
            })

        # counts live in matching <tool-tip for="tooltip-id">N contributions on ...</tool-tip>
        tooltips = soup.select("tool-tip")
        tip_map = {}
        for tip in tooltips:
            for_id = tip.get("for")
            if for_id:
                tip_map[for_id] = tip.get_text(strip=True)

        for d in days:
            text = tip_map.get(d.get("_tooltip_id"), "")
            count = extract_count(text)
            d["count"] = count
            d.pop("_tooltip_id", None)
    else:
        # Fallback: older <rect class="ContributionCalendar-day"> SVG format
        rects = soup.select("rect.ContributionCalendar-day, rect[data-date]")
        for rect in rects:
            date_str = rect.get("data-date")
            level = rect.get("data-level", 0)
            count_attr = rect.get("data-count")
            if date_str is None:
                continue
            days.append({
                "date": date_str,
                "level": int(level) if level else 0,
                "count": int(count_attr) if count_attr else 0,
            })

    days.sort(key=lambda d: d["date"])
    return days


def extract_count(text: str) -> int:
    """'5 contributions on January 1st' -> 5 ; 'No contributions on ...' -> 0"""
    text = text.strip().lower()
    if text.startswith("no contributions"):
        return 0
    parts = text.split()
    if parts and parts[0].isdigit():
        return int(parts[0])
    return 0


def compute_metrics(days):
    total = sum(d["count"] for d in days)

    # Longest streak (consecutive days with count > 0)
    longest = 0
    current_run = 0
    for d in days:
        if d["count"] > 0:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 0

    # Current streak = consecutive days with count > 0 ending at the most
    # recent day that actually has data (today may not be counted yet)
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            # Allow "today" to be zero without breaking the streak once
            if d is days[-1]:
                continue
            break

    best_day = max(days, key=lambda d: d["count"]) if days else None

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": best_day,
    }


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else GITHUB_USERNAME_DEFAULT

    print(f"[*] Fetching contribution calendar for '{username}' ...")
    try:
        html = fetch_calendar_html(username)
    except Exception as e:
        print(f"[!] Failed to fetch calendar: {e}")
        sys.exit(1)

    days = parse_calendar(html)
    if not days:
        print("[!] No contribution cells parsed — GitHub markup may have changed.")
        sys.exit(1)

    metrics = compute_metrics(days)

    payload = {
        "username": username,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_contributions": metrics["total_contributions"],
        "current_streak": metrics["current_streak"],
        "longest_streak": metrics["longest_streak"],
        "best_day": metrics["best_day"],
        "days": days,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"[✓] Parsed {len(days)} days | total={metrics['total_contributions']} "
          f"| current_streak={metrics['current_streak']} | longest_streak={metrics['longest_streak']}")
    print(f"[✓] Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
