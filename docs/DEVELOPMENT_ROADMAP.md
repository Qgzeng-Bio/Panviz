# Panviz Development Roadmap

## Stage 0: Baseline Preservation

- Keep `/data9/home/qgzeng/projects/2-C_quinoa/tmp/Panviz` unchanged.
- Treat the 2026-06-30 accepted figures as visual regression references.
- Run smoke tests into `results/`, not into the accepted quinoa output directory.

## Stage 1: Software Packaging

- Add a stable command-line interface.
- Move configurable visual settings into a JSON/YAML config.
- Split data conversion, rendering, and export into separate modules.
- Add validation for GFA, path group TSV, region file, and output integrity.

## Stage 2: Panviz-Owned Static Export Core

- Move axis generation from `harness/export_mainfig_natural.js` into `src/axis`.
- Move node-outline regularization into `src/style`.
- Move viewport/panel sizing into `src/export`.
- Add visual regression checks for SVG structure and PNG dimensions.

## Stage 3: Panviz-Owned Layout Core

- Fork the parts of `src/panviz_core/tubemap.js` that control layout.
- Refactor into:

```text
src/model
src/layout
src/geometry
src/style
src/axis
src/render_svg
src/export
```

- Replace official node-width and lane-placement rules with Panviz rules.
- Preserve provenance for any SequenceTubeMap-derived functions.

## Stage 4: Independent Release

- Remove dependency on project-local paths.
- Provide installation instructions.
- Include toy example data.
- Include a methods paragraph and citation/license notes.

