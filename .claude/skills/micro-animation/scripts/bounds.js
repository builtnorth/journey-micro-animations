#!/usr/bin/env node
/*
 * Measure a graphic's solid artwork in its finished frame, in frame px.
 *
 *   node bounds.js <folder>
 *
 * Renders the untrimmed frame on a transparent page at the finished frame
 * and prints the box of the solid pixels (alpha >= 64, so soft shadows don't
 * count): the stage is trimmed to it, so the artwork fills the block edge to
 * edge. `cropped` lists the frame edges the artwork runs off (cut by the
 * frame in Figma, like a phone running off the bottom): those stay clipped;
 * on the other sides shadows and motion may spill past the block.
 * Images are replaced by opaque placeholders (Cloudinary is blocked here),
 * which is right because photos are opaque rectangles.
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(execSync('npm root -g').toString().trim(), 'playwright'));

const folder = process.argv[2];
if (!folder) { console.error('usage: node bounds.js <folder>'); process.exit(2); }
const name = path.basename(path.resolve(folder));
const html = fs.readFileSync(path.join(folder, `${name}.html`), 'utf8');
const css = fs.readFileSync(path.join(folder, `${name}.css`), 'utf8');
const scene = css.match(/^\.scene \{[^}]*\bwidth: ([\d.]+)px; height: ([\d.]+)px;/m);
if (!scene) { console.error(`${name}.css: no .scene { … width: <w>px; height: <h>px; … }`); process.exit(1); }
const W = Number(scene[1]), H = Number(scene[2]);
const PIXEL = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgYGAAAAAEAAH2FzhVAAAAAElFTkSuQmCC', 'base64');

(async () => {
  const browser = await chromium.launch({ executablePath: fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined });
  const page = await browser.newPage({ viewport: { width: Math.ceil(W) + 400, height: Math.ceil(H) + 400 } });
  await page.route(/^https?:/, (r) => (/\.(png|jpe?g|webp|avif)/i.test(r.request().url()) ? r.fulfill({ body: PIXEL, contentType: 'image/png' }) : r.abort()));
  // The stage is measured untrimmed: undo any trim so the whole frame is visible.
  await page.setContent(`<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:transparent}${css}
    .stage{aspect-ratio:auto!important;width:${W}px!important;height:${H}px!important;overflow:visible!important}
    .scene{left:0!important;top:0!important;zoom:1!important}</style><div style="width:${W}px;margin:200px">${html}</div>`);
  await page.waitForTimeout(300);
  const box = { x0: Infinity, y0: Infinity, x1: -Infinity, y1: -Infinity };
  for (const f of [0.999]) {
    await page.evaluate((f) => document.getAnimations().forEach((a) => {
      const t = a.effect.getComputedTiming(); a.pause(); a.currentTime = (t.delay || 0) + f * t.duration;
    }), f);
    const png = await page.screenshot({ omitBackground: true, clip: { x: 200, y: 200, width: W, height: H } });
    const b = await page.evaluate(async (b64) => {
      const img = new Image(); img.src = 'data:image/png;base64,' + b64; await img.decode();
      const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
      const g = c.getContext('2d'); g.drawImage(img, 0, 0);
      const d = g.getImageData(0, 0, c.width, c.height).data;
      let x0 = Infinity, y0 = Infinity, x1 = -1, y1 = -1;
      for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) {
        if (d[(y * c.width + x) * 4 + 3] >= 64) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
      }
      return { x0, y0, x1: x1 + 1, y1: y1 + 1 };
    }, png.toString('base64'));
    if (b.x1 > 0) { box.x0 = Math.min(box.x0, b.x0); box.y0 = Math.min(box.y0, b.y0); box.x1 = Math.max(box.x1, b.x1); box.y1 = Math.max(box.y1, b.y1); }
  }
  await browser.close();
  const cropped = [box.y0 <= 0 && 'top', box.x1 >= Math.floor(W) && 'right', box.y1 >= Math.floor(H) && 'bottom', box.x0 <= 0 && 'left'].filter(Boolean);
  const r = { frame: [W, H], x: box.x0, y: box.y0, w: box.x1 - box.x0, h: box.y1 - box.y0, cropped };
  console.log(JSON.stringify(r));
})();
