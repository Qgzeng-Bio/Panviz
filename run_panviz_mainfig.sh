#!/usr/bin/env bash
set -euo pipefail

cd /data9/home/qgzeng/projects/3-Biotools_create/Panviz

python3 render_pantubemap_mainfig.py \
  --out-root results/mainfig_axis_ticks_x032_trial_20260630 \
  --x-compression 0.32 \
  --panel-width 1800 \
  --pad-y 170 \
  "$@"
