#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

KITTI_GEN="${ROOT_DIR}/experiments/kitti/upstream_hosts/host172/tools_py/gen_kitti_combo_dataset.py"
CH2_GEN="${ROOT_DIR}/experiments/udacity/upstream_hosts/host172/tools/gen_combo_dataset.py"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/data/prepare_augmented_inputs.sh [options]

Options:
  --task <all|kitti|ch2>     What to prepare (default: all)
  --kitti-root <path>        KITTI root (default: <repo>/data/kitti)
  --ch2-root <path>          Udacity CH2 root (default: <repo>/data/ch2)
  --kitti-pipelines <spec>   all or comma list (default: all)
  --ch2-pipelines <spec>     all or comma list (default: all)
  --segments <list>          CH2 segments list (default: 1,2,3,4,5,6)
  --process-method-root <p>  process_mothod root (default: <repo>/third_party/process_mothod)
  --force                    Regenerate existing outputs
  --dry-run                  Print commands only
  --help                     Show this help

Examples:
  bash scripts/data/prepare_augmented_inputs.sh --task kitti
  bash scripts/data/prepare_augmented_inputs.sh --task ch2 --segments 1,2,3
  bash scripts/data/prepare_augmented_inputs.sh --task all --process-method-root ./third_party/process_mothod
EOF
}

TASK="all"
KITTI_ROOT="${ROOT_DIR}/data/kitti"
CH2_ROOT="${ROOT_DIR}/data/ch2"
KITTI_PIPELINES="all"
CH2_PIPELINES="all"
SEGMENTS="1,2,3,4,5,6"
PROCESS_METHOD_ROOT="${ROOT_DIR}/third_party/process_mothod"
FORCE="0"
DRY_RUN="0"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --task)
      TASK="${2:-}"
      shift 2
      ;;
    --kitti-root)
      KITTI_ROOT="${2:-}"
      shift 2
      ;;
    --ch2-root)
      CH2_ROOT="${2:-}"
      shift 2
      ;;
    --kitti-pipelines)
      KITTI_PIPELINES="${2:-}"
      shift 2
      ;;
    --ch2-pipelines)
      CH2_PIPELINES="${2:-}"
      shift 2
      ;;
    --segments)
      SEGMENTS="${2:-}"
      shift 2
      ;;
    --process-method-root)
      PROCESS_METHOD_ROOT="${2:-}"
      shift 2
      ;;
    --force)
      FORCE="1"
      shift
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ "${TASK}" != "all" ] && [ "${TASK}" != "kitti" ] && [ "${TASK}" != "ch2" ]; then
  echo "Invalid --task: ${TASK}" >&2
  exit 1
fi

run_cmd() {
  local -a cmd=("$@")
  echo "${cmd[*]}"
  if [ "${DRY_RUN}" != "1" ]; then
    "${cmd[@]}"
  fi
}

run_kitti() {
  if [ ! -f "${KITTI_GEN}" ]; then
    echo "KITTI generator not found: ${KITTI_GEN}" >&2
    exit 1
  fi
  if [ "${DRY_RUN}" != "1" ]; then
    if [ ! -d "${KITTI_ROOT}/object_0/training/image_2" ]; then
      echo "Missing KITTI input: ${KITTI_ROOT}/object_0/training/image_2" >&2
      exit 2
    fi
    if [ ! -d "${KITTI_ROOT}/object_2/training/image_2" ]; then
      echo "Missing KITTI input: ${KITTI_ROOT}/object_2/training/image_2" >&2
      exit 2
    fi
    if [ ! -d "${PROCESS_METHOD_ROOT}" ]; then
      echo "Missing process_mothod root: ${PROCESS_METHOD_ROOT}" >&2
      exit 2
    fi
  fi

  local -a cmd=(
    python "${KITTI_GEN}"
    --pipelines "${KITTI_PIPELINES}"
    --kitti-root "${KITTI_ROOT}"
    --output-root "${KITTI_ROOT}/combo"
    --process-method-root "${PROCESS_METHOD_ROOT}"
    --srgan-model-path "${PROCESS_METHOD_ROOT}/SRGAN/results/checkpoint_srgan.pth"
    --swinir-model-path "${PROCESS_METHOD_ROOT}/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth"
    --rife-model-dir "${PROCESS_METHOD_ROOT}/ECCV2022-RIFE/train_log"
  )
  if [ "${FORCE}" = "1" ]; then
    cmd+=(--force)
  fi
  echo "[prepare] KITTI combo generation"
  run_cmd "${cmd[@]}"
}

run_ch2() {
  if [ ! -f "${CH2_GEN}" ]; then
    echo "CH2 generator not found: ${CH2_GEN}" >&2
    exit 1
  fi
  if [ "${DRY_RUN}" != "1" ]; then
    if [ ! -d "${CH2_ROOT}/input" ]; then
      echo "Missing CH2 input: ${CH2_ROOT}/input" >&2
      exit 2
    fi
    if [ ! -d "${PROCESS_METHOD_ROOT}" ]; then
      echo "Missing process_mothod root: ${PROCESS_METHOD_ROOT}" >&2
      exit 2
    fi
  fi

  local -a pipelines=()
  if [ "${CH2_PIPELINES}" = "all" ]; then
    pipelines=(
      GN8 GN16
      A B C
      "A->B" "B->A" "A->C" "C->A" "B->C" "C->B"
      "A->B->C" "A->C->B" "B->A->C" "B->C->A" "C->A->B" "C->B->A"
    )
  else
    IFS=',' read -r -a pipelines <<< "${CH2_PIPELINES}"
  fi

  echo "[prepare] CH2 combo generation (${#pipelines[@]} pipelines)"
  local pipeline
  for pipeline in "${pipelines[@]}"; do
    local -a cmd=(
      python "${CH2_GEN}"
      --pipeline "${pipeline}"
      --segments "${SEGMENTS}"
      --input-root "${CH2_ROOT}/input"
      --output-root "${CH2_ROOT}/input_combo"
      --process-method-root "${PROCESS_METHOD_ROOT}"
      --srgan-model-path "${PROCESS_METHOD_ROOT}/SRGAN/results/checkpoint_srgan.pth"
      --swinir-model-path "${PROCESS_METHOD_ROOT}/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth"
      --rife-model-dir "${PROCESS_METHOD_ROOT}/ECCV2022-RIFE/train_log"
    )
    if [ "${FORCE}" = "1" ]; then
      cmd+=(--force)
    fi
    run_cmd "${cmd[@]}"
  done
}

echo "[prepare] task=${TASK}"
echo "[prepare] kitti_root=${KITTI_ROOT}"
echo "[prepare] ch2_root=${CH2_ROOT}"
echo "[prepare] process_method_root=${PROCESS_METHOD_ROOT}"

if [ "${TASK}" = "all" ] || [ "${TASK}" = "kitti" ]; then
  run_kitti
fi

if [ "${TASK}" = "all" ] || [ "${TASK}" = "ch2" ]; then
  run_ch2
fi

echo "[prepare] done"
