"""Render orchestration: payload -> static export adapter -> SVG/PNG/PDF.

This module writes the render payload and per-locus sidecar files, invokes the
Node static export adapter (``harness/export_mainfig_natural.js``), and assembles
the render metadata. It does not implement layout or drawing; those live in the
SequenceTubeMap-derived core under ``src/panviz_core/``.
"""
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

from .config import REPO_ROOT, RenderConfig
from .discover import LocusInput
from .gfa import gfa_to_payload
from .validate import png_dimensions, validate_output

UPSTREAM_COMMIT = "33b7a7e5df9f8052974ef8e6c689a031dac6e2c9"


class RenderError(Exception):
    """A render failed for a reason worth reporting to the user without a traceback."""

SUMMARY_FIELDS = [
    "Locus",
    "Nodes",
    "Tracks",
    "Panel_Width",
    "Panel_Height",
    "X_Compression",
    "SVG",
    "PDF",
    "PNG",
    "Status",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    # extrasaction="ignore" so path-group rows with extra columns do not raise.
    with Path(path).open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def _rel(path: Path) -> str:
    """Path relative to the repo root when possible, else absolute string."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def render_locus(cfg: RenderConfig, item: LocusInput) -> dict[str, Any]:
    payload, counts, group_rows = gfa_to_payload(item, cfg)
    locus_out = cfg.out_root / item.locus
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
    write_tsv(
        path_key,
        group_rows,
        ["locus", "collapsed_path", "n_members", "representative_member", "members"],
    )

    cmd = [
        "node",
        str(cfg.rebuild_root / "harness/export_mainfig_natural.js"),
        "--input",
        str(input_json),
        "--svg",
        str(svg),
        "--png",
        str(png),
        "--pdf",
        str(pdf),
        "--browser",
        str(cfg.browser),
    ]
    try:
        proc = run(cmd, cwd=cfg.rebuild_root)
    except FileNotFoundError as exc:
        raise RenderError(
            f"`node` was not found on PATH ({exc}). Install Node.js >=16 and ensure `node` is runnable."
        ) from exc
    except subprocess.CalledProcessError as exc:
        tail = "\n".join((exc.stderr or exc.stdout or "").strip().splitlines()[-15:])
        raise RenderError(
            f"renderer failed for {item.locus} (node exit {exc.returncode}):\n{tail}"
        ) from exc
    try:
        browser_counts = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RenderError(
            f"could not parse renderer output for {item.locus}: {exc}\n{proc.stdout[-500:]}"
        ) from exc
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
                f"- x-coordinate compression: {cfg.x_compression}",
                f"- node stroke width: {cfg.node_stroke_width}px",
                "- no `preserveAspectRatio=none`; text and stroke widths are not non-uniformly scaled",
                "",
            ]
        )
    )
    # Output integrity: files non-empty, PNG is a real PNG of the expected size.
    expected_w = round(browser_counts["panelWidth"] * cfg.device_scale_factor)
    expected_h = round(browser_counts["panelHeight"] * cfg.device_scale_factor)
    dims = png_dimensions(png)
    png_ok = dims is not None and abs(dims[0] - expected_w) <= 1 and abs(dims[1] - expected_h) <= 1
    ok = validate_output(svg, png, pdf) and png_ok
    return {
        "Locus": item.locus,
        "Nodes": counts["nodes"],
        "Tracks": counts["tracks"],
        "Panel_Width": browser_counts["panelWidth"],
        "Panel_Height": browser_counts["panelHeight"],
        "X_Compression": cfg.x_compression,
        "SVG": _rel(svg),
        "PDF": _rel(pdf),
        "PNG": _rel(png),
        "Status": "ok"
        if ok and browser_counts["trackChildren"] > 0 and browser_counts["nodeChildren"] > 0
        else "failed",
    }


def render_all(cfg: RenderConfig, loci: list[LocusInput]) -> list[dict[str, Any]]:
    bundle = cfg.rebuild_root / "harness" / "dist" / "sequencetubemap_exact_bundle.js"
    if not bundle.exists():
        raise RenderError(
            f"render bundle not found: {bundle}\n"
            "  fix: rebuild with `npm install && npm run build`, or point "
            "--rebuild-root / PANVIZ_REBUILD_ROOT at the Panviz repo."
        )
    cfg.out_root.mkdir(parents=True, exist_ok=True)
    summary = [render_locus(cfg, item) for item in loci]
    write_tsv(cfg.out_root / "render_summary.tsv", summary, SUMMARY_FIELDS)
    return summary
