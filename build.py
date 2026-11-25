# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["skia-pathops"]
# ///
"""Lint authoring SVGs in icons/, flatten each to one filled path, write dist/.

Run: uv run build.py [--radius 2]
  icons/<name>.<filled|stroked>.svg   authoring source (hand drawn)
  dist/svg/                           authoring SVG for every built name (incl. composed)
  dist/<variant>.json                 {name: single path d}
  dist/relations.json                 {name: {uses: [{icon, role}], used_in: [names]}}
  dist/outline-aliases.json           {mdi -outline name: base name whose stroked variant replaces it}
  dist/sheet.html                     contact sheet for visual review
"""
import argparse, json, math, pathlib, re, sys
import xml.etree.ElementTree as ET
from pathops import ArcSize, Direction, LineCap, LineJoin, Path, PathOp, PathVerb
from pathops import op as _op

ROOT = pathlib.Path(__file__).parent
NS = "{http://www.w3.org/2000/svg}"
VARIANTS = ("filled", "stroked")
SHAPES = {"rect", "circle", "line", "polyline", "polygon", "path"}
ATTRS = {"viewBox", "fill", "stroke", "stroke-width", "stroke-linejoin", "stroke-linecap", "x", "y", "width",
         "height", "rx", "cx", "cy", "r", "x1", "y1", "x2", "y2", "points", "d", "id", "mask",
         "data-keyline", "data-overflow", "data-exceptions", "data-r", "data-uses"}
NUM = r"-?\d*\.?\d+"
# Corner radius. Authoring SVGs are drawn for radius 2; --radius re-renders the whole set at another value.
# K scales every rounding: rect rx, polygon data-r, the stroke on filled masses, and line joins and caps.
K = 1.0

# Modifier kit: one fixed glyph + one fixed cut per suffix, shared by every icon and both variants.
# Badges sit 1 px into the padding (paint up to 23) so the base icon keeps more room.
# Each cut hugs its glyph (1 px gap at the closest point) so it never takes more of the base than it needs.
G = 'fill="none" stroke="currentColor" stroke-width="2"'
CUT = 'fill="none" stroke="#000" stroke-width="4"'
ROUND_CUT = '<circle cx="19" cy="19" r="5" fill="#000" stroke="none"/>'
MODS = {
    "plus": (f'<path d="M16 19H22M19 16V22" {G}/>', ROUND_CUT),
    "minus": (f'<path d="M16 19H22" {G}/>', f'<path d="M16 19H22" {CUT}/>'),
    "check": (f'<polyline points="16,19 18,21 21,18" {G}/>', ROUND_CUT),
    "alert": (f'<path d="M19 16V19" {G}/><circle cx="19" cy="22" r="1" fill="currentColor" stroke="none"/>',
              f'<path d="M19 16V22" {CUT}/>'),
    "lock": ('<rect x="15" y="18" width="8" height="5" rx="1" fill="currentColor" stroke="none"/>'
             f'<path d="M17 18V15A2 2 0 0 1 21 15V18" {G}/>',
             '<rect x="14" y="11" width="10" height="13" rx="2" fill="#000" stroke="none"/>'),
    "off": (f'<path d="M4 4L20 20" {G}/>', f'<path d="M4 4L20 20" {CUT}/>'),
}
WARNINGS = []  # filled by modifier_cut, drained per icon in main


def op(a, b, how):
    for p in (a, b):  # skia's winding fix cannot read conics
        p.convertConicsToQuads(0.02)
    return _op(a, b, how)


def tag(el):
    return el.tag.removeprefix(NS)


def path_cmds(d):
    """Yield (cmd, args) for absolute M L H V A Z; anything else raises."""
    toks = re.findall(rf"[A-Za-z]|{NUM}", d)
    need = {"M": 2, "L": 2, "H": 1, "V": 1, "A": 7, "Z": 0}
    i = 0
    while i < len(toks):
        c = toks[i]
        if c not in need:
            raise ValueError(f"path command {c!r} not allowed (only M L H V A Z)")
        i += 1
        if c == "Z":
            yield c, []
            continue
        first = True
        while first or (i < len(toks) and toks[i] not in need and not toks[i].isalpha()):
            yield ("L" if c == "M" and not first else c), [float(t) for t in toks[i:i + need[c]]]
            i += need[c]
            first = False


def arc(p, r, x, y, large=False, sweep=True):
    p.arcTo(r, r, 0, ArcSize.LARGE if large else ArcSize.SMALL, Direction.CW if sweep else Direction.CCW, x, y)


