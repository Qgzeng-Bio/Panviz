"""Panviz render configuration: defaults, file loading, and precedence merge.

Resolution precedence (lowest to highest):

    package DEFAULTS  <  --config JSON file  <  explicit CLI flags

The deployment-specific paths (input root, browser) are kept as defaults so the
tool runs out-of-the-box on the current server; they are overridable via a
config file or CLI flags, and are expected to move out of the package before an
independent release (see docs/DEVELOPMENT_ROADMAP.md, Stage 4).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

# Repository root: panviz/ lives directly under it.
REPO_ROOT = Path(__file__).resolve().parents[1]

# Default deployment input root (collaborator-provided locus packages).
DEFAULT_INPUT_ROOT = (
    "/data9/home/ysxia/Adata/plant/youzong/rawdata/analysis/22_answer_reviews/"
    "05_sv_gene/gene_tubemap_all34_pathcollapsed_20260629"
)
DEFAULT_BROWSER = (
    "/data9/home/qgzeng/.cache/ms-playwright/chromium-1187/chrome-linux/chrome"
)

DEFAULTS: dict[str, Any] = {
    "input_root": DEFAULT_INPUT_ROOT,
    "out_root": str(REPO_ROOT / "results/mainfig_axis_ticks_x032_trial_20260630"),
    "rebuild_root": str(REPO_ROOT),
    "browser": DEFAULT_BROWSER,
    "panel_width": 1800,
    "x_compression": 0.32,
    "pad_x": 35,
    "pad_y": 170,
    "node_stroke_width": 1.5,
    "device_scale_factor": 2.0,
}

# Keys that may be supplied via config file or overridden on the CLI.
CONFIG_KEYS = tuple(DEFAULTS.keys())


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
