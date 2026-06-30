#!/usr/bin/env python3
"""Generate the Panviz toy locus package (deterministic, no private data).

Writes a minimal but realistic path-collapsed GFA locus into
``examples/toy_data/toy_locus/`` so anyone can run Panviz end-to-end:

    python3 examples/generate_toy.py
    panviz render --config config/mainfig_baseline.json \\
        --input-root examples/toy_data --only toy_locus --out-root results/toy

The graph is a reference backbone plus three structural variants:
a deletion, a substitution (alternate allele), and an insertion.
"""
from __future__ import annotations

from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "toy_data" / "toy_locus"
CHROM = "chrTOY"
# Off-round start so the endpoint labels do not collide with axis ticks
# (real gene loci are rarely on a whole-Mb boundary).
START = 1_234_000

# Reference backbone: (name, length).
BACKBONE = [
    ("bb00", 2000), ("bb01", 1500), ("bb02", 2500), ("bb03", 1800),
    ("bb04", 1200), ("bb05", 2200), ("bb06", 1600), ("bb07", 2400),
    ("bb08", 1400), ("bb09", 2600), ("bb10", 2000),
]
# Structural-variant nodes: name -> (length, TYPE, SVLEN).
SV_NODES = {
    "delX": (2500, "DEL", -2500),   # deletion bubble (in reference, lost in some)
    "subR": (1800, "REF", 0),       # substitution: reference allele
    "subA": (1800, "SNP", 0),       # substitution: alternate allele
    "insY": (1500, "INS", 1500),    # insertion bubble (absent from reference)
}

# Reference path: backbone with delX (after bb03) and subR (after bb06).
REF_PATH = [
    "bb00", "bb01", "bb02", "bb03", "delX", "bb04", "bb05", "bb06",
    "subR", "bb07", "bb08", "bb09", "bb10",
]

# Collapsed haplotype paths: name -> (n_members, node list).
HAPLOTYPES = {
    "hap1": (9, REF_PATH),                                   # identical to reference
    "hap2": (6, [n for n in REF_PATH if n != "delX"]),       # deletion of delX
    "hap3": (5, ["subA" if n == "subR" else n for n in REF_PATH]),  # substitution
    "hap4": (3, [                                            # insertion of insY
        "bb00", "bb01", "bb02", "bb03", "delX", "bb04", "bb05", "bb06",
        "subR", "bb07", "insY", "bb08", "bb09", "bb10",
    ]),
    "hap5": (2, [                                            # del + subA + insY
        "bb00", "bb01", "bb02", "bb03", "bb04", "bb05", "bb06",
        "subA", "bb07", "insY", "bb08", "bb09", "bb10",
    ]),
}


def node_length(name: str) -> int:
    for bn, blen in BACKBONE:
        if bn == name:
            return blen
    return SV_NODES[name][0]


def write_gfa(path: Path) -> None:
    lines = ["H\tVN:Z:1.0"]
    for name, length in BACKBONE:
        lines.append(f"S\t{name}\t*\tLN:i:{length}")
    for name, (length, typ, svlen) in SV_NODES.items():
        lines.append(f"S\t{name}\t*\tLN:i:{length}\tTYPE:Z:{typ}\tSVLEN:i:{svlen}")
    # Reference first, then haplotypes (CN = collapsed member count).
    lines.append(f"P\tRef\t{','.join(n + '+' for n in REF_PATH)}\t*\tCN:i:1")
    for name, (n_members, nodes) in HAPLOTYPES.items():
        lines.append(f"P\t{name}\t{','.join(n + '+' for n in nodes)}\t*\tCN:i:{n_members}")
    path.write_text("\n".join(lines) + "\n")


def write_path_groups(path: Path) -> None:
    header = ["locus", "collapsed_path", "n_members", "representative_member", "members"]
    rows = [["toy_locus", "Ref", "1", "Ref", "Ref"]]
    acc = 1
    for name, (n_members, _nodes) in HAPLOTYPES.items():
        members = [f"acc{acc + i:02d}" for i in range(n_members)]
        acc += n_members
        rows.append(["toy_locus", name, str(n_members), members[0], ",".join(members)])
    path.write_text("\n".join("\t".join(r) for r in [header, *rows]) + "\n")


def write_region(path: Path) -> None:
    span = sum(node_length(n) for n in REF_PATH)
    end = START + span
    path.write_text(
        f"reference_coordinate={CHROM}:{START}-{end}\n"
        f"recommended_SequenceTubeMap_region={CHROM}:{START}-{end}\n"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_gfa(OUT_DIR / "toy_locus_pathcollapsed_SV1kb.gfa")
    write_path_groups(OUT_DIR / "toy_locus_pathcollapsed_SV1kb.path_groups.tsv")
    write_region(OUT_DIR / "region.txt")
    print(f"wrote toy locus package to {OUT_DIR}")


if __name__ == "__main__":
    main()
