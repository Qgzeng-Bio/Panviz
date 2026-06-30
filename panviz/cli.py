"""Panviz command-line interface.

Subcommands:
  render     convert locus packages and export static SVG/PNG/PDF figures
  validate   check locus-package inputs without rendering
  version    print the Panviz version

Configuration precedence: package defaults < --config JSON < explicit flags.
"""
from __future__ import annotations

import argparse
import shutil
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
    if not str(cfg.browser) or not cfg.browser.exists():
        sys.stderr.write(
            f"error: Chromium browser not found at: {cfg.browser or '(unset)'}\n"
            "  fix: run `playwright install chromium`, or pass --browser PATH "
            "/ set PANVIZ_BROWSER.\n"
        )
        return 2
    try:
        loci = discover_loci(cfg.input_root, args.only)
    except FileNotFoundError as exc:
        sys.stderr.write(
            f"error: {exc}\n"
            "  fix: set --input-root PATH, --config FILE, or PANVIZ_INPUT_ROOT to a "
            "directory of locus packages.\n"
            "  see examples/ for the expected input layout.\n"
        )
        return 2

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
    try:
        loci = discover_loci(cfg.input_root, args.only)
    except FileNotFoundError as exc:
        sys.stderr.write(
            f"error: {exc}\n"
            "  fix: set --input-root PATH, --config FILE, or PANVIZ_INPUT_ROOT to a "
            "directory of locus packages.\n"
        )
        return 2
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


def _cmd_doctor(args: argparse.Namespace) -> int:
    """Check the runtime/build environment and report what is missing."""
    cfg = resolve_config(args.config, {k: getattr(args, k, None) for k in ("rebuild_root", "browser")})
    root = cfg.rebuild_root
    bundle = root / "harness" / "dist" / "sequencetubemap_exact_bundle.js"
    playwright = root / "node_modules" / "playwright-core"

    # (label, ok, required, hint)
    checks: list[tuple[str, bool, bool, str]] = [
        (f"python {sys.version.split()[0]}", True, True, ""),
        (
            f"node ({shutil.which('node') or 'not found'})",
            shutil.which("node") is not None,
            True,
            "install Node.js >=16 and ensure `node` is on PATH",
        ),
        (
            f"chromium ({cfg.browser if str(cfg.browser) else 'not found'})",
            bool(str(cfg.browser)) and cfg.browser.exists(),
            True,
            "run `playwright install chromium`, or set --browser / PANVIZ_BROWSER",
        ),
        (
            f"render bundle ({bundle})",
            bundle.exists() and bundle.stat().st_size > 0,
            True,
            "rebuild with `npm install && npm run build`",
        ),
        (
            "playwright-core (node_modules)",
            playwright.exists(),
            True,
            "run `npm install`",
        ),
        (
            "build deps (d3, webpack)",
            (root / "node_modules" / "d3").exists() and (root / "node_modules" / "webpack").exists(),
            False,
            "optional; only needed to rebuild the bundle: `npm install`",
        ),
    ]

    ok_required = True
    for label, ok, required, hint in checks:
        if ok:
            mark = "ok  "
        elif required:
            mark = "MISS"
            ok_required = False
        else:
            mark = "warn"
        line = f"  [{mark}] {label}"
        if not ok and hint:
            line += f"\n         -> {hint}"
        print(line)

    print(
        f"\n{'environment OK — ready to render' if ok_required else 'missing required components (see above)'}"
    )
    return 0 if ok_required else 1


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

    p_doctor = sub.add_parser("doctor", help="check the runtime/build environment")
    p_doctor.add_argument("--config", type=Path, default=None)
    p_doctor.add_argument("--rebuild-root", type=Path, default=None)
    p_doctor.add_argument("--browser", type=Path, default=None)
    p_doctor.set_defaults(func=_cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
