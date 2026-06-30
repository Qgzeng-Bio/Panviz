#!/usr/bin/env python3
"""Render Panviz static main-figure panels from path-collapsed GFA packages."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
PANVIZ_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_ROOT = Path(
    "/data9/home/ysxia/Adata/plant/youzong/rawdata/analysis/22_answer_reviews/05_sv_gene/"
    "gene_tubemap_all34_pathcollapsed_20260629"
)
DEFAULT_REBUILD_ROOT = PANVIZ_ROOT
DEFAULT_OUT_ROOT = PROJECT_ROOT / "results/mainfig_axis_ticks_x032_trial_20260630"
DEFAULT_BROWSER = Path("/data9/home/qgzeng/.cache/ms-playwright/chromium-1187/chrome-linux/chrome")
UPSTREAM_COMMIT = "33b7a7e5df9f8052974ef8e6c689a031dac6e2c9"


@dataclass
class LocusInput:
    locus: str
    gfa: Path
    path_groups: Path
    region: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--rebuild-root", type=Path, default=DEFAULT_REBUILD_ROOT)
    parser.add_argument("--browser", type=Path, default=DEFAULT_BROWSER)
    parser.add_argument("--only", nargs="*", default=None, help="Optional locus IDs to render.")
    parser.add_argument("--panel-width", type=int, default=1800, help="Final SVG/PDF CSS pixel width.")
    parser.add_argument("--x-compression", type=float, default=0.32, help="Coordinate-level x compression factor.")
    parser.add_argument("--pad-x", type=int, default=35)
    parser.add_argument("--pad-y", type=int, default=170)
    parser.add_argument("--node-stroke-width", type=float, default=1.5)
    parser.add_argument("--device-scale-factor", type=float, default=2.0)
    return parser.parse_args()


def discover_loci(input_root: Path, only: list[str] | None) -> list[LocusInput]:
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


def parse_gfa_tags(fields: list[str]) -> dict[str, Any]:
    tags: dict[str, Any] = {}
    for field in fields:
        parts = field.split(":", 2)
        if len(parts) != 3:
            continue
        key, typ, value = parts
        if typ == "i":
            try:
                tags[key] = int(value)
            except ValueError:
                tags[key] = value
        else:
            tags[key] = value
    return tags


def parse_path_token(token: str) -> str:
    token = token.strip()
    if not token:
        raise ValueError("empty path token")
    orient = token[-1]
    node = token[:-1]
    if orient == "+":
        return node
    if orient == "-":
        return f"-{node}"
    raise ValueError(f"bad GFA path token: {token}")


def read_path_groups(path: Path) -> tuple[dict[str, int], list[dict[str, str]]]:
    freq: dict[str, int] = {}
    rows: list[dict[str, str]] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            name = row["collapsed_path"]
            try:
                freq[name] = int(row.get("n_members") or "1")
            except ValueError:
                freq[name] = 1
            rows.append(row)
    return freq, rows


def read_region(path: Path) -> list[int]:
    for line in path.read_text().splitlines():
        if line.startswith("recommended_SequenceTubeMap_region="):
            value = line.split("=", 1)[1].strip()
            match = re.search(r":(\d+)-(\d+)$", value)
            if not match:
                raise ValueError(f"bad SequenceTubeMap region in {path}: {value}")
            return [int(match.group(1)), int(match.group(2))]
    raise ValueError(f"missing recommended_SequenceTubeMap_region in {path}")


def read_reference_coordinate(path: Path) -> dict[str, int | str]:
    for line in path.read_text().splitlines():
        if line.startswith("reference_coordinate="):
            value = line.split("=", 1)[1].strip()
            match = re.fullmatch(r"([^:]+):(\d+)-(\d+)", value)
            if not match:
                raise ValueError(f"bad reference_coordinate in {path}: {value}")
            return {"chrom": match.group(1), "start": int(match.group(2)), "end": int(match.group(3))}
    raise ValueError(f"missing reference_coordinate in {path}")


def gfa_to_payload(item: LocusInput, args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, int], list[dict[str, str]]]:
    path_freq, group_rows = read_path_groups(item.path_groups)
    nodes: list[dict[str, Any]] = []
    tracks_raw: list[dict[str, Any]] = []
    with item.gfa.open() as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if not fields or not fields[0]:
                continue
            if fields[0] == "S":
                tags = parse_gfa_tags(fields[3:])
                seq = fields[2]
                length = int(tags.get("LN", len(seq)))
                nodes.append(
                    {
                        "sourceTrackID": 0,
                        "name": fields[1],
                        "seq": seq,
                        "sequence": seq,
                        "sequenceLength": length,
                        "width": length,
                        "metadata": {
                            "sequenceLength": length,
                            "TYPE": tags.get("TYPE"),
                            "CO": tags.get("CO"),
                            "SVLEN": tags.get("SVLEN"),
                        },
                    }
                )
            elif fields[0] == "P":
                name = fields[1]
                tags = parse_gfa_tags(fields[4:])
                tracks_raw.append(
                    {
                        "id": None,
                        "sourceTrackID": 0,
                        "name": name,
                        "sequence": [parse_path_token(tok) for tok in fields[2].split(",") if tok],
                        "freq": int(path_freq.get(name, tags.get("CN", 1) or 1)),
                        "type": "haplotype",
                    }
                )
    tracks_raw.sort(key=lambda row: (0 if row["name"] == "Ref" else 1, row["name"]))
    for idx, track in enumerate(tracks_raw):
        track["id"] = idx
        if track["name"] == "Ref":
            track["indexOfFirstBase"] = 1
    payload = {
        "locus": item.locus,
        "nodes": nodes,
        "tracks": tracks_raw,
        "reads": [],
        "region": read_region(item.region),
        "visOptions": {
            "compressedView": True,
            "removeRedundantNodes": False,
            "transparentNodes": False,
            "showReads": False,
            "showSoftClips": False,
            "coloredNodes": [],
            "mappingQualityCutoff": 0,
        },
        "viewport": {"width": 2400, "height": max(1200, 260 + 38 * max(1, len(tracks_raw)))},
        "referenceCoordinate": read_reference_coordinate(item.region),
        "mainFigure": {
            "panelWidth": args.panel_width,
            "xCompression": args.x_compression,
            "padX": args.pad_x,
            "padY": args.pad_y,
            "nodeStrokeWidth": args.node_stroke_width,
            "deviceScaleFactor": args.device_scale_factor,
        },
        "input": {"gfa": str(item.gfa), "path_groups": str(item.path_groups), "region": str(item.region)},
    }
    return payload, {"nodes": len(nodes), "tracks": len(tracks_raw)}, group_rows


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_locus(args: argparse.Namespace, item: LocusInput) -> dict[str, Any]:
    payload, counts, group_rows = gfa_to_payload(item, args)
    locus_out = args.out_root / item.locus
    locus_out.mkdir(parents=True, exist_ok=True)
    prefix = item.locus
    input_json = locus_out / f"{prefix}_sequencetubemap_mainfig_natural_input.json"
    path_key = locus_out / f"{prefix}_path_group_key.tsv"
    metadata_json = locus_out / f"{prefix}_mainfig_natural_render_metadata.json"
    notes_md = locus_out / f"{prefix}_mainfig_natural_notes.md"
    svg = locus_out / f"{prefix}_sequencetubemap_mainfig_natural.svg"
    png = locus_out / f"{prefix}_sequencetubemap_mainfig_natural.png"
    pdf = locus_out / f"{prefix}_sequencetubemap_mainfig_natural.pdf"
    input_json.write_text(json.dumps(payload, indent=2))
    write_tsv(path_key, group_rows, ["locus", "collapsed_path", "n_members", "representative_member", "members"])

    proc = run(
        [
            "node",
            str(args.rebuild_root / "harness/export_mainfig_natural.js"),
            "--input",
            str(input_json),
            "--svg",
            str(svg),
            "--png",
            str(png),
            "--pdf",
            str(pdf),
            "--browser",
            str(args.browser),
        ],
        cwd=args.rebuild_root,
    )
    browser_counts = json.loads(proc.stdout.strip().splitlines()[-1])
    metadata = {
        "status": "trial",
        "renderer": "official SequenceTubeMap tubemap.js with coordinate-level x compression",
        "upstream_commit": UPSTREAM_COMMIT,
        "locus": item.locus,
        "input": payload["input"],
        "output": {"svg": str(svg), "png": str(png), "pdf": str(pdf), "input_json": str(input_json)},
        "counts": {
            "input_nodes": counts["nodes"],
            "input_tracks": counts["tracks"],
            **browser_counts,
        },
        "visOptions": payload["visOptions"],
        "referenceCoordinate": payload["referenceCoordinate"],
        "mainFigure": payload["mainFigure"],
        "note": "X coordinates are compressed after official layout; no non-uniform SVG scaling is used, so strokes and text are not squeezed.",
    }
    metadata_json.write_text(json.dumps(metadata, indent=2))
    notes_md.write_text(
        "\n".join(
            [
                f"# {item.locus} SequenceTubeMap natural main-figure trial",
                "",
                "- status: trial",
                f"- upstream commit: `{UPSTREAM_COMMIT}`",
                "- official `src/util/tubemap.js` generates the layout first",
                f"- x-coordinate compression: {args.x_compression}",
                f"- node stroke width: {args.node_stroke_width}px",
                "- no `preserveAspectRatio=none`; text and stroke widths are not non-uniformly scaled",
                "",
            ]
        )
    )
    ok = all(p.exists() and p.stat().st_size > 0 for p in (svg, png, pdf))
    return {
        "Locus": item.locus,
        "Nodes": counts["nodes"],
        "Tracks": counts["tracks"],
        "Panel_Width": browser_counts["panelWidth"],
        "Panel_Height": browser_counts["panelHeight"],
        "X_Compression": args.x_compression,
        "SVG": str(svg.relative_to(PROJECT_ROOT)),
        "PDF": str(pdf.relative_to(PROJECT_ROOT)),
        "PNG": str(png.relative_to(PROJECT_ROOT)),
        "Status": "ok" if ok and browser_counts["trackChildren"] > 0 and browser_counts["nodeChildren"] > 0 else "failed",
    }


def main() -> int:
    args = parse_args()
    args.out_root = args.out_root.resolve()
    if not args.browser.exists():
        raise FileNotFoundError(args.browser)
    args.out_root.mkdir(parents=True, exist_ok=True)
    summary = [render_locus(args, item) for item in discover_loci(args.input_root, args.only)]
    write_tsv(
        args.out_root / "render_summary.tsv",
        summary,
        ["Locus", "Nodes", "Tracks", "Panel_Width", "Panel_Height", "X_Compression", "SVG", "PDF", "PNG", "Status"],
    )
    failed = [row for row in summary if row["Status"] != "ok"]
    if failed:
        sys.stderr.write(f"failed loci: {', '.join(row['Locus'] for row in failed)}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
