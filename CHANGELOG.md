# Changelog

All notable changes to Panviz are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
