#!/bin/bash
# LMDrive evaluation script with optional sensor data processor configurations.

# Example command (run as a non-root user with the lmdrive conda env activated):
#降噪增强
# (cd /path/to/IntuitionTester/third_party/lmdrive && \
# CARLA_ROOT=../carla START_CARLA=1 CLEAN_CARLA_ENV=1 \
# CARLA_KEEP_DISPLAY=1 DISPLAY=:99 CARLA_SDL_VIDEODRIVER=x11 \
# CARLA_CUDA_VISIBLE_DEVICES=0 \
# PY_CUDA_VISIBLE_DEVICES=1,2 DATA_PROCESSOR_GPU_ID=1 \
# DATA_PROCESSOR_TILE=none \
# bash leaderboard/scripts/run_evaluation_lmdrive_with_processor.sh langauto_long denoise15)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LMDRIVE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INTERFUSER_ROOT_DEFAULT="${LMDRIVE_ROOT}/../interfuser_project"
INTERFUSER_ROOT="${INTERFUSER_ROOT:-${INTERFUSER_ROOT_DEFAULT}}"
cd "${LMDRIVE_ROOT}"

# ===== Environment variables (can be overridden by the caller) =====
# CARLA_ROOT: CARLA installation root (contains CarlaUE4.sh). Defaults to sibling `carla/`.
export CARLA_ROOT=${CARLA_ROOT:-"${LMDRIVE_ROOT}/../carla"}
# START_CARLA: 1 to start CARLA locally; 0 to connect to an already-running server.
START_CARLA=${START_CARLA:-1}
# PORT / PT: CARLA RPC port. If PORT is not set, pick a random high port to avoid collisions.
export PT=${PORT:-$(($RANDOM % 1000 + 16000))}
# KILL_EXISTING_CARLA: 1 to stop any existing CARLA processes owned by this user before starting.
KILL_EXISTING_CARLA=${KILL_EXISTING_CARLA:-1}
if [ "${START_CARLA}" = "1" ] && [ "${KILL_EXISTING_CARLA}" = "1" ]; then
  if pgrep -u "$(id -u)" -f "CarlaUE4-Linux-Shipping" >/dev/null 2>&1 \
    || pgrep -u "$(id -u)" -f "CarlaUE4\.sh" >/dev/null 2>&1; then
    echo "Detected existing CARLA processes for user $(id -un). Stopping them..."
    pkill -u "$(id -u)" --signal TERM -f "CarlaUE4-Linux-Shipping" >/dev/null 2>&1 || true
    pkill -u "$(id -u)" --signal TERM -f "CarlaUE4\.sh" >/dev/null 2>&1 || true
    sleep 3
    pkill -u "$(id -u)" --signal KILL -f "CarlaUE4-Linux-Shipping" >/dev/null 2>&1 || true
    pkill -u "$(id -u)" --signal KILL -f "CarlaUE4\.sh" >/dev/null 2>&1 || true
    sleep 1
  fi
fi

if [ "${START_CARLA}" = "1" ] && [ "$(id -u)" = "0" ]; then
  echo "Error: refusing to start CARLA as root. Run as a non-root user, or set START_CARLA=0 to connect to an external CARLA server." >&2
  exit 1
fi

# GPU_ID: default GPU id used to populate CUDA_VISIBLE_DEVICES when the caller did not set it.
# CUDA_VISIBLE_DEVICES: used by the Python process (LMDrive agent) unless overridden by PY_CUDA_VISIBLE_DEVICES.
# CARLA_CUDA_VISIBLE_DEVICES: used only for the CARLA server process.
# PY_CUDA_VISIBLE_DEVICES: used only for the Python (LMDrive) process.
GPU_ID=${GPU_ID:-0}
if [ -z "${CUDA_VISIBLE_DEVICES}" ]; then
  export CUDA_VISIBLE_DEVICES=${GPU_ID}
fi
CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES:-${CUDA_VISIBLE_DEVICES}}
PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES:-${CUDA_VISIBLE_DEVICES}}
export CUDA_VISIBLE_DEVICES="${PY_CUDA_VISIBLE_DEVICES}"

# ===== Headless / display control for CARLA startup =====
# CARLA_KEEP_DISPLAY: 1 to keep DISPLAY (use an external Xorg, e.g. DISPLAY=:99). 0 to unset DISPLAY.
# On this machine we run a headless NVIDIA Xorg managed by systemd on :99.
CARLA_KEEP_DISPLAY=${CARLA_KEEP_DISPLAY:-1}
# DISPLAY: X server display to use when CARLA_KEEP_DISPLAY=1.
if [ "${CARLA_KEEP_DISPLAY}" = "1" ] && [ -z "${DISPLAY:-}" ]; then
  export DISPLAY=:99
