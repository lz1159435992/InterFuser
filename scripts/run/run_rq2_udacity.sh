#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ORIG_DIR="${ROOT_DIR}/experiments/udacity/rq2_scripts_original"
PIPELINE_TOOLS="${ROOT_DIR}/experiments/udacity/pipeline/udacity/tools"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run/run_rq2_udacity.sh [--profile <name>] [--dry-run] [--] [extra args...]

Profiles:
  original            Use original lightweight violation script (default).
  paper-ch2-main      Main paper profile for CH2 rerun (recommended).
  paper-ch2-variant   Secondary CH2 variant profile.
  legacy-ch2-main     Backward-compatible alias of paper-ch2-main.
  legacy-ch2-variant  Backward-compatible alias of paper-ch2-variant.

Examples:
  bash scripts/run/run_rq2_udacity.sh
  bash scripts/run/run_rq2_udacity.sh --profile paper-ch2-main -- --pipelines all --segments 1,2,3,4,5,6 --resume
  bash scripts/run/run_rq2_udacity.sh --profile paper-ch2-main -- --skip-eval --pipelines all

Notes:
  - paper-ch2-main/paper-ch2-variant default to --ch2-root ${ROOT_DIR}/data/ch2
    and --weights-root ${ROOT_DIR}/data/community-models.
  - paper-ch2-main/paper-ch2-variant enforce --skip-gen by default. Prepare combo
    inputs first via scripts/data/prepare_augmented_inputs.sh.
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
  TARGET="${ORIG_DIR}/calculate_rq2_violations.py"
  CMD=(python "${TARGET}" "${EXTRA_ARGS[@]}")
elif [ "${PROFILE}" = "paper-ch2-main" ] || [ "${PROFILE}" = "legacy-ch2-main" ]; then
  TARGET="${PIPELINE_TOOLS}/run_combo_eval.py"
  if has_flag "--ch2-root"; then
    CH2_ROOT="$(flag_value --ch2-root || true)"
  else
    CH2_ROOT="${ROOT_DIR}/data/ch2"
  fi
  if has_flag "--weights-root"; then
    W_ROOT="$(flag_value --weights-root || true)"
  else
    W_ROOT="${ROOT_DIR}/data/community-models"
  fi
  if [ "${DRY_RUN}" != "1" ] && ( [ ! -d "${CH2_ROOT}" ] || [ ! -d "${W_ROOT}" ] ); then
    echo "RQ2 paper profile requires CH2 and weights paths." >&2
    echo "Use: -- --ch2-root /path/to/CH2 --weights-root /path/to/community-models" >&2
    exit 2
  fi
  if ! has_flag "--out-root"; then
    EXTRA_ARGS+=(--out-root "${ROOT_DIR}/results/raw/rq2/ch2_main")
  fi
  if ! has_flag "--run-id"; then
    EXTRA_ARGS+=(--run-id "rq2_$(date +%Y%m%d_%H%M%S)")
  fi
  if ! has_flag "--ch2-root"; then
    EXTRA_ARGS+=(--ch2-root "${CH2_ROOT}")
  fi
  if ! has_flag "--weights-root"; then
    EXTRA_ARGS+=(--weights-root "${W_ROOT}")
  fi
  if ! has_flag "--skip-gen"; then
    EXTRA_ARGS+=(--skip-gen)
  fi
  if [ "${DRY_RUN}" != "1" ] && [ ! -d "${CH2_ROOT}/input_combo" ]; then
    echo "RQ2 requires prepared combo inputs at: ${CH2_ROOT}/input_combo" >&2
    echo "Run: bash scripts/data/prepare_augmented_inputs.sh --task ch2 --ch2-root ${CH2_ROOT}" >&2
    exit 2
  fi
  CMD=(python "${TARGET}" "${EXTRA_ARGS[@]}")
elif [ "${PROFILE}" = "paper-ch2-variant" ] || [ "${PROFILE}" = "legacy-ch2-variant" ]; then
  TARGET="${PIPELINE_TOOLS}/run_combo_eval.py"
  if has_flag "--ch2-root"; then
    CH2_ROOT="$(flag_value --ch2-root || true)"
  else
    CH2_ROOT="${ROOT_DIR}/data/ch2"
  fi
  if has_flag "--weights-root"; then
    W_ROOT="$(flag_value --weights-root || true)"
  else
    W_ROOT="${ROOT_DIR}/data/community-models"
  fi
  if [ "${DRY_RUN}" != "1" ] && ( [ ! -d "${CH2_ROOT}" ] || [ ! -d "${W_ROOT}" ] ); then
    echo "RQ2 paper profile requires CH2 and weights paths." >&2
    echo "Use: -- --ch2-root /path/to/CH2 --weights-root /path/to/community-models" >&2
    exit 2
  fi
  if ! has_flag "--out-root"; then
    EXTRA_ARGS+=(--out-root "${ROOT_DIR}/results/raw/rq2/ch2_variant")
  fi
  if ! has_flag "--run-id"; then
    EXTRA_ARGS+=(--run-id "rq2_$(date +%Y%m%d_%H%M%S)")
  fi
  if ! has_flag "--ch2-root"; then
    EXTRA_ARGS+=(--ch2-root "${CH2_ROOT}")
  fi
  if ! has_flag "--weights-root"; then
    EXTRA_ARGS+=(--weights-root "${W_ROOT}")
  fi
  if ! has_flag "--skip-gen"; then
    EXTRA_ARGS+=(--skip-gen)
  fi
  if [ "${DRY_RUN}" != "1" ] && [ ! -d "${CH2_ROOT}/input_combo" ]; then
    echo "RQ2 requires prepared combo inputs at: ${CH2_ROOT}/input_combo" >&2
    echo "Run: bash scripts/data/prepare_augmented_inputs.sh --task ch2 --ch2-root ${CH2_ROOT}" >&2
    exit 2
  fi
  CMD=(python "${TARGET}" "${EXTRA_ARGS[@]}")
else
  echo "Unknown profile: ${PROFILE}" >&2
  usage >&2
  exit 1
fi

if [ ! -f "${TARGET}" ]; then
  echo "RQ2 entry script not found: ${TARGET}" >&2
  exit 1
fi

echo "[RQ2] profile=${PROFILE}"
echo "[RQ2] cmd=${CMD[*]}"

if [ "${DRY_RUN}" = "1" ]; then
  exit 0
fi

cd "$(dirname "${TARGET}")"
"${CMD[@]}"
