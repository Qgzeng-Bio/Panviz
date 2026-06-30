# Panviz tests

Structural visual-regression checks that protect the accepted rendering
baseline while Panviz is refactored toward an independent tool.

This is a **structural** regression test (SVG geometry, classes, labels,
element counts), not a pixel diff.

## Layout

```text
tests/
├── check_svg_structure.py          # the validator (Python stdlib only)
└── baseline/
    ├── <locus>.expected.json       # the regression contract (human-readable)
    ├── <locus>.reference.svg       # committed reference render (diffable text)
    └── <locus>.metadata.json       # reference render metadata (for count checks)
```

Currently covered loci:

- `01_FAD2_FAD2_chr08B`
- `04_KAS_I_II_KAS_I_II_chr03B`
- `toy_locus` (the bundled synthetic example)

## Run

Offline — validate the committed reference fixtures (no rendering needed):

```bash
cd /data9/home/qgzeng/projects/3-Biotools_create/Panviz
python3 tests/check_svg_structure.py
```

Validate a fresh render (one subdirectory per locus):

```bash
bash scripts/run_panviz_mainfig.sh --only 01_FAD2_FAD2_chr08B --out-root results/check_01
python3 tests/check_svg_structure.py --from results/check_01
```

Restrict to one locus:

```bash
python3 tests/check_svg_structure.py --locus 01_FAD2_FAD2_chr08B
```

Exit code is `0` only if every checked locus passes, so it can gate commits.

## What each contract asserts

- **Byte-exact** match to the committed reference SVG (in `--from` mode, a fresh
  render must be byte-identical to `tests/baseline/<locus>.reference.svg`).
- SVG root `width` / `height` / `viewBox` match the baseline.
- Required classes present: `track`, `node`, `genomic-axis`, `genomic-scale-bar`.
- Required text present: axis endpoint coordinates and the `5 kb` scale bar.
- Forbidden absent: `preserveAspectRatio="none"` (no non-uniform squeezing).
- If render metadata is available, element/panel counts match exactly
  (`input_nodes`, `input_tracks`, `nodeChildren`, `trackChildren`,
  `panelWidth`, `panelHeight`, `viewBoxWidth`, `viewBoxHeight`).

## Updating a baseline

If a rendering change is **intended**, re-render the locus, copy the new
`*_natural.svg` and `*_render_metadata.json` into `tests/baseline/` as the
`<locus>.reference.svg` / `<locus>.metadata.json`, update the matching
`<locus>.expected.json`, and record the change in `CHANGELOG.md`.