def geom(el):
    f = lambda k: float(el.get(k, 0))
    t, p = tag(el), Path()
    if t == "rect":
        x, y, w, h, r = f("x"), f("y"), f("width"), f("height"), f("rx")
        r = r if r > 2 else min(r * K, w / 2, h / 2)
        p.moveTo(x + r, y)
        for lx, ly, ax, ay in ((x + w - r, y, x + w, y + r), (x + w, y + h - r, x + w - r, y + h),
                               (x + r, y + h, x, y + h - r), (x, y + r, x + r, y)):
            p.lineTo(lx, ly)
            if r:
                arc(p, r, ax, ay)
        p.close()
    elif t == "circle":
        cx, cy, r = f("cx"), f("cy"), f("r")
        p.moveTo(cx + r, cy)
        arc(p, r, cx - r, cy)
        arc(p, r, cx + r, cy)
        p.close()
    elif t == "line":
        p.moveTo(f("x1"), f("y1"))
        p.lineTo(f("x2"), f("y2"))
    elif t == "polygon" and f("data-r") * K:
        fillet(p, [float(v) for v in re.findall(NUM, el.get("points", ""))], f("data-r") * K)
    elif t in ("polyline", "polygon"):
        n = [float(v) for v in re.findall(NUM, el.get("points", ""))]
        p.moveTo(n[0], n[1])
        for i in range(2, len(n), 2):
            p.lineTo(n[i], n[i + 1])
        if t == "polygon":
            p.close()
    else:
        x = y = 0
        for c, a in path_cmds(el.get("d", "")):
            if c == "Z":
                p.close()
                continue
            if c == "A":
                arc(p, a[0], a[5], a[6], bool(a[3]), bool(a[4]))
            x, y = (a[0], y) if c == "H" else (x, a[0]) if c == "V" else (a[-2], a[-1])
            if c == "M":
                p.moveTo(x, y)
            elif c != "A":
                p.lineTo(x, y)
    return p


def fillet(p, n, r):
    """Closed polygon with every corner replaced by an arc of radius r (less where edges are short)."""
    pts = list(zip(n[::2], n[1::2]))
    for i, v in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % len(pts)]
        ua, ub = (a[0] - v[0], a[1] - v[1]), (b[0] - v[0], b[1] - v[1])
        la, lb = math.hypot(*ua), math.hypot(*ub)
        half = math.acos(max(-1, min(1, (ua[0] * ub[0] + ua[1] * ub[1]) / la / lb))) / 2
        t = min(r / math.tan(half), la / 2, lb / 2)
        start = (v[0] + ua[0] / la * t, v[1] + ua[1] / la * t)
        (p.lineTo if i else p.moveTo)(*start)
        arc(p, t * math.tan(half), v[0] + ub[0] / lb * t, v[1] + ub[1] / lb * t, sweep=ua[0] * ub[1] - ua[1] * ub[0] < 0)
    p.close()


def stroked(p, width, cap=LineCap.ROUND_CAP, join=LineJoin.ROUND_JOIN):
    s = Path(p)
    s.stroke(width, cap, join, 10 if join == LineJoin.MITER_JOIN else 4)
    return s


def line_region(g, sw):
    """A stroke whose joins and caps have radius K * sw/2 (never more than sw/2)."""
    rho = min(K, 1) * sw / 2
    if rho > sw / 2 - 1e-6:
        return op(Path(), stroked(g, sw), PathOp.UNION)
    sharp = op(Path(), stroked(g, sw, LineCap.SQUARE_CAP, LineJoin.MITER_JOIN), PathOp.UNION)
    if rho < 1e-6:
        return sharp
    core = op(sharp, stroked(sharp, 2 * rho), PathOp.DIFFERENCE)  # opening: erode, then dilate
    return op(core, stroked(core, 2 * rho), PathOp.UNION)


def mass_region(g, nominal):
    """A filled shape drawn inset by `nominal` with a stroke of 2 * nominal: corners get radius K * nominal,
    straight edges stay where they are."""
    rho = K * nominal
    if abs(rho - nominal) < 1e-6:
        return op(g, stroked(g, 2 * nominal), PathOp.UNION)
    if rho < nominal:
        core = op(g, stroked(g, 2 * (nominal - rho), LineCap.BUTT_CAP, LineJoin.MITER_JOIN), PathOp.UNION)
    else:
        core = op(g, stroked(g, 2 * (rho - nominal)), PathOp.DIFFERENCE)
        if not contours(core):  # too thin to take this much rounding: keep it as drawn
            return op(g, stroked(g, 2 * nominal), PathOp.UNION)
    return op(core, stroked(core, 2 * rho), PathOp.UNION) if rho > 1e-6 else core


