# ha-icons

A redrawn icon set for Home Assistant: every Material Design Icons concept, rebuilt on a 24 px grid in a filled and a stroked variant. The rules are in [RULES.md](RULES.md).

- `icons/` holds the hand-drawn authoring SVGs. `template.svg` has the drawing guides.
- `build.py` lints them, derives modifier variants (plus, minus, check, alert, lock, off), and flattens everything to single paths.
- `worker/` signs reviewers in with GitHub so they can comment and set an icon's status from the preview. Setup is in [worker/README.md](worker/README.md).

```bash
uv run build.py
```

Output goes to `dist/`: `filled.json` and `stroked.json` (name to path), `relations.json`, `outline-aliases.json`, and `sheet.html`, the preview.

The preview compares against MDI when the originals are present. Fetch them once:

```bash
mkdir -p vendor/mdi && npm pack @mdi/svg --pack-destination vendor && tar -xzf vendor/mdi-svg-*.tgz -C vendor/mdi --strip-components=1
```

Icon names and concepts come from [Material Design Icons](https://pictogrammers.com/library/mdi/) (Apache 2.0). The drawings are new.
