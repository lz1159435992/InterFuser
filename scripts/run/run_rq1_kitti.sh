#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ORIG_DIR="${ROOT_DIR}/experiments/kitti/rq1_scripts_original"
PIPELINE_DIR="${ROOT_DIR}/experiments/kitti/pipeline/tools_py"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run/run_rq1_kitti.sh [--profile <name>] [--dry-run] [--] [extra args...]

Profiles:
  original               Use original lightweight table script (default).
  paper-kitti-main       Main paper profile for KITTI rerun (recommended).
  paper-kitti-gpu        GPU-accelerated KITTI quality profile.
  legacy-kitti-main      Backward-compatible alias of paper-kitti-main.
  legacy-kitti-gpu       Backward-compatible alias of paper-kitti-gpu.

Examples:
  bash scripts/run/run_rq1_kitti.sh
  bash scripts/run/run_rq1_kitti.sh --profile paper-kitti-main -- --kitti-root ./data/kitti --sources combo,objects
  bash scripts/run/run_rq1_kitti.sh --profile paper-kitti-gpu -- --kitti-root ./data/kitti --sources combo

Notes:
  - paper-kitti-main defaults to full-run flags when no task flags are provided:
    --run-niqe-brisque --run-psnr-ssim-lpips --run-virconv --run-did-m3d
EOF
}

PROFILE="original"
DRY_RUN="0"
EXTRA_ARGS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --profile)
      PROFILE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      EXTRA_ARGS=("$@")
      break
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

has_flag() {
  local needle="$1"
  for a in "${EXTRA_ARGS[@]:-}"; do
    if [ "${a}" = "${needle}" ]; then
      return 0
    fi
  done
  return 1
}

