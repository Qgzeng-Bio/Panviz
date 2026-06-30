"""Panviz: a static, publication-oriented sequence tube map renderer.

This package owns Panviz's data conversion, configuration, validation, render
orchestration, and command-line interface. The low-level layout/drawing core is
the SequenceTubeMap-derived JavaScript under ``src/panviz_core/`` (MIT), invoked
through the static export adapter in ``harness/``.
"""
from __future__ import annotations

__version__ = "0.1.0.dev0"
__all__ = ["__version__"]
