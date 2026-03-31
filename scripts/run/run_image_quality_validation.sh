#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IQV_DIR="$ROOT_DIR/experiments/common/image_quality_validation"
SCRIPTS_DIR="$IQV_DIR/tools_py_2026"
OUT_DIR="$IQV_DIR/output"
PYTHON_BIN="${PYTHON_BIN:-python3}"

MODE="${1:-niqe_brisque}"
shift || true

mkdir -p "$OUT_DIR"

case "$MODE" in
  niqe_brisque)
    IMG_DIR=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --img-dir) IMG_DIR="$2"; shift 2 ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
      esac
    done
    if [[ -z "$IMG_DIR" ]]; then
      echo "Usage: $0 niqe_brisque --img-dir <enhanced_image_dir>" >&2
      exit 1
    fi
    "$PYTHON_BIN" "$SCRIPTS_DIR/niqe_brisque_main.py" --img_dir "$IMG_DIR"
    ;;
  ssim_lpips)
    GT_DIR=""
    ENH_DIR=""
    GT_DIR2=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --gt-dir) GT_DIR="$2"; shift 2 ;;
        --enh-dir) ENH_DIR="$2"; shift 2 ;;
        --gt-dir2) GT_DIR2="$2"; shift 2 ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
      esac
    done
    if [[ -z "$GT_DIR" || -z "$ENH_DIR" ]]; then
      echo "Usage: $0 ssim_lpips --gt-dir <gt_dir> --enh-dir <enh_dir> [--gt-dir2 <gt_dir2>]" >&2
      exit 1
    fi
    if [[ -n "$GT_DIR2" ]]; then
      "$PYTHON_BIN" "$SCRIPTS_DIR/ssim_lpips.py" --gt_dir "$GT_DIR" --gt_dir2 "$GT_DIR2" --enh_dir "$ENH_DIR"
    else
      "$PYTHON_BIN" "$SCRIPTS_DIR/ssim_lpips.py" --gt_dir "$GT_DIR" --enh_dir "$ENH_DIR"
    fi
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    echo "Supported: niqe_brisque | ssim_lpips" >&2
    exit 1
    ;;
esac
