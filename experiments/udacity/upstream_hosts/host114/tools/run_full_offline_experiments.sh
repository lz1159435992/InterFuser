#!/usr/bin/env bash
set -euo pipefail

# One-shot runner for the full offline evaluation matrix:
# - 15 combo pipelines (A/B/C permutations)
# - + GN8/GN16 standalone noise pipelines
# - segments 1..6
# - resume enabled (skip already completed summaries)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
python3 "${SCRIPT_DIR}/run_combo_eval.py" --pipelines all --segments 1,2,3,4,5,6 --docker-sudo --resume
