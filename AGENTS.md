# AGENTS.md - Panviz Development

Scope: `/data9/home/qgzeng/projects/3-Biotools_create/Panviz`.

Panviz is the development workspace for a static sequence-tube-map plotting
tool. The accepted quinoa rendering baseline remains under:

```text
/data9/home/qgzeng/projects/2-C_quinoa/tmp/Panviz
/data9/home/qgzeng/projects/2-C_quinoa/tmp/static_svg_rendered_sequencetubemap_mainfig_axis_ticks_x032_trial_20260630
```

Development rules:

- Do not modify the accepted baseline unless the user explicitly asks.
- Default new renders to this project's `results/` directory.
- Keep SequenceTubeMap-derived code identifiable and preserve the MIT license.
- Prefer adding Panviz-owned modules under `src/` instead of editing
  `src/panviz_core/tubemap.js` directly.
- When changing rendering behavior, run at least one smoke test and compare
  SVG structure for `g.track`, `g.node`, and coordinate-axis elements.

