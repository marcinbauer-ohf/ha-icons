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
- The radius is a build setting, 4 px by default: `uv run build.py --radius N` re-renders the whole set. Rectangles and filled shapes scale with it. A pointed or thin filled shape that would lose more than a tenth of its area keeps the 2 px radius it was drawn with, and 2 px lines cannot get rounder than fully round. (build)

## Filled variant

- Built from solid masses. Detail is cut out as negative space, not drawn as extra lines. (by eye)
- A cut-out is never smaller than 2 x 2 px. (lint)
- Avoid large blobs and avoid slivers thinner than 2 px. (by eye)
- A large, plain, rounded mass may carry one glint: a short 2 px dash cut out near its edge, about 3 px long and angled to follow the curve (the bulb, the water drop, the shield). It goes bottom left by default (the water drop, the shield). It goes top right only when bottom left would run into the off slash (the bulb). It never goes bottom right, where a badge would cut it away, and it is left out when it would crowd other detail, as in `shield-check`. The stroked variant draws the arc as a line only where it keeps a clear gap to the outline; the stroked water drop is too small for one. (by eye)

## Stroked variant

- Same skeleton and proportions as the filled variant, `fill="none"` on the root, 2 px strokes. (lint for the attributes, by eye for the proportions)
- An icon that is just strokes (close, plus, check, chevrons, arrows, reload, chart-line, wifi, snowflake, sleep) is the same drawing in both variants: 2 px lines, with nothing to fill. It has one authoring file, `icons/<name>.stroked.svg`, and the build uses it for the filled set too. (build)

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
- The cut that makes room for a badge hugs the badge, with a 2 px gap at the closest point. It never takes a whole corner out of the base. (build)
- The off slash lies over the icon. On its lower-left side it merges with the base; only its upper-right side is cut back, by about 2 px. (build)
- A cut-out keeps a 2 px wall to a badge cut. The part of a cut-out that comes closer is filled in, so a clock or timer keeps most of its hands. If less than half of the cut-out would be left, or less than 2 x 2 px, it is filled in completely and the build flags the icon. Filled variant only. The off slash is the exception: it is meant to cross the icon, cut-outs included. (build)
- A badge cut must not leave sharp corners. Corners and line ends created by the cut are rounded. (build)
- A cut never takes under 1 px² from any part of the icon. This is judged per piece: where the cut would only graze a part (the edge of the head in `account-lock`), that part is left whole, and the cut still applies where it takes a real bite. (build)
- A badge cut must not nick the base. If it removes between 1 and 4 px² of the base, the icon is flagged and needs a hand-drawn version. (build warns)
- A piece that a cut splits off or whittles down to under 8 px² (a 2 px line shorter than 4 px) is too small to read and is removed. Parts the cut never touched are kept, however small. (build)
- A pinhole under 1 px² that a cut leaves behind is filled in. (build)
- A suffix is only a modifier when it means one. `toggle-switch-off` is a state, so it is drawn by hand. (by eye)
- The badge keeps its corner. When it would cover the part that identifies the icon (the handle of the magnifier in `magnify-plus`), that part is moved or mirrored in a hand-drawn version so both stay visible. (by eye)
- When a line of the icon runs parallel to the off slash and would vanish into it (the arrowhead in `download-off`), the icon is redrawn by hand with that part clear of the slash. (by eye)
- When the build cannot make a derived icon work, draw it by hand: add `icons/<name>.filled.svg` and `icons/<name>.stroked.svg`. A hand-drawn file always wins. (build)

## Reuse

- An icon that reuses another icon records it. Derived icons record their base and modifier automatically; hand-drawn ones list them in `data-uses="name:role"`, with roles `base`, `badge` or `cutout`. The relationships are written to `dist/relations.json`. (build)

## Motion (experiment)

- The main body of an icon is always visible. An icon never fades, slides or scales in as a whole. (by eye)
- Only parts move, and the movement says what the thing does: fan blades spin, wifi waves light up, a bell swings. (by eye)
- Motion is for an active state. An idle icon stands still. (by eye)
- Parts that move are marked in the authoring file with `data-anim`, and the root describes the movement in `data-motion`. The keyframes live in the preview template. (build)
- Motion stops when the viewer has asked for reduced motion. (build)
- The static icon must be complete on its own; motion never carries the meaning alone. (by eye)
- A part that only exists while the icon moves (the charge level in `battery`) is marked `display="none"`, so the static icon and the built path never show it. (build)

## Waivers

- A rule can be knowingly switched off for one icon after it has been reviewed. The waiver goes in `waivers.json` as icon, rule and reason. A waived rule no longer fails the build; it shows on the icon as a note, in the preview's Issues view under "Waived", and as the filter "A rule is waived for this icon". (build)
- Rules that can be waived: `gap` (a gap or cut-out under 1 px), `small` (a cut-out or fragment under 2 x 2 px), `bounds` (paint outside the live area), `nick` (a badge cut that only nicks the base), `filled-cutout` (a cut-out lost to a badge).
- Current waivers: `flash-off`, `star-off`, `lightbulb-off` and `lock-off` for `gap`, where the off slash leaves a narrow pocket; `map-marker-minus` for `nick`.

## Pictogrammers metadata

- Every icon keeps its MDI name, and with it Pictogrammers' own record: categories, search aliases, author and the version it was added in. The build copies these from the MDI package into `dist/metadata.json`; they are never edited by hand. (build)

## Outline names

- An MDI `-outline` name is not an icon of its own. It is the stroked variant of its base and is listed in `dist/outline-aliases.json`. Draw it only when it means something different. (build)

## Display

- In a tile card the icon is shown at 32 px in a 40 px container. 32 sits on the 4 px grid and is pixel-exact on 3x screens; 34 is never pixel-exact. (by eye)
