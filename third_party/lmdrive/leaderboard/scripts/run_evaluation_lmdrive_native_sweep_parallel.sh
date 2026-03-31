#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LMDRIVE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Semicolon-separated list of EVAL_TYPE values.
# Default covers all 3 groups.
EVAL_TYPES=${EVAL_TYPES:-"langauto_tiny;langauto_short;langauto_long"}

# Comma-separated list of NATIVE_ENHANCE values.
# Example: "none" or "high_fps" or "high_fps,no_noise".
CONFIGS=${CONFIGS:-"none,high_fps,high_fps,no_noise,high_res,high_res,no_noise"}

# GPUs to use, comma-separated. Default: 0,1,2,3
GPUS=${GPUS:-"0,1,2,3"}

# Base directory for outputs (SAVE_PATH and CHECKPOINT_ENDPOINT). Timestamped by default.
RUN_TAG=${RUN_TAG:-"$(date +%Y%m%d_%H%M%S)"}
BASE_SAVE_ROOT=${BASE_SAVE_ROOT:-"${LMDRIVE_ROOT}/data/eval_native_sweep/${RUN_TAG}"}
BASE_CKPT_ROOT=${BASE_CKPT_ROOT:-"${LMDRIVE_ROOT}/results/native_sweep/${RUN_TAG}"}

# Use fixed ports per GPU to reduce collisions. Can be overridden.
PORT_BASE=${PORT_BASE:-2000}
PORT_STRIDE=${PORT_STRIDE:-100}
TM_PORT_OFFSET=${TM_PORT_OFFSET:-500}

# Common env defaults; you can override from shell.
AUTO_START_CARLA=${AUTO_START_CARLA:-1}
FORCE_CARLA_PY37=${FORCE_CARLA_PY37:-1}
CARLA_PY37_BIN=${CARLA_PY37_BIN:-/opt/conda_envs/interfuser/bin/python3.7}
CARLA_ROOT=${CARLA_ROOT:-"${LMDRIVE_ROOT}/../carla"}

mkdir -p "${BASE_SAVE_ROOT}"
mkdir -p "${BASE_CKPT_ROOT}"

IFS=',' read -r -a GPU_ARR <<< "${GPUS}"

IFS=';' read -r -a EVAL_TYPE_LIST <<< "${EVAL_TYPES}"

# Parse CONFIGS which can contain commas inside a single config (e.g. high_fps,no_noise).
# We accept CONFIGS as a semicolon-separated list primarily, but keep comma list as a convenience.
# Priority:
# - If CONFIGS contains ';', split on ';'
# - Else split on ',' and treat each token as an independent config (no multi-token configs)
CONFIG_LIST=()
if [[ "${CONFIGS}" == *";"* ]]; then
  IFS=';' read -r -a CONFIG_LIST <<< "${CONFIGS}"
else
  IFS=',' read -r -a CONFIG_LIST <<< "${CONFIGS}"
fi