flag_value() {
  local needle="$1"
  local i=0
  while [ $i -lt ${#EXTRA_ARGS[@]} ]; do
    if [ "${EXTRA_ARGS[$i]}" = "${needle}" ]; then
      local j=$((i + 1))
      if [ $j -lt ${#EXTRA_ARGS[@]} ]; then
        echo "${EXTRA_ARGS[$j]}"
        return 0
      fi
    fi
    i=$((i + 1))
  done
  return 1
}

if [ "${PROFILE}" = "original" ]; then
  TARGET="${ORIG_DIR}/calculate_rq1_table_from_csv.py"
  CMD=(python "${TARGET}" "${EXTRA_ARGS[@]}")
elif [ "${PROFILE}" = "paper-kitti-main" ] || [ "${PROFILE}" = "legacy-kitti-main" ]; then
  TARGET="${PIPELINE_DIR}/run_kitti_eval.py"
  if has_flag "--kitti-root"; then
    KROOT="$(flag_value --kitti-root || true)"
  else
    KROOT="${ROOT_DIR}/data/kitti"
  fi
  if [ "${DRY_RUN}" != "1" ] && [ ! -d "${KROOT}" ]; then
    echo "RQ1 paper profile requires KITTI path. Pass: -- --kitti-root /your/KITTI/root" >&2
    exit 2
  fi
  if ! has_flag "--kitti-root"; then
    EXTRA_ARGS+=(--kitti-root "${KROOT}")
  fi
  if ! has_flag "--det-gt-root"; then
    EXTRA_ARGS+=(--det-gt-root "${KROOT}/object")
  fi
  if ! has_flag "--gt0-dir"; then
    EXTRA_ARGS+=(--gt0-dir "${KROOT}/object_0/training/image_2")
  fi
  if ! has_flag "--gt3-dir"; then
    EXTRA_ARGS+=(--gt3-dir "${KROOT}/object_3/training/image_2")
  fi
  if ! has_flag "--fi-gt0-dir"; then
    EXTRA_ARGS+=(--fi-gt0-dir "${KROOT}/object_0/training/image_2")
  fi
  if ! has_flag "--fi-gt2-dir"; then
    EXTRA_ARGS+=(--fi-gt2-dir "${KROOT}/object_2/training/image_2")
  fi
  if ! has_flag "--fi-gt0-x2-dir"; then
    EXTRA_ARGS+=(--fi-gt0-x2-dir "${KROOT}/object_3/training/image_2")
  fi
  if ! has_flag "--out-root"; then
    EXTRA_ARGS+=(--out-root "${ROOT_DIR}/results/raw/rq1/kitti_main")
  fi
  if ! has_flag "--run-id"; then
    EXTRA_ARGS+=(--run-id "rq1_$(date +%Y%m%d_%H%M%S)")
  fi
  if ! has_flag "--run-niqe-brisque" && ! has_flag "--run-psnr-ssim-lpips" && ! has_flag "--run-virconv" && ! has_flag "--run-did-m3d"; then
    EXTRA_ARGS+=(--run-niqe-brisque --run-psnr-ssim-lpips --run-virconv --run-did-m3d)
  fi
  if [ "${DRY_RUN}" != "1" ]; then
    if has_flag "--virconv-root"; then
      VROOT="$(flag_value --virconv-root || true)"
    else
      VROOT="${ROOT_DIR}/data/virconv"
    fi
    if has_flag "--did-m3d-root"; then
      DROOT="$(flag_value --did-m3d-root || true)"
    else
      DROOT="${ROOT_DIR}/experiments/kitti/support_files/did_m3d"
    fi
    if [ ! -d "${VROOT}" ]; then
      echo "RQ1 full-run requires VirConv root. Pass: -- --virconv-root /path/to/VirConv" >&2
      exit 2
    fi
    if [ ! -d "${DROOT}" ]; then
      echo "RQ1 full-run requires DID-M3D root. Pass: -- --did-m3d-root /path/to/did_m3d" >&2
      exit 2
    fi
    if has_flag "--kitti-native-eval-bin"; then
      KBIN="$(flag_value --kitti-native-eval-bin || true)"
    else
      KBIN="${ROOT_DIR}/experiments/kitti/support_files/kitti_native_evaluation/evaluate_object_3d_offline"
    fi
    if [ ! -f "${KBIN}" ]; then
      echo "RQ1 full-run requires KITTI native eval binary: ${KBIN}" >&2
      echo "Build it first: make -C ${ROOT_DIR}/experiments/kitti/support_files/kitti_native_evaluation" >&2
      exit 2
    fi
  fi
  if ! has_flag "--virconv-root"; then
    EXTRA_ARGS+=(--virconv-root "${ROOT_DIR}/data/virconv")
  fi
  if ! has_flag "--did-m3d-root"; then
    EXTRA_ARGS+=(--did-m3d-root "${ROOT_DIR}/experiments/kitti/support_files/did_m3d")
  fi
  if ! has_flag "--kitti-native-eval-bin"; then
    EXTRA_ARGS+=(--kitti-native-eval-bin "${ROOT_DIR}/experiments/kitti/support_files/kitti_native_evaluation/evaluate_object_3d_offline")
  fi
  CMD=(python "${TARGET}" "${EXTRA_ARGS[@]}")
elif [ "${PROFILE}" = "paper-kitti-gpu" ] || [ "${PROFILE}" = "legacy-kitti-gpu" ]; then
  TARGET="${PIPELINE_DIR}/run_kitti_eval_gpu.py"
  if has_flag "--kitti-root"; then
    KROOT="$(flag_value --kitti-root || true)"
  else
    KROOT="${ROOT_DIR}/data/kitti"
  fi
  if [ "${DRY_RUN}" != "1" ] && [ ! -d "${KROOT}" ]; then
    echo "RQ1 paper GPU profile requires KITTI path. Pass: -- --kitti-root /your/KITTI/root" >&2
    exit 2
  fi
  if ! has_flag "--kitti-root"; then
    EXTRA_ARGS+=(--kitti-root "${KROOT}")
  fi
  if ! has_flag "--out-root"; then
    EXTRA_ARGS+=(--out-root "${ROOT_DIR}/results/raw/rq1/kitti_gpu")
  fi
  if ! has_flag "--run-id"; then
    EXTRA_ARGS+=(--run-id "rq1gpu_$(date +%Y%m%d_%H%M%S)")
  fi
  CMD=(python "${TARGET}" "${EXTRA_ARGS[@]}")
else
  echo "Unknown profile: ${PROFILE}" >&2
  usage >&2
  exit 1
fi

if [ ! -f "${TARGET}" ]; then
  echo "RQ1 entry script not found: ${TARGET}" >&2
  exit 1
fi

echo "[RQ1] profile=${PROFILE}"
echo "[RQ1] cmd=${CMD[*]}"

if [ "${DRY_RUN}" = "1" ]; then
  exit 0
fi

cd "$(dirname "${TARGET}")"
"${CMD[@]}"
