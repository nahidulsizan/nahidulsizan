#!/usr/bin/env python3
"""
prep_photo.py
-------------
Takes a raw portrait photo, strips the background with rembg (U2Net),
applies CLAHE contrast enhancement, and crops/resizes it to a clean
square-ish portrait ready for ASCII conversion.

Usage:
    python scripts/prep_photo.py hero.png [output.png]
"""

import sys
import os
import io

import numpy as np
from PIL import Image
import cv2

try:
    from rembg import remove, new_session
except ImportError:
    print("[!] rembg not installed. Run: pip install rembg[cpu]")
    sys.exit(1)

TARGET_WIDTH = 900          # working resolution before ASCII downsample
TARGET_ASPECT = 1.15        # height / width ratio for portrait crop
MODEL_NAME = "u2net_human_seg"  # tuned for human portraits


def remove_background(input_path: str) -> Image.Image:
    """Run U2Net human-segmentation background removal."""
    with open(input_path, "rb") as f:
        input_bytes = f.read()

    session = new_session(MODEL_NAME)
    output_bytes = remove(
        input_bytes,
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10,
    )
    img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    return img


def apply_clahe(img: Image.Image) -> Image.Image:
    """Apply CLAHE contrast enhancement on the RGB channels, preserving alpha."""
    rgba = np.array(img)
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3]

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)

    lab_eq = cv2.merge((l_eq, a, b))
    rgb_eq = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)

    out = np.dstack([rgb_eq, alpha])
    return Image.fromarray(out, mode="RGBA")


def crop_and_resize(img: Image.Image) -> Image.Image:
    """Crop tightly around the non-transparent subject, then cover-fit to target."""
    target_h = int(TARGET_WIDTH * TARGET_ASPECT)

    alpha = np.array(img)[:, :, 3]
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0 or len(ys) == 0:
        # No transparent regions found (segmentation failed) — skip crop
        cropped = img
    else:
        subj_w = xs.max() - xs.min()
        subj_h = ys.max() - ys.min()
        pad_x = int(subj_w * 0.10)
        pad_y_top = int(subj_h * 0.08)
        pad_y_bottom = int(subj_h * 0.02)
        x0 = max(xs.min() - pad_x, 0)
        x1 = min(xs.max() + pad_x, img.width)
        y0 = max(ys.min() - pad_y_top, 0)
        y1 = min(ys.max() + pad_y_bottom, img.height)
        cropped = img.crop((x0, y0, x1, y1))

    # Cover-fit: scale so the crop fully fills the target canvas (no empty
    # margins), then center-crop any overflow — anchored slightly toward
    # the top so faces aren't cut off.
    target_ratio = TARGET_WIDTH / target_h
    src_ratio = cropped.width / cropped.height

    if src_ratio > target_ratio:
        # source is relatively wider -> match height, crop sides
        scale_h = target_h
        scale_w = int(target_h * src_ratio)
    else:
        # source is relatively taller -> match width, crop top/bottom
        scale_w = TARGET_WIDTH
        scale_h = int(TARGET_WIDTH / src_ratio)

    resized = cropped.resize((scale_w, scale_h), Image.LANCZOS)

    off_x = (scale_w - TARGET_WIDTH) // 2
    off_y = int((scale_h - target_h) * 0.15)  # bias crop toward the top
    off_y = max(0, min(off_y, scale_h - target_h))

    canvas = resized.crop((off_x, off_y, off_x + TARGET_WIDTH, off_y + target_h))
    return canvas


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <input.png> [output.png]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"

    if not os.path.exists(input_path):
        print(f"[!] Input file not found: {input_path}")
        sys.exit(1)

    print(f"[*] Loading {input_path} ...")
    print("[*] Removing background with U2Net (human-seg model) ...")
    fg = remove_background(input_path)

    print("[*] Applying CLAHE contrast enhancement ...")
    fg = apply_clahe(fg)

    print("[*] Cropping & resizing to portrait canvas ...")
    fg = crop_and_resize(fg)

    fg.save(output_path)
    print(f"[✓] Saved: {output_path} ({fg.width}x{fg.height})")


if __name__ == "__main__":
    main()
