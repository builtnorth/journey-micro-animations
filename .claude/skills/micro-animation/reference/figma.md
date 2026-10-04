# Figma snippets for micro animations

All `use_figma` calls here are read-only; load the figma-use guidance first
and pass `skillNames: "resource:figma-use"`. Responses are capped at about
20 KB: export big things one at a time.

## Layer properties the design context leaves out

```js
const root = await figma.getNodeByIdAsync('<frame id>');
const ox = root.absoluteTransform[0][2], oy = root.absoluteTransform[1][2];
const paint = p => (p || []).map(f => ({ t: f.type, c: f.color && [f.color.r, f.color.g, f.color.b].map(v => Math.round(v * 255)), o: f.opacity }));
const out = {};
for (const id of ['<id>', '<id>']) {
  const n = await figma.getNodeByIdAsync(id), b = n.absoluteBoundingBox;
  out[id] = {
    name: n.name, x: +(b.x - ox).toFixed(3), y: +(b.y - oy).toFixed(3), w: +b.width.toFixed(3), h: +b.height.toFixed(3),
    fills: paint(n.fills), strokes: paint(n.strokes), sw: n.strokeWeight, align: n.strokeAlign, dash: n.dashPattern,
    r: n.cornerRadius, fx: (n.effects || []).map(e => ({ t: e.type, r: e.radius, c: e.color, o: e.offset })),
    t: n.absoluteTransform,                                  // a -1 in [0][0] means flipped
    font: 'fontName' in n ? [n.fontName, n.fontSize, n.lineHeight, n.letterSpacing] : undefined,
  };
}
return out;
```

`absoluteBoundingBox` is the visual box: use it for flipped or rotated
layers, where `x`/`y` in `get_metadata` point at the transform origin.

## Icon SVGs

The asset URLs from `get_design_context` are already SVG exports. To export
a node yourself:

```js
const n = await figma.getNodeByIdAsync('<id>');
return { svg: await n.exportAsync({ format: 'SVG_STRING' }) };
```

Exports of a node with a drop shadow grow to fit the shadow (the viewBox no
longer matches the layer box): drop the filter and use a CSS
`filter: drop-shadow()` on the wrapper instead.

## Image fills

```js
const n = await figma.getNodeByIdAsync('<image node id>');
const f = n.fills.find(x => x.type === 'IMAGE');
return { scaleMode: f.scaleMode, transform: f.imageTransform, size: await figma.getImageByHash(f.imageHash).getSizeAsync() };
```

`CROP` with the identity transform `[[1,0,0],[0,1,0]]` stretches the image
to the node's box (`prepare_photo.py --fill`). The raw image is usually the
`.png`/`.jpg` asset in the design context; its pixel size should match.
Masks are separate vector layers (`isMask` or a layer named `Mask`): their
path, offset by the layer's x/y, is the `--mask` polygon.

## Reference render

`get_screenshot` with `contentsOnly: true` and `maxDimension` = the frame
width, then `curl -sSL -o figma.png "<image_url>"` for `compare.py diff`.
