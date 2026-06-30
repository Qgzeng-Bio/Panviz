# Contributing to Panviz

Thanks for your interest in improving Panviz. This guide covers the dev setup,
the test suite, and the one rule that matters most: **don't change the rendering
output unless you mean to.**

## Development setup

```bash
git clone git@github.com:Qgzeng-Bio/Panviz.git
cd Panviz
pip install -e ".[dev]"     # editable install + ruff/mypy

# rendering runtime (only needed to actually draw figures)
npm install
npx playwright install chromium
panviz doctor               # check your environment
```

## Tests and checks

```bash
# lint + types
ruff check panviz tests
mypy panviz

# unit tests
python -m unittest discover -s tests -p 'test_*.py' -v

# structural visual-regression (offline, against committed fixtures)
python tests/check_svg_structure.py

# end-to-end regression for a fresh render (needs node + Chromium)
panviz render --config config/mainfig_baseline.json \
  --only toy_locus --out-root results/check
python tests/check_svg_structure.py --from results/check
```

CI (`.github/workflows/ci.yml`) runs ruff, the unit tests, and the offline
regression on Python 3.9 and 3.12.

## The rendering invariant

The accepted figures must stay **byte-for-byte identical** unless a change is
intentional. Every PR that touches `panviz/`, `harness/`, or `src/panviz_core/`
must keep `python tests/check_svg_structure.py` green, and a fresh render
(`--from`) must remain byte-identical to the fixtures in `tests/baseline/`.

### Intentionally changing the figure

If you *mean* to change the output:

1. Re-render the covered loci (`01`, `04`, `toy_locus`).
2. Copy the new `*_natural.svg` and `*_render_metadata.json` into
   `tests/baseline/` as `<locus>.reference.svg` / `<locus>.metadata.json`.
3. Update the matching `<locus>.expected.json` contract.
4. Describe the visual change in `CHANGELOG.md`.

## Rebuilding the render bundle

Editing `src/panviz_core/` or `harness/tubemap_exact_entry.js` requires rebuilding
`harness/dist/` — see [docs/INSTALL.md](docs/INSTALL.md). The core uses d3 v5
APIs; stay on the d3 v5 line, and re-run the regression after rebuilding.

## Commit style

Conventional-commit prefixes (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`,
`chore:`) with a short imperative summary. Keep commits focused.