fi
# CARLA_SDL_VIDEODRIVER: SDL video backend used by UE4 (x11/dummy/offscreen). Default to x11 for DISPLAY=:99.
CARLA_SDL_VIDEODRIVER=${CARLA_SDL_VIDEODRIVER:-x11}
if [ -z "${CARLA_SDL_VIDEODRIVER}" ] && [ -z "${DISPLAY:-}" ]; then
  CARLA_SDL_VIDEODRIVER=dummy
fi

if [ "${START_CARLA}" = "1" ]; then
  if [ "${CARLA_KEEP_DISPLAY}" != "1" ]; then
    unset DISPLAY
  fi
  # XDG_RUNTIME_DIR: required by some SDL/UE4 paths in headless environments; create a private runtime dir.
  if [ -z "${XDG_RUNTIME_DIR}" ]; then
    export XDG_RUNTIME_DIR="/tmp/xdg-runtime-$(id -u)"
    mkdir -p "${XDG_RUNTIME_DIR}" >/dev/null 2>&1 || true
    chmod 700 "${XDG_RUNTIME_DIR}" >/dev/null 2>&1 || true
  fi
  # SDL_AUDIODRIVER: dummy prevents audio initialization issues on headless machines.
  export SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-dummy}
  # CARLA_ARGS: extra command-line args passed to CarlaUE4.sh. Default uses OpenGL + offscreen rendering.
  CARLA_ARGS=${CARLA_ARGS:--opengl -RenderOffScreen -nosound -stdout -FullStdOutLogOutput}
  # Some presets used to include -quality-level=Low; drop it here to keep runs consistent on this machine.
  CARLA_ARGS=${CARLA_ARGS//-quality-level=Low/}
  # CLEAN_CARLA_ENV: 1 to unset conda/LD/PYTHON env vars before launching CARLA (avoids library conflicts).
  CLEAN_CARLA_ENV=${CLEAN_CARLA_ENV:-1}
  # CARLA_LOG_DIR: directory for CARLA stdout/stderr logs written by this script.
  CARLA_LOG_DIR=${CARLA_LOG_DIR:-results/carla_logs}
  mkdir -p "${CARLA_LOG_DIR}"
  CARLA_LOG="${CARLA_LOG_DIR}/carla_${PT}_$(date +%Y%m%d_%H%M%S).log"
  CARLA_START_TS=$(date +%s)
  tail_unreal_log() {
    ENGINE_LOG_DIRS=(
      "${CARLA_ROOT}/CarlaUE4/Saved/Logs"
      "${CARLA_ROOT}/Saved/Logs"
      "${HOME}/.config/Epic/CarlaUE4/Saved/Logs"
      "${HOME}/.config/Epic/UnrealEngine/CarlaUE4/Saved/Logs"
    )
    ENGINE_CRASH_DIRS=(
      "${HOME}/.config/Epic/CarlaUE4/Saved/Crashes"
      "${HOME}/.config/Epic/UnrealEngine/CarlaUE4/Saved/Crashes"
    )
    for ENGINE_LOG_DIR in "${ENGINE_LOG_DIRS[@]}"; do
      if [ -d "${ENGINE_LOG_DIR}" ]; then
        ENGINE_LOG_FILE=$(ls -1t "${ENGINE_LOG_DIR}"/*.log 2>/dev/null | head -n 1)
        if [ -n "${ENGINE_LOG_FILE}" ]; then
          echo "--- Tail Unreal log: ${ENGINE_LOG_FILE} ---" >&2
          tail -n 200 "${ENGINE_LOG_FILE}" >&2 || true
          return 0
        fi
      fi
    done
    for ENGINE_CRASH_DIR in "${ENGINE_CRASH_DIRS[@]}"; do
      if [ -d "${ENGINE_CRASH_DIR}" ]; then
        CRASH_DIR=""
        for d in "${ENGINE_CRASH_DIR}"/crashinfo-CarlaUE4-pid-*; do
          [ -d "$d" ] || continue
          d_ts=$(stat -c %Y "$d" 2>/dev/null || echo 0)
          if [ "$d_ts" -ge "${CARLA_START_TS}" ]; then
            if [ -z "${CRASH_DIR}" ]; then
              CRASH_DIR="$d"
            else
              cur_ts=$(stat -c %Y "${CRASH_DIR}" 2>/dev/null || echo 0)
              if [ "$d_ts" -gt "$cur_ts" ]; then
                CRASH_DIR="$d"
              fi
            fi
          fi
        done
        if [ -n "${CRASH_DIR}" ] && [ -f "${CRASH_DIR}/Diagnostics.txt" ]; then
          echo "--- Unreal crash diagnostics: ${CRASH_DIR}/Diagnostics.txt ---" >&2
          tail -n 200 "${CRASH_DIR}/Diagnostics.txt" >&2 || true
          return 0
        fi
      fi
    done
    return 0
  }
  # Start CARLA from the InterFuser root (parent of LMDrive)
  echo "Starting CARLA: ${CARLA_ROOT}/CarlaUE4.sh --world-port=${PT} ${CARLA_ARGS}"
  echo "CARLA_LOG=${CARLA_LOG}"
  mkdir -p "${CARLA_ROOT}/CarlaUE4/Saved/Logs" >/dev/null 2>&1 || true
  (
    if [ "${CLEAN_CARLA_ENV}" = "1" ]; then
      unset LD_LIBRARY_PATH
      unset LD_PRELOAD
      unset PYTHONHOME
      unset PYTHONPATH
      unset CONDA_PREFIX
      unset CONDA_DEFAULT_ENV
      unset CONDA_SHLVL
      unset VIRTUAL_ENV
    fi
    cd "${CARLA_ROOT}" && SDL_VIDEODRIVER="${CARLA_SDL_VIDEODRIVER}" CUDA_VISIBLE_DEVICES="${CARLA_CUDA_VISIBLE_DEVICES}" bash ./CarlaUE4.sh --world-port=$PT ${CARLA_ARGS}
  ) >"${CARLA_LOG}" 2>&1 &
  CARLA_PID=$!
  sleep 4
  if ! kill -0 ${CARLA_PID} >/dev/null 2>&1; then
    echo "Error: CARLA server exited early (PID ${CARLA_PID}). Check CARLA logs above." >&2
    set +e
    wait ${CARLA_PID} >/dev/null 2>&1
    CARLA_EXIT_CODE=$?
    set -e
    echo "CARLA exit code: ${CARLA_EXIT_CODE}" >&2
    tail -n 120 "${CARLA_LOG}" >&2 || true

    tail_unreal_log
    exit 1
  fi

  cleanup_carla_on_failure() {
    EXIT_CODE=$?
    trap - EXIT
    if [ "${EXIT_CODE}" -ne 0 ] && [ -n "${CARLA_PID:-}" ]; then
      if kill -0 "${CARLA_PID}" >/dev/null 2>&1; then
        pkill -TERM -f "world-port=${PT}" >/dev/null 2>&1 || true
        pkill -TERM -P "${CARLA_PID}" >/dev/null 2>&1 || true
        kill "${CARLA_PID}" >/dev/null 2>&1 || true
        sleep 1
        pkill -KILL -f "world-port=${PT}" >/dev/null 2>&1 || true
        pkill -KILL -P "${CARLA_PID}" >/dev/null 2>&1 || true
        kill -KILL "${CARLA_PID}" >/dev/null 2>&1 || true
      fi
    fi
    exit "${EXIT_CODE}"
  }
  trap cleanup_carla_on_failure EXIT
fi

# Usage:
#   bash leaderboard/scripts/run_evaluation_lmdrive_with_processor.sh [EVAL_TYPE] [CONFIG_TYPE]
#
# EVAL_TYPE:
#   langauto_long   - LangAuto Long benchmark (default)
#   langauto_short  - LangAuto Short benchmark
#   langauto_tiny   - LangAuto Tiny benchmark
#
# CONFIG_TYPE (mapped in sensor_data_processor_module/data_processor_config.py):
#   no_processing   - baseline, no processing
#   denoise15       - SwinIR color denoise noise=15
#   denoise25       - SwinIR color denoise noise=25
#   denoise50       - SwinIR color denoise noise=50
#   sr2x            - SwinIR 2x SR
#   sr4x            - SwinIR 4x SR
#   jpeg_repair     - SwinIR JPEG repair
#   srgan_2x        - SRGAN 2x SR
#   srgan_enhance   - SRGAN 1x enhance
#   srgan_4x        - SRGAN 4x SR
#   custom          - use DATA_PROCESSOR_CONFIG

# EVAL_TYPE: which route set to evaluate (langauto_long/langauto_short/langauto_tiny).
EVAL_TYPE=${1:-langauto_long}
# CONFIG_TYPE: which data-processor preset to use (no_processing/denoise15/...).
CONFIG_TYPE=${2:-no_processing}

# DATA_PROCESSOR_CONFIG_TYPE: consumed by sensor_data_processor_module/data_processor_config.py to pick a preset.
# DATA_PROCESSOR_GPU_ID: optional; if set, the config will use device cuda:<id> for SwinIR/SRGAN.
# Note: DATA_PROCESSOR_GPU_ID is interpreted as a CUDA ordinal in the current Python process.
# Pass configuration type to shared data processor module
export DATA_PROCESSOR_CONFIG_TYPE=${CONFIG_TYPE}

# Basic CARLA / Leaderboard setup (reuse LMDrive defaults where possible)
# Assume this script is executed from the LMDrive root.
CARLA_PYTHONPATH="${CARLA_ROOT}/PythonAPI:${CARLA_ROOT}/PythonAPI/carla:${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg"
if [ -n "${PYTHONPATH:-}" ]; then
  export PYTHONPATH="${CARLA_PYTHONPATH}:${PYTHONPATH}"
else
  export PYTHONPATH="${CARLA_PYTHONPATH}"
fi
export PYTHONPATH="leaderboard:leaderboard/team_code:scenario_runner:vision_encoder:${PYTHONPATH}"
if [ -d "${LMDRIVE_ROOT}/sensor_data_processor_module" ]; then
  SENSOR_MODULE_ROOT="${LMDRIVE_ROOT}"
elif [ -d "${INTERFUSER_ROOT}/sensor_data_processor_module" ]; then
  SENSOR_MODULE_ROOT="${INTERFUSER_ROOT}"
else
  SENSOR_MODULE_ROOT="${LMDRIVE_ROOT}/.."
fi
export PYTHONPATH="${SENSOR_MODULE_ROOT}:${PYTHONPATH}"

# LEADERBOARD_ROOT: leaderboard root directory (relative to this script).
export LEADERBOARD_ROOT=leaderboard
# CHALLENGE_TRACK_CODENAME: leaderboard track (SENSORS for sensor-based agents).
export CHALLENGE_TRACK_CODENAME=SENSORS
# PORT: CARLA RPC port used by evaluator/agent; matches CarlaUE4.sh --world-port.
export PORT=$PT
# TM_PORT: CARLA Traffic Manager port.
export TM_PORT=$(($PT+500))
# DEBUG_CHALLENGE: leaderboard debug flag (0/1).
export DEBUG_CHALLENGE=${DEBUG_CHALLENGE:-0}
# REPETITIONS: number of times to repeat each route.
export REPETITIONS=${REPETITIONS:-1}
# EVAL_TIMEOUT: passed to the evaluator --timeout; also used by watchdog during agent setup.
EVAL_TIMEOUT=${EVAL_TIMEOUT:-600}
# CARLA_TICK_TIMEOUT: used by Python side to set world.tick(seconds=...) timeout.
export CARLA_TICK_TIMEOUT=${CARLA_TICK_TIMEOUT:-${EVAL_TIMEOUT}}

# Select routes and scenarios based on EVAL_TYPE
case ${EVAL_TYPE} in
  langauto_long)
    export ROUTES=${LANGAUTO_ROUTE_LONG:-langauto/benchmark_long.xml}
    export SCENARIOS=${LANGAUTO_SCENARIOS:-leaderboard/data/official/all_towns_traffic_scenarios_public.json}
    RESULT_BASE="langauto_long_${CONFIG_TYPE}"
    ;;
  langauto_short)
    export ROUTES=${LANGAUTO_ROUTE_SHORT:-langauto/benchmark_short.xml}
    export SCENARIOS=${LANGAUTO_SCENARIOS:-leaderboard/data/official/all_towns_traffic_scenarios_public.json}
    RESULT_BASE="langauto_short_${CONFIG_TYPE}"
    ;;
  langauto_tiny)
    export ROUTES=${LANGAUTO_ROUTE_TINY:-langauto/benchmark_tiny.xml}
    export SCENARIOS=${LANGAUTO_SCENARIOS:-leaderboard/data/official/all_towns_traffic_scenarios_public.json}
    RESULT_BASE="langauto_tiny_${CONFIG_TYPE}"
    ;;
  *)
    echo "Unknown EVAL_TYPE: ${EVAL_TYPE}"
    echo "Supported: langauto_long | langauto_short | langauto_tiny"
    exit 1
    ;;
esac

if [ ! -f "${LMDRIVE_ROOT}/${ROUTES}" ]; then
  echo "Error: route file not found: ${LMDRIVE_ROOT}/${ROUTES}" >&2
  echo "Hint: set LANGAUTO_ROUTE_LONG/LANGAUTO_ROUTE_SHORT/LANGAUTO_ROUTE_TINY for your local route files." >&2
  exit 1
fi
if [ ! -f "${LMDRIVE_ROOT}/${SCENARIOS}" ]; then
  echo "Error: scenario file not found: ${LMDRIVE_ROOT}/${SCENARIOS}" >&2
  echo "Hint: set LANGAUTO_SCENARIOS for your local scenarios json." >&2
  exit 1
fi

# Use LMDrive agent with processor-enabled config
# TEAM_AGENT: python entry for the LMDrive agent.
export TEAM_AGENT=leaderboard/team_code/lmdriver_agent.py
# TEAM_CONFIG: agent config file used by TEAM_AGENT.
export TEAM_CONFIG=leaderboard/team_code/lmdriver_config_processor.py

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p results/with_processor
mkdir -p data/eval_with_processor

# CHECKPOINT_ENDPOINT: leaderboard output JSON (per-route statistics).
export CHECKPOINT_ENDPOINT=${CHECKPOINT_ENDPOINT:-"results/with_processor/${RESULT_BASE}_${TIMESTAMP}.json"}
# SAVE_PATH: directory for saved sensor data / intermediate outputs.
export SAVE_PATH=${SAVE_PATH:-"data/eval_with_processor/${RESULT_BASE}_${TIMESTAMP}"}
mkdir -p "${SAVE_PATH}"

echo "Running LMDrive evaluation with processor:"
echo "  EVAL_TYPE   = ${EVAL_TYPE}"
echo "  CONFIG_TYPE = ${CONFIG_TYPE} (DATA_PROCESSOR_CONFIG_TYPE=${DATA_PROCESSOR_CONFIG_TYPE})"
echo "  GPU_ID      = ${GPU_ID}"
echo "  CARLA_GPU   = ${CARLA_CUDA_VISIBLE_DEVICES}"
echo "  PY_GPU      = ${PY_CUDA_VISIBLE_DEVICES}"
echo "  ROUTES      = ${ROUTES}"
echo "  SCENARIOS   = ${SCENARIOS}"
echo "  TIMEOUT     = ${EVAL_TIMEOUT}s"
echo "  RESULT JSON = ${CHECKPOINT_ENDPOINT}"
echo "  SAVE_PATH   = ${SAVE_PATH}"

# AUTO_CONDA_ACTIVATE: 1 to auto-activate CONDA_ENV_NAME if numpy is missing.
AUTO_CONDA_ACTIVATE=${AUTO_CONDA_ACTIVATE:-1}
# CONDA_ENV_NAME: conda environment name to activate when AUTO_CONDA_ACTIVATE=1.
CONDA_ENV_NAME=${CONDA_ENV_NAME:-lmdrive}

PYTHON_BIN_WAS_SET=1
# PYTHON_BIN: python executable to run evaluator (defaults to python3, may switch to conda's python).
if [ -z "${PYTHON_BIN+x}" ] || [ -z "${PYTHON_BIN}" ]; then
  PYTHON_BIN_WAS_SET=0
  PYTHON_BIN=python3
fi

try_activate_conda_env() {
  if [ "${AUTO_CONDA_ACTIVATE}" != "1" ]; then
    return 1
  fi
  command -v conda >/dev/null 2>&1 || return 1
  CONDA_BASE=$(conda info --base 2>/dev/null) || return 1
  if [ -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]; then
    source "${CONDA_BASE}/etc/profile.d/conda.sh" || return 1
  else
    return 1
  fi
  conda activate "${CONDA_ENV_NAME}" >/dev/null 2>&1 || return 1
  return 0
}

if ! ${PYTHON_BIN} -c "import numpy" >/dev/null 2>&1; then
  if try_activate_conda_env; then
    echo "Activated conda env: ${CONDA_ENV_NAME}"
    if [ "${PYTHON_BIN_WAS_SET}" = "0" ]; then
      PYTHON_BIN=python
    fi
  fi
fi

if ! ${PYTHON_BIN} -c "import numpy" >/dev/null 2>&1; then
  if [ "${PYTHON_BIN}" != "python3" ]; then
    if python3 -c "import numpy" >/dev/null 2>&1; then
      PYTHON_BIN=python3
    fi
  fi
fi

if ! ${PYTHON_BIN} -c "import numpy" >/dev/null 2>&1; then
  echo "Error: numpy not found for ${PYTHON_BIN}. Activate the lmdrive environment or set PYTHON_BIN to a python with numpy." >&2
  exit 1
fi

# CARLA_READY_TIMEOUT: time to wait for CARLA to respond to client.get_world() before failing.
CARLA_READY_TIMEOUT=${CARLA_READY_TIMEOUT:-60}
if [ "${START_CARLA}" = "1" ]; then
  echo "Waiting for CARLA to become ready on localhost:${PORT} (timeout: ${CARLA_READY_TIMEOUT}s)"
else
  echo "Checking CARLA reachability on localhost:${PORT} (timeout: ${CARLA_READY_TIMEOUT}s)"
fi
  READY=0
  END_TS=$(( $(date +%s) + CARLA_READY_TIMEOUT ))
  while [ "$(date +%s)" -lt "${END_TS}" ]; do
    if [ "${START_CARLA}" = "1" ] && [ -n "${CARLA_PID:-}" ] && ! kill -0 "${CARLA_PID}" >/dev/null 2>&1; then
      echo "Error: CARLA server exited during startup (PID ${CARLA_PID})." >&2
      if [ -n "${CARLA_LOG:-}" ]; then
        echo "--- Tail CARLA log: ${CARLA_LOG} ---" >&2
        tail -n 120 "${CARLA_LOG}" >&2 || true
      fi
      tail_unreal_log
      exit 1
    fi

    if ${PYTHON_BIN} - <<PY >/dev/null 2>&1
import carla
client = carla.Client('localhost', int('${PORT}'))
client.set_timeout(30.0)
client.get_world()
print('ok')
PY
    then
      READY=1
      break
    fi
    sleep 2
  done

  if [ "${READY}" != "1" ]; then
    echo "Error: CARLA not reachable (or not responding) on localhost:${PORT} after ${CARLA_READY_TIMEOUT}s." >&2
    if [ "${START_CARLA}" = "1" ] && [ -n "${CARLA_LOG:-}" ]; then
      echo "--- Tail CARLA log: ${CARLA_LOG} ---" >&2
      tail -n 120 "${CARLA_LOG}" >&2 || true
    fi
    exit 1
  fi

set +e
RESUME_ARGS=()
if [ -n "${RESUME:-}" ] && [ "${RESUME}" != "0" ]; then
  RESUME_ARGS=(--resume=True)
fi
${PYTHON_BIN} -u ${LEADERBOARD_ROOT}/leaderboard/leaderboard_evaluator.py \
  --scenarios=${SCENARIOS} \
  --routes=${ROUTES} \
  --repetitions=${REPETITIONS} \
  --track=${CHALLENGE_TRACK_CODENAME} \
  --checkpoint=${CHECKPOINT_ENDPOINT} \
  --agent=${TEAM_AGENT} \
  --agent-config=${TEAM_CONFIG} \
  --debug=${DEBUG_CHALLENGE} \
  --timeout=${EVAL_TIMEOUT} \
  "${RESUME_ARGS[@]}" \
  --port=${PORT} \
  --trafficManagerPort=${TM_PORT}

EVAL_EXIT_CODE=$?
set -e

if [ "${EVAL_EXIT_CODE}" -ne 0 ]; then
  echo "Error: evaluator exited with code ${EVAL_EXIT_CODE}." >&2
  if [ "${START_CARLA}" = "1" ] && [ -n "${CARLA_PID:-}" ]; then
    if kill -0 "${CARLA_PID}" >/dev/null 2>&1; then
      echo "CARLA process still running (PID ${CARLA_PID}) after evaluator failure." >&2
    else
      echo "CARLA process not running (PID ${CARLA_PID}) after evaluator failure." >&2
    fi
  fi
  if [ -n "${CARLA_LOG:-}" ]; then
    echo "--- Tail CARLA log: ${CARLA_LOG} ---" >&2
    tail -n 200 "${CARLA_LOG}" >&2 || true
  fi
  if [ "${START_CARLA}" = "1" ] && type tail_unreal_log >/dev/null 2>&1; then
    tail_unreal_log
  fi
fi

exit "${EVAL_EXIT_CODE}"