num_gpus=${#GPU_ARR[@]}
num_cfgs=${#CONFIG_LIST[@]}
num_eval_types=${#EVAL_TYPE_LIST[@]}

if [ "${num_gpus}" -le 0 ]; then
  echo "Error: GPUS is empty" >&2
  exit 1
fi
if [ "${num_cfgs}" -le 0 ]; then
  echo "Error: CONFIGS is empty" >&2
  exit 1
fi
if [ "${num_eval_types}" -le 0 ]; then
  echo "Error: EVAL_TYPES is empty" >&2
  exit 1
fi

RUNNER="${SCRIPT_DIR}/run_evaluation_lmdrive_native.sh"

worker_pids=()

echo "Sweep tag: ${RUN_TAG}" >&2
echo "EVAL_TYPES: ${EVAL_TYPES}" >&2
echo "GPUS: ${GPUS}" >&2
echo "BASE_SAVE_ROOT: ${BASE_SAVE_ROOT}" >&2
echo "BASE_CKPT_ROOT: ${BASE_CKPT_ROOT}" >&2
echo "EVAL_TYPES(${num_eval_types}):" >&2
for e in "${EVAL_TYPE_LIST[@]}"; do
  echo "  - ${e}" >&2
done
echo "CONFIGS(${num_cfgs}):" >&2
for c in "${CONFIG_LIST[@]}"; do
  echo "  - ${c}" >&2
done


# Build task lists for each GPU (round-robin assignment).
declare -a TASKS
for ((gi=0; gi<num_gpus; gi++)); do
  TASKS[$gi]=""
done

task_index=0
for eval_type in "${EVAL_TYPE_LIST[@]}"; do
  for cfg in "${CONFIG_LIST[@]}"; do
    gi=$(( task_index % num_gpus ))
    if [ -z "${TASKS[$gi]}" ]; then
      TASKS[$gi]="${eval_type}|${cfg}"
    else
      TASKS[$gi]="${TASKS[$gi]}::${eval_type}|${cfg}"
    fi
    task_index=$((task_index + 1))
  done
done

worker() {
  local gi="$1"
  local gpu="$2"
  local task_blob="$3"

  local fail_local=0
  local local_index=0

  if [ -z "${task_blob}" ]; then
    return 0
  fi

  IFS='::' read -r -a items <<< "${task_blob}"
  for item in "${items[@]}"; do
    eval_type="${item%%|*}"
    cfg="${item#*|}"

    port=$(( PORT_BASE + gi * PORT_STRIDE + local_index ))
    tm_port=$(( port + TM_PORT_OFFSET ))

    native_tag=$(echo "${cfg}" | tr ', ' '__')
    save_path="${BASE_SAVE_ROOT}/${eval_type}/${eval_type}_${native_tag}"
    ckpt_path="${BASE_CKPT_ROOT}/${eval_type}_${native_tag}.json"

    mkdir -p "${save_path}"

    echo "[worker ${gi}] eval_type='${eval_type}' cfg='${cfg}' gpu=${gpu} port=${port} tm_port=${tm_port}" >&2
    echo "[worker ${gi}] SAVE_PATH=${save_path}" >&2
    echo "[worker ${gi}] CHECKPOINT_ENDPOINT=${ckpt_path}" >&2

    if ! (
      set -e
      CUDA_VISIBLE_DEVICES=${gpu} \
      CARLA_CUDA_VISIBLE_DEVICES=${gpu} \
      PY_CUDA_VISIBLE_DEVICES=${gpu} \
      AUTO_START_CARLA=${AUTO_START_CARLA} \
      FORCE_CARLA_PY37=${FORCE_CARLA_PY37} \
      CARLA_PY37_BIN=${CARLA_PY37_BIN} \
      CARLA_ROOT=${CARLA_ROOT} \
      PORT=${port} \
      TM_PORT=${tm_port} \
      SAVE_PATH=${save_path} \
      CHECKPOINT_ENDPOINT=${ckpt_path} \
      PARALLEL_SAFE=1 \
      PRE_CLEANUP=1 \
      bash "${RUNNER}" "${eval_type}" "${cfg}"
    ) >"${save_path}/sweep_stdout.log" 2>&1; then
      echo "[worker ${gi}] FAILED eval_type='${eval_type}' cfg='${cfg}'" >&2
      fail_local=1
    fi

    local_index=$((local_index + 1))

    # Small stagger to reduce startup races between workers.
    sleep 2
  done

  return ${fail_local}
}

echo "Launching ${num_gpus} workers (1 job per GPU at a time)..." >&2
for ((gi=0; gi<num_gpus; gi++)); do
  gpu="${GPU_ARR[$gi]}"
  (
    worker "${gi}" "${gpu}" "${TASKS[$gi]}"
  ) &
  worker_pids+=("$!")
  echo "[worker ${gi}] pid=$! gpu=${gpu}" >&2
done

echo "Waiting for ${#worker_pids[@]} workers..." >&2

fail=0
for pid in "${worker_pids[@]}"; do
  if ! wait "${pid}"; then
    fail=1
  fi
done

if [ "${fail}" -ne 0 ]; then
  echo "One or more jobs failed. Check logs under ${BASE_SAVE_ROOT}." >&2
  exit 1
fi

echo "All jobs finished. Results:" >&2
echo "  - SAVE_PATH root: ${BASE_SAVE_ROOT}" >&2
echo "  - CHECKPOINT root: ${BASE_CKPT_ROOT}" >&2
