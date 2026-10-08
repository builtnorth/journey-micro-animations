# Agent rules: Journey micro animations

Each folder is one graphic for the Coded Graphic block (`polaris/coded-graphic`)
in WordPress: `<name>.html` (markup), `<name>.css` (stylesheet) and any image
files it uses. Read these rules before adding or changing a graphic, and
use the `micro-animation` skill (`.claude/skills/micro-animation/`) for the
procedure and the scripts: `lint.py` checks a graphic against the rules
below and must pass before committing.

## Motion: keep it intentional

An animation earns its place only if it explains the idea the graphic shows.
The default is the build, then stillness.

- **Animate the story, once.** Build the graphic in the order that tells it
  (the subject first, then what connects to it, then what it connects to),
  then hold on the finished frame. Example: the customer appears, the
  connectors draw out from her, and each card fades in as its connector arrives.
- **Do not animate the parts.** No icon actions (ringing phones, typing
  codes, wallets, cursors, sparkles), no floating, bobbing, pulsing or
  wobbling cards, no ripples, glows, shimmer or idle "life" on photos,
  devices or backgrounds. Icons, cards, photos and devices stay still once
  they are in.
- **Animate what is live in the scene.** State that really changes in the
  moment moves as it would in real life: a call timer counts up a second at
  a time, a progress value climbs. This is not the same as giving icons
  actions.
- **At most one ambient loop**, and only when it shows something real, such as
  data flowing along a connector. Keep it slow and quiet. Don't add a second one.
- **When the story is a flow inside a UI** (steps confirming, a screen
  changing), the UI is simply there from the start, with no entrance; the
  motion is the flow itself. Run it all the way to its outcome and end
  on that (e.g. every step confirmed and a "Payment confirmed" screen),
  with each item waiting (dots), working (spinner) and done (tick) in turn.
- **Entrances are simple:** opacity plus scale (or a short move), eased
  out, with no overshoot or bounce. The subject and what frames it come in
  together first. Rings and connectors around it then expand from its centre
  (scale about 0.6 to 1) or draw out from it, one after another. Small
  repeated items (badges, icon circles) grow in last (scale about 0.5 to 1),
  one at a time in a shuffled order, about 150ms apart. Bigger elements
  stagger by group, not one at a time.
- **Connectors match the frame.** Draw lines and rings whole, as Figma has
  them (full dashed arcs running behind the cards), not cut into pieces
  between cards.
- When unsure, leave it out. Ask before adding motion the brief didn't ask for.

## Timing

- **Every animation is `infinite`; the block's Loop setting decides.**
  Loop on: the whole sequence repeats (with a pause button). Loop off:
  every animation plays once and stops. So the build runs on one `--cycle`
  (10–12s is fine) with `infinite`, whose **first and last keyframes are
  the finished graphic**: play-once and reduced motion (the block jumps to
  the end) show it, and on a loop the short 0–4% reset eases from the
  finished graphic back to the start. A `--start` negative delay (past 4%)
  skips that reset on the first pass. The editor preview ignores Loop, so
  check both settings on the front end.
- **Put live motion inside the cycle when it belongs to a moment** (dots
  while a step waits, a spinner while it works): bake it into the cycle's
  keyframes so it plays in full with Loop off too. Only state that runs on
  its own clock (a call timer, a flow along connectors) gets its own short
  `infinite` animation.
- A looping value has to loop without a visible jump. A timer reel ends on a
  repeat of its first entry and runs on `steps()`.
- **Only transform whole boxes.** Don't scale, rotate or move shapes
  *inside* an `<svg>` (`<circle>`, `<path>`, `<g>`): with
  `transform-box`/`transform-origin` and the block scaling the graphic, some
  browsers draw them in the wrong place (Safari especially). Give anything
  that moves its own element and animate that: a positioned `<div>` wrapping
  an `<svg>` with no class (`<div class="ring"><svg viewBox="…">…</svg></div>`).
  Put position, size and animation on the `<div>`, never on the `<svg>`
  itself: on the site a styled `<svg>` lost its size and drew at full width. Animating paint inside an SVG (opacity, stroke-dashoffset,
  fill) is fine.
- **Write keyframe names literally, in the `animation` shorthand** (not a separate `animation-name`, which the block may not rename: bars set up that way never moved on the site). The
  block scopes the CSS and renames every `@keyframes`, so a name held in a
  custom property (`animation: var(--draw) …`) never matches and the
  animation silently doesn't run on the site, though it works in the editor.
  Keep keyframe values literal too: one `@keyframes` per variant, no `var()`
  inside them. `var()` for durations and delays is fine.

## What the block allows (it sanitizes on the front end)

The editor preview shows the raw code, but `render.php` sanitizes the markup
and CSS on every page load, and **prints nothing if the markup is rejected**.
So a graphic can work in the editor and be missing on the site. Stay inside
these limits:

- **Markup:** HTML and inline SVG only. No scripts, links (`<a>`), buttons,
  forms, `style` attributes or event handlers.
