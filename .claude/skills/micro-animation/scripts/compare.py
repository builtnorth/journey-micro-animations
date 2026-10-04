#!/usr/bin/env python3
"""Compare a render with Figma, and lay out build frames as a strip.

  python3 compare.py diff  <rest.png> <figma.png> [--out=diff.png]
  python3 compare.py strip <outdir> [--out=strip.png]

diff   figma.png is get_screenshot of the same node (contentsOnly: true) at
       1:1: call it once, then again with maxDimension = the original_width
       it reports (shadow bleed makes it wider than the frame). The offset
       of the frame inside it is found automatically. Prints the mean difference and
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
    f = load(figma)
    rh, rw = r.shape[:2]
    fh, fw = f.shape[:2]
    if fw < rw or fh < rh:
        sys.exit(f'figma image ({fw}x{fh}) is smaller than the render ({rw}x{rh}): request it at '
                 'maxDimension = its original size (1:1), not the frame width')
    # The frame may carry shadow bleed on any side: find the offset, coarse then fine.
    def score(x, y, step=1):
        return np.abs(f[y:y + rh:step, x:x + rw:step] - r[::step, ::step]).mean()
    coarse = min(((score(x, y, 4), x, y) for x in range(0, fw - rw + 1, 2) for y in range(0, fh - rh + 1, 2)))
    _, cx, cy = coarse
    best = min(((score(x, y), x, y) for x in range(max(0, cx - 2), min(fw - rw, cx + 2) + 1)
                for y in range(max(0, cy - 2), min(fh - rh, cy + 2) + 1)))
    _, x0, y0 = best
    d = np.abs(f[y0:y0 + rh, x0:x0 + rw] - r).max(axis=2)
    Image.fromarray(np.clip(d * 3, 0, 255).astype(np.uint8)).save(out)
    print(f'offset in figma image: ({x0}, {y0}); mean difference {d.mean():.2f} (0-255; about 1-2 is '
          f'anti-aliasing and photo resampling), pixels off by >40: {int((d > 40).sum())} -> {out}')


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
