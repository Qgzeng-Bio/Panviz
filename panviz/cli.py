"""Panviz command-line interface.

Subcommands:
  render     convert locus packages and export static SVG/PNG/PDF figures
  validate   check locus-package inputs without rendering
  version    print the Panviz version

Configuration precedence: package defaults < --config JSON < explicit flags.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import CONFIG_KEYS, resolve_config
from .discover import discover_loci
from .render import render_all
from .validate import validate_locus_input

# Render flags whose argparse dest matches a config key. Defaults are None so
# that "unset" can fall back to the config file / package defaults.
_PATH_FLAGS = ("input_root", "out_root", "rebuild_root", "browser")
_INT_FLAGS = ("panel_width", "pad_x", "pad_y")
_FLOAT_FLAGS = ("x_compression", "node_stroke_width", "device_scale_factor")


def _add_render_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", type=Path, default=None, help="JSON config file with render settings.")
    p.add_argument("--input-root", type=Path, default=None, help="Root holding locus packages.")
    p.add_argument("--out-root", type=Path, default=None, help="Output root directory.")
    p.add_argument("--rebuild-root", type=Path, default=None, help="Panviz root holding harness/.")
    p.add_argument("--browser", type=Path, default=None, help="Chromium executable for rendering.")
    p.add_argument("--only", nargs="*", default=None, help="Restrict to these locus IDs.")
    p.add_argument("--panel-width", type=int, default=None, help="Final SVG/PDF CSS pixel width.")
    p.add_argument("--x-compression", type=float, default=None, help="Coordinate-level x compression.")
    p.add_argument("--pad-x", type=int, default=None)
    p.add_argument("--pad-y", type=int, default=None)
    p.add_argument("--node-stroke-width", type=float, default=None)
    p.add_argument("--device-scale-factor", type=float, default=None)
    p.add_argument(
        "--validate",
        action="store_true",
        help="Validate each locus package before rendering; abort on errors.",
    )


def _overrides(args: argparse.Namespace) -> dict:
    return {k: getattr(args, k) for k in CONFIG_KEYS}


def _cmd_render(args: argparse.Namespace) -> int:
    cfg = resolve_config(args.config, _overrides(args))
    cfg.out_root = cfg.out_root.resolve()
    if not cfg.browser.exists():
        sys.stderr.write(f"browser executable not found: {cfg.browser}\n")
        return 2
    loci = discover_loci(cfg.input_root, args.only)

    if args.validate:
        bad = False
        for item in loci:
            errs = validate_locus_input(item)
            if errs:
                bad = True
                sys.stderr.write(f"[invalid] {item.locus}\n")
                for e in errs:
                    sys.stderr.write(f"  - {e}\n")
        if bad:
            sys.stderr.write("validation failed; nothing rendered\n")
            return 1

    summary = render_all(cfg, loci)
    failed = [row for row in summary if row["Status"] != "ok"]
    for row in summary:
        print(f"{row['Status']:>6}  {row['Locus']}  ({row['Nodes']} nodes, {row['Tracks']} tracks)")
    print(f"\nwrote {len(summary)} loci to {cfg.out_root}")
    if failed:
        sys.stderr.write(f"failed loci: {', '.join(row['Locus'] for row in failed)}\n")
        return 1
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    cfg = resolve_config(args.config, {"input_root": args.input_root})
    loci = discover_loci(cfg.input_root, args.only)
    all_ok = True
    for item in loci:
        errs = validate_locus_input(item)
        if errs:
            all_ok = False
            print(f"[FAIL] {item.locus}")
            for e in errs:
                print(f"   - {e}")
        else:
            print(f"[ ok ] {item.locus}")
    print(f"\n{'all loci valid' if all_ok else 'validation errors found'} ({len(loci)} loci)")
    return 0 if all_ok else 1


def _cmd_version(args: argparse.Namespace) -> int:
    print(f"panviz {__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="panviz", description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=f"panviz {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="render static tube-map figures")
    _add_render_flags(p_render)
    p_render.set_defaults(func=_cmd_render)

    p_validate = sub.add_parser("validate", help="validate locus-package inputs")
    p_validate.add_argument("--config", type=Path, default=None)
    p_validate.add_argument("--input-root", type=Path, default=None)
    p_validate.add_argument("--only", nargs="*", default=None)
    p_validate.set_defaults(func=_cmd_validate)

    p_version = sub.add_parser("version", help="print the Panviz version")
    p_version.set_defaults(func=_cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
