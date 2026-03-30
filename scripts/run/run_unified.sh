#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run/run_unified.sh <rq1|rq2|rq3|all> [options] [-- extra args]

Options:
  --rq1-profile <name>  Profile passed to run_rq1_kitti.sh
  --rq2-profile <name>  Profile passed to run_rq2_udacity.sh
  --rq3-profile <name>  Profile passed to run_rq3_carla.sh
  --dry-run             Print delegated commands only
  --help                Show this help

Examples:
  bash scripts/run/run_unified.sh rq1
  bash scripts/run/run_unified.sh rq2 --rq2-profile paper-ch2-main -- --pipelines all --resume
  bash scripts/run/run_unified.sh rq3 --rq3-profile paper-carla-summary
  bash scripts/run/run_unified.sh all
EOF
}

if [ "$#" -lt 1 ]; then
  usage
  exit 1
fi

MODE="$1"
shift

RQ1_PROFILE=""
RQ2_PROFILE=""
RQ3_PROFILE=""
DRY_RUN="0"
EXTRA_ARGS=()

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

run_rq1=("${SCRIPT_DIR}/run_rq1_kitti.sh")
run_rq2=("${SCRIPT_DIR}/run_rq2_udacity.sh")
run_rq3=("${SCRIPT_DIR}/run_rq3_carla.sh")

if [ -n "${RQ1_PROFILE}" ]; then
  run_rq1+=(--profile "${RQ1_PROFILE}")
fi
if [ -n "${RQ2_PROFILE}" ]; then
  run_rq2+=(--profile "${RQ2_PROFILE}")
fi
if [ -n "${RQ3_PROFILE}" ]; then
  run_rq3+=(--profile "${RQ3_PROFILE}")
fi
if [ "${DRY_RUN}" = "1" ]; then
  run_rq1+=(--dry-run)
  run_rq2+=(--dry-run)
  run_rq3+=(--dry-run)
fi

case "${MODE}" in
  rq1)
    bash "${run_rq1[@]}" -- "${EXTRA_ARGS[@]}"
    ;;
  rq2)
    bash "${run_rq2[@]}" -- "${EXTRA_ARGS[@]}"
    ;;
  rq3)
    bash "${run_rq3[@]}" -- "${EXTRA_ARGS[@]}"
    ;;
  all)
    bash "${run_rq1[@]}"
    bash "${run_rq2[@]}"
    bash "${run_rq3[@]}"
    ;;
  *)
    usage
    exit 1
    ;;
esac
