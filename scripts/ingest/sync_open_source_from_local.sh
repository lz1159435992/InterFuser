#!/usr/bin/env bash
set -euo pipefail

# Sync local mirrored open-source projects into publication-friendly paths.
# Source mirror default:
#   ../IntuitionTester_sources/carla_source_mirror

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_ROOT="${INTUITION_TESTER_SOURCES:-$ROOT_DIR/../IntuitionTester_sources}"
SRC_MIRROR="$SRC_ROOT/carla_source_mirror"

if [[ ! -d "$SRC_MIRROR" ]]; then
  for candidate in "$SRC_ROOT"/*; do
    [[ -d "$candidate" ]] || continue
    if [[ -d "$candidate/LMDrive" && -d "$candidate/carla_native_enhancement" ]]; then
      SRC_MIRROR="$candidate"
      break
    fi
  done
fi

if [[ ! -d "$SRC_MIRROR" ]]; then
  echo "[error] source mirror not found: $SRC_MIRROR" >&2
  echo "Set INTUITION_TESTER_SOURCES to your local mirror root." >&2
  echo "Expected: <mirror_root>/carla_source_mirror (or any subdirectory containing LMDrive and carla_native_enhancement)." >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "[error] rsync is required for this script." >&2
  exit 1
fi

INTERFUSER_DST="$ROOT_DIR/third_party/interfuser_project"
LMDRIVE_DST="$ROOT_DIR/third_party/lmdrive"

COMMON_EXCLUDES=(
  --exclude '.git/'
  --exclude '.svn/'
  --exclude '.vscode/'
  --exclude '.idea/'
  --exclude '__pycache__/'
  --exclude 'results/'
  --exclude 'output/'
  --exclude 'logs/'
  --exclude 'runs/'
  --exclude 'wandb/'
  --exclude '*.pth'
  --exclude '*.pt'
  --exclude '*.ckpt'
  --exclude '*.onnx'
  --exclude '*.pkl'
  --exclude '*.npy'
  --exclude '*.npz'
  --exclude '*.zip'
  --exclude '*.7z'
  --exclude '*.tar'
  --exclude '*.tar.gz'
  --exclude '*.tgz'
)

mkdir -p "$INTERFUSER_DST" "$LMDRIVE_DST"

echo "[sync] InterFuser root -> $INTERFUSER_DST"
rsync -a --delete \
  "${COMMON_EXCLUDES[@]}" \
  --exclude 'LMDrive/' \
  --exclude 'data/' \
  --exclude 'dataset/' \
  --exclude 'env_exports/' \
  --exclude '_trash_*/' \
  --exclude '.trash_*/' \
  "$SRC_MIRROR/" "$INTERFUSER_DST/"

echo "[sync] LMDrive root -> $LMDRIVE_DST"
rsync -a --delete \
  "${COMMON_EXCLUDES[@]}" \
  "$SRC_MIRROR/LMDrive/" "$LMDRIVE_DST/"

echo "[ok] local open-source sync complete."
