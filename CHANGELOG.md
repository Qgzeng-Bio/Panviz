# Changelog

All notable changes to Panviz are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Optional SV node annotation (`--annotate-sv` / `annotate_sv` config): labels
  each variant node with its type and signed size (e.g. `INS +10.8 kb`,
  `DEL -3.0 kb`, `SNP 1.8 kb`), placed one ribbon-height above the node box with
  a white halo for legibility. Labels are real (searchable) SVG text. Off by
  default, so the accepted baseline rendering stays byte-identical. Implemented
  Python-side (`sv_label`, payload `svAnnotations`) plus a `drawSvLabels` step in
  the Panviz-owned `harness/lib/postprocess.js`; unit tests added.
- Reproducible JS build: committed `package-lock.json` pinning the bundle
  toolchain. `npm ci && npm run build` now rebuilds
  `harness/dist/sequencetubemap_exact_bundle.js` **deterministically**
  (two builds byte-identical) and reproduces **byte-identical SVG** output for
  the covered loci. The committed bundle was regenerated from the locked
  toolchain (figures unchanged); this unblocks the Stage 6 core fork.

### Changed (repo layout)
- Consolidated all runnable scripts under `scripts/` — the CLI launcher
  (`bin/panviz` → `scripts/panviz`), the baseline wrapper
  (`run_panviz_mainfig.sh`), and the deprecated shim
  (`render_pantubemap_mainfig.py`) — and moved the development handoff into
  `docs/`. The repository root now holds only standard project files (README,
  LICENSE, CHANGELOG, CONTRIBUTING, CITATION, pyproject, package.json, AGENTS),
  and the top-level `bin/` directory was removed. Updated all references
  (README, docs, examples, package.json, CI); rendering output unchanged.

### Fixed (review pass 2)
- Validation severity hardening: non-positive `LN`, non-integer `LN`, duplicate
  segment ids, path tokens without `+/-` orientation, malformed/short `S` lines,
  invalid `n_members`, and malformed region coordinates are now **errors**
  (previously warnings or unchecked), so `panviz render` aborts on inputs that
  could crash the renderer. New unit tests cover these.
- `panviz doctor --config <bad>` now prints a friendly error instead of a
  traceback.
- CI gained a `node --check` step for `export_mainfig_natural.js` and
  `harness/lib/postprocess.js` (Stage 5 JS was previously unexercised).
- README render examples default to the toy locus; the server batch is shown as
  an explicit `PANVIZ_INPUT_ROOT` command.

### Added
- Panviz-owned export layer (Stage 5): in-browser post-processing
  (x-compression, node outlines, genomic axis, scale bar, viewport) extracted
  from the adapter into `harness/lib/postprocess.js`; the adapter is now a thin
  orchestrator. Verified byte-identical output.
- Quality & release scaffolding (Stage 7): `tests/test_unit.py` (15 stdlib
  unit tests), `ruff`/`mypy` config and a `dev` extra, GitHub Actions CI
  (lint + unit tests + offline regression on Python 3.9/3.12), `CONTRIBUTING.md`,
  and `CITATION.cff`.
- `docs/CORE_ARCHITECTURE.md` (Stage 6): ownership map and the gated plan for
  forking the SequenceTubeMap-derived layout core (blocked on the bundle-rebuild
  toolchain and a layout-snapshot guard).

### Fixed (review pass 1)
- Robust render error handling: a `RenderError` now reports missing `node`,
  missing render bundle, node failures (with stderr tail), and unparseable
  renderer output as friendly CLI errors instead of tracebacks.
- Semantic input validation: `panviz validate` and (by default) `panviz render`
  now check that paths reference defined segments, flag missing `Ref`,
  non-positive `LN`/`n_members`, duplicate segment ids, and reversed region
  coordinates — with error/warning severities. Disable with `--no-validate`.
- Output integrity: PNG header/dimension check (expected = panel × scale) is
  folded into the per-locus `ok` status.
- The structural regression test now also enforces **byte-identical** SVG vs the
  committed reference fixture in `--from` mode.
- `PANVIZ_BROWSER` is now authoritative (a wrong path errors clearly instead of
  being silently replaced by auto-detection).
- Config-file relative paths are anchored at the repo root (CWD-independent).
- `write_tsv` ignores extra columns, so path-group TSVs with extra fields no
  longer crash.

### Changed (review pass 1)
- De-localized defaults: the built-in `input_root` and `config/defaults.json`
  now point at `examples/toy_data` (no private `/data9` paths); the server batch
  is reached via `PANVIZ_INPUT_ROOT`. `run_panviz_mainfig.sh` derives its repo
  dir from `BASH_SOURCE` instead of a hard-coded path.
- Documented that Panviz installs editable from a clone (renderer reads repo
  assets by path); README/pyproject clarified. Added
  `LICENSES/THIRD_PARTY_NOTICES.md` for bundled JS (d3, d3-selection-multi,
  deep-equal) and tooling.

### Added
- Reproducible build & setup (Stage 4): `package.json` now declares the bundle
  build toolchain (d3 v5 line, d3-selection-multi, deep-equal, webpack,
  webpack-cli as devDependencies) and a `build` script; `playwright-core` stays
  the only runtime dependency.
- `panviz doctor` command that checks node, Chromium, the render bundle,
  `playwright-core`, and (optionally) the build tools, with fix hints.
- `docs/INSTALL.md` covering Python install, rendering runtime
  (`npm install` + `playwright install chromium`), environment check, a toy
  smoke test, and the advanced bundle-rebuild path with its regression gate.
- Examples & docs (Stage 3): a self-contained synthetic toy locus under
  `examples/` (reproducible via `examples/generate_toy.py`) demonstrating a
  deletion, substitution, and insertion across a reference and five haplotypes,
  with a committed preview figure `examples/toy_locus.png`.
- `docs/INPUT_FORMAT.md` (precise GFA / path_groups / region schema) and
  `docs/FIGURE_ANATOMY.md` (figure element walkthrough, SV reading guide, output
  files, and parameters). README gains a gallery image and 30-second quick start.
- Regression coverage extended to the toy locus (now 3 loci: 01, 04, toy).
- Portability (Stage 2): Chromium browser auto-detection (scans
  `PANVIZ_BROWSER`, `PLAYWRIGHT_BROWSERS_PATH`, `~/.cache/ms-playwright`,
  newest version preferred) and `PANVIZ_*` environment overrides
  (`PANVIZ_INPUT_ROOT`, `PANVIZ_OUT_ROOT`, `PANVIZ_REBUILD_ROOT`,
  `PANVIZ_BROWSER`). Config precedence is now
  defaults < env < `--config` < CLI flags.
- `config/example.json` template for users on other machines.
- Actionable CLI errors (exit code 2, no traceback) when the browser or input
  root is missing, pointing at the fix.
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
