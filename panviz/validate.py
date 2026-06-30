"""Input and output validation for Panviz locus packages.

``validate_locus_input`` returns a list of ``(severity, message)`` issues where
severity is ``"error"`` or ``"warning"``:

- **error** — would crash the renderer or produce a wrong figure (missing files,
  empty graph, a path referencing an undefined segment, a malformed region).
- **warning** — suspicious but renderable (no ``Ref`` path, non-positive lengths
  or member counts, duplicate segment ids, reversed coordinates).

``panviz render`` aborts on errors by default (override with ``--no-validate``)
and prints warnings; ``panviz validate`` reports both and exits non-zero on any
error. ``validate_output`` checks exported files; ``png_dimensions`` reads a
PNG's pixel size from its header (standard library only).
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

from .discover import LocusInput

Issue = tuple[str, str]  # (severity, message)

REQUIRED_PATH_GROUP_COLUMNS = ("collapsed_path",)
REQUIRED_REGION_KEYS = (
    "recommended_SequenceTubeMap_region=",
    "reference_coordinate=",
)
_COORD_RE = re.compile(r"=([^:]+):(\d+)-(\d+)\s*$")


def _strip_orientation(token: str) -> str:
    return token[:-1] if token and token[-1] in "+-" else token


def _parse_gfa(path: Path) -> tuple[dict[str, int | None], dict[str, list[str]], list[str]]:
    """Return (segments name->LN, paths name->tokens, duplicate segment names)."""
    segments: dict[str, int | None] = {}
    paths: dict[str, list[str]] = {}
    duplicates: list[str] = []
    with path.open() as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if not fields or not fields[0]:
                continue
            if fields[0] == "S" and len(fields) >= 2:
                name = fields[1]
                length: int | None = None
                for tag in fields[3:]:
                    parts = tag.split(":", 2)
                    if len(parts) == 3 and parts[0] == "LN" and parts[1] == "i":
                        try:
                            length = int(parts[2])
                        except ValueError:
                            length = None
                if name in segments:
                    duplicates.append(name)
                segments[name] = length
            elif fields[0] == "P" and len(fields) >= 3:
                paths[fields[1]] = [t for t in fields[2].split(",") if t]
    return segments, paths, duplicates


def _check_gfa(path: Path) -> list[Issue]:
    if not path.exists():
        return [("error", f"GFA missing: {path}")]
    if path.stat().st_size == 0:
        return [("error", f"GFA empty: {path}")]

    segments, paths, duplicates = _parse_gfa(path)
    issues: list[Issue] = []
    if not segments:
        issues.append(("error", f"GFA has no segment (S) lines: {path}"))
    if not paths:
        issues.append(("error", f"GFA has no path (P) lines: {path}"))

    if duplicates:
        uniq = ", ".join(sorted(set(duplicates))[:5])
        issues.append(("warning", f"duplicate segment ids ({uniq}): {path}"))

    bad_len = sorted(n for n, ln in segments.items() if ln is not None and ln <= 0)
    if bad_len:
        issues.append(("warning", f"segments with non-positive LN ({', '.join(bad_len[:5])}): {path}"))

    if paths and "Ref" not in paths:
        issues.append(("warning", f"no reference path named 'Ref': {path}"))

    # Every path token must reference a defined segment.
    missing: set[str] = set()
    for tokens in paths.values():
        for token in tokens:
            name = _strip_orientation(token)
            if name not in segments:
                missing.add(name)
    if missing:
        sample = ", ".join(sorted(missing)[:5])
        issues.append(("error", f"path references undefined segment(s) ({sample}): {path}"))
    return issues


def _check_path_groups(path: Path) -> list[Issue]:
    if not path.exists():
        return [("error", f"path_groups TSV missing: {path}")]
    text = path.read_text()
    if not text.strip():
        return [("error", f"path_groups TSV empty: {path}")]
    lines = text.splitlines()
    header = lines[0].split("\t")
    issues: list[Issue] = [
        ("error", f"path_groups TSV missing column {c!r}: {path}")
        for c in REQUIRED_PATH_GROUP_COLUMNS
        if c not in header
    ]
    if "n_members" in header:
        idx = header.index("n_members")
        for row in lines[1:]:
            cells = row.split("\t")
            if len(cells) <= idx or not cells[idx]:
                continue
            try:
                if int(cells[idx]) <= 0:
                    raise ValueError
            except ValueError:
                issues.append(("warning", f"invalid n_members {cells[idx]!r} in {path}"))
                break
    return issues


def _check_region(path: Path) -> list[Issue]:
    if not path.exists():
        return [("error", f"region file missing: {path}")]
    text = path.read_text()
    issues: list[Issue] = []
    for key in REQUIRED_REGION_KEYS:
        line = next((ln for ln in text.splitlines() if ln.startswith(key)), None)
        if line is None:
            issues.append(("error", f"region file missing {key!r}: {path}"))
            continue
        match = _COORD_RE.search(line)
        if match and int(match.group(2)) >= int(match.group(3)):
            issues.append(("error", f"region {key.rstrip('=')} start >= end: {line.strip()}"))
    return issues


def validate_locus_input(item: LocusInput) -> list[Issue]:
    """Return a list of (severity, message) issues (empty == fully valid)."""
    return _check_gfa(item.gfa) + _check_path_groups(item.path_groups) + _check_region(item.region)


def has_errors(issues: list[Issue]) -> bool:
    return any(sev == "error" for sev, _ in issues)


def png_dimensions(path: Path) -> tuple[int, int] | None:
    """Return (width, height) from a PNG header, or None if not a valid PNG."""
    try:
        with Path(path).open("rb") as handle:
            head = handle.read(24)
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def validate_output(*paths: Path) -> bool:
    """True only if every path exists and is non-empty."""
    return all(Path(p).exists() and Path(p).stat().st_size > 0 for p in paths)
