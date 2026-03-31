#!/usr/bin/env bash
set -euo pipefail

# Sync KITTI/Udacity related scripts from local mirrors into publication paths.
#
# Expected source layout (direct or auto-detected subdirectory):
#   tools/py
#   udacity
#   process_mothod (legacy upstream name)
#   kitti_test

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_ROOT="${INTUITION_TESTER_SOURCES:-$ROOT_DIR/../IntuitionTester_sources}"
SRC_MIRROR="$SRC_ROOT/kitti_udacity_source_mirror"

if [[ ! -d "$SRC_MIRROR" ]]; then
  for candidate in "$SRC_ROOT"/*; do
    [[ -d "$candidate" ]] || continue
    if [[ -d "$candidate/tools/py" && -d "$candidate/udacity" && -d "$candidate/process_mothod" && -d "$candidate/kitti_test" ]]; then
      SRC_MIRROR="$candidate"
      break
    fi
  done
fi

if [[ ! -d "$SRC_MIRROR" ]]; then
  echo "[error] source mirror not found: $SRC_MIRROR" >&2
  echo "Set INTUITION_TESTER_SOURCES to your local mirror root." >&2
  echo "Expected: <mirror_root>/kitti_udacity_source_mirror (or a subdirectory containing tools/py, udacity, process_mothod (legacy), kitti_test)." >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "[error] rsync is required for this script." >&2
  exit 1
fi

IQV_2026_DST="$ROOT_DIR/experiments/common/image_quality_validation/tools_py_2026"
KITTI_TOOLS_DST="$ROOT_DIR/experiments/kitti/pipeline/tools_py"
KITTI_SUPPORT_DST="$ROOT_DIR/experiments/kitti/support_files"
UDACITY_PIPELINE_DST="$ROOT_DIR/experiments/udacity/pipeline/udacity"
PROCESS_METHODS_DST="$ROOT_DIR/third_party/process_methods"

mkdir -p \
  "$IQV_2026_DST" \
  "$KITTI_TOOLS_DST" \
  "$KITTI_SUPPORT_DST" \
  "$UDACITY_PIPELINE_DST" \
  "$PROCESS_METHODS_DST"

COMMON_EXCLUDES=(
  --exclude '.git/'
  --exclude '.svn/'
  --exclude '.vscode/'
  --exclude '.idea/'
  --exclude '__pycache__/'
  --exclude '*.log'
  --exclude '*.tmp'
)

HEAVY_EXCLUDES=(
  --exclude '*.pth'
  --exclude '*.pt'
  --exclude '*.ckpt'
  --exclude '*.onnx'
  --exclude '*.npy'
  --exclude '*.npz'
  --exclude '*.zip'
  --exclude '*.7z'
  --exclude '*.tar'
  --exclude '*.tar.gz'
  --exclude '*.tgz'
)

echo "[sync] tools/py -> $KITTI_TOOLS_DST"
rsync -a --delete \
  "${COMMON_EXCLUDES[@]}" \
  "$SRC_MIRROR/tools/py/" "$KITTI_TOOLS_DST/"

echo "[sync] tools/py (2026 scripts) -> $IQV_2026_DST"
find "$SRC_MIRROR/tools/py" -maxdepth 1 -type f -name '*.py' -newermt '2026-01-01' -print0 | while IFS= read -r -d '' f; do
  cp -f "$f" "$IQV_2026_DST/"
done

echo "[sync] kitti_test -> $KITTI_SUPPORT_DST"
rsync -a --delete \
  "${COMMON_EXCLUDES[@]}" \
  "$SRC_MIRROR/kitti_test/" "$KITTI_SUPPORT_DST/"

echo "[sync] udacity -> $UDACITY_PIPELINE_DST (excluding outputs)"
rsync -a --delete \
  "${COMMON_EXCLUDES[@]}" \
  "${HEAVY_EXCLUDES[@]}" \
  --exclude 'out_eval/' \
  --exclude 'out_eval_combo/' \
  --exclude 'results/' \
  --exclude 'logs/' \
  --exclude 'self-driving-car/datasets/' \
  "$SRC_MIRROR/udacity/" "$UDACITY_PIPELINE_DST/"

echo "[sync] process_mothod (legacy source name) -> $PROCESS_METHODS_DST (publish name: process_methods)"
rsync -a --delete \
  "${COMMON_EXCLUDES[@]}" \
  "${HEAVY_EXCLUDES[@]}" \
  --exclude 'train_log/' \
  --exclude 'results/' \
  --exclude 'logs/' \
  "$SRC_MIRROR/process_mothod/" "$PROCESS_METHODS_DST/"

echo "[ok] kitti/udacity source sync complete."
