# Changelog

All notable changes to Panviz are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Installable `panviz` Python package (stdlib only) splitting the former
  monolithic script into modules: `config`, `discover`, `gfa`, `render`,
  `validate`, and `cli`.
- `panviz` command-line interface with `render`, `validate`, and `version`
  subcommands, plus a `bin/panviz` launcher and a `pyproject.toml` console-script
  entry point (`pip install -e .`).
- Externalised render configuration under `config/` (`defaults.json`,
  `mainfig_baseline.json`) with precedence: defaults < `--config` < CLI flags.
- Input validation (GFA segment/path lines, path_groups columns, region keys)
  via `panviz validate` and an opt-in `panviz render --validate`.
- Structural visual-regression test (`tests/check_svg_structure.py`) with
  committed reference fixtures and per-locus contracts under `tests/baseline/`
  for loci 01 (FAD2) and 04 (KAS_I_II). Runs offline against fixtures or against
  a fresh render via `--from`; exits non-zero on any regression.

### Changed
- `run_panviz_mainfig.sh` now calls `panviz render --config config/mainfig_baseline.json`.
- `render_pantubemap_mainfig.py` is now a thin deprecated shim forwarding to
  `panviz render` (unchanged behaviour and outputs).

### Removed
- Unreferenced legacy export scripts `harness/export_exact.js` and
  `harness/export_mainfig.js` (dead code; not on the active render path).

### Verified
- Render payload for loci 01/04 is byte-identical to the accepted baseline
  `input.json`; a fresh end-to-end render of locus 01 via the new CLI produces a
  byte-identical SVG to the committed reference fixture and passes the regression
  test.

## [0.1.0-baseline] - 2026-06-30

First version-controlled snapshot. Captures the verified rendering baseline so
that all later refactoring toward an independent Panviz tool has a recoverable
reference point.

### Added
- Panviz development workspace separated from the SequenceTubeMap source tree;
  no top-level `sequenceTubeMap/` or `vendor/` runtime directory.
- Upstream-derived rendering core copied into `src/panviz_core/` with provenance
  headers (vgteam/sequenceTubeMap commit
  `33b7a7e5df9f8052974ef8e6c689a031dac6e2c9`, MIT).
- Static SVG/PNG/PDF export pipeline:
  `render_pantubemap_mainfig.py` → `harness/export_mainfig_natural.js` →
  Playwright → `harness/dist/sequencetubemap_exact_bundle.js`.
- Publication baseline parameters: x compression `0.32`, panel width `1800`,
  top genomic axis with endpoint labels, upward-only coordinate ticks, lower
  scale bar, regularized rounded node outlines (stroke `1.5`), no
  `preserveAspectRatio="none"` non-uniform squeezing.
- Verified smoke tests for locus `01_FAD2_FAD2_chr08B` (77 nodes, 16 tracks,
  panel 1800×688) and `04_KAS_I_II_KAS_I_II_chr03B`; both `Status=ok`.
- Project documentation: `README.md`, `AGENTS.md`,
  `docs/DEVELOPMENT_ROADMAP.md`, and the 2026-06-30 development handoff.
- MIT license for Panviz-owned code; upstream MIT preserved in `LICENSES/`.

[Unreleased]: https://example.com/panviz/compare/v0.1.0-baseline...HEAD
[0.1.0-baseline]: https://example.com/panviz/releases/tag/v0.1.0-baseline
