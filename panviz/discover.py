"""Discover path-collapsed GFA locus packages under an input root.

A locus package is a directory containing exactly one
``*_pathcollapsed_SV1kb.gfa``, one ``*_pathcollapsed_SV1kb.path_groups.tsv``,
and a ``region.txt``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class LocusInput:
    locus: str
    gfa: Path
    path_groups: Path
    region: Path


def discover_loci(input_root: Path, only: list[str] | None) -> list[LocusInput]:
    input_root = Path(input_root)
    if not input_root.exists():
        raise FileNotFoundError(f"input root not found: {input_root}")
    loci: list[LocusInput] = []
    wanted = set(only or [])
    for locus_dir in sorted(p for p in input_root.iterdir() if p.is_dir()):
        if wanted and locus_dir.name not in wanted:
            continue
        gfas = sorted(locus_dir.glob("*_pathcollapsed_SV1kb.gfa"))
        groups = sorted(locus_dir.glob("*_pathcollapsed_SV1kb.path_groups.tsv"))
        region = locus_dir / "region.txt"
        if not gfas and not groups and not region.exists():
            continue
        if len(gfas) != 1 or len(groups) != 1 or not region.exists():
            raise FileNotFoundError(f"incomplete locus package: {locus_dir}")
        loci.append(LocusInput(locus_dir.name, gfas[0], groups[0], region))
    if wanted:
        found = {item.locus for item in loci}
        missing = sorted(wanted - found)
        if missing:
            raise FileNotFoundError(f"requested loci not found: {', '.join(missing)}")
    if not loci:
        raise FileNotFoundError(f"no locus packages found under {input_root}")
    return loci
