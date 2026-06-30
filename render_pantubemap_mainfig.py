#!/usr/bin/env python3
"""Deprecated entry point. Use ``panviz render`` (or ``bin/panviz render``).

Kept for backward compatibility with the original flat-flag interface and with
``run_panviz_mainfig.sh``. All arguments are forwarded verbatim to the
``panviz render`` subcommand, so behaviour is unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from panviz.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.stderr.write(
        "note: render_pantubemap_mainfig.py is deprecated; "
        "use `panviz render` or `bin/panviz render`.\n"
    )
    raise SystemExit(main(["render", *sys.argv[1:]]))
