#!/usr/bin/env python3
"""
make_ascii_svg.py
------------------
Converts source-prepped.png into hxni-ascii.svg: a gold monospace ASCII-art
portrait rendered inside a dark terminal card, with a line-by-line reveal
animation (CSS @keyframes + staggered delays, safe for GitHub's camo image
proxy which strips <script> but keeps <style>/SMIL).

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png] [hxni-ascii.svg]
"""

import sys
from PIL import Image
import numpy as np

# Brightness -> character density ramp (dark -> light)
RAMP = " .:-=+*cs#%@"

# Grid dimensions (columns x rows) — tuned for readability at width=370
COLS = 90
ROWS = 60

GOLD = "#D4AF37"
GOLD_DIM = "#8a7226"
BG = "#0d0d0d"
BORDER = "#2a2a2a"

CHAR_W = 6.0
CHAR_H = 11.0
PAD_X = 22
PAD_Y = 46
TITLE_H = 34


def image_to_ascii(img_path: str):
    img = Image.open(img_path).convert("RGBA")

    # Resize RGBA (not a flattened composite) so we keep the alpha mask —
    # this lets us tell "background" apart from "subject in shadow", which
    # would otherwise both collapse to the same blank character.
    small = img.resize((COLS, ROWS), Image.LANCZOS)
    arr = np.array(small, dtype=np.float32)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3] / 255.0

    gray = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]) / 255.0

    # Gamma-lift shadows so dark hair/clothing still reads as visible
    # texture instead of disappearing into the background.
    gray = np.power(gray, 0.6)

    ramp_len = len(RAMP)
    subject_ramp = RAMP[1:]  # never let subject pixels collapse to blank
    subject_len = len(subject_ramp)

    rows = []
    for r in range(ROWS):
        line = []
        for c in range(COLS):
            a = alpha[r, c]
            if a < 0.15:
                line.append(" ")
                continue
            v = gray[r, c]
            idx = min(int(v * subject_len), subject_len - 1)
            line.append(subject_ramp[idx])
        rows.append("".join(line))
    return rows


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(rows, out_path: str):
    width = PAD_X * 2 + COLS * CHAR_W
    height = TITLE_H + PAD_Y + ROWS * CHAR_H + 18

    n_lines = len(rows)
    total_reveal = 2.4  # seconds for full reveal
    stagger = total_reveal / max(n_lines, 1)

    style_lines = []
    for i in range(n_lines):
        delay = round(i * stagger, 3)
        style_lines.append(
            f".ln{i}{{animation:fin .45s ease-out {delay}s both;}}"
        )

    text_rows = []
    for i, row in enumerate(rows):
        y = TITLE_H + PAD_Y + i * CHAR_H
        text_rows.append(
            f'<text class="ln{i}" x="{PAD_X}" y="{y:.1f}" '
            f'xml:space="preserve">{esc(row)}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}"
     viewBox="0 0 {width:.0f} {height:.0f}" font-family="'JetBrains Mono','Fira Code',Consolas,monospace">
  <defs>
    <linearGradient id="goldFade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{GOLD}"/>
      <stop offset="100%" stop-color="{GOLD_DIM}"/>
    </linearGradient>
    <clipPath id="cardClip">
      <rect x="0" y="0" width="{width:.0f}" height="{height:.0f}" rx="14" ry="14"/>
    </clipPath>
    <style>
      @keyframes fin {{
        0%   {{ opacity: 0; transform: translateX(-4px); }}
        100% {{ opacity: 1; transform: translateX(0); }}
      }}
      @keyframes blinkCursor {{
        0%, 49% {{ opacity: 1; }}
        50%, 100% {{ opacity: 0; }}
      }}
      .term-bg {{ fill: {BG}; }}
      .term-border {{ fill: none; stroke: {BORDER}; stroke-width: 1.5; }}
      .dot {{ }}
      .title {{ fill: #cfcfcf; font-size: 13px; font-weight: 600; letter-spacing: .5px; }}
      text {{ font-size: 9.2px; fill: url(#goldFade); white-space: pre; }}
      .cursor {{ fill: {GOLD}; animation: blinkCursor 1s step-end infinite; }}
      {' '.join(style_lines)}
    </style>
  </defs>

  <g clip-path="url(#cardClip)">
    <rect class="term-bg" x="0" y="0" width="{width:.0f}" height="{height:.0f}"/>
    <rect class="term-border" x="0.75" y="0.75" width="{width-1.5:.0f}" height="{height-1.5:.0f}" rx="14" ry="14"/>

    <!-- title bar -->
    <rect x="0" y="0" width="{width:.0f}" height="{TITLE_H}" fill="#161616"/>
    <line x1="0" y1="{TITLE_H}" x2="{width:.0f}" y2="{TITLE_H}" stroke="{BORDER}" stroke-width="1"/>
    <circle class="dot" cx="20" cy="{TITLE_H/2:.0f}" r="5.5" fill="#ff5f56"/>
    <circle class="dot" cx="38" cy="{TITLE_H/2:.0f}" r="5.5" fill="#ffbd2e"/>
    <circle class="dot" cx="56" cy="{TITLE_H/2:.0f}" r="5.5" fill="#27c93f"/>
    <text class="title" x="{width/2:.0f}" y="{TITLE_H/2+4.5:.0f}" text-anchor="middle">nahidulsizan@portrait ~ %</text>

    <g>
      {''.join(text_rows)}
      <rect class="cursor" x="{PAD_X}" y="{TITLE_H + PAD_Y + n_lines*CHAR_H - 8:.1f}" width="6" height="10"/>
    </g>
  </g>
</svg>'''

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "hxni-ascii.svg"

    print(f"[*] Reading {src} ...")
    rows = image_to_ascii(src)

    print(f"[*] Building animated SVG ({COLS}x{ROWS} grid) ...")
    build_svg(rows, out)

    print(f"[✓] Saved: {out}")


if __name__ == "__main__":
    main()
