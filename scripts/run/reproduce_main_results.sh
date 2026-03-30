#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run/reproduce_main_results.sh [options]

Options:
  --rq1-profile <name>  Profile for RQ1 runner (default: paper-kitti-main)
  --rq2-profile <name>  Profile for RQ2 runner (default: paper-ch2-main)
  --rq3-profile <name>  Profile for RQ3 runner (default: paper-carla-native)
  --prepare-data        Prepare KITTI/CH2 augmented inputs before running RQs
  --prepare-only        Only run data preparation then exit
  --skip-merge          Skip merge/index stage
  --dry-run             Print commands only
  --help                Show this help
EOF
}

RQ1_PROFILE="paper-kitti-main"
RQ2_PROFILE="paper-ch2-main"
RQ3_PROFILE="paper-carla-native"
SKIP_MERGE="0"
DRY_RUN="0"
PREPARE_DATA="0"
PREPARE_ONLY="0"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --rq1-profile)
      RQ1_PROFILE="${2:-}"
      shift 2
      ;;
    --rq2-profile)
      RQ2_PROFILE="${2:-}"
      shift 2
      ;;
    --rq3-profile)
      RQ3_PROFILE="${2:-}"
      shift 2
      ;;
    --skip-merge)
      SKIP_MERGE="1"
      shift
      ;;
    --prepare-data)
      PREPARE_DATA="1"
      shift
      ;;
    --prepare-only)
      PREPARE_DATA="1"
      PREPARE_ONLY="1"
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

prepare_cmd=(bash "${ROOT_DIR}/scripts/data/prepare_augmented_inputs.sh" --task all)
rq1_cmd=(bash "${SCRIPT_DIR}/run_rq1_kitti.sh" --profile "${RQ1_PROFILE}")
rq2_cmd=(bash "${SCRIPT_DIR}/run_rq2_udacity.sh" --profile "${RQ2_PROFILE}")
rq3_cmd=(bash "${SCRIPT_DIR}/run_rq3_carla.sh" --profile "${RQ3_PROFILE}")
merge_cmd=(python "${SCRIPT_DIR}/../merge/merge_results.py" --input-root "${ROOT_DIR}/results/raw" --output-root "${ROOT_DIR}/results/processed")
rq1_norm_cmd=(python "${SCRIPT_DIR}/../merge/extract_rq1_runs_to_csv.py" --input-root "${ROOT_DIR}/results/raw/rq1" --output-csv "${ROOT_DIR}/results/processed/rq1_summary_normalized.csv")
rq2_norm_cmd=(python "${SCRIPT_DIR}/../merge/extract_rq2_runs_to_csv.py" --input-root "${ROOT_DIR}/results/raw/rq2" --output-csv "${ROOT_DIR}/results/processed/rq2_summary_normalized.csv")

if [ "${DRY_RUN}" = "1" ]; then
  prepare_cmd+=(--dry-run)
fi

if [ "${PREPARE_DATA}" = "1" ]; then
  echo "[0/3] Prepare KITTI/CH2 augmented inputs"
  echo "  ${prepare_cmd[*]}"
  if [ "${DRY_RUN}" != "1" ]; then
    "${prepare_cmd[@]}"
  fi
  if [ "${PREPARE_ONLY}" = "1" ]; then
    echo "Finished (prepare-only)."
    exit 0
  fi
fi

echo "[1/3] RQ1 KITTI"
echo "  ${rq1_cmd[*]}"
if [ "${DRY_RUN}" != "1" ]; then
  "${rq1_cmd[@]}"
fi

echo "[2/3] RQ2 Udacity"
echo "  ${rq2_cmd[*]}"
if [ "${DRY_RUN}" != "1" ]; then
  "${rq2_cmd[@]}"
fi

echo "[3/3] RQ3 CARLA"
echo "  ${rq3_cmd[*]}"
if [ "${DRY_RUN}" != "1" ]; then
  "${rq3_cmd[@]}"
fi

if [ "${SKIP_MERGE}" = "1" ]; then
  echo "Skip merge stage."
else
  echo "Normalizing RQ1 summaries"
  echo "  ${rq1_norm_cmd[*]}"
  if [ "${DRY_RUN}" != "1" ]; then
    "${rq1_norm_cmd[@]}"
  fi

  echo "Normalizing RQ2 summaries"
  echo "  ${rq2_norm_cmd[*]}"
  if [ "${DRY_RUN}" != "1" ]; then
    "${rq2_norm_cmd[@]}"
  fi

  echo "Merging outputs"
  echo "  ${merge_cmd[*]}"
  if [ "${DRY_RUN}" != "1" ]; then
    "${merge_cmd[@]}"
  fi
fi

echo "Finished."
