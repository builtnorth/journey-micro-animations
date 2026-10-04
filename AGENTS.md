# Agent rules: Journey micro animations

Each folder is one graphic for the Coded Graphic block (`polaris/coded-graphic`)
in WordPress: `<name>.html` (markup), `<name>.css` (stylesheet) and any image
files it uses. Read these rules before adding or changing a graphic.

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
- **Entrances are simple:** opacity plus at most a small scale (0.94 to 1) or
  a short move, eased out, with no overshoot or bounce. Stagger by group in
  story order, not one item at a time.
- **Connectors match the frame.** Draw lines and rings whole, as Figma has
  them (full dashed arcs running behind the cards), not cut into pieces
  between cards.
- When unsure, leave it out. Ask before adding motion the brief didn't ask for.

## Timing

- **The build plays once.** One `--cycle` (10s is fine) for the build, with
  no `infinite`, whose **first and last keyframes are the finished graphic**,
  so play-once and reduced motion (the block jumps to the end) show it.
  A `--start` negative delay skips the short reset (0 to 4%) at the start.
- **Only live loops are `infinite`** (a call timer, a flow along
  connectors), each on its own short duration, independent of the build.
  They run on the site only when the block's **Loop** setting is on (which
  also adds the pause button); Loop off plays every animation once. The
  editor preview ignores this, so check loops on the front end.
- A looping value has to loop without a visible jump. A timer reel ends on a
  repeat of its first entry and runs on `steps()`.
- **Write keyframe names literally** in `animation` / `animation-name`. The
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
  upload, and use the link they send back. Until then, use a clear
  placeholder such as `src="CLOUDINARY_URL:<file name>"` and
  say the graphic is waiting on it. Never commit the image or invent a URL.
  Set `width`/`height` on the `<img>` to the 1x size.
- **Images must be opaque.** WordPress converts imported images to AVIF,
  which turns transparent edges into a dark, noisy fringe. Export photos as
  JPG (or flatten them onto a solid colour; shapes like circles are cut in
  CSS), and link a JPG. For a PNG already on Cloudinary, add `b_white/` (or
  the background colour) to the URL's transformations and change the
  extension to `.jpg`.
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

## Building from Figma

- Lay out on the Figma frame's grid: `--u` is one frame pixel
  (`calc(100cqw / <frame width>)`) and every size and position is a multiple of it.
- Use the Figma exports as they are: SVG icons with their paths unchanged,
  photos as exported. Don't redraw, simplify or recolor them. Only strip
  `id`s, Figma wrapper groups and anything that breaks the rules above.
- Take type sizes and weights, colors, radii, borders and shadows from the frame (read them with
  the Figma MCP tools, not from a screenshot).
- Before committing, render the graphic (Playwright with Chromium is
  available) and compare the finished frame against a Figma render of the
  same node, and check a few mid-build frames for show-through or jumps.