- **SVG allowlist** (from `Navas\Utility\Helpers\EscapeSvg`, wp_kses):
  `svg g path circle rect polygon polyline line ellipse title desc` with
  presentation attributes only (`d`, `points`, `cx`…, `fill`, `fill-rule`,
  `stroke`, `stroke-width`, `stroke-linecap/linejoin` (path), `opacity`,
  `transform`; `viewBox`, `class` on `<svg>`). `class` on inner shapes
  survives on the site in practice. Not allowed: `pathLength`,
  `stroke-dasharray`, `fill-opacity`, `stroke-opacity`, `<text>`, `<use>`,
  filters. Style these with CSS instead; `lint.py` warns on the rest.
- **No `url()` anywhere:** not in CSS, and not in SVG attributes either.
  That rules out `mask="url(#…)"`, `clip-path="url(#…)"`,
  `filter="url(#…)"`, gradient or pattern fills, `<use href>`, and the
  `<defs>` they point to. Use CSS instead: `clip-path: inset()` for reveals,
  `filter: drop-shadow()` for shadows, CSS gradients on HTML elements.
- **No `id` attributes.** Figma exports add them; strip them.
- **No `data:` URIs, and no images in the repo.** Images are hosted on
  Cloudinary and the `<img src>` is the full Cloudinary URL the user gives
  you (`https://res.cloudinary.com/dxat7whi/image/upload/…`); WordPress
  imports it into the media library. When a graphic needs an image: export
  it from Figma (photos at 2x, PNG or JPG), send the file to the user to
  upload, and use the link they send back. Until then, use
  `src="https://res.cloudinary.com/dxat7whi/image/upload/PENDING/<file name>"`
  and say the graphic is waiting on it. (Not a made-up scheme like
  `CLOUDINARY_URL:<file>`: WordPress strips unknown schemes and silently
  leaves a relative `<file>` that can't load or import.) Never commit the
  image or invent a URL.
  Set `width`/`height` on the `<img>` to the 1x size.
- **Images are plain rectangles.** Export the photo or screen as a
  rectangular JPG covering its box (compositing any layers Figma stacks
  inside it), with nothing baked in: no rounded corners, circle crops,
  rings, borders or shadows. Do all of that in CSS (`border-radius`,
  `border`, `box-shadow`, `object-fit: cover`).
- **Images must be opaque, unless they are cut-outs.** WordPress converts
  imported images to AVIF, which turns transparent edges into a dark, noisy
  fringe. Export photos as JPG (or flatten them onto a solid colour; shapes
  like circles are cut in CSS), and link a JPG. For a PNG already on
  Cloudinary, add `b_white/` (or the background colour) to the URL's
  transformations and change the extension to `.jpg`.
  Only when the design truly needs transparency (a cut-out subject whose
  outline overlaps other layers, like the get-demo agent), export a PNG: crop it to the visible area, bake in Figma's mask
  shape, and **bleed the edge colours into every transparent pixel** (their
  RGB must not be black), so the AVIF conversion has nothing dark to pull
  into the edges. Pillow and numpy can be pip-installed for this.
- **CSS** is scoped to the block automatically. Theme preset variables
  (`var(--wp--preset--…)`) are fine.
- **Fonts:** set them once on the graphic's root with
  `font-family: var(--wp--custom--animation--font, "Inter"), sans-serif;`
  and let everything inherit it, including text inside devices. Never load
  fonts (`@import`, `@font-face`, `<link>`) and don't name other families,
  even when Figma uses them; keep Figma's sizes and weights.
  The font differs from Figma's and by site, so anything holding text grows
  to fit it (`min-width` at the Figma width, not a fixed `width`), growing
  away from the frame edge it sits against.
- **Design width:** the graphic is designed at a fixed px width and the block
  scales it. Set the block's design width to the Figma frame's width.
- **Size in px, never container query units.** The block scales the stage
  with `zoom`, and Safari resolves `cqw`/`cqh` inside a zoomed element
  against the already-shrunk width and then zooms again, so a `cqw` graphic
  draws at the scale squared, shrunk into the top-left corner. Don't set
  `container-type`; size everything in px (through `--u: 1px`).

## Building from Figma

- Lay out on the Figma frame's grid: `--u` is one frame pixel (`1px`) and
  every size and position is a multiple of it; the root is the frame's width
  in px (`width: <frame width>px`) and the block scales it.
- Use the Figma exports as they are: SVG icons with their paths unchanged,
  photos as exported. Don't redraw, simplify or recolor them. Only strip
  `id`s, Figma wrapper groups and anything that breaks the rules above.
- Take type sizes and weights, colors, radii, borders and shadows from the frame (read them with
  the Figma MCP tools, not from a screenshot).
- Before committing, render the graphic (Playwright with Chromium is
  available) and compare the finished frame against a Figma render of the
  same node, and check a few mid-build frames for show-through or jumps.
