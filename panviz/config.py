"""Panviz render configuration: defaults, file loading, and precedence merge.

Resolution precedence (lowest to highest):

    built-in defaults  <  PANVIZ_* env vars  <  --config JSON file  <  explicit CLI flags

Environment overrides: ``PANVIZ_INPUT_ROOT``, ``PANVIZ_OUT_ROOT``,
``PANVIZ_REBUILD_ROOT``, ``PANVIZ_BROWSER`` (and ``PLAYWRIGHT_BROWSERS_PATH``
for browser auto-detection).

The deployment-specific paths (input root, browser) are kept as last-resort
defaults so the tool still runs on the original server; the browser is normally
auto-detected. They are overridable via env vars, a config file, or CLI flags,
and are expected to move out of the package before an independent release (see
docs/DEVELOPMENT_ROADMAP.md, Stage 4).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

# Repository root: panviz/ lives directly under it.
REPO_ROOT = Path(__file__).resolve().parents[1]

# Out-of-the-box input root: the bundled toy example, so `panviz render` works
# immediately after a clone. Point at your own locus packages with --input-root,
# a config file, or the PANVIZ_INPUT_ROOT environment variable.
#
# The original server batch lived at
#   /data9/home/ysxia/.../05_sv_gene/gene_tubemap_all34_pathcollapsed_20260629
# which is not a built-in default; set PANVIZ_INPUT_ROOT to reproduce it.
DEFAULT_INPUT_ROOT = str(REPO_ROOT / "examples" / "toy_data")
# Last-resort browser path for the original deployment; normally the browser is
# auto-detected (see detect_browser) or set via --browser / PANVIZ_BROWSER.
LEGACY_BROWSER = (
    "/data9/home/qgzeng/.cache/ms-playwright/chromium-1187/chrome-linux/chrome"
)


def _env(name: str, default: str) -> str:
    """Return a non-empty environment override, else the default."""
    value = os.environ.get(name)
    return value if value else default


def _chromium_version(path: Path) -> int:
    match = re.search(r"chromium-(\d+)", str(path))
    return int(match.group(1)) if match else -1


def detect_browser() -> str:
    """Locate a Chromium executable for rendering, newest version preferred.

    Search order: ``PANVIZ_BROWSER`` -> ``PLAYWRIGHT_BROWSERS_PATH`` ->
    ``~/.cache/ms-playwright`` -> the legacy deployment path. Returns "" if none
    is found, so the CLI can emit an actionable error.
    """
    # An explicit PANVIZ_BROWSER is authoritative: return it as-is (even if it
    # does not exist) so a wrong path surfaces as a clear "not found" error
    # rather than being silently replaced by an auto-detected browser.
    explicit = os.environ.get("PANVIZ_BROWSER")
    if explicit:
        return explicit

    roots: list[Path] = []
    pbp = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if pbp:
        roots.append(Path(pbp))
    roots.append(Path.home() / ".cache" / "ms-playwright")

    candidates: list[Path] = []
    for root in roots:
        if root.exists():
            # chrome-linux (Linux) and chrome-linux64 layouts, plus mac/win names.
            for pattern in (
                "chromium-*/chrome-linux/chrome",
                "chromium-*/chrome-linux64/chrome",
                "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
                "chromium-*/chrome-win/chrome.exe",
            ):
                candidates.extend(root.glob(pattern))

    legacy = Path(LEGACY_BROWSER)
    if legacy.exists():
        candidates.append(legacy)

    existing = [c for c in candidates if c.exists()]
    if not existing:
        return ""
    existing.sort(key=_chromium_version)
    return str(existing[-1])


DEFAULTS: dict[str, Any] = {
    "input_root": _env("PANVIZ_INPUT_ROOT", DEFAULT_INPUT_ROOT),
    "out_root": _env(
        "PANVIZ_OUT_ROOT", str(REPO_ROOT / "results/mainfig_axis_ticks_x032_trial_20260630")
    ),
    "rebuild_root": _env("PANVIZ_REBUILD_ROOT", str(REPO_ROOT)),
    "browser": detect_browser() or LEGACY_BROWSER,
    "panel_width": 1800,
    "x_compression": 0.32,
    "pad_x": 35,
    "pad_y": 170,
    "node_stroke_width": 1.5,
    "device_scale_factor": 2.0,
}

# Keys that may be supplied via config file or overridden on the CLI.
CONFIG_KEYS = tuple(DEFAULTS.keys())
# Path-like keys; relative values in a config file are anchored at REPO_ROOT so
# they do not depend on the caller's current working directory.
PATH_CONFIG_KEYS = ("input_root", "out_root", "rebuild_root", "browser")


@dataclass
class RenderConfig:
    """Fully resolved render configuration."""

    input_root: Path
    out_root: Path
    rebuild_root: Path
    browser: Path
    panel_width: int
    x_compression: float
    pad_x: int
    pad_y: int
    node_stroke_width: float
    device_scale_factor: float

    def __post_init__(self) -> None:
        self.input_root = Path(self.input_root)
        self.out_root = Path(self.out_root)
        self.rebuild_root = Path(self.rebuild_root)
        self.browser = Path(self.browser)
        self.panel_width = int(self.panel_width)
        self.x_compression = float(self.x_compression)
        self.pad_x = int(self.pad_x)
        self.pad_y = int(self.pad_y)
        self.node_stroke_width = float(self.node_stroke_width)
        self.device_scale_factor = float(self.device_scale_factor)


def load_config_file(path: Path) -> dict[str, Any]:
    """Load and validate a JSON config file; return only recognised keys."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"config file must be a JSON object: {path}")
    # Ignore commentary keys that start with an underscore.
    cleaned = {k: v for k, v in data.items() if not k.startswith("_")}
    unknown = sorted(set(cleaned) - set(CONFIG_KEYS))
    if unknown:
        allowed = ", ".join(CONFIG_KEYS)
        raise ValueError(
            f"unknown config keys in {path}: {', '.join(unknown)}\nallowed keys: {allowed}"
        )
    # Anchor relative path values at REPO_ROOT so they are independent of CWD.
    for key in PATH_CONFIG_KEYS:
        value = cleaned.get(key)
        if isinstance(value, str) and value and not os.path.isabs(value):
            cleaned[key] = str(REPO_ROOT / value)
    return cleaned


def resolve_config(config_file: Path | None, overrides: dict[str, Any]) -> RenderConfig:
    """Merge DEFAULTS < config file < explicit overrides into a RenderConfig.

    ``overrides`` should contain only keys whose value was explicitly provided
    (i.e. not None); CLI flags left unset must be omitted so they fall back to
    the file/default value.
    """
    merged: dict[str, Any] = dict(DEFAULTS)
    if config_file is not None:
        merged.update(load_config_file(config_file))
    merged.update({k: v for k, v in overrides.items() if v is not None})
    known = {f.name for f in fields(RenderConfig)}
    return RenderConfig(**{k: v for k, v in merged.items() if k in known})