def union(paths):
    out = Path()
    for p in paths:
        out = op(out, p, PathOp.UNION)
    return out


def area(el, style, ids):
    """Painted region of an element as a Path. Masks subtract their non-white children."""
    style = {**style, **{k: el.get(k) for k in ("fill", "stroke", "stroke-width") if el.get(k)}}
    t = tag(el)
    if t in ("svg", "g"):
        out = union(area(c, style, ids) for c in el if tag(c) != "mask")
        if m := el.get("mask"):
            cut = union(area(c, style, ids) for c in ids[m[5:-1]] if c.get("fill") != "#fff")
            if m.startswith("url(#mod-"):
                return modifier_cut(out, cut, solid=style.get("fill") != "none")
            out = op(out, cut, PathOp.DIFFERENCE)
        return out
    filled = style.get("fill") != "none" and t != "line"
    sw = float(style.get("stroke-width", 1)) if style.get("stroke", "none") != "none" else 0
    if filled and sw:
        return mass_region(geom(el), sw / 2)
    return line_region(geom(el), sw) if sw else geom(el) if filled else Path()


def contours(p):
    """[[('M'|'L'|'Q'|'C', points...)]], one list per contour."""
    # ponytail: arcs become many short quads (long path strings); emit A commands if file size matters
    p.convertConicsToQuads(0.02)
    out = []
    for verb, pts in p:
        if verb == PathVerb.MOVE:
            out.append([("M", pts[0])])
        elif verb != PathVerb.CLOSE:
            out[-1].append(("L" if verb == PathVerb.LINE else "Q" if verb == PathVerb.QUAD else "C", *pts))
    return out


def to_d(p):
    n = lambda v: f"{round(v, 2):g}"
    return "".join("".join(s[0] + " ".join(f"{n(x)} {n(y)}" for x, y in s[1:]) for s in c) + "Z" for c in contours(p))


def sharp_corners(p):
    """Convex line-to-line vertices on outer contours (holes and concave joins may be sharp)."""
    cs, found = contours(p), []
    signed = [signed_area(c) for c in cs]
    if not cs:
        return found
    outer = math.copysign(1, max(signed, key=abs))
    for c, sa in zip(cs, signed):
        if sa * outer <= 0:
            continue
        segs = [(c[i - 1][-1], s[-1], s[0]) for i, s in enumerate(c) if i]
        if segs[-1][1] != c[0][-1]:
            segs.append((segs[-1][1], c[0][-1], "L"))  # implicit closing line
        segs = [s for s in segs if s[0] != s[1]]
        for (a0, a1, ka), (b0, b1, kb) in zip(segs, segs[1:] + segs[:1]):
            if ka == kb == "L":
                turn = math.atan2(b1[1] - b0[1], b1[0] - b0[0]) - math.atan2(a1[1] - a0[1], a1[0] - a0[0])
                turn = math.remainder(turn, math.tau)
                if abs(turn) > math.radians(10) and turn * sa > 0:  # convex only; concave joins are fine
                    found.append(f"({a1[0]:g},{a1[1]:g})")
    return found


