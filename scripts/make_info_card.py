#!/usr/bin/env python3
"""
make_info_card.py
------------------
Generates info-card.svg — a neofetch/terminal-style "system info" card,
sized to visually pair with hxni-ascii.svg, with gold key labels, silver
value labels, and per-line staggered fade-in animation.

Usage:
    python scripts/make_info_card.py [info-card.svg]
"""

import sys

GOLD = "#D4AF37"
SILVER = "#C9C9C9"
DIM = "#7a7a7a"
BG = "#0d0d0d"
BORDER = "#2a2a2a"

WIDTH = 640
# Match the ASCII card's height (TITLE_H + PAD_Y + ROWS*CHAR_H + 18 ≈ 706)
HEIGHT = 706
TITLE_H = 34
PAD_X = 30
LINE_H = 30
START_Y = TITLE_H + 46

FIELDS = [
    ("OS", "GitHub OS 24.04 LTS x86_64"),
    ("Host", "nahidulsizan / Portfolio Server"),
    ("Role", "BS in Computer Science @ UofR"),
    ("Title", "Full-Stack Web Developer"),
    ("Certs", "CISCO Cybersecurity | Google IT Support Professional"),
    ("Location", "Regina, Saskatchewan, Canada"),
    ("Frontend", "HTML · Tailwind CSS · Vanilla JS"),
    ("Backend", "Node.js · Express · MySQL · MongoDB · PHP"),
    ("Tools", "GitHub · VS Code · Wireshark · Kali · Parrot · VMware"),
    ("Portfolio", "webdev.cs.uregina.ca/~nsx513"),
    ("LinkedIn", "in/nahidul-islam-sizan-091280343"),
    ("GitHub", "github.com/nahidulsizan"),
    ("Email", "nahidulsizan@gmail.com"),
]


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def color_swatches(x: int, y: int) -> str:
    colors = ["#ff5f56", "#ffbd2e", "#27c93f", "#4fc3f7", "#b388ff",
              "#ff8a80", "#ffd54f", "#80cbc4"]
    out = []
    for i, c in enumerate(colors):
        out.append(f'<rect x="{x + i*22}" y="{y}" width="16" height="16" rx="3" fill="{c}"/>')
    return "".join(out)


def build_svg(out_path: str):
    n = len(FIELDS)
    total_reveal = 1.6
    stagger = total_reveal / n

    style_lines = []
    for i in range(n + 1):  # +1 for the color swatch row
        delay = round(i * stagger, 3)
        style_lines.append(f".row{i}{{animation:fin .4s ease-out {delay}s both;}}")

    rows_svg = []
    for i, (key, val) in enumerate(FIELDS):
        y = START_Y + i * LINE_H
        rows_svg.append(
            f'<g class="row{i}">'
            f'<text x="{PAD_X}" y="{y}" class="key">{esc(key)}</text>'
            f'<text x="{PAD_X + 128}" y="{y}" class="val">{esc(val)}</text>'
            f'</g>'
        )

    divider_y = START_Y + n * LINE_H - 6
    swatch_row_idx = n
    swatches_y = divider_y + 22

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}"
     viewBox="0 0 {WIDTH} {HEIGHT}" font-family="'JetBrains Mono','Fira Code',Consolas,monospace">
  <defs>
    <clipPath id="infoClip">
      <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" rx="14" ry="14"/>
    </clipPath>
    <style>
      @keyframes fin {{
        0%   {{ opacity: 0; transform: translateY(4px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
      }}
      .term-bg {{ fill: {BG}; }}
      .term-border {{ fill: none; stroke: {BORDER}; stroke-width: 1.5; }}
      .title {{ fill: #cfcfcf; font-size: 13px; font-weight: 600; letter-spacing: .5px; }}
      .key {{ fill: {GOLD}; font-size: 13px; font-weight: 700; }}
      .val {{ fill: {SILVER}; font-size: 13px; }}
      .dim {{ fill: {DIM}; font-size: 12px; }}
      {' '.join(style_lines)}
    </style>
  </defs>

  <g clip-path="url(#infoClip)">
    <rect class="term-bg" x="0" y="0" width="{WIDTH}" height="{HEIGHT}"/>
    <rect class="term-border" x="0.75" y="0.75" width="{WIDTH-1.5}" height="{HEIGHT-1.5}" rx="14" ry="14"/>

    <rect x="0" y="0" width="{WIDTH}" height="{TITLE_H}" fill="#161616"/>
    <line x1="0" y1="{TITLE_H}" x2="{WIDTH}" y2="{TITLE_H}" stroke="{BORDER}" stroke-width="1"/>
    <circle cx="20" cy="{TITLE_H/2:.0f}" r="5.5" fill="#ff5f56"/>
    <circle cx="38" cy="{TITLE_H/2:.0f}" r="5.5" fill="#ffbd2e"/>
    <circle cx="56" cy="{TITLE_H/2:.0f}" r="5.5" fill="#27c93f"/>
    <text class="title" x="{WIDTH/2}" y="{TITLE_H/2+4.5:.0f}" text-anchor="middle">The Cipher Stack</text>

    {''.join(rows_svg)}

    <line x1="{PAD_X}" y1="{divider_y}" x2="{WIDTH-PAD_X}" y2="{divider_y}" stroke="{BORDER}" stroke-width="1"/>
    <g class="row{swatch_row_idx}">
      <text x="{PAD_X}" y="{swatches_y}" class="dim">Palette</text>
      {color_swatches(PAD_X, swatches_y + 12)}
    </g>
  </g>
</svg>'''

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    print("[*] Building info-card.svg ...")
    build_svg(out)
    print(f"[✓] Saved: {out}")


if __name__ == "__main__":
    main()
