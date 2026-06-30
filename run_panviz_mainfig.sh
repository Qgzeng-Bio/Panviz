#!/usr/bin/env bash
# Reproduce the accepted Panviz main-figure baseline rendering.
# Extra arguments (e.g. --only 01_FAD2_FAD2_chr08B) are forwarded to the CLI.
set -euo pipefail

cd /data9/home/qgzeng/projects/3-Biotools_create/Panviz

python3 bin/panviz render --config config/mainfig_baseline.json "$@"