def lint_source(root, variant):
    """Rules that only make sense on hand-written authoring SVG."""
    errs = []
    exempt = root.get("data-exceptions")
    if root.get("viewBox") != "0 0 24 24":
        errs.append("viewBox must be 0 0 24 24")
    if root.get("stroke-linejoin") != "round" or root.get("stroke-linecap") != "round":
        errs.append("root needs stroke-linejoin and stroke-linecap round")
    if variant == "stroked" and root.get("fill") != "none":
        errs.append("stroked root needs fill none")

    for u in root.get("data-uses", "").split():  # a hand-drawn badge must be the shared glyph, not a variation
        n, _, role = u.partition(":")
        if role == "badge" and n in MODS:
            have = [(tag(e), e.attrib) for e in root.iter()]
            if any((tag(e), e.attrib) not in have for e in ET.fromstring(f"<g>{MODS[n][0]}</g>")):
                errs.append(f"the {n} badge differs from the shared glyph in build.py (MODS)")

    def walk(el, in_mask):
        t = tag(el)
        if t not in SHAPES | {"svg", "g", "mask"}:
            errs.append(f"<{t}> not allowed")
        in_mask = in_mask or t == "mask"
        for k, v in el.attrib.items():
            if k not in ATTRS:
                errs.append(f"attribute {k} not allowed")
            if k in ("fill", "stroke") and v not in (("#fff", "#000", "none") if in_mask else ("currentColor", "none")):
                errs.append(f'{k}="{v}" not allowed {"inside" if in_mask else "outside"} a mask')
            if k == "data-r" and t != "polygon":
                errs.append("data-r (corner radius) is only supported on <polygon>")
            if k == "stroke-width" and v not in ("2", "4"):
                errs.append(f"stroke-width {v} (only 2 or 4)")
            if k == "stroke-width" and v == "4" and variant == "stroked" and not in_mask:
                errs.append("stroke-width 4 is for filled masses, not the stroked variant")
            if not exempt and not k.startswith("data-") and k not in ("viewBox", "id", "mask") \
                    and any("." in n for n in re.findall(NUM, v)):
                errs.append(f'{k}="{v}" has decimals (add data-exceptions="why" if needed)')
        if t == "path":
            try:
                x = y = 0
                for c, a in path_cmds(el.get("d", "")):
                    if c == "A":
                        r, dx, dy = a[0], (x - a[5]) / 2, (y - a[6]) / 2
                        k = r * r / (dx * dx + dy * dy) - 1 if dx or dy else -1
                        if a[0] != a[1] or a[2]:
                            errs.append("arcs must be circular (rx = ry, no rotation)")
                        elif k < -1e-9:
                            errs.append(f"arc radius {r:g} too small for its endpoints")
                        elif not exempt:
                            k = math.sqrt(max(k, 0)) * (1 if a[3] != a[4] else -1)
                            cx, cy = k * dy + (x + a[5]) / 2, -k * dx + (y + a[6]) / 2
                            if abs(cx - round(cx)) > 1e-6 or abs(cy - round(cy)) > 1e-6:
                                errs.append(f"arc centre ({cx:.2f},{cy:.2f}) not on whole pixels")
                    if c != "Z":
                        x, y = (a[0], y) if c == "H" else (x, a[0]) if c == "V" else (a[-2], a[-1])
            except ValueError as e:
                errs.append(str(e))
        for c in el:
            walk(c, in_mask)

    walk(root, False)
    return errs


def lint_shape(p, overflow):
    errs = []
    lo, hi = (1, 23) if overflow else (2, 22)
    b = p.bounds
    if min(b[0], b[1]) < lo - 0.01 or max(b[2], b[3]) > hi + 0.01:
        errs.append(f"paint {[round(v, 2) for v in b]} outside {lo}..{hi}")
    fat = Path(p)
    fat.stroke(0.96, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN, 4)
    if len(contours(op(p, fat, PathOp.UNION))) != len(contours(p)):
        errs.append("a gap or cut-out is under 1 px")
    for hole, w, h, x, y in small_parts(p):
        errs.append(f"{'cut-out' if hole else 'fragment'} at ({x:.1f},{y:.1f}) is {w:.1f} x {h:.1f}, minimum is 2 x 2")
    return errs


def signed_area(c):
    pts = [s[-1] for s in c]
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))


def small_parts(p, keep=None):
    """(is_hole, w, h, x, y) for contours under 2 x 2. With keep, collect the other contours there."""
    cs, found = contours(p), []
    outer = math.copysign(1, max(map(signed_area, cs), key=abs)) if cs else 1
    for c in cs:
        xs, ys = [q[0] for s in c for q in s[1:]], [q[1] for s in c for q in s[1:]]
        w, h, hole = max(xs) - min(xs), max(ys) - min(ys), signed_area(c) * outer < 0
        if min(w, h) < 1.98:
            found.append((hole, w, h, min(xs), min(ys)))
        if keep is not None and (hole or min(w, h) >= 1.98):
            keep.append(c)
    return found


def to_path(cs):
    out = Path()
    for c in cs:
        for k, *pts in c:
            getattr(out, {"M": "moveTo", "L": "lineTo", "Q": "quadTo", "C": "cubicTo"}[k])(*(v for q in pts for v in q))
        out.close()
    return out


def without_crumbs(p):
    """Drop fragments under 2 x 2 that a modifier cut leaves behind."""
    keep = []
    if not any(not hole for hole, *_ in small_parts(p, keep)):
        return p
    return to_path(keep)


