#!/usr/bin/env bash
# Render with the accepted Panviz main-figure baseline visual parameters.
#
# Input defaults to the bundled toy locus. To render your own data, pass
# --input-root PATH (or set PANVIZ_INPUT_ROOT). Extra arguments such as
# --only <locus_id> are forwarded to the CLI. Example:
#   ./run_panviz_mainfig.sh --input-root /path/to/loci --only 01_FAD2_FAD2_chr08B
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

python3 bin/panviz render --config config/mainfig_baseline.json "$@"
