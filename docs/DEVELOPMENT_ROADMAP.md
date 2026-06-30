# Panviz Development Roadmap

The hard invariant throughout: **the rendering output must not change**. Every
stage is gated by `tests/check_svg_structure.py` (structural + byte-exact vs the
committed reference fixtures).

## Stage 0 — Git foundation ✅

- MIT `LICENSE`, `.gitattributes`, `CHANGELOG`, baseline commit + tag
  `v0.1.0-baseline`.

## Stage 1 — Software packaging ✅

- Installable `panviz` package (config / discover / gfa / render / validate /
  cli), `scripts/panviz`, `pyproject.toml`, externalised `config/`.

## Stage 2 — Portability ✅

- Chromium auto-detection, `PANVIZ_*` env overrides, friendly CLI errors.

## Stage 3 — Examples & documentation ✅

- Synthetic toy locus (`examples/`), `docs/INPUT_FORMAT.md`,
  `docs/FIGURE_ANATOMY.md`, README gallery + quick start.

## Stage 4 — Reproducible build & self-check ✅

- `package.json` build toolchain, `panviz doctor`, `docs/INSTALL.md`.

## Stage 5 — Panviz-owned export layer

- Move axis generation, node-outline regularization, and panel/viewBox sizing
  from `harness/export_mainfig_natural.js` into Panviz-owned modules under
  `harness/` / `src/`. Node-side post-processing — no bundle rebuild required.

## Stage 6 — Panviz-owned layout core

- Fork the layout-controlling parts of `src/panviz_core/tubemap.js` into
  Panviz modules (model / layout / geometry / style / render), preserving MIT
  provenance. Guard with layout snapshots in addition to SVG byte-equality.

## Stage 7 — Quality & release

- Unit tests (gfa / config / validate), `ruff` + `mypy`, GitHub Actions CI,
  `CONTRIBUTING.md`, semantic versioning, v1.0.0 release, optional PyPI /
  Zenodo DOI + `CITATION.cff`.