def modifier_cut(base, cut, solid):
    """Cut a modifier badge's space out of a base icon without leaving damage (see RULES.md, Modifiers)."""
    cs = contours(base)
    outer = math.copysign(1, max(map(signed_area, cs), key=abs)) if cs else 1
    if solid:
        # A cut-out the badge would open, or leave a wall under 2 px next to, is filled in instead.
        for c in cs:
            hole = to_path([c])
            if signed_area(c) * outer < 0 and contours(op(op(hole, stroked(hole, 4), PathOp.UNION), cut, PathOp.INTERSECTION)):
                base = op(base, hole, PathOp.UNION)
    taken = sum(abs(signed_area(c)) for c in contours(op(base, cut, PathOp.INTERSECTION))) / 2
    if 0.5 < taken < 4:  # under half a square pixel is a graze nobody can see
        WARNINGS.append(f"modifier cut only nicks the base ({taken:.1f} px²); draw this icon by hand")
    out = op(base, cut, PathOp.DIFFERENCE)
    r = 0.75 * min(K, 1)  # under half a 2 px line, so a cut line keeps a solid core while its end rounds off
    if r < 0.05 or not contours(out):
        return out
    # Round the corners the cut created (opening), but only near the cut: the rest stays exactly as drawn.
    core = op(out, stroked(out, 2 * r), PathOp.DIFFERENCE)
    opened = op(core, stroked(core, 2 * r), PathOp.UNION)
    # skia's stroker leaves pinholes when it thickens something thinner than the stroke; fill them
    keep, sign = [], math.copysign(1, max(map(signed_area, contours(opened)), key=abs))
    for c in contours(opened):
        xs, ys = [q[0] for s in c for q in s[1:]], [q[1] for s in c for q in s[1:]]
        if signed_area(c) * sign > 0 or min(max(xs) - min(xs), max(ys) - min(ys)) >= 1.98:
            keep.append(c)
    opened = op(to_path(keep), Path(), PathOp.UNION)
    near = op(cut, stroked(cut, 6), PathOp.UNION)
    return op(op(out, near, PathOp.DIFFERENCE), op(opened, near, PathOp.INTERSECTION), PathOp.UNION)


def source(name, variant):
    """Authoring SVG text: hand-drawn file, else base + modifier."""
    f = ROOT / "icons" / f"{name}.{variant}.svg"
    if f.exists():
        return f.read_text()
    base, _, suffix = name.rpartition("-")
    if not base:
        return None
    if suffix in MODS and (src := source(base, variant)):
        head, body = re.match(r"(<svg[^>]*>)(.*)</svg>", src, re.S).groups()
        glyph, cut = MODS[suffix]
        return (f'{head}<mask id="mod-{suffix}"><rect width="24" height="24" fill="#fff"/>{cut}</mask>'
                f'<g mask="url(#mod-{suffix})">{body.strip()}</g>{glyph}</svg>\n')
    return None


def uses(name, drawn):
    """[[icon, role]] this icon is built from. Roles: base, badge (small modifier glyph), cutout."""
    if name in drawn:
        declared = ET.fromstring(source(name, "filled")).get("data-uses", "")
        return [u.split(":") if ":" in u else [u, "part"] for u in declared.split()]
    base, _, suffix = name.rpartition("-")
    return [[base, "base"], [suffix, "badge"]]


def markdown(text):
    """Just enough Markdown for RULES.md: headings, bullet lists, paragraphs, `code`, **bold**."""
    out, in_list = [], False
    for line in text.splitlines():
        line = re.sub(r"`([^`]+)`", r"<code>\1</code>", line.replace("&", "&amp;").replace("<", "&lt;"))
        line = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", line)
        line = re.sub(r"\((lint|build|by eye)([^)]*)\)$", r'<span class="how \1">\1\2</span>', line)
        if in_list and not line.startswith("- "):
            out.append("</ul>")
            in_list = False
        if line.startswith("- "):
            out.append(("" if in_list else "<ul>") + f"<li>{line[2:]}</li>")
            in_list = True
        elif m := re.match(r"(#+) (.*)", line):
            out.append(f"<h{len(m[1])}>{m[2]}</h{len(m[1])}>")
        elif line.strip():
            out.append(f"<p>{line}</p>")
    return "".join(out) + ("</ul>" if in_list else "")


