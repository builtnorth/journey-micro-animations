#!/usr/bin/env python3
"""Prepare a Figma photo for Cloudinary: crop it to what the frame shows,
apply Figma's mask, and make it safe for WordPress's AVIF conversion.

  python3 prepare_photo.py SOURCE OUT --fill=X,Y,W,H [--mask="x,y x,y ..."]
                           [--opaque [--bg="#ffffff"]] [--scale=S]

Use the --opt=value form: values can be negative (an image hanging off the
frame's left edge has a negative x).

SOURCE   the image fill as uploaded to Figma (download_assets rawImages, or
         the get_design_context asset for the image node).
OUT      .png for a cut-out (keeps transparency), .jpg for --opaque.
--fill   where the fill is drawn, in frame px: the image node's x,y,w,h
         (get_metadata). A CROP fill with an identity transform is
         stretched to exactly this box, as Figma does.
--mask   the mask polygon's points in frame px (the mask vector's path,
         offset by its x,y). Without it, the visible box is the --fill box
         clipped to the frame; pass --clip X,Y,W,H to use another box.
--opaque flatten onto --bg and save a JPG (use whenever the design doesn't
         need the photo's transparency). Otherwise transparent pixels get
         the colour of the nearest visible pixels ("bleed"), so lossy
         re-encoding can't pull black into the edges.
--scale  output px per frame px (default: the source's own resolution, so
         nothing is upscaled; use 2 for 2x when the source is big enough).

Prints the <img> placement (left, top, width, height in frame px) to put
in the CSS, and the width/height attributes for the <img>.
Needs Pillow and numpy:  pip install pillow numpy
"""
import argparse

import numpy as np
from PIL import Image, ImageDraw


def nums(s, n=None):
    v = [float(x) for x in s.replace(',', ' ').split()]
    if n and len(v) != n:
        raise SystemExit(f'expected {n} numbers: {s}')
    return v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source'); ap.add_argument('out')
    ap.add_argument('--fill', required=True)
    ap.add_argument('--mask'); ap.add_argument('--clip')
    ap.add_argument('--opaque', action='store_true'); ap.add_argument('--bg', default='#ffffff')
    ap.add_argument('--scale', type=float)
    a = ap.parse_args()

    im = Image.open(a.source).convert('RGBA')
    fx, fy, fw, fh = nums(a.fill, 4)
    sx, sy = fw / im.width, fh / im.height          # frame px per source px

    if a.mask:
        pts = nums(a.mask)
        poly = list(zip(pts[0::2], pts[1::2]))
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        bx0, by0, bx1, by1 = min(xs), min(ys), max(xs), max(ys)
    else:
        bx0, by0, bw, bh = nums(a.clip, 4) if a.clip else (fx, fy, fw, fh)
        bx1, by1 = bx0 + bw, by0 + bh
        poly = None
    bx0, by0, bx1, by1 = max(bx0, fx), max(by0, fy), min(bx1, fx + fw), min(by1, fy + fh)

    # Crop on whole source pixels (no resampling unless --scale asks for it).
    cx0, cy0 = int((bx0 - fx) / sx), int((by0 - fy) / sy)
    cx1, cy1 = -int(-(bx1 - fx) / sx), -int(-(by1 - fy) / sy)
    im = im.crop((cx0, cy0, cx1, cy1))
    left, top = fx + cx0 * sx, fy + cy0 * sy
    width, height = (cx1 - cx0) * sx, (cy1 - cy0) * sy
    if a.scale:
        im = im.resize((round(width * a.scale), round(height * a.scale)), Image.LANCZOS)

    px_x, px_y = im.width / width, im.height / height   # output px per frame px
    rgba = np.asarray(im, dtype=np.float32).copy()
    if poly:
        S = 4
        m = Image.new('L', (im.width * S, im.height * S), 0)
        ImageDraw.Draw(m).polygon([((x - left) * px_x * S, (y - top) * px_y * S) for x, y in poly], fill=255)
        rgba[..., 3] *= np.asarray(m.resize(im.size, Image.LANCZOS), dtype=np.float32) / 255

    if a.opaque:
        bg = np.array([int(a.bg.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
        al = rgba[..., 3:4] / 255
        out = Image.fromarray(np.clip(rgba[..., :3] * al + bg * (1 - al) + 0.5, 0, 255).astype(np.uint8), 'RGB')
        out.save(a.out, quality=90, optimize=True, progressive=True)
    else:
        # Take colour only from solid pixels: faint edge pixels often store black.
        rgb, known = rgba[..., :3].copy(), rgba[..., 3] >= 128
        for _ in range(max(im.size)):
            if known.all():
                break
            acc = np.zeros_like(rgb); cnt = np.zeros(known.shape, np.float32)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    k = np.roll(np.roll(known, dy, 0), dx, 1)
                    acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * k[..., None]; cnt += k
            grow = (~known) & (cnt > 0)
            rgb[grow] = acc[grow] / cnt[grow][:, None]
            known |= grow
        rgba[..., :3] = rgb
        Image.fromarray(np.clip(rgba + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(a.out, optimize=True)

    print(f'{a.out}: {im.width}x{im.height}')
    print(f'CSS (frame px): left {left:.3f}; top {top:.3f}; width {width:.3f}; height {height:.3f}')
    print(f'<img width="{round(width)}" height="{round(height)}">')


if __name__ == '__main__':
    main()
