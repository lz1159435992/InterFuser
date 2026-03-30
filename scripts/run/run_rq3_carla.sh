#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ORIG_DIR="${ROOT_DIR}/experiments/carla/rq3_scripts_original"
UPSTREAM_NATIVE_DIR="${ROOT_DIR}/experiments/carla/upstream_hosts/host210/carla_native_enhancement"
UPSTREAM_RESULTS_DIR="${ROOT_DIR}/experiments/carla/upstream_hosts/host210/results_native"
SUMMARY_SCRIPT="${ROOT_DIR}/scripts/merge/extract_rq3_native_json_to_csv.py"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run/run_rq3_carla.sh [--profile <name>] [--dry-run] [--] [extra args...]

Profiles:
  original                Use original extract_rq3_tables.py (default).
  paper-carla-native      Main paper profile for native CARLA rerun (recommended).
  paper-carla-summary     Summarize integrated results_native/*.json to CSV.
  upstream-host210-native Backward-compatible alias of paper-carla-native.
  upstream-host210-summary Backward-compatible alias of paper-carla-summary.

Examples:
  bash scripts/run/run_rq3_carla.sh
  bash scripts/run/run_rq3_carla.sh --profile paper-carla-summary
  bash scripts/run/run_rq3_carla.sh --profile paper-carla-native -- town05 high_fps
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

if [ "${PROFILE}" = "original" ]; then
  TARGET="${ORIG_DIR}/extract_rq3_tables.py"
  CMD=(python "${TARGET}" "${EXTRA_ARGS[@]}")
elif [ "${PROFILE}" = "paper-carla-native" ] || [ "${PROFILE}" = "upstream-host210-native" ]; then
  TARGET="${UPSTREAM_NATIVE_DIR}/run_evaluation_native.sh"
  CMD=(bash "${TARGET}" "${EXTRA_ARGS[@]}")
elif [ "${PROFILE}" = "paper-carla-summary" ] || [ "${PROFILE}" = "upstream-host210-summary" ]; then
  TARGET="${SUMMARY_SCRIPT}"
  OUT="${ROOT_DIR}/results/raw/rq3/carla_native_summary.csv"
  CMD=(python "${TARGET}" --input-dir "${UPSTREAM_RESULTS_DIR}" --output-csv "${OUT}" "${EXTRA_ARGS[@]}")
else
  echo "Unknown profile: ${PROFILE}" >&2
  usage >&2
  exit 1
fi

if [ ! -f "${TARGET}" ]; then
  echo "RQ3 entry script not found: ${TARGET}" >&2
  exit 1
fi

echo "[RQ3] profile=${PROFILE}"
echo "[RQ3] cmd=${CMD[*]}"

if [ "${DRY_RUN}" = "1" ]; then
  exit 0
fi

cd "$(dirname "${TARGET}")"
"${CMD[@]}"
