"""Input and output validation for Panviz locus packages.

``validate_locus_input`` performs lightweight, format-level checks so that
problems are reported clearly before a (relatively expensive) browser render.
``validate_output`` checks that exported files exist and are non-empty.
"""
from __future__ import annotations

from pathlib import Path

from .discover import LocusInput

# Columns required in a *_pathcollapsed_SV1kb.path_groups.tsv header.
REQUIRED_PATH_GROUP_COLUMNS = ("collapsed_path",)
# Keys required in region.txt.
REQUIRED_REGION_KEYS = (
    "recommended_SequenceTubeMap_region=",
    "reference_coordinate=",
)


def _check_gfa(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"GFA missing: {path}"]
    if path.stat().st_size == 0:
        return [f"GFA empty: {path}"]
    has_s = has_p = False
    with path.open() as handle:
        for line in handle:
            if line.startswith("S\t"):
                has_s = True
            elif line.startswith("P\t"):
                has_p = True
            if has_s and has_p:
                break
    if not has_s:
        errors.append(f"GFA has no segment (S) lines: {path}")
    if not has_p:
        errors.append(f"GFA has no path (P) lines: {path}")
    return errors


def _check_path_groups(path: Path) -> list[str]:
    if not path.exists():
        return [f"path_groups TSV missing: {path}"]
    if path.stat().st_size == 0:
        return [f"path_groups TSV empty: {path}"]
    header = path.read_text().splitlines()[0].split("\t") if path.read_text() else []
    missing = [c for c in REQUIRED_PATH_GROUP_COLUMNS if c not in header]
    return [f"path_groups TSV missing column {c!r}: {path}" for c in missing]


def _check_region(path: Path) -> list[str]:
    if not path.exists():
        return [f"region file missing: {path}"]
    text = path.read_text()
    return [
        f"region file missing {key!r}: {path}"
        for key in REQUIRED_REGION_KEYS
        if key not in text
    ]


def validate_locus_input(item: LocusInput) -> list[str]:
    """Return a list of validation error messages (empty == valid)."""
    errors: list[str] = []
    errors += _check_gfa(item.gfa)
    errors += _check_path_groups(item.path_groups)
    errors += _check_region(item.region)
    return errors


def validate_output(*paths: Path) -> bool:
    """True only if every path exists and is non-empty."""
    return all(Path(p).exists() and Path(p).stat().st_size > 0 for p in paths)
