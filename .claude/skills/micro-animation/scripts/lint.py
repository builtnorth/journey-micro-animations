#!/usr/bin/env python3
"""Check a micro animation folder against what the Coded Graphic block allows.

Usage: python3 lint.py <folder> [<folder> ...]

ERROR  breaks on the site (each one has failed there before, silently).
WARN   may be stripped or misbehave; check it on the front end.

The SVG allowlist below mirrors Navas\\Utility\\Helpers\\EscapeSvg (wp_kses).
The block's own sanitizer is at least this permissive (e.g. `class` on
<path> survives on the site), so anything outside it is a warning, not an
error. Exits 1 if there are errors.
"""
import re
import sys
from pathlib import Path

SVG_ALLOWED = {
    'svg': {'class', 'aria-hidden', 'aria-labelledby', 'role', 'xmlns', 'width', 'height', 'viewbox',
            'preserveaspectratio', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin'},
    'g': {'fill', 'fill-rule', 'clip-rule', 'clip-path', 'stroke', 'stroke-width', 'transform'},
    'title': {'title'}, 'desc': set(),
    'path': {'d', 'fill', 'fill-rule', 'clip-rule', 'clip-path', 'stroke', 'stroke-width', 'stroke-linecap',
             'stroke-linejoin', 'opacity', 'transform'},
    'circle': {'cx', 'cy', 'r', 'fill', 'stroke', 'stroke-width', 'opacity', 'transform'},
    'rect': {'x', 'y', 'width', 'height', 'fill', 'stroke', 'stroke-width', 'rx', 'ry', 'opacity', 'transform'},
    'polygon': {'points', 'fill', 'fill-rule', 'clip-rule', 'clip-path', 'stroke', 'stroke-width', 'opacity', 'transform'},
    'polyline': {'points', 'fill', 'stroke', 'stroke-width', 'opacity', 'transform'},
    'line': {'x1', 'y1', 'x2', 'y2', 'stroke', 'stroke-width', 'opacity', 'transform'},
    'ellipse': {'cx', 'cy', 'rx', 'ry', 'fill', 'stroke', 'stroke-width', 'opacity', 'transform'},
}
SVG_INNER = {'g', 'path', 'circle', 'rect', 'polygon', 'polyline', 'line', 'ellipse'}
# Seen surviving on the site although EscapeSvg doesn't list it.
OBSERVED_OK = {('path', 'class'), ('circle', 'class'), ('g', 'class'), ('rect', 'class')}
HTML_OK = {'div', 'span', 'img', 'p', 'strong', 'em', 'br', 'small'}
TRANSFORMING = re.compile(r'\b(transform|translate|scale|rotate)\s*:')


def lint(folder: Path):
    errors, warns = [], []
    name = folder.name
    html_p, css_p = folder / f'{name}.html', folder / f'{name}.css'
    if not html_p.exists() or not css_p.exists():
        return [f'{folder}: needs {name}.html and {name}.css'], []
    html, css = html_p.read_text(), css_p.read_text()

    E = lambda m: errors.append(m)
    W = lambda m: warns.append(m)

    # --- files in the folder: no images in the repo
    for f in folder.iterdir():
        if f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.avif', '.gif'}:
            E(f'{f.name}: images live on Cloudinary, not in the repo')

    # --- markup
    for pat, msg in [
        (r'url\(', 'url() in markup (mask/clip-path/filter/fill refs are stripped)'),
        (r'\sid="', 'id attribute (stripped; Figma exports add them)'),
        (r'\sstyle="', 'style attribute (stripped)'),
        (r'data:', 'data: URI (stripped; host images on Cloudinary)'),
        (r'<script|<a[\s>]|<button|<form|<input|<iframe|<link', 'scripts, links, buttons and forms are not allowed'),
        (r'\son[a-z]+="', 'event handler attribute'),
        (r'<use[\s>]|<filter|<fe[A-Z]|<mask|<clipPath|<linearGradient|<radialGradient|<pattern|<defs|<text[\s>]|<foreignObject',
         'SVG element that needs url()/href or is not allowed (draw it plainly, use CSS for effects)'),
        (r'pathLength=', 'pathLength (stripped; reveal with CSS clip-path: inset() instead)'),
        (r'CLOUDINARY_URL|src="(?!https://)', 'img src must be a full https URL (pending: https://res.cloudinary.com/dxat7whi/image/upload/PENDING/<file>)'),
    ]:
        for m in re.finditer(pat, html):
            line = html.count('\n', 0, m.start()) + 1
            E(f'{name}.html:{line}: {msg}')
    for m in re.finditer(r'<img\s[^>]*>', html):
        tag = m.group(0)
        if '/PENDING/' in tag:
            W(f'{name}.html: image still PENDING upload: {tag[:90]}')
        elif 'res.cloudinary.com' not in tag:
            W(f'{name}.html: img not on Cloudinary: {tag[:90]}')
        if not re.search(r'\swidth="\d', tag) or not re.search(r'\sheight="\d', tag):
            W(f'{name}.html: img needs width and height (1x size)')

    # Element / attribute allowlists.
    in_svg = 0
    inner_class_sets = []
    svg_classes = set()
    for m in re.finditer(r'<(/?)([a-zA-Z][\w-]*)([^>]*)>', html):
        closing, tag, attrs = m.group(1), m.group(2), m.group(3)
        t = tag.lower()
        if t == 'svg':
            in_svg += -1 if closing else (0 if attrs.rstrip().endswith('/') else 1)
        if closing:
            continue
        names = re.findall(r'\s([a-zA-Z][\w:-]*)=', attrs)
        cls = re.search(r'\sclass="([^"]*)"', attrs)
        if t in SVG_ALLOWED:
            for a in names:
                if a.lower() not in SVG_ALLOWED[t] and (t, a.lower()) not in OBSERVED_OK:
                    W(f'{name}.html: <{tag} {a}=…> is outside the SVG allowlist and may be stripped')
            if cls and t in SVG_INNER:
                inner_class_sets.append(set(cls.group(1).split()))
            if cls and t == 'svg':
                svg_classes.update(cls.group(1).split())
        elif in_svg:
            E(f'{name}.html: <{tag}> inside an SVG is not allowed')
        elif t not in HTML_OK:
            W(f'{name}.html: <{tag}> may not be allowed; prefer div/span/img')

    # --- CSS
    for pat, msg in [
        (r'url\(', 'url() in CSS'),
        (r'@import|@font-face', 'loading fonts or files; use the theme font variable'),
        (r'animation(-name)?\s*:\s*var\(', 'animation name from var(): the block renames @keyframes, so it never matches'),
        (r'!important', '!important (the block controls playback with its own classes)'),
    ]:
        for m in re.finditer(pat, css):
            line = css.count('\n', 0, m.start()) + 1
            E(f'{name}.css:{line}: {msg}')
    for m in re.finditer(r'font-family\s*:\s*([^;]+);', css):
        if '--wp--custom--animation--font' not in m.group(1):
            E(f'{name}.css: font-family must be var(--wp--custom--animation--font, "Inter"), sans-serif (found: {m.group(1).strip()})')

    keyframes = {}
    for m in re.finditer(r'@keyframes\s+([\w-]+)\s*\{', css):
        depth, i = 1, m.end()
        while depth and i < len(css):
            depth += {'{': 1, '}': -1}.get(css[i], 0)
            i += 1
        body = css[m.end():i - 1]
        keyframes[m.group(1)] = body
        if 'var(' in body:
            E(f'{name}.css: var() inside @keyframes {m.group(1)} (keep keyframe values literal)')

    rules = re.findall(r'([^{}@]+)\{([^{}]*)\}', re.sub(r'@keyframes\s+[\w-]+\s*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}', '', css))
    looping = set()
    for sel, body in rules:
        sel = re.sub(r'/\*.*?\*/', '', sel, flags=re.S).strip()
        anims = re.findall(r'animation\s*:\s*([^;]+)', body)
        names = [p.strip().split()[0] for a in anims for p in a.split(',')]
        for a in anims:
            for part in a.split(','):
                if 'infinite' in part and 'var(--cycle)' not in part:
                    looping.add(part.strip().split()[0])
                if 'var(--cycle)' in part and 'infinite' not in part:
                    E(f'{name}.css: `{sel}` runs {part.strip().split()[0]} on the cycle without `infinite`: the block\'s Loop setting can\'t repeat it')
        for n in names:
            if n not in keyframes and not n.startswith('var('):
                E(f'{name}.css: `{sel}` uses @keyframes {n}, which is not defined')
        # Judge each selector by its subject (the last compound), e.g. `.lines .r1` -> `.r1`.
        for one in sel.split(','):
            subject = re.split(r'[\s>+~]+', one.strip())[-1]
            sub_classes = set(re.findall(r'\.([\w-]+)', subject))
            moves = TRANSFORMING.search(body) or any(TRANSFORMING.search(keyframes.get(n, '')) for n in names)
            if moves and ((sub_classes and any(sub_classes <= c for c in inner_class_sets)) or re.match(r'(path|circle|g|rect|polygon|ellipse)\b', subject)):
                E(f'{name}.css: `{one.strip()}` transforms a shape inside an SVG; give it its own <div> wrapper and animate that')
            if sub_classes & svg_classes and re.search(r'\b(left|top)\s*:\s*calc', body):
                E(f'{name}.css: `{one.strip()}` positions an <svg> itself (rings drew at full width on the site); put it in a positioned <div>')
    for n in sorted(looping):
        W(f'{name}.css: @keyframes {n} runs on its own clock: keep it to live state (it repeats only with the block\'s Loop on)')

    return errors, warns


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    total = 0
    for arg in sys.argv[1:]:
        errors, warns = lint(Path(arg).resolve())
        print(f'== {arg}: {len(errors)} error(s), {len(warns)} warning(s)')
        for e in errors:
            print('  ERROR', e)
        for w in warns:
            print('  WARN ', w)
        total += len(errors)
    sys.exit(1 if total else 0)


if __name__ == '__main__':
    main()
