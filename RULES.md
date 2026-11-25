# Icon set rules

The rules this icon set follows today. Each rule says how it is enforced: **lint** means `build.py` fails the icon, **build** means `build.py` applies it automatically, **by eye** means nothing checks it and it is judged in the preview.

## Goal

- Redraw every Material Design Icons (MDI) concept under these rules. Keep the MDI name and meaning; do not trace the MDI outline. (by eye)
- Every icon ships in two variants built from the same skeleton: **filled** (primary) and **stroked** (secondary). (build)

## Canvas

- Canvas is 24 x 24 px, `viewBox="0 0 24 24"`. (lint)
- Paint stays inside 2..22, a 20 px live area with 2 px padding. (lint)
- An icon may reach 1 px into the padding (1..23) when it would otherwise look too small. Mark it with `data-overflow="reason"`. Never paint within 1 px of the canvas edge. (lint)
- Keylines keep optical size equal: circle 20, square 18 x 18, portrait 16 x 20, landscape 20 x 16. Record the one used in `data-keyline`. (by eye)

## Coordinates

- Every coordinate, size and radius in an authoring file is a whole number. Use `data-exceptions="reason"` when a half pixel is unavoidable. (lint)
- Arcs are circular and their centre lands on a whole pixel, so only quarter arcs, half arcs and 3-4-5 arcs are possible. (lint)
- Stroke width is 2 or 4. In the stroked variant only 2 is allowed; 4 is for building filled masses. (lint)
- Prefer horizontal, vertical and 45 degree segments. (by eye)

## Primitives

- Allowed elements: `rect`, `circle`, `line`, `polyline`, `polygon`, `path`, plus `g` and `mask` for cut-outs. (lint)
- Paths use only `M L H V A Z`, absolute. No Bezier commands. (lint)
- `stroke-linejoin` and `stroke-linecap` are `round` on the root. (lint)
- Colour is `currentColor`. Inside a `mask`, `#fff` and `#000` are allowed and nothing else. No gradients, opacity, filters or transforms. (lint)

## Corners

- No sharp convex corners on the outer silhouette. (build reports them as a note)
- Authoring files are drawn for a corner radius of 2 px on large parts and 1 px on small parts. (by eye)
- Rectangles are rounded with `rx`. An `rx` above 2 means a pill and stays a pill. (build)
- A filled shape that is not a rectangle is drawn inset by the radius with a same-colour stroke of twice the radius. (build)
- A stroked polygon gets rounded centreline corners from `data-r`. Plain joins only round the outside by 1 px. (build)
- The radius is a build setting: `uv run build.py --radius N` re-renders the whole set. The useful range is 0 to 2. (build)

## Filled variant

- Built from solid masses. Detail is cut out as negative space, not drawn as extra lines. (by eye)
- A cut-out is never smaller than 2 x 2 px. (lint)
- Avoid large blobs and avoid slivers thinner than 2 px. (by eye)

## Stroked variant

- Same skeleton and proportions as the filled variant, `fill="none"` on the root, 2 px strokes. (lint for the attributes, by eye for the proportions)
- Pure line glyphs (close, plus, check, chevrons) are the same drawing in both variants. (by eye)

## Spacing

- A gap between two parts, or a cut-out, is never under 1 px. 2 px is preferred between major parts. (lint for 1 px)
- No double roundings: a small part must not be a round-capped stroke sitting right against another stroke (the battery terminal). Merge the two into one shape or leave a clear gap. (by eye)

## Readability

- Silhouette first: the icon reads from its outer shape alone. (by eye)
- One idea per icon. (by eye)
- Consistent optical weight against the plain circle and square. (by eye)
- Optical, not geometric, centring for asymmetric shapes. (by eye)
- Face forward and flat; no perspective. (by eye)
- Two icons never differ by a 1 px detail only. (by eye)
- Judge at 24 px, light and dark, next to neighbours. (by eye)

## Modifiers (plus, minus, check, alert, lock, off)

- Each modifier has one fixed glyph, size and position across the set. (build)
- A modifier badge may sit 1 px into the padding, so paint may reach 23. (lint allows it)
- The cut that makes room for a badge hugs the badge, with a 1 px gap at the closest point. It never takes a whole corner out of the base. (build)
- A badge cut must not break an existing cut-out. If the cut would open a cut-out (the lock's keyhole, the house's door) or leave a wall under 2 px beside it, the cut-out is filled in instead. Filled variant only. (build)
- A badge cut must not leave sharp corners. Corners and line ends created by the cut are rounded. (build)
- A badge cut must not nick the base. If it removes under 4 px² of the base, the icon is flagged and needs a hand-drawn version. (build warns)
- Fragments under 2 x 2 px left behind by a cut are dropped. (build)
- A suffix is only a modifier when it means one. `toggle-switch-off` is a state, so it is drawn by hand. (by eye)
- When the build cannot make a derived icon work, draw it by hand: add `icons/<name>.filled.svg` and `icons/<name>.stroked.svg`. A hand-drawn file always wins. (build)

## Reuse

- An icon that reuses another icon records it. Derived icons record their base and modifier automatically; hand-drawn ones list them in `data-uses="name:role"`, with roles `base`, `badge` or `cutout`. The relationships are written to `dist/relations.json`. (build)

## Outline names

- An MDI `-outline` name is not an icon of its own. It is the stroked variant of its base and is listed in `dist/outline-aliases.json`. Draw it only when it means something different. (build)

## Display

- In a tile card the icon is shown at 32 px in a 40 px container. 32 sits on the 4 px grid and is pixel-exact on 3x screens; 34 is never pixel-exact. (by eye)
