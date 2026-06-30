#!/usr/bin/env python3
"""Panviz structural visual-regression check.

Validates that a rendered sequence-tube-map SVG still matches the accepted
baseline contract for a locus. This protects the verified rendering while the
project is refactored toward an independent Panviz tool.

It is a STRUCTURAL regression test, not a pixel diff. For each locus it asserts:
  - SVG root width / height / viewBox match the expected values
  - required CSS classes are present (g.track, g.node, genomic-axis, scale-bar)
  - required text labels are present (axis endpoint coordinates, scale bar)
  - forbidden substrings are absent (e.g. preserveAspectRatio="none")
  - if render metadata is available, element/panel counts match exactly

Each locus contract lives in tests/baseline/<locus>.expected.json.

Usage:
  # Offline: validate the committed reference fixtures (default)
  python3 tests/check_svg_structure.py

  # Validate a fresh render directory (one subdir per locus)
  python3 tests/check_svg_structure.py --from results/smoke_01_local_node_modules

  # Restrict to one locus
  python3 tests/check_svg_structure.py --locus 01_FAD2_FAD2_chr08B

Exit code is 0 only if every checked locus passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

BASELINE_DIR = Path(__file__).resolve().parent / "baseline"

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


def _c(text: str, color: str) -> str:
    return f"{color}{text}{RESET}" if sys.stdout.isatty() else text


def parse_svg_root(svg_text: str) -> dict:
    """Extract width/height/viewBox from the opening <svg ...> tag."""
    m = re.search(r"<svg\b[^>]*>", svg_text)
    if not m:
        return {}
    tag = m.group(0)
    out = {}
    for attr in ("width", "height", "viewBox"):
        am = re.search(rf'\b{attr}="([^"]*)"', tag)
        if am:
            out[attr] = am.group(1)
    return out


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_locus(
    spec_path: Path,
    svg_path: Path,
    metadata_path: Path | None,
    reference_svg: Path | None = None,
) -> list[tuple[bool, str]]:
    """Return a list of (passed, message) checks for one locus."""
    results: list[tuple[bool, str]] = []

    def add(ok: bool, msg: str) -> None:
        results.append((bool(ok), msg))

    spec = json.loads(spec_path.read_text())

    if not svg_path.exists():
        add(False, f"SVG not found: {svg_path}")
        return results
    svg_text = svg_path.read_text()
    add(len(svg_text) > 0, f"SVG non-empty ({len(svg_text)} bytes)")

    # 1. SVG root geometry
    root = parse_svg_root(svg_text)
    for key, want in spec.get("svg_root", {}).items():
        got = root.get(key)
        add(got == want, f"svg root {key}: want {want!r}, got {got!r}")

    # 2. Required classes present (>= expected count)
    for cls, want_count in spec.get("required_classes", {}).items():
        got_count = svg_text.count(f'class="{cls}"')
        add(got_count >= want_count, f'class="{cls}" count >= {want_count} (got {got_count})')

    # 3. Required text labels present
    for text in spec.get("required_text", []):
        add(text in svg_text, f"text present: {text!r}")

    # 4. Forbidden substrings absent
    for bad in spec.get("forbidden_substrings", []):
        add(bad not in svg_text, f"forbidden absent: {bad!r}")

    # 5. Metadata counts (optional)
    want_counts = spec.get("metadata_counts", {})
    if want_counts:
        if metadata_path and metadata_path.exists():
            counts = json.loads(metadata_path.read_text()).get("counts", {})
            for key, want in want_counts.items():
                got = counts.get(key)
                add(got == want, f"metadata count {key}: want {want}, got {got}")
        else:
            add(False, f"metadata json not found (counts unchecked): {metadata_path}")

    # Byte-exact regression: a fresh render must match the committed reference
    # SVG exactly. Skipped when validating the reference against itself.
    if reference_svg and reference_svg.exists() and reference_svg.resolve() != svg_path.resolve():
        add(
            _sha256(svg_path) == _sha256(reference_svg),
            f"SVG byte-identical to reference fixture ({reference_svg.name})",
        )

    return results


def resolve_inputs(locus: str, from_dir: Path | None) -> tuple[Path, Path, Path | None, Path]:
    """Return (spec_path, svg_path, metadata_path, reference_svg) for a locus."""
    spec_path = BASELINE_DIR / f"{locus}.expected.json"
    reference_svg = BASELINE_DIR / f"{locus}.reference.svg"
    if from_dir is None:
        # Offline: validate the committed reference fixtures themselves.
        return spec_path, reference_svg, BASELINE_DIR / f"{locus}.metadata.json", reference_svg
    # Fresh render: locate output files under <from_dir>/<locus>/.
    locus_dir = from_dir / locus
    svgs = sorted(locus_dir.glob("*_natural.svg"))
    metas = sorted(locus_dir.glob("*_render_metadata.json"))
    svg_path = svgs[0] if svgs else locus_dir / f"{locus}.svg"
    meta_path = metas[0] if metas else None
    return spec_path, svg_path, meta_path, reference_svg


def main() -> int:
    ap = argparse.ArgumentParser(description="Panviz structural visual-regression check")
    ap.add_argument(
        "--from",
        dest="from_dir",
        default=None,
        help="render output root to validate (one subdir per locus); "
        "default validates committed reference fixtures",
    )
    ap.add_argument("--locus", action="append", help="restrict to locus (repeatable)")
    args = ap.parse_args()

    from_dir = Path(args.from_dir).resolve() if args.from_dir else None

    if args.locus:
        loci = args.locus
    else:
        loci = sorted(p.name[: -len(".expected.json")] for p in BASELINE_DIR.glob("*.expected.json"))

    if not loci:
        print(_c("No locus contracts found in tests/baseline/.", RED))
        return 2

    mode = f"fresh render under {from_dir}" if from_dir else "committed reference fixtures"
    print(f"Panviz visual regression — validating {mode}\n")

    all_passed = True
    for locus in loci:
        spec_path, svg_path, meta_path, reference_svg = resolve_inputs(locus, from_dir)
        if not spec_path.exists():
            print(_c(f"[SKIP] {locus}: no expected.json contract", RED))
            all_passed = False
            continue
        checks = check_locus(spec_path, svg_path, meta_path, reference_svg)
        passed = sum(1 for ok, _ in checks if ok)
        total = len(checks)
        locus_ok = passed == total
        all_passed = all_passed and locus_ok
        head = _c("PASS", GREEN) if locus_ok else _c("FAIL", RED)
        print(f"[{head}] {locus}  ({passed}/{total} checks)")
        for ok, msg in checks:
            mark = _c("  ok ", GREEN) if ok else _c("  XX ", RED)
            line = f"{mark} {msg}"
            print(line if ok else _c(line, RED))
        print()

    summary = _c("ALL LOCI PASS", GREEN) if all_passed else _c("REGRESSION DETECTED", RED)
    print(f"==> {summary}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
