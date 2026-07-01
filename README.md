# Panviz

Panviz is the development workspace for a static, publication-oriented
sequence tube map renderer.

![Panviz toy locus tube map](examples/toy_locus.png)

*Example: the bundled toy locus (`examples/`) showing a deletion, a substitution,
and an insertion across a reference and five haplotypes. See
[docs/FIGURE_ANATOMY.md](docs/FIGURE_ANATOMY.md).*

## Installation

Requirements: **Python ≥ 3.9**, **Node.js ≥ 16**, and **git**.

```bash
# 1. clone
git clone https://github.com/Qgzeng-Bio/Panviz.git
cd Panviz

# 2. install the Python CLI (pure standard library; editable install)
pip install -e .

# 3. install the rendering runtime (needed to draw figures)
npm ci                            # installs playwright-core reproducibly (package-lock.json)
npx playwright install chromium   # download a Chromium build

# 4. check the environment
panviz doctor

# 5. smoke test on the bundled toy locus (no private data needed)
panviz render --config config/mainfig_baseline.json \
  --only toy_locus --out-root results/toy
# -> results/toy/toy_locus/toy_locus_sequencetubemap_mainfig_natural.{svg,pdf,png}
```

Prefer not to install? Run it in place with `python3 scripts/panviz …`. Only
rendering needs Node/Chromium — `panviz validate` and the conversion layer are
pure Python. An editable install (`-e`) is required because the renderer reads
repo assets (`config/`, `harness/`, `src/panviz_core/`) by path.

Documentation: [install details](docs/INSTALL.md) ·
[input format](docs/INPUT_FORMAT.md) ·
[figure anatomy](docs/FIGURE_ANATOMY.md) · [examples](examples/README.md)

This repository starts from the accepted `2-C_quinoa/tmp/Panviz` baseline but
is intended to evolve into an independent plotting tool. The current development version carries an upstream-derived core copy in
`src/panviz_core/`, while Panviz owns the GFA conversion, static export, axis
annotation, horizontal compaction, and publication styling layer.

## Baseline Policy

The accepted rendering scripts and outputs in the quinoa project are kept
unchanged:

```text
/data9/home/qgzeng/projects/2-C_quinoa/tmp/Panviz
/data9/home/qgzeng/projects/2-C_quinoa/tmp/static_svg_rendered_sequencetubemap_mainfig_axis_ticks_x032_trial_20260630
```

Development work should happen here:

```text
/data9/home/qgzeng/projects/3-Biotools_create/Panviz
```

## Command-line interface

After [installation](#installation), the `panviz` command provides:

```bash
panviz render     # convert locus packages and export static SVG/PNG/PDF
panviz validate   # check locus-package inputs without rendering
panviz doctor     # check node / Chromium / bundle / playwright-core
panviz version    # print the Panviz version
```

(Without installing, use `python3 scripts/panviz <subcommand>` instead.)

Render settings resolve with precedence:
built-in defaults < `PANVIZ_*` env vars < `--config <json>` < explicit flags.
See `config/defaults.json` for the full key list. Validation runs before render
by default; disable with `--no-validate`.

Render the bundled toy locus (the default input is `examples/toy_data`):

```bash
bash scripts/run_panviz_mainfig.sh --only toy_locus
# equivalent to:
python3 scripts/panviz render --config config/mainfig_baseline.json \
  --only toy_locus --out-root results/toy
```

Render your own locus packages by pointing at their root:

```bash
python3 scripts/panviz render --config config/mainfig_baseline.json \
  --input-root /path/to/loci --only my_locus --out-root results/my_locus
```

Reproduce the original server batch (set the private input root):

```bash
PANVIZ_INPUT_ROOT=/data9/.../gene_tubemap_all34_pathcollapsed_20260629 \
  bash scripts/run_panviz_mainfig.sh
```

Validate inputs first:

```bash
python3 scripts/panviz validate            # validates examples/toy_data
python3 scripts/panviz validate --input-root /path/to/loci
```

> `scripts/render_pantubemap_mainfig.py` is kept as a deprecated shim that
> forwards to `panviz render`; prefer the CLI.

## Main Files

There is no top-level `sequenceTubeMap/` runtime directory. The required
upstream-derived rendering code has been copied into Panviz-owned source files.


```text
panviz/                             # Panviz Python package (the tool)
  cli.py                            #   command-line interface (render/validate/doctor)
  config.py                         #   defaults + JSON config + precedence merge
  discover.py                       #   locus-package discovery
  gfa.py                            #   GFA/path_groups/region -> render payload
  render.py                         #   render orchestration (-> Node export adapter)
  validate.py                       #   input/output validation
pyproject.toml                      # packaging + `panviz` console script
scripts/panviz                      # CLI launcher (no install required)
config/                             # render configuration
  defaults.json                     #   documented default settings
  mainfig_baseline.json             #   accepted 2026-06-30 baseline parameters
scripts/run_panviz_mainfig.sh       # baseline run wrapper (-> panviz render)
scripts/render_pantubemap_mainfig.py # deprecated shim -> panviz render
harness/export_mainfig_natural.js   # static export adapter (Node + playwright)
harness/lib/postprocess.js          # Panviz axis/style/compaction/viewport
harness/render_page.html            # local browser render page
harness/tubemap_exact_entry.js      # adapter to the Panviz core renderer
src/panviz_core/tubemap.js          # upstream-derived Panviz layout core (MIT)
```

## Current Baseline Parameters

- upstream SequenceTubeMap commit: `33b7a7e5df9f8052974ef8e6c689a031dac6e2c9`
- x compression: `0.32`
- panel width: `1800`
- top genomic axis with endpoint labels
- short upward-only axis ticks
- lower scale bar
- regularized rounded node outlines
- no `preserveAspectRatio="none"` non-uniform SVG squeezing


## JavaScript Runtime Dependencies

`node_modules/` is git-ignored; install it locally with `npm install`. Rendering
needs only `playwright-core` (1.61.1) plus a Chromium build
(`npx playwright install chromium`); the committed bundle in `harness/dist/`
already contains the Panviz core and D3-based drawing logic. The d3/webpack
build tools are `devDependencies`, needed only to rebuild the bundle. See
[docs/INSTALL.md](docs/INSTALL.md). Run `panviz doctor` to check your setup.

## Development Goal

The goal is to turn Panviz from a SequenceTubeMap export adapter into its own
static plotting software. A practical route is:

1. Keep the accepted baseline reproducible.
2. Isolate official SequenceTubeMap-derived code inside `src/panviz_core/` with provenance headers.
3. Move custom logic from `harness/export_mainfig_natural.js` into Panviz-owned
   modules under `src/`.
4. Gradually replace layout, geometry, styling, and axis logic with Panviz
   implementations.
5. Keep visual regression tests against the accepted 17-locus baseline.

## License Note

SequenceTubeMap is MIT licensed. The original license is copied in:

```text
LICENSES/SequenceTubeMap_LICENSE.txt
```

Any Panviz release that includes SequenceTubeMap-derived code must retain the
MIT license notice.

