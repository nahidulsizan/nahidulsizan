#!/usr/bin/env python3
"""
render_heatmap_svg.py
------------------------
Reads data/contributions.json and renders a custom high-resolution SVG
contribution heatmap (contrib-heatmap.svg), styled to match the gold/
dark "Cipher Stack" theme, with month labels, weekday labels, a color
legend, and summary stats (total / current streak / longest streak / best day).

Usage:
    python scripts/render_heatmap_svg.py
"""

import os
import json
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "contributions.json")
OUT_PATH = os.path.join(BASE_DIR, "contrib-heatmap.svg")

BG = "#0d0d0d"
BORDER = "#2a2a2a"
TEXT_MUTED = "#8a8a8a"
TEXT_MAIN = "#cfcfcf"
GOLD = "#D4AF37"

# Level 0..4 color ramp (dark -> gold)
LEVEL_COLORS = ["#161616", "#3a2f0f", "#6b5417", "#a5821f", "#D4AF37"]

CELL = 11
GAP = 3
LEFT_PAD = 44
TOP_PAD = 56
RIGHT_PAD = 24
BOTTOM_PAD = 70

WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_week_grid(days):
    """Arrange days into GitHub-style columns (weeks) x rows (weekdays 0=Sun..6=Sat)."""
    parsed = []
    for d in days:
        try:
            dt = datetime.date.fromisoformat(d["date"])
        except Exception:
            continue
        parsed.append((dt, d.get("level", 0), d.get("count", 0)))
    parsed.sort(key=lambda x: x[0])
    if not parsed:
        return []

    first_date = parsed[0][0]
    # Align to the Sunday on/before the first date
    start_offset = (first_date.weekday() + 1) % 7  # python Mon=0 -> convert to Sun=0
    weeks = []
    week = [None] * 7
    day_index = 0
    cursor_weekday = start_offset

    for dt, level, count in parsed:
        weekday = (dt.weekday() + 1) % 7  # Sun=0..Sat=6
        if weekday == 0 and any(c is not None for c in week):
            weeks.append(week)
            week = [None] * 7
        week[weekday] = (dt, level, count)
    weeks.append(week)
    return weeks


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(payload):
    days = payload.get("days", [])
    weeks = build_week_grid(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * (CELL + GAP) + RIGHT_PAD
    height = TOP_PAD + 7 * (CELL + GAP) + BOTTOM_PAD

    # Month labels: mark the week where a new month starts
    month_labels = []
    last_month = None
    for wi, week in enumerate(weeks):
        for cell in week:
            if cell is None:
                continue
            dt = cell[0]
            if dt.month != last_month:
                month_labels.append((wi, MONTH_NAMES[dt.month - 1]))
                last_month = dt.month
            break

    cells_svg = []
    for wi, week in enumerate(weeks):
        for wd, cell in enumerate(week):
            x = LEFT_PAD + wi * (CELL + GAP)
            y = TOP_PAD + wd * (CELL + GAP)
            if cell is None:
                continue
            dt, level, count = cell
            level = max(0, min(level, 4))
            color = LEVEL_COLORS[level]
            title = f"{count} contribution{'s' if count != 1 else ''} on {dt.strftime('%b %d, %Y')}"
            cells_svg.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" ry="2.5" '
                f'fill="{color}" stroke="#000" stroke-width="0.5">'
                f'<title>{esc(title)}</title></rect>'
            )

    month_svg = []
    for wi, name in month_labels:
        x = LEFT_PAD + wi * (CELL + GAP)
        month_svg.append(f'<text x="{x}" y="{TOP_PAD - 12}" class="axis">{name}</text>')

    weekday_svg = []
    for wd, label in WEEKDAY_LABELS.items():
        y = TOP_PAD + wd * (CELL + GAP) + CELL - 1
        weekday_svg.append(f'<text x="{LEFT_PAD - 10}" y="{y}" class="axis" text-anchor="end">{label}</text>')

    total = payload.get("total_contributions", 0)
    current_streak = payload.get("current_streak", 0)
    longest_streak = payload.get("longest_streak", 0)
    best_day = payload.get("best_day") or {}
    best_day_str = ""
    if best_day.get("date"):
        try:
            bd = datetime.date.fromisoformat(best_day["date"])
            best_day_str = f'{best_day.get("count", 0)} on {bd.strftime("%b %d, %Y")}'
        except Exception:
            best_day_str = f'{best_day.get("count", 0)}'

    legend_x = width - RIGHT_PAD - (len(LEVEL_COLORS) * (CELL + GAP)) - 40
    legend_y = height - 26
    legend_cells = []
    for i, c in enumerate(LEVEL_COLORS):
        lx = legend_x + i * (CELL + GAP)
        legend_cells.append(f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')

    stats_y = height - 26
    stats = (
        f'<text x="{LEFT_PAD}" y="{stats_y}" class="stat">'
        f'<tspan fill="{GOLD}" font-weight="700">{total}</tspan> contributions &#183; '
        f'<tspan fill="{GOLD}" font-weight="700">{current_streak}</tspan>d current streak &#183; '
        f'<tspan fill="{GOLD}" font-weight="700">{longest_streak}</tspan>d longest streak'
        + (f' &#183; best: {esc(best_day_str)}' if best_day_str else '')
        + '</text>'
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" font-family="'JetBrains Mono','Fira Code',Consolas,monospace">
  <defs>
    <clipPath id="hmClip"><rect x="0" y="0" width="{width}" height="{height}" rx="14" ry="14"/></clipPath>
    <style>
      .axis {{ fill: {TEXT_MUTED}; font-size: 10px; }}
      .stat {{ fill: {TEXT_MAIN}; font-size: 12px; }}
      rect.cell {{ transition: opacity .2s; }}
    </style>
  </defs>
  <g clip-path="url(#hmClip)">
    <rect x="0" y="0" width="{width}" height="{height}" fill="{BG}"/>
    <rect x="0.75" y="0.75" width="{width-1.5}" height="{height-1.5}" rx="14" ry="14" fill="none" stroke="{BORDER}" stroke-width="1.5"/>
    <text x="{LEFT_PAD}" y="26" fill="{GOLD}" font-size="14" font-weight="700">Contribution Activity</text>
    {''.join(month_svg)}
    {''.join(weekday_svg)}
    {''.join(cells_svg)}
    {stats}
    {''.join(legend_cells)}
    <text x="{legend_x - 8}" y="{legend_y + CELL - 1}" class="axis" text-anchor="end">Less</text>
    <text x="{legend_x + len(LEVEL_COLORS)*(CELL+GAP) + 6}" y="{legend_y + CELL - 1}" class="axis">More</text>
  </g>
</svg>'''

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    if not os.path.exists(DATA_PATH):
        print(f"[!] {DATA_PATH} not found. Run fetch_contributions.py first.")
        raise SystemExit(1)

    print("[*] Loading contribution data ...")
    payload = load_data()

    print("[*] Rendering heatmap SVG ...")
    build_svg(payload)

    print(f"[✓] Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
