#!/usr/bin/env python3
"""Compare a render with Figma, and lay out build frames as a strip.

  python3 compare.py diff  <rest.png> <figma.png> [--out=diff.png]
  python3 compare.py strip <outdir> [--out=strip.png]

diff   figma.png is get_screenshot of the same node (contentsOnly: true),
       downloaded with curl. It may include shadow bleed; the best offset
       (within 24px) is found automatically. Prints the mean difference and
       writes a 3x-amplified difference image: anti-aliasing shows as thin
       outlines; anything solid is a real mismatch.
strip  puts <outdir>/t*.png side by side in time order.
Needs Pillow and numpy:  pip install pillow numpy
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

BG = (245, 248, 251)  # the page colour render.js uses


def opt(k, d):
    return next((a.split('=', 1)[1] for a in sys.argv if a.startswith(f'--{k}=')), d)


def load(p, size=None):
    im = Image.open(p).convert('RGBA')
    bg = Image.new('RGBA', im.size, BG + (255,)); bg.alpha_composite(im)
    im = bg.convert('RGB')
    return np.asarray(im.resize(size, Image.LANCZOS) if size else im, np.float32)


def diff(rest, figma, out):
    r = load(rest)
    f_img = Image.open(figma)
    # Same scale as the render: the frame width is the render width.
    fw, fh = f_img.size
    best = None
    for pad in range(0, 33, 2):                         # shadow bleed on each side
        if fw - 2 * pad <= 0:
            break
        s = r.shape[1] / (fw - 2 * pad)
        f = load(figma, (round(fw * s), round(fh * s)))
        for dy in range(-24, 25, 2):
            y0 = round(pad * s) + dy
            if y0 < 0 or y0 + r.shape[0] > f.shape[0]:
                continue
            x0 = round(pad * s)
            d = np.abs(f[y0:y0 + r.shape[0], x0:x0 + r.shape[1]] - r).mean()
            if best is None or d < best[0]:
                best = (d, f, x0, y0)
    if best is None:
        sys.exit('figma image is smaller than the render; check the node')
    _, f, x0, y0 = best
    d = np.abs(f[y0:y0 + r.shape[0], x0:x0 + r.shape[1]] - r).max(axis=2)
    Image.fromarray(np.clip(d * 3, 0, 255).astype(np.uint8)).save(out)
    print(f'mean difference {d.mean():.2f} (0-255; about 1-2 is anti-aliasing and photo resampling), '
          f'pixels off by >40: {int((d > 40).sum())} -> {out}')


def strip(outdir, out):
    frames = sorted(Path(outdir).glob('t*.png'), key=lambda p: float(p.stem[1:]))
    ims = [Image.open(p).convert('RGB') for p in frames]
    w = 360
    ims = [im.resize((w, round(im.height * w / im.width))) for im in ims]
    s = Image.new('RGB', (len(ims) * (w + 8), max(i.height for i in ims)), 'white')
    for i, im in enumerate(ims):
        s.paste(im, (i * (w + 8), 0))
    s.save(out)
    print(f'{len(ims)} frames ({", ".join(p.stem for p in frames)}) -> {out}')


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ('diff', 'strip'):
        sys.exit(__doc__)
    if sys.argv[1] == 'diff':
        diff(sys.argv[2], sys.argv[3], opt('out', 'diff.png'))
    else:
        strip(sys.argv[2], opt('out', str(Path(sys.argv[2]) / 'strip.png')))
