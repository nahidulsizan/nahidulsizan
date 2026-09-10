# Getting Started

This repo is your GitHub profile repo (`nahidulsizan/nahidulsizan`). Everything below assumes
you've copied these files into that repo's root.

## 1. One-time local setup (for the ASCII portrait + info card)

```bash
cd scripts
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt # full deps, incl. rembg + opencv
```

> `rembg` downloads the U2Net model (~170MB) on first run — this needs a real
> internet connection and will take a minute the first time.

## 2. Add your photo

Drop a clear, front-facing portrait photo into the repo root as `hero.png`
(good lighting, plain-ish background works best — U2Net still handles busy
backgrounds fine, but a clean shot gives the sharpest cutout).

## 3. Run the pipeline, in order

```bash
python scripts/prep_photo.py hero.png        # -> source-prepped.png
python scripts/make_ascii_svg.py              # -> hxni-ascii.svg
python scripts/make_info_card.py              # -> info-card.svg
python scripts/fetch_contributions.py         # -> data/contributions.json
python scripts/render_heatmap_svg.py          # -> contrib-heatmap.svg
```

Open `hxni-ascii.svg` and `info-card.svg` in a browser to preview the
animations (GitHub's `<img>` embedding strips `<script>` but keeps CSS
`@keyframes`/SMIL, which is what these use, so they'll animate fine in the
rendered README too).

## 4. Push to GitHub

```bash
git add .
git commit -m "feat: cinematic animated profile"
git push origin main
```

## 5. Daily automation

`.github/workflows/update-profile-art.yml` is already wired up:

- Runs every day at **06:17 UTC** (and on-demand via the **Actions** tab →
  *Update Profile Art* → *Run workflow*).
- Re-scrapes your public contribution calendar and re-renders
  `contrib-heatmap.svg`.
- Commits changes back to `main` with `[skip ci]` so it doesn't loop.
- Only needs `scripts/requirements-ci.txt` (lightweight — no rembg/opencv in
  CI, since the photo pipeline is a one-time/manual step, not a daily one).

No secrets or API keys are required — `permissions: contents: write` on the
default `GITHUB_TOKEN` is enough to push back to the repo.

## Notes on what's already been generated for you

- `contrib-heatmap.svg` and `data/contributions.json` in this delivery were
  generated **live** against your real `nahidulsizan` GitHub contribution
  calendar — you can see actual current numbers already in there.
- `info-card.svg` was generated with your real profile details.
- `hxni-ascii.svg` was generated from a **placeholder silhouette** (no photo
  was provided), just so the layout/animation is verifiable end-to-end.
  Swap it out by running the real pipeline with your own `hero.png` — the
  SVG dimensions (370-wide card) will stay consistent either way.
