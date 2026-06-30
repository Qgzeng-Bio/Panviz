# HANDOFF 2026-06-30 Panviz development

## Current Objective

Develop Panviz as an independent static sequence-tube-map plotting software under:

```text
/data9/home/qgzeng/projects/3-Biotools_create/Panviz
```

The accepted oil-palm key-gene pan-visualization final rendering result must remain unchanged unless explicitly requested:

```text
/data9/home/qgzeng/projects/2-C_quinoa/tmp/Panviz
/data9/home/qgzeng/projects/2-C_quinoa/tmp/static_svg_rendered_sequencetubemap_mainfig_axis_ticks_x032_trial_20260630
```


## Final Oil-Palm Key-Gene Pan-Visualization Result

The final accepted result directory for the current oil-palm key-gene pan-visualization figure set is:

```text
/data9/home/qgzeng/projects/2-C_quinoa/tmp/static_svg_rendered_sequencetubemap_mainfig_axis_ticks_x032_trial_20260630
```

Treat this directory as the final/currently satisfactory figure output. Do not overwrite, move, or delete it unless the user explicitly asks.

This result contains the 17-locus batch output with per-locus SVG/PNG/PDF/input JSON/metadata files plus `render_summary.tsv`. The accepted visual style includes:

- x compression: `0.32`
- panel width: `1800`
- top chromosome coordinate axis
- endpoint coordinate labels
- short upward-only coordinate ticks
- lower scale bar, e.g. `5 kb` for 01
- regularized rounded node outlines
- node stroke width: `1.5`
- no `preserveAspectRatio="none"` non-uniform SVG squeezing

The 01 output from this final directory was visually accepted by the user and used as the reference style for later Panviz development smoke tests.

## 2026-06-30 Drawing Progress Summary

Today's rendering work progressed through these stages:

1. Reused the official SequenceTubeMap layout/rendering logic as the baseline renderer.
2. Added a natural main-figure export layer rather than using non-uniform SVG squeezing.
3. Set x-coordinate compression to `0.32` for a compact main-figure panel.
4. Regularized node outlines into rounded boxes with consistent stroke settings.
5. Added a top genomic coordinate axis with labels such as `chr08B:14.05-14.11 Mb`.
6. Replaced endpoint-only axis labels with a true ruler: visible ticks and Mb labels.
7. Shortened coordinate-axis tick marks so they only extend upward from the axis.
8. Added explicit endpoint coordinate labels, e.g. `14.046 Mb` and `14.107 Mb` for 01.
9. Added/kept the lower scale bar, e.g. `5 kb` for 01.
10. Batch-rendered all 17 loci into the final accepted result directory above.
11. Verified SVG/PDF/PNG outputs were non-empty and retained `g.track`, `g.node`, `genomic-axis`, and `genomic-scale-bar`.
12. Started the independent Panviz development workspace under `/data9/home/qgzeng/projects/3-Biotools_create/Panviz`.
13. Moved the upstream-derived rendering core into Panviz-owned `src/panviz_core/` and removed top-level or vendor `sequenceTubeMap/` runtime directories.
14. Replaced the `node_modules` symlink with a local minimal runtime dependency copy: `node_modules/playwright-core 1.61.1`.
15. Verified the development Panviz workspace with 01 and 04 smoke tests under `results/`.

## Current Status

Panviz has been separated from the visible `sequenceTubeMap/` directory structure.
There is no top-level `sequenceTubeMap/` or `vendor/sequenceTubeMap/` runtime directory in the development workspace.

The upstream-derived core code has been copied into Panviz-owned source files:

```text
src/panviz_core/tubemap.js
src/panviz_core/common.mjs
src/panviz_core/config-client.js
src/panviz_core/config-global.mjs
src/panviz_core/config.json
```

`src/panviz_core/tubemap.js` has a provenance header:

```text
Derived from vgteam/sequenceTubeMap src/util/tubemap.js
upstream commit 33b7a7e5df9f8052974ef8e6c689a031dac6e2c9.
Original project license: MIT; see LICENSES/SequenceTubeMap_LICENSE.txt.
```

## Current Directory Layout

```text
Panviz/
├── AGENTS.md
├── README.md
├── package.json
├── render_pantubemap_mainfig.py
├── run_panviz_mainfig.sh
├── LICENSES/
│   └── SequenceTubeMap_LICENSE.txt
├── docs/
│   └── DEVELOPMENT_ROADMAP.md
├── harness/
│   ├── export_mainfig_natural.js
│   ├── render_page.html
│   ├── tubemap_exact_entry.js
│   ├── webpack.exact.config.js
│   └── dist/sequencetubemap_exact_bundle.js
├── src/
│   ├── README.md
│   └── panviz_core/
├── node_modules/
│   └── playwright-core/
└── results/
```

## Runtime Dependencies

`node_modules` is now a real local directory, not a symlink.

Current runtime dependency copied into Panviz:

```text
node_modules/playwright-core 1.61.1
```

Why only this dependency exists:

- The D3-based core is already bundled into `harness/dist/sequencetubemap_exact_bundle.js`.
- Runtime SVG/PNG/PDF export only needs `playwright-core` to launch Chromium.
- Editing `src/panviz_core/tubemap.js` requires rebuilding the bundle, which will need full JS build dependencies later: `d3`, `d3-selection-multi`, `deep-equal`, `webpack`, `webpack-cli`.

`package.json` records this current state.

## Current Render Flow

