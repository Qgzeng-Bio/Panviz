"""Convert a path-collapsed GFA locus package into a Panviz render payload.

The payload schema matches what the SequenceTubeMap-derived core expects, plus a
``mainFigure`` block carrying Panviz's static-figure parameters. This module is
the data-conversion layer; it does no rendering.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from .config import RenderConfig
from .discover import LocusInput


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
    with Path(path).open(newline="") as handle:
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
    for line in Path(path).read_text().splitlines():
        if line.startswith("recommended_SequenceTubeMap_region="):
            value = line.split("=", 1)[1].strip()
            match = re.search(r":(\d+)-(\d+)$", value)
            if not match:
                raise ValueError(f"bad SequenceTubeMap region in {path}: {value}")
            return [int(match.group(1)), int(match.group(2))]
    raise ValueError(f"missing recommended_SequenceTubeMap_region in {path}")


def read_reference_coordinate(path: Path) -> dict[str, int | str]:
    for line in Path(path).read_text().splitlines():
        if line.startswith("reference_coordinate="):
            value = line.split("=", 1)[1].strip()
            match = re.fullmatch(r"([^:]+):(\d+)-(\d+)", value)
            if not match:
                raise ValueError(f"bad reference_coordinate in {path}: {value}")
            return {"chrom": match.group(1), "start": int(match.group(2)), "end": int(match.group(3))}
    raise ValueError(f"missing reference_coordinate in {path}")


def gfa_to_payload(
    item: LocusInput, cfg: RenderConfig
) -> tuple[dict[str, Any], dict[str, int], list[dict[str, str]]]:
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
            "panelWidth": cfg.panel_width,
            "xCompression": cfg.x_compression,
            "padX": cfg.pad_x,
            "padY": cfg.pad_y,
            "nodeStrokeWidth": cfg.node_stroke_width,
            "deviceScaleFactor": cfg.device_scale_factor,
        },
        "input": {"gfa": str(item.gfa), "path_groups": str(item.path_groups), "region": str(item.region)},
    }
    return payload, {"nodes": len(nodes), "tracks": len(tracks_raw)}, group_rows
