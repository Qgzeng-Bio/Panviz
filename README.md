# Panviz

Panviz is the development workspace for a static, publication-oriented
sequence tube map renderer.

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

## Current Run Command

Render all default loci into this development workspace:

```bash
cd /data9/home/qgzeng/projects/3-Biotools_create/Panviz
bash run_panviz_mainfig.sh
```

Render one locus:

```bash
cd /data9/home/qgzeng/projects/3-Biotools_create/Panviz
bash run_panviz_mainfig.sh --only 04_KAS_I_II_KAS_I_II_chr03B --out-root results/smoke_04
```

## Main Files

There is no top-level `sequenceTubeMap/` runtime directory. The required
upstream-derived rendering code has been copied into Panviz-owned source files.


```text
render_pantubemap_mainfig.py        # Python batch/data-conversion entry point
run_panviz_mainfig.sh               # fixed baseline run wrapper
harness/export_mainfig_natural.js   # current custom static export adapter
harness/render_page.html            # local browser render page
harness/tubemap_exact_entry.js      # adapter to the Panviz core renderer
src/panviz_core/tubemap.js          # current upstream-derived Panviz layout core
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

Panviz currently carries a minimal local `node_modules/` runtime dependency copy.
It is not a symlink. The current copied runtime dependency is:

```text
node_modules/playwright-core 1.61.1
```

The browser bundle in `harness/dist/` already contains the bundled Panviz core
and D3-based drawing logic. When the core is edited, rebuild the bundle after
installing the full JavaScript development dependencies.

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

