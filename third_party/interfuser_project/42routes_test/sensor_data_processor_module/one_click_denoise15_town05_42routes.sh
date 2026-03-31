#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MAIN_ROOT="$(cd "${PROJECT_ROOT}/.." && pwd)"

EVAL_TARGET=${1:-42routes}

if [ ! -e "${PROJECT_ROOT}/leaderboard/team_code/interfuser.pth.tar" ] && [ -e "${MAIN_ROOT}/leaderboard/team_code/interfuser.pth.tar" ]; then
  mkdir -p "${PROJECT_ROOT}/leaderboard/team_code" >/dev/null 2>&1 || true
  ln -s "${MAIN_ROOT}/leaderboard/team_code/interfuser.pth.tar" "${PROJECT_ROOT}/leaderboard/team_code/interfuser.pth.tar" 2>/dev/null || true
fi

if [ ! -e "${PROJECT_ROOT}/process_mothod/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth" ] && [ -e "${MAIN_ROOT}/process_mothod/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth" ]; then
  mkdir -p "${PROJECT_ROOT}/process_mothod/SwinIR/model_zoo/swinir" >/dev/null 2>&1 || true
  ln -s "${MAIN_ROOT}/process_mothod/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth" "${PROJECT_ROOT}/process_mothod/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth" 2>/dev/null || true
fi

if [ ! -e "${PROJECT_ROOT}/process_mothod/SRGAN/results/checkpoint_srgan.pth" ] && [ -e "${MAIN_ROOT}/process_mothod/SRGAN/results/checkpoint_srgan.pth" ]; then
  mkdir -p "${PROJECT_ROOT}/process_mothod/SRGAN/results" >/dev/null 2>&1 || true
  ln -s "${MAIN_ROOT}/process_mothod/SRGAN/results/checkpoint_srgan.pth" "${PROJECT_ROOT}/process_mothod/SRGAN/results/checkpoint_srgan.pth" 2>/dev/null || true
fi

if [ ! -e "${PROJECT_ROOT}/process_mothod/SRGAN/results/checkpoint_srresnet.pth" ] && [ -e "${MAIN_ROOT}/process_mothod/SRGAN/results/checkpoint_srresnet.pth" ]; then
  mkdir -p "${PROJECT_ROOT}/process_mothod/SRGAN/results" >/dev/null 2>&1 || true
  ln -s "${MAIN_ROOT}/process_mothod/SRGAN/results/checkpoint_srresnet.pth" "${PROJECT_ROOT}/process_mothod/SRGAN/results/checkpoint_srresnet.pth" 2>/dev/null || true
fi

RUN_AS_USER=${RUN_AS_USER:-}
if [ "$(id -u)" = "0" ] && [ -z "${RUN_AS_USER}" ]; then
  RUN_AS_USER=carlauser
fi

DEFAULT_CONDA_ENV_NAME=interfuser
CONDA_ENV_NAME=${CONDA_ENV_NAME:-${DEFAULT_CONDA_ENV_NAME}}

DEFAULT_CARLA_GPU_ID=2
DEFAULT_PY_CUDA_VISIBLE_DEVICES="2,3"
DEFAULT_DATA_PROCESSOR_GPU_ID=1
DEFAULT_DATA_PROCESSOR_TILE="none"
DEFAULT_DATA_PROCESSOR_HALF="0"
DEFAULT_CARLA_PORT=2002

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

CARLA_PORT=${CARLA_PORT:-${PORT:-${DEFAULT_CARLA_PORT}}}
PORT=${PORT:-${CARLA_PORT}}
CARLA_LOG_DIR=${CARLA_LOG_DIR:-${TMPDIR:-/tmp}}
mkdir -p "${CARLA_LOG_DIR}" >/dev/null 2>&1 || true
CARLA_LOG="${CARLA_LOG_DIR}/carla_${CARLA_PORT}_$(date +%Y%m%d_%H%M%S).log"

echo "Worktree root:            ${PROJECT_ROOT}"
echo "Eval target:              ${EVAL_TARGET}"
echo "CARLA_PORT/PORT:          ${CARLA_PORT}"
echo "GPU isolation in use:     CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} (CARLA_GPU_ID=${CARLA_GPU_ID}), PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES}, DATA_PROCESSOR_GPU_ID=${DATA_PROCESSOR_GPU_ID}"
echo "Denoise15 in use:         DATA_PROCESSOR_TILE=${DATA_PROCESSOR_TILE}, DATA_PROCESSOR_HALF=${DATA_PROCESSOR_HALF}"
echo "Conda env:                ${CONDA_ENV_NAME}"
echo "PYTHON_BIN:               ${PYTHON_BIN:-}"
echo "CARLA log:                ${CARLA_LOG}"

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

if [ "${EVAL_TARGET}" = "town05" ] || [ "${EVAL_TARGET}" = "both" ]; then
  echo "Running town05 denoise15 (worktree)"
  run_as_user "PROJECT_ROOT=${PROJECT_ROOT} PORT=${PORT} SAVE_PATH=${SAVE_PATH:-} CHECKPOINT_ENDPOINT=${CHECKPOINT_ENDPOINT:-} RESUME=${RESUME:-} CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES} DATA_PROCESSOR_GPU_ID=${DATA_PROCESSOR_GPU_ID} DATA_PROCESSOR_TILE=${DATA_PROCESSOR_TILE} DATA_PROCESSOR_HALF=${DATA_PROCESSOR_HALF} CONDA_ENV_NAME=${CONDA_ENV_NAME} PYTHON_BIN=${PYTHON_BIN:-} bash /path/to/project/sensor_data_processor_module/run_evaluation_with_processor.sh town05 denoise15"
fi

if [ "${EVAL_TARGET}" = "42routes" ] || [ "${EVAL_TARGET}" = "both" ]; then
  echo "Running 42routes denoise15 (worktree)"
  run_as_user "PROJECT_ROOT=${PROJECT_ROOT} PORT=${PORT} SAVE_PATH=${SAVE_PATH:-} CHECKPOINT_ENDPOINT=${CHECKPOINT_ENDPOINT:-} RESUME=${RESUME:-} CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES} DATA_PROCESSOR_GPU_ID=${DATA_PROCESSOR_GPU_ID} DATA_PROCESSOR_TILE=${DATA_PROCESSOR_TILE} DATA_PROCESSOR_HALF=${DATA_PROCESSOR_HALF} CONDA_ENV_NAME=${CONDA_ENV_NAME} PYTHON_BIN=${PYTHON_BIN:-} bash /path/to/project/sensor_data_processor_module/run_evaluation_with_processor.sh 42routes denoise15"
fi
