#!/usr/bin/env node
/*
 * Render a micro animation with Playwright (Chromium) at chosen moments.
 *
 *   node render.js <folder> <outdir> [--width=<design width>] [--times=0,0.8,1.6,2.4,3.2]
 *                  [--img=<src>=<local file>] [--scale=2]
 *
 * Writes <outdir>/t<seconds>.png for each time, plus rest.png. Times are
 * seconds into each animation's keyframes: 0 is the first keyframe, which by
 * the rules is the finished graphic (so rest.png = t0); the build itself
 * starts at the --start offset (0.45s), e.g. 0.8s is early in the build.
 *
 * --img maps an <img src> to a local file (data URI), for images that this
 * sandbox can't fetch (Cloudinary is blocked here) or that aren't uploaded yet.
 * Repeat it for several images.
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(execSync('npm root -g').toString().trim(), 'playwright'));

const args = process.argv.slice(2);
const opt = (k, d) => { const a = args.find((x) => x.startsWith(`--${k}=`)); return a ? a.slice(k.length + 3) : d; };
const [folder, outdir] = args.filter((a) => !a.startsWith('--'));
if (!folder || !outdir) { console.error('usage: node render.js <folder> <outdir> [--width=] [--times=] [--img=src=file]'); process.exit(2); }

const name = path.basename(path.resolve(folder));
let html = fs.readFileSync(path.join(folder, `${name}.html`), 'utf8');
const css = fs.readFileSync(path.join(folder, `${name}.css`), 'utf8');
for (const a of args.filter((x) => x.startsWith('--img='))) {
  const v = a.slice(6); const i = v.lastIndexOf('=');
  const src = v.slice(0, i), file = v.slice(i + 1);
  const mime = /\.jpe?g$/i.test(file) ? 'image/jpeg' : 'image/png';
  html = html.split(`src="${src}"`).join(`src="data:${mime};base64,${fs.readFileSync(file).toString('base64')}"`);
}
const width = Number(opt('width', (css.match(/calc\(100cqw \/ ([\d.]+)\)/) || [])[1] || 1000));
const times = opt('times', '0,0.8,1.6,2.4,3.2,4').split(',').map(Number);
const scale = Number(opt('scale', 1));
fs.mkdirSync(outdir, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Math.round(width), height: 2000 }, deviceScaleFactor: scale });
  const errors = [];
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  page.on('requestfailed', (r) => errors.push(`failed to load ${r.url().slice(0, 100)}`));
  // A neutral page and no theme font: the graphic must hold up with the Inter fallback.
  await page.setContent(`<!doctype html><style>body{margin:0;background:#f5f8fb}${css}
    *, *::before, *::after { animation-play-state: paused !important; }</style>${html}`, { waitUntil: 'load' });
  const box = await page.evaluate(() => { const r = document.body.firstElementChild.getBoundingClientRect(); return { x: 0, y: 0, width: r.width, height: Math.ceil(r.height) }; });
  const seek = (t) => page.evaluate((t) => document.getAnimations().forEach((a) => {
    a.currentTime = t * 1000 + (a.effect.getTiming().delay || 0);
  }), t);
  await seek(0);
  await page.screenshot({ path: path.join(outdir, 'rest.png'), clip: box });
  for (const t of times) {
    await seek(t);
    await page.screenshot({ path: path.join(outdir, `t${t}.png`), clip: box });
  }
  const loops = await page.evaluate(() => [...new Set(document.getAnimations().filter((a) => a.effect.getTiming().iterations === Infinity).map((a) => a.animationName))]);
  console.log(`rendered ${name} at ${width}px: rest.png + ${times.map((t) => `t${t}.png`).join(' ')} -> ${outdir}`);
  if (loops.length) console.log(`looping: ${loops.join(', ')} (only with the block's Loop on)`);
  if (errors.length) console.log('page errors:\n  ' + errors.join('\n  '));
  await browser.close();
})();
