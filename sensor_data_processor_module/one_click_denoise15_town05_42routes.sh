#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

EVAL_TARGET=${1:-both}

RUN_AS_USER=${RUN_AS_USER:-}
if [ "$(id -u)" = "0" ] && [ -z "${RUN_AS_USER}" ]; then
  RUN_AS_USER=carlauser
fi

DEFAULT_CONDA_ENV_NAME=interfuser
CONDA_ENV_NAME=${CONDA_ENV_NAME:-${DEFAULT_CONDA_ENV_NAME}}

DEFAULT_CARLA_GPU_ID=0
DEFAULT_PY_CUDA_VISIBLE_DEVICES="1,2"
DEFAULT_DATA_PROCESSOR_GPU_ID=1
DEFAULT_DATA_PROCESSOR_TILE="none"
DEFAULT_DATA_PROCESSOR_HALF="0"

if [ -z "${CARLA_GPU_ID+x}" ] || [ -z "${CARLA_GPU_ID}" ]; then
  if [ -n "${CARLA_CUDA_VISIBLE_DEVICES:-}" ]; then
    CARLA_GPU_ID="${CARLA_CUDA_VISIBLE_DEVICES%%,*}"
  else
    CARLA_GPU_ID="${DEFAULT_CARLA_GPU_ID}"
  fi
fi

CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES:-${CARLA_GPU_ID}}
PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES:-${DEFAULT_PY_CUDA_VISIBLE_DEVICES}}
DATA_PROCESSOR_GPU_ID=${DATA_PROCESSOR_GPU_ID:-${DEFAULT_DATA_PROCESSOR_GPU_ID}}
DATA_PROCESSOR_TILE=${DATA_PROCESSOR_TILE:-${DEFAULT_DATA_PROCESSOR_TILE}}
DATA_PROCESSOR_HALF=${DATA_PROCESSOR_HALF:-${DEFAULT_DATA_PROCESSOR_HALF}}

echo "GPU isolation defaults: CARLA_GPU_ID=${DEFAULT_CARLA_GPU_ID}, PY_CUDA_VISIBLE_DEVICES=${DEFAULT_PY_CUDA_VISIBLE_DEVICES}, DATA_PROCESSOR_GPU_ID=${DEFAULT_DATA_PROCESSOR_GPU_ID}"
echo "GPU isolation in use:    CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} (CARLA_GPU_ID=${CARLA_GPU_ID}), PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES}, DATA_PROCESSOR_GPU_ID=${DATA_PROCESSOR_GPU_ID}"
echo "Denoise15 defaults:      DATA_PROCESSOR_TILE=${DEFAULT_DATA_PROCESSOR_TILE}, DATA_PROCESSOR_HALF=${DEFAULT_DATA_PROCESSOR_HALF}"
echo "Denoise15 in use:        DATA_PROCESSOR_TILE=${DATA_PROCESSOR_TILE}, DATA_PROCESSOR_HALF=${DATA_PROCESSOR_HALF}"

CARLA_PORT=${CARLA_PORT:-${PORT:-2000}}
PORT=${PORT:-${CARLA_PORT}}
CARLA_LOG="${SCRIPT_DIR}/carla_${CARLA_PORT}_$(date +%Y%m%d_%H%M%S).log"

CARLA_ALREADY_RUNNING=0
CARLA_LAUNCH_PID=""

cleanup() {
  if [ "${CARLA_ALREADY_RUNNING}" = "1" ]; then
    return 0
  fi
  if [ -n "${CARLA_LAUNCH_PID}" ]; then
    kill -0 "${CARLA_LAUNCH_PID}" >/dev/null 2>&1 || return 0
    kill "${CARLA_LAUNCH_PID}" >/dev/null 2>&1 || true
    sleep 3
    kill -9 "${CARLA_LAUNCH_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

run_as_user() {
  local cmd="$1"
  if [ -n "${RUN_AS_USER}" ] && [ "$(id -un)" != "${RUN_AS_USER}" ]; then
    if command -v sudo >/dev/null 2>&1; then
      sudo -u "${RUN_AS_USER}" -H bash -lc "${cmd}"
    else
      su - "${RUN_AS_USER}" -c "bash -lc \"${cmd}\""
    fi
  else
    bash -lc "${cmd}"
  fi
}

if timeout 1 bash -c "echo > /dev/tcp/localhost/${CARLA_PORT}" 2>/dev/null; then
  CARLA_ALREADY_RUNNING=1
else
  echo "Starting CARLA on port ${CARLA_PORT} (GPU ${CARLA_GPU_ID})"
  (
    run_as_user "CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} PORT=${CARLA_PORT} bash ${PROJECT_ROOT}/evaluation_scripts/start_carla_server.sh ${CARLA_GPU_ID} ${CARLA_PORT}"
  ) >"${CARLA_LOG}" 2>&1 &
  CARLA_LAUNCH_PID=$!

  READY=0
  for _ in $(seq 1 90); do
    if timeout 1 bash -c "echo > /dev/tcp/localhost/${CARLA_PORT}" 2>/dev/null; then
      READY=1
      break
    fi
    if ! kill -0 "${CARLA_LAUNCH_PID}" >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  if [ "${READY}" != "1" ]; then
    echo "Error: CARLA not reachable on localhost:${CARLA_PORT}"
    tail -n 200 "${CARLA_LOG}" 2>/dev/null || true
    exit 1
  fi
fi

echo "Running town05 denoise15"

if [ "${EVAL_TARGET}" = "town05" ] || [ "${EVAL_TARGET}" = "both" ]; then
  run_as_user "PROJECT_ROOT=${PROJECT_ROOT} PORT=${PORT} SAVE_PATH=${SAVE_PATH:-} CHECKPOINT_ENDPOINT=${CHECKPOINT_ENDPOINT:-} RESUME=${RESUME:-} CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES} DATA_PROCESSOR_GPU_ID=${DATA_PROCESSOR_GPU_ID} DATA_PROCESSOR_TILE=${DATA_PROCESSOR_TILE} DATA_PROCESSOR_HALF=${DATA_PROCESSOR_HALF} CONDA_ENV_NAME=${CONDA_ENV_NAME} PYTHON_BIN=${PYTHON_BIN:-} bash ${SCRIPT_DIR}/run_evaluation_with_processor.sh town05 denoise15"
fi

echo "Running 42routes denoise15"

if [ "${EVAL_TARGET}" = "42routes" ] || [ "${EVAL_TARGET}" = "both" ]; then
  run_as_user "PROJECT_ROOT=${PROJECT_ROOT} PORT=${PORT} SAVE_PATH=${SAVE_PATH:-} CHECKPOINT_ENDPOINT=${CHECKPOINT_ENDPOINT:-} RESUME=${RESUME:-} CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES} DATA_PROCESSOR_GPU_ID=${DATA_PROCESSOR_GPU_ID} DATA_PROCESSOR_TILE=${DATA_PROCESSOR_TILE} DATA_PROCESSOR_HALF=${DATA_PROCESSOR_HALF} CONDA_ENV_NAME=${CONDA_ENV_NAME} PYTHON_BIN=${PYTHON_BIN:-} bash ${SCRIPT_DIR}/run_evaluation_with_processor.sh 42routes denoise15"
fi
