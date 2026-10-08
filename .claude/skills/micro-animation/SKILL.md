---
name: micro-animation
description: Build or change a Journey micro animation (a pure HTML + CSS graphic for the Coded Graphic WordPress block) from a Figma frame. Use when asked to create, port, animate, fix or tweak a graphic in this repo, or when given a figma.com link for one. Covers the Figma exports, layout on the frame grid, the build animation, photo prep for Cloudinary, lint against what the block strips, and render checks.
---

# Micro animation from Figma

The rules (what the block allows, how motion should behave) are in
`AGENTS.md` at the repo root. Read it first; this skill is the procedure.
Scripts live in `.claude/skills/micro-animation/scripts/`.

## 1. Read the frame

The user gives a Figma link: `fileKey` is the path segment after
`/design/`, `nodeId` is `node-id` with `-` → `:`.

1. `get_design_context` (load the figma-design-to-code guidance first) for
   the code, asset URLs and screenshot. `www.figma.com` is reachable here,
   so download its asset URLs with `curl` into the scratchpad right away
   (they expire).
2. `get_metadata` for exact positions and sizes of every layer.
3. Anything the context leaves out (stroke align, dash patterns, effects,
   fonts, image fills, exact icon bounds): read it with `use_figma`.
   Snippets are in `reference/figma.md`. Strokes are often `INSIDE`, which
   moves a shape's centreline in from its box.

The frame's width and height are the design grid: every position below is
in frame px.

## 2. Plan the motion, then confirm it if unsure

Write the story in one sentence: what comes in first, what follows, what
holds. Follow `AGENTS.md` (subject and its frame together, then rings or
connectors, then small items; build once; only live state loops). If the
brief doesn't say, propose the sequence to the user in one or two lines
before building rather than inventing extra motion.

## 3. Build the folder

`<name>/<name>.html` and `<name>/<name>.css`, `<name>` from the Figma
layer (e.g. `Graphic / get-demo-graphic` → `get-demo`).

- Root: `<div class="<prefix>"><div class="stage">…</div></div>`; the root
  sets `--u: 1px`, `width: <frame width>px` (px only: no `cqw` or
  `container-type`, the block does the scaling) and the font
  (`var(--wp--custom--animation--font, "Inter"), sans-serif`);
  `.stage` has `aspect-ratio: <w> / <h>` and `overflow: hidden`.
- Static layers that never move (panels, backgrounds, connector lines):
  one full-frame `<svg viewBox="0 0 <w> <h>">` with plain shapes.
- Everything that moves (rings, badges, cards, photos): its own positioned
  `<div>` (left/top/width/height as `calc(<frame px> * var(--u))`), with a
  class-less `<svg>` inside for vector content. Animate the div.
- Icons: the Figma SVG exports with paths unchanged; strip `id`s, Figma
  wrapper `<g>`s, `<defs>`, filters and anything `lint.py` flags.
- Text: real text, sized in `--u`; containers use `min-width` at the Figma
  width so another font can't overflow them.
- Keyframes: one `--cycle` (10–12s) with a `--start` delay just past the
  reset (e.g. `-0.5s`); every animation `infinite` (the block's Loop
  setting decides whether it repeats); each keyframe set starts and ends on
  the finished state, with a short reset at 0–4% (copy the pattern from an
  existing graphic). Literal keyframe names, no `var()` inside keyframes.

## 4. Images (Cloudinary)

Images never go in the repo. For each photo:

```
python3 .claude/skills/micro-animation/scripts/prepare_photo.py SOURCE OUT \
  --fill=<image node x,y,w,h> [--mask="<polygon in frame px>"] [--opaque --bg="#hex"]
```

- A plain rectangular JPG (`--opaque`) covering the image's box: no rounded
  corners, circle crops, rings or shadows baked in; CSS does those. If Figma
  stacks several images inside one shape (a cut-out on a background photo),
  composite them into one rectangle first. Only a cut-out whose outline
  overlaps other layers gets a PNG with bled edges (the default).
- To export a whole rendered area (an app screen), use `download_assets`
  with `defaultScale: 2` on the innermost content frame (the app, not the
  phone's screen frame), then run it through `prepare_photo.py --opaque`.
  Figma still bakes a clipping parent's rounded corners into the export
  (painted near-white): fill those corners with the neighbouring colours
  so the file is a clean rectangle, and recreate the clip in CSS (a
  wrapper `<div>` with `border-radius` and `overflow: hidden`). Likewise a
  source photo that is itself a circle cut-out: bleed its edges into the
  corners. Open the files and check before sending them.
- It prints the CSS placement and the `<img width height>`.
- Send the file to the user (SendUserFile) to upload to Cloudinary. Until
  they reply, use
  `src="https://res.cloudinary.com/dxat7whi/image/upload/PENDING/<file>"`.
  Then swap in their exact link. This sandbox can't reach Cloudinary, so
  don't try to verify the link; render with `--img` (below) instead.

## 5. Check

```
S=.claude/skills/micro-animation/scripts
python3 $S/lint.py <name>                                   # must be 0 errors
node $S/render.js <name> <scratch>/r --img=<cloudinary src>=<local file>
curl -sSL -o <scratch>/figma.png "<get_screenshot url>"     # contentsOnly: true, 1:1 (see below)
python3 $S/compare.py diff <scratch>/r/rest.png <scratch>/figma.png --out=<scratch>/r/diff.png
python3 $S/compare.py strip <scratch>/r
```

- Get the Figma render at 1:1: call `get_screenshot` once, then again with
  `maxDimension` = the `original_width` it reports (shadows can make it
  wider than the frame; `compare.py` finds the offset).
- Look at `rest.png`, `diff.png` and `strip.png` (Read them). A mean
  difference around 1–2 is anti-aliasing and resampling; text set in a
  different font from Figma's also shows up, which is expected. Solid
  shapes in the diff are real mismatches: fix them.
- In the strip, check the order matches the plan, nothing shows through a
  fading element, and nothing jumps.
- `pip install pillow numpy` if the Python scripts need them.

## 6. Commit and hand over

- Add the folder to the README table (with its design width).
- Commit as `Dan Northern <157666970+dannorthern@users.noreply.github.com>`
  with **no** Claude attribution lines, and push to the repo's default branch
  (`claude/confident-goodall-excjjt`):
  `git -c user.name="Dan Northern" -c user.email="157666970+dannorthern@users.noreply.github.com" commit …`
- Tell the user: the block's design width, whether Loop needs to be on
  (only if the graphic has a live loop), and any image still pending.

## When something works in the editor but not on the site

The editor preview shows the raw code; the site sanitizes it. Run `lint.py`
first. Known causes, all checked by it: `url()` or `id`s in markup, a
`var()` keyframe name, `var()` inside keyframes, a styled or positioned
`<svg>`, transforms on shapes inside an SVG, attributes outside the SVG
allowlist (`pathLength`, `stroke-dasharray` …), a non-https image `src`,
and loops with the block's Loop off. When you find a new one, add it to
`AGENTS.md` and to `lint.py`.

If a graphic is right in Chrome but shrinks into the top-left corner in
Safari, it is sizing itself with container query units (`cqw`) or
`container-type`. The block scales the stage with `zoom`, and Safari
applies that zoom twice to `cq` units. Size everything in px
(`--u: 1px`, root `width: <frame width>px`) and set the block's design
width; never make a graphic scale itself. `render.js` only runs Chromium,
so it won't show this: `lint.py` catches it.