```text
render_pantubemap_mainfig.py
  -> converts GFA/path_groups/region to Panviz JSON
  -> calls harness/export_mainfig_natural.js
  -> Playwright opens harness/render_page.html
  -> render_page.html loads harness/dist/sequencetubemap_exact_bundle.js
  -> bundle was built from harness/tubemap_exact_entry.js
  -> tubemap_exact_entry.js imports ../src/panviz_core/tubemap.js
  -> SVG/PNG/PDF written to results/
```

Important current command:

```bash
cd /data9/home/qgzeng/projects/3-Biotools_create/Panviz
bash run_panviz_mainfig.sh
```

Test one locus:

```bash
cd /data9/home/qgzeng/projects/3-Biotools_create/Panviz
bash run_panviz_mainfig.sh --only 01_FAD2_FAD2_chr08B --out-root results/smoke_01_local_node_modules
```

## Verified Tests

### 01 smoke test

Command:

```bash
cd /data9/home/qgzeng/projects/3-Biotools_create/Panviz
bash run_panviz_mainfig.sh --only 01_FAD2_FAD2_chr08B --out-root results/smoke_01_local_node_modules
```

Result:

```text
Status: ok
Nodes: 77
Tracks: 16
Panel: 1800 x 688
PNG: 3600 x 1376
```

Output:

```text
results/smoke_01_local_node_modules/01_FAD2_FAD2_chr08B/
```

Validation:

- SVG/PDF/PNG non-empty.
- SVG contains `class="track"`.
- SVG contains `class="node"`.
- SVG contains `class="genomic-axis"`.
- SVG contains `class="genomic-scale-bar"`.
- Endpoint labels `14.046 Mb` and `14.107 Mb` present.
- Lower `5 kb` scale bar present.
- No `preserveAspectRatio="none"`.

### 04 smoke tests

Known passing outputs:

```text
results/smoke_04_panviz_core/
results/smoke_04_local_node_modules/
```

Both reported `Status=ok` for `04_KAS_I_II_KAS_I_II_chr03B`.

## Baseline Visual Parameters

Current accepted visual behavior inherited from the quinoa baseline:

- x compression: `0.32`
- panel width: `1800`
- top genomic axis with endpoint coordinates
- short upward-only coordinate ticks
- lower scale bar
- regularized rounded node outlines
- node stroke width: `1.5`
- no non-uniform SVG squeezing via `preserveAspectRatio="none"`

## Important Files

Current core:

```text
src/panviz_core/tubemap.js
```

Current static export adapter:

```text
harness/export_mainfig_natural.js
```

Current browser bundle:

```text
harness/dist/sequencetubemap_exact_bundle.js
```

Current Python batch/data conversion entry:

```text
render_pantubemap_mainfig.py
```

Current fixed wrapper:

```text
run_panviz_mainfig.sh
```

Development notes:

```text
README.md
docs/DEVELOPMENT_ROADMAP.md
src/README.md
AGENTS.md
```

## Next Development Steps

Recommended next steps, in order:

1. Add a real Panviz CLI layer, for example `bin/panviz` or `src/cli/`.
2. Move axis code from `harness/export_mainfig_natural.js` into `src/axis/`.
3. Move node-outline regularization from `harness/export_mainfig_natural.js` into `src/style/`.
4. Move panel/viewBox/export sizing from `harness/export_mainfig_natural.js` into `src/export/`.
5. Decide whether GFA conversion stays Python or moves into `src/io/`.
6. Add a small visual regression script comparing 01 and 04 SVG structure.
7. Only after these are stable, begin refactoring `src/panviz_core/tubemap.js` into smaller modules.

Do not start by heavily editing `src/panviz_core/tubemap.js`; it is still the current baseline rendering core.

## Known Caveats

- `harness/dist/sequencetubemap_exact_bundle.js` must be rebuilt after editing `src/panviz_core/tubemap.js` or `harness/tubemap_exact_entry.js`.
- Current Panviz has only minimal runtime JS dependency copied locally: `playwright-core`.
- Rebuilding the bundle requires full build dependencies, currently not all copied into Panviz.
- Full JS dependency plan should be handled later by creating a proper `package-lock.json` and running `npm ci` when network/package installation is allowed.
- Playwright/Chromium rendering usually needs elevated tool permissions in Codex because the restricted sandbox blocks browser process/socket operations.

## Safety Notes

- Do not modify `/data9/home/qgzeng/data/`.
- Do not modify `/data9/home/qgzeng/tools/`.
- Do not modify the accepted oil-palm key-gene final result under `/data9/home/qgzeng/projects/2-C_quinoa/tmp/static_svg_rendered_sequencetubemap_mainfig_axis_ticks_x032_trial_20260630` unless the user explicitly asks.
- Do not modify the accepted baseline scripts under `/data9/home/qgzeng/projects/2-C_quinoa/tmp/Panviz` unless the user explicitly asks.
- New development renders should go under:

```text
/data9/home/qgzeng/projects/3-Biotools_create/Panviz/results/
```

## One-Sentence Resume Prompt

Continue Panviz development in `/data9/home/qgzeng/projects/3-Biotools_create/Panviz`: use `src/panviz_core/` as the current upstream-derived Panviz core, keep the 2-C quinoa tmp Panviz baseline unchanged, and next start modularizing `harness/export_mainfig_natural.js` into Panviz-owned `src/axis`, `src/style`, and `src/export` while preserving the passing 01/04 smoke tests.
