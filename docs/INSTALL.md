# Installing Panviz

Panviz has two layers:

- a **Python** layer (data conversion + CLI) — pure standard library;
- a **rendering** layer (Node + a Chromium browser) that turns the graph into
  SVG/PNG/PDF using a prebuilt JavaScript bundle.

For most users the committed bundle means you only need Node, Chromium, and
`playwright-core` — you do **not** need to rebuild anything.

## 1. Python CLI

```bash
git clone git@github.com:Qgzeng-Bio/Panviz.git
cd Panviz

# run without installing
python3 scripts/panviz --help

# or install the console script (no third-party Python deps)
pip install -e .
panviz --help
```

Requires Python ≥ 3.9.

## 2. Rendering runtime (to actually draw figures)

```bash
# Node.js >= 16 must be on PATH
node --version

# install the headless-browser launcher used by the renderer
npm install            # installs playwright-core (and dev build tools)

# install a Chromium build for Playwright
npx playwright install chromium
```

Panviz auto-detects the Chromium it finds under `~/.cache/ms-playwright` (or
`PLAYWRIGHT_BROWSERS_PATH`). Override with `--browser` or `PANVIZ_BROWSER` if
needed.

## 3. Check your environment

```bash
panviz doctor
```

This reports whether `node`, Chromium, the render bundle, and `playwright-core`
are present, and flags the optional build tools.

## 4. Smoke test

```bash
panviz render --config config/mainfig_baseline.json \
  --input-root examples/toy_data --only toy_locus --out-root results/toy
```

You should get `results/toy/toy_locus/…natural.{svg,pdf,png}` matching
[`examples/toy_locus.png`](../examples/toy_locus.png).

---

## Rebuilding the render bundle (advanced)

Only needed if you edit `src/panviz_core/` or `harness/tubemap_exact_entry.js`.

```bash
npm ci                 # reproducible install from the committed package-lock.json
                       # (d3 v5 line, d3-selection-multi, deep-equal, webpack)
npm run build          # webpack -> harness/dist/sequencetubemap_exact_bundle.js
```

`npm ci && npm run build` rebuilds the bundle deterministically (two builds are
byte-identical) and reproduces byte-identical SVG output for the covered loci.

> The core uses d3 **v5** APIs (`d3.event`) and `d3-selection-multi`; stay on the
> d3 v5 line. The committed bundle is the authoritative baseline. **After any
> rebuild**, run the regression check and byte-compare before committing a new
> bundle:
>
> ```bash
> panviz render --config config/mainfig_baseline.json \
>   --only 01_FAD2_FAD2_chr08B --out-root results/rebuild_check
> python3 tests/check_svg_structure.py --from results/rebuild_check
> ```

`package-lock.json` is committed, so `npm ci` pins the exact build toolchain.
