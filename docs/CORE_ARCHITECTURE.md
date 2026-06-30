# Panviz architecture and the core-ownership roadmap (Stage 6)

## Rendering pipeline

```text
panviz (Python)                         Panviz-owned
  config / discover / gfa / validate  ──┐
  render orchestration                  │  writes payload JSON, runs Node
        │                               │
        ▼                               │
harness/export_mainfig_natural.js  ─────┤  thin orchestrator (Panviz-owned)
        │                               │
        ▼                               │
harness/dist/…bundle.js  ◄── src/panviz_core/tubemap.js   SequenceTubeMap-derived (MIT)
   (layout + drawing)                   │
        │                               │
        ▼                               │
harness/lib/postprocess.js  ────────────┘  axis / style / compaction / viewport
   (genomic axis, node outlines,            (Panviz-owned, Stage 5)
    scale bar, viewBox/panel)
        │
        ▼
   SVG / PNG / PDF
```

## Ownership map

| Component | Owner | Notes |
| --- | --- | --- |
| `panviz/` (Python package) | Panviz | data conversion, CLI, validation, orchestration |
| `harness/export_mainfig_natural.js` | Panviz | Chromium launch + export orchestration |
| `harness/lib/postprocess.js` | Panviz | axis, node style, x-compaction, viewport (Stage 5) |
| `src/panviz_core/*.js` | SequenceTubeMap-derived (MIT) | graph **layout + drawing** core |
| `harness/dist/…bundle.js` | built artifact | bundle of the core + d3 |

The only remaining non-Panviz logic is the layout/drawing **core** under
`src/panviz_core/`, kept verbatim (with provenance) as the rendering baseline.

## Stage 6 — forking the layout core

Goal: replace `src/panviz_core/tubemap.js` with Panviz-owned modules:

```text
src/model      graph + track data model
src/layout     node ordering and lane placement
src/geometry   coordinate / path generation
src/style      colors, strokes, node shapes
src/render     SVG emission
```

### Why this is gated, not yet executed

1. **It requires rebuilding the bundle.** `tubemap.js` is compiled into
   `harness/dist/…bundle.js`; any change to the core only takes effect after
   `npm run build`. That needs the JS build toolchain (`d3` v5 line,
   `d3-selection-multi`, `deep-equal`, `webpack`) installed via `npm install`,
   which is currently deferred (large download / network). See
   [INSTALL.md](INSTALL.md) and `package.json`.

2. **It must not change the output.** The hard invariant is byte-identical
   figures. Before any core rewrite, two guards must be in place:
   - the existing SVG byte-exact regression (`tests/check_svg_structure.py`), and
   - a finer **layout snapshot** (pre-post-processing SVG / node+lane geometry)
     so a refactor can be localized, not just detected at the final pixel.

### Recommended execution order (when the toolchain is enabled)

1. Commit a reproducible bundle build (`npm ci` + `package-lock.json`).
2. Add the layout-snapshot guard.
3. Fork one function at a time (node width, lane placement, path generation…),
   each behind the regression + snapshot, preserving MIT provenance for any
   derived portion.
4. Retire `src/panviz_core/` once every function is Panviz-owned, keeping the
   SequenceTubeMap attribution in `LICENSES/`.

Until then, `src/panviz_core/` remains the authoritative baseline core and is
not edited.