def main():
    global K
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--radius", type=float, default=2, help="corner radius in px (default 2, the radius the icons are drawn for)")
    radius = ap.parse_args().radius
    K = radius / 2
    drawn = sorted({f.name.split(".")[0] for f in (ROOT / "icons").glob("*.svg")})
    wanted = json.loads((ROOT / "ha-default-icons.json").read_text())
    bases = {n[:-8] for n in wanted if n.endswith("-outline")}  # built so the outline name has something to alias
    names = [n for n in sorted(set(drawn) | set(wanted) | bases) if source(n, "filled") and source(n, "stroked")]
    names.sort(key=lambda n: (n not in ("circle", "square"), n))
    # An -outline name is not an icon of its own: it is the stroked variant of its base.
    # Draw icons/<name>-outline.*.svg only when the outline means something different.
    aliases = {n: n[:-8] for n in sorted(wanted) if n.endswith("-outline") and n not in names and n[:-8] in names}
    dist = ROOT / "dist"
    (dist / "svg").mkdir(parents=True, exist_ok=True)
    out, defs, meta, failed = {v: {} for v in VARIANTS}, [], [], 0
    for name in names:
        cells, notes = [], []
        for v in VARIANTS:
            src = source(name, v)
            root = ET.fromstring(src)
            ids = {el.get("id"): el for el in root.iter() if el.get("id")}
            hand = (ROOT / "icons" / f"{name}.{v}.svg").exists()
            errs = lint_source(root, v) if hand else []
            try:
                p = area(root, {}, ids)
                if not hand:
                    p = without_crumbs(p)
                errs += lint_shape(p, bool(root.get("data-overflow")) or not hand)
                d = to_d(p)
                if hand and (sc := sharp_corners(p)):
                    notes.append(f"{v}: sharp outer corner at {' '.join(sc[:4])}")
            except Exception as e:  # keep going so the sheet shows every failure
                errs.append(f"flatten failed: {e}")
                d = ""
            (dist / "svg" / f"{name}.{v}.svg").write_text(src)
            out[v][name] = d
            notes += [f"{v}: {w}" for w in WARNINGS]
            WARNINGS.clear()
            for k in ("overflow", "exceptions"):
                if root.get(f"data-{k}"):
                    notes.append(f"{v} {k}: {root.get(f'data-{k}')}")
            failed += bool(errs)
            notes += [f"ERROR {v}: {e}" for e in errs]
            cells.append(d)
        for n in notes:
            print(f"{name}: {n}")
        mdi_file = ROOT / "vendor" / "mdi" / "svg" / f"{name}.svg"
        mdi = re.search(r' d="([^"]*)"', mdi_file.read_text()).group(1) if mdi_file.exists() else ""
        # each path is written once as a <symbol>; the sheet's script reuses it at every size
        defs.append("".join(f'<symbol id="{name}-{k}" viewBox="0 0 24 24"><path d="{d}"/></symbol>'
                            for k, d in (("filled", cells[0]), ("stroked", cells[1]), ("mdi", mdi)) if d))
        meta.append({"n": name, "d": name in drawn, "b": name.rpartition("-")[0], "m": bool(mdi), "e": any(n.startswith("ERROR") for n in notes),
                     "k": ET.fromstring(source(name, "filled")).get("data-keyline", "?"), "u": uses(name, drawn),
                     "s": [len(cells[0]), len(cells[1]), len(mdi)], "t": notes})
    for v in VARIANTS:
        (dist / f"{v}.json").write_text(json.dumps(out[v], indent=0))
    (dist / "outline-aliases.json").write_text(json.dumps(aliases, indent=0))
    relations = {m["n"]: {"uses": [{"icon": n, "role": r} for n, r in m["u"]],
                          "used_in": [o["n"] for o in meta if any(n == m["n"] for n, _ in o["u"])]} for m in meta}
    (dist / "relations.json").write_text(json.dumps(relations, indent=1))
    page = (ROOT / "sheet.template.html").read_text()
    for k, v in (("defs", "".join(defs)), ("data", json.dumps(meta)), ("radius", f"{radius:g}"),
                 ("rules", markdown((ROOT / "RULES.md").read_text()))):
        page = page.replace("{{" + k + "}}", v)
    (dist / "sheet.html").write_text(page)
    print(f"{len(names)} icons built ({len(drawn)} drawn, {len(names) - len(drawn)} derived), "
          f"{len(aliases)} outline names aliased to a stroked base, {len(wanted)} in the Home Assistant list, {failed} variant(s) with errors")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
