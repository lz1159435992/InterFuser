#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LMDRIVE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INTERFUSER_ROOT_DEFAULT="${LMDRIVE_ROOT}/../interfuser_project"
INTERFUSER_ROOT="${INTERFUSER_ROOT:-${INTERFUSER_ROOT_DEFAULT}}"
TEAM_CODE_DIR="${LMDRIVE_ROOT}/leaderboard/team_code"
BACKUP_DIR="${SCRIPT_DIR}/.backup_native_$(date +%Y%m%d_%H%M%S)"

EVAL_TYPE=${1:-langauto_long}
NATIVE_ENHANCE=${2:-none}

# ===== Optional, safe cleanup to allow parallel runs =====
# PRE_CLEANUP: 1 to stop evaluator processes that match this CHECKPOINT_ENDPOINT, and CARLA process that matches --world-port=${PORT}
PRE_CLEANUP=${PRE_CLEANUP:-0}
PRE_CLEANUP_USER=${PRE_CLEANUP_USER:-$(id -un)}

DEFAULT_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-${GPU_ID:-0}}
CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES:-${DEFAULT_VISIBLE_DEVICES}}
PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES:-${DEFAULT_VISIBLE_DEVICES}}

mkdir -p "${BACKUP_DIR}"

# Agent deployment strategy:
# - Default (PARALLEL_SAFE=0): overwrite leaderboard/team_code/lmdriver_agent.py (legacy behavior)
# - Parallel-safe (PARALLEL_SAFE=1): write a per-run agent copy under SAVE_PATH and point evaluator --agent to it.
PARALLEL_SAFE=${PARALLEL_SAFE:-0}
AGENT_RESTORED=0
AGENT_DEPLOYED=0
AGENT_PATH="${TEAM_CODE_DIR}/lmdriver_agent.py"

cleanup() {
  EXIT_CODE=$?
  set +e

  if [ "${AUTO_START_CARLA:-0}" = "1" ] && [ "${CARLA_ALREADY_RUNNING:-0}" != "1" ] && [ -n "${PORT:-}" ]; then
    CARLA_PIDS=$(ps -ww -eo pid=,args= 2>/dev/null | grep -F -- "--world-port=${PORT}" | grep -E "CarlaUE4-Linux-Shipping|CarlaUE4\.sh" | awk '{print $1}')
    if [ -n "${CARLA_PIDS}" ]; then
      kill ${CARLA_PIDS} >/dev/null 2>&1 || true
      sleep 3
      kill -9 ${CARLA_PIDS} >/dev/null 2>&1 || true
    fi
  fi

  if [ "${AGENT_RESTORED}" != "1" ]; then
    if [ "${PARALLEL_SAFE}" != "1" ] && [ "${AGENT_DEPLOYED}" = "1" ]; then
      if [ -f "${BACKUP_DIR}/lmdriver_agent.py.bak" ]; then
        cp "${BACKUP_DIR}/lmdriver_agent.py.bak" "${TEAM_CODE_DIR}/lmdriver_agent.py"
      fi
      rm -rf "${TEAM_CODE_DIR}/__pycache__" >/dev/null 2>&1 || true
    fi
    AGENT_RESTORED=1
  fi

  return ${EXIT_CODE}
}
trap cleanup EXIT

# ===== Python / CARLA env =====
cd "${LMDRIVE_ROOT}"

export CARLA_ROOT=${CARLA_ROOT:-"${LMDRIVE_ROOT}/../carla"}
export CARLA_SERVER=${CARLA_ROOT}/CarlaUE4.sh

AUTO_CONDA_ACTIVATE=${AUTO_CONDA_ACTIVATE:-1}
CONDA_ENV_NAME=${CONDA_ENV_NAME:-lmdrive}

PYTHON_BIN_WAS_SET=1
if [ -z "${PYTHON_BIN+x}" ] || [ -z "${PYTHON_BIN}" ]; then
  PYTHON_BIN_WAS_SET=0
  PYTHON_BIN=python3
fi
ORIGINAL_PYTHON_BIN="${PYTHON_BIN}"

FORCE_CARLA_PY37=${FORCE_CARLA_PY37:-0}
CARLA_PY37_BIN=${CARLA_PY37_BIN:-/opt/conda_envs/interfuser/bin/python3.7}
if [ "${FORCE_CARLA_PY37}" = "1" ] && [ "${PYTHON_BIN_WAS_SET}" = "0" ]; then
  if [ -x "${CARLA_PY37_BIN}" ]; then
    PYTHON_BIN="${CARLA_PY37_BIN}"
    AUTO_CONDA_ACTIVATE=0
  else
    echo "Error: FORCE_CARLA_PY37=1 but CARLA_PY37_BIN not executable: ${CARLA_PY37_BIN}" >&2
    exit 1
  fi
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

# Align with run_evaluation_lmdrive_with_processor.sh behavior:
# if core deps are missing in the current python, try activating CONDA_ENV_NAME.
if ! ${PYTHON_BIN} -c "import numpy" >/dev/null 2>&1; then
  if try_activate_conda_env; then
    echo "Activated conda env: ${CONDA_ENV_NAME}" >&2
    if [ "${PYTHON_BIN_WAS_SET}" = "0" ]; then
      PYTHON_BIN=python
    fi
  fi
fi

# If conda activation switched python to an unsupported version for CARLA 0.9.10 egg, revert.
# When FORCE_CARLA_PY37=1 we intentionally keep the py3.7 interpreter.
if [ "${FORCE_CARLA_PY37}" != "1" ]; then
  POST_ACTIVATE_PY_VER=$(${PYTHON_BIN} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
  if [ "${POST_ACTIVATE_PY_VER}" != "3.7" ] && [ "${POST_ACTIVATE_PY_VER}" != "2.7" ]; then
    PYTHON_BIN="${ORIGINAL_PYTHON_BIN}"
  fi
fi

PY_VER=$(${PYTHON_BIN} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
USE_PIP_CARLA=${USE_PIP_CARLA:-0}
CARLA_EGG=""
if [ "${PY_VER}" = "3.7" ]; then
  CARLA_EGG="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg"
elif [ "${PY_VER}" = "2.7" ]; then
  CARLA_EGG="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py2.7-linux-x86_64.egg"
fi
SKIP_CARLA_EGG_CHECK=${SKIP_CARLA_EGG_CHECK:-0}
if [ "${USE_PIP_CARLA}" = "1" ]; then
  if ! ${PYTHON_BIN} -c "import carla" >/dev/null 2>&1; then
    echo "Error: USE_PIP_CARLA=1 but 'import carla' failed under ${PYTHON_BIN} (py${PY_VER}). Install a compatible carla wheel, e.g. 'pip install carla'." >&2
    exit 1
  fi
else
  if [ -z "${CARLA_EGG}" ] || [ ! -f "${CARLA_EGG}" ]; then
  if [ "${SKIP_CARLA_EGG_CHECK}" = "1" ]; then
    CARLA_EGG_FALLBACK="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg"
    if [ -f "${CARLA_EGG_FALLBACK}" ]; then
      CARLA_EGG="${CARLA_EGG_FALLBACK}"
      echo "Warning: SKIP_CARLA_EGG_CHECK=1: forcing CARLA egg ${CARLA_EGG} under python ${PY_VER} (${PYTHON_BIN})." >&2
    else
      echo "Error: SKIP_CARLA_EGG_CHECK=1 but fallback CARLA egg not found: ${CARLA_EGG_FALLBACK}" >&2
      exit 1
    fi
  else
    echo "Error: CARLA PythonAPI egg not available for python ${PY_VER} (${PYTHON_BIN})" >&2
    exit 1
  fi
fi
fi

export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla
if [ "${USE_PIP_CARLA}" != "1" ]; then
  export PYTHONPATH=$PYTHONPATH:${CARLA_EGG}
fi
export PYTHONPATH=$PYTHONPATH:leaderboard
export PYTHONPATH=$PYTHONPATH:leaderboard/team_code
export PYTHONPATH=$PYTHONPATH:scenario_runner
if [ -d "${LMDRIVE_ROOT}/sensor_data_processor_module" ]; then
  SENSOR_MODULE_ROOT="${LMDRIVE_ROOT}"
elif [ -d "${INTERFUSER_ROOT}/sensor_data_processor_module" ]; then
  SENSOR_MODULE_ROOT="${INTERFUSER_ROOT}"
else
  SENSOR_MODULE_ROOT="${LMDRIVE_ROOT}/.."
fi
export PYTHONPATH=$PYTHONPATH:${SENSOR_MODULE_ROOT}:vision_encoder
export PYTHONPATH=$PYTHONPATH:${LMDRIVE_ROOT}/LAVIS

# Preflight: ensure key third-party deps are available in the active python env.
MISSING_DEPS=()
if ! ${PYTHON_BIN} -c "import omegaconf" >/dev/null 2>&1; then
  MISSING_DEPS+=(omegaconf)
fi
if ! ${PYTHON_BIN} -c "import iopath" >/dev/null 2>&1; then
  MISSING_DEPS+=(iopath)
fi
if ! ${PYTHON_BIN} -c "import einops" >/dev/null 2>&1; then
  MISSING_DEPS+=(einops)
fi
if ! ${PYTHON_BIN} -c "import transformers" >/dev/null 2>&1; then
  MISSING_DEPS+=(transformers)
fi
if ! ${PYTHON_BIN} -c "import fairscale" >/dev/null 2>&1; then
  MISSING_DEPS+=(fairscale)
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
  echo "Error: python env is missing required deps for LMDrive/LAVIS: ${MISSING_DEPS[*]}" >&2
  echo "Current PYTHON_BIN=${PYTHON_BIN}" >&2
  echo "Fix options:" >&2
  echo "  1) Install into current env (py3.7 required for CARLA egg):" >&2
  if printf '%s\n' "${MISSING_DEPS[@]}" | grep -q '^transformers$'; then
    echo "     ${PYTHON_BIN} -m pip install omegaconf iopath einops 'transformers==4.25.1' sentencepiece fairscale==0.4.4" >&2
  else
    echo "     ${PYTHON_BIN} -m pip install ${MISSING_DEPS[*]}" >&2
  fi
  echo "  2) Or use a py3.7 env that already has LAVIS deps and set:" >&2
  echo "     PYTHON_BIN=/path/to/python3.7 bash leaderboard/scripts/run_evaluation_lmdrive_native.sh ..." >&2
  exit 1
fi

export LEADERBOARD_ROOT=leaderboard
export CHALLENGE_TRACK_CODENAME=SENSORS

export NATIVE_ENHANCE="${NATIVE_ENHANCE}"

export PORT=${PORT:-0}
if [ "${PORT}" = "0" ] || [ "${PORT}" = "random" ]; then
  set +e
  PORT_CANDIDATE=$(${PYTHON_BIN} - <<'PY' 2>/dev/null
import random
import socket
import sys

def can_bind(p: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', p))
    except OSError:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass
    return True

for _ in range(300):
    p = random.randint(2000, 40000)
    if can_bind(p) and can_bind(p + 1) and can_bind(p + 2):
        print(p)
        sys.exit(0)

sys.exit(1)
PY
)
  PORT_CANDIDATE_EXIT_CODE=$?
  set -e
  if [ "${PORT_CANDIDATE_EXIT_CODE}" -eq 0 ] && [ -n "${PORT_CANDIDATE}" ]; then
    export PORT=${PORT_CANDIDATE}
  else
    export PORT=2000
  fi
fi

echo "CARLA RPC port: ${PORT}"

TM_PORT=${TM_PORT:-$((PORT+500))}
set +e
TM_PORT_CANDIDATE=$(${PYTHON_BIN} - <<PY 2>/dev/null
import socket
import sys
start = int(${TM_PORT})
end = start + 50
for p in range(start, end + 1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', p))
    except OSError:
        s.close()
        continue
    s.close()
    print(p)
    sys.exit(0)
sys.exit(1)
PY
)
TM_PORT_CANDIDATE_EXIT_CODE=$?
set -e
if [ "${TM_PORT_CANDIDATE_EXIT_CODE}" -eq 0 ] && [ -n "${TM_PORT_CANDIDATE}" ]; then
  TM_PORT=${TM_PORT_CANDIDATE}
fi
export TM_PORT=${TM_PORT}
echo "Traffic Manager port: ${TM_PORT}"

# Select routes and scenarios based on EVAL_TYPE.
# Allow explicit override by env:
# - LANGAUTO_ROUTE_LONG / LANGAUTO_ROUTE_SHORT / LANGAUTO_ROUTE_TINY
# - LANGAUTO_SCENARIOS
case ${EVAL_TYPE} in
  langauto_long)
    export ROUTES=${LANGAUTO_ROUTE_LONG:-langauto/benchmark_long.xml}
    export SCENARIOS=${LANGAUTO_SCENARIOS:-leaderboard/data/official/all_towns_traffic_scenarios_public.json}
    ;;
  langauto_short)
    export ROUTES=${LANGAUTO_ROUTE_SHORT:-langauto/benchmark_short.xml}
    export SCENARIOS=${LANGAUTO_SCENARIOS:-leaderboard/data/official/all_towns_traffic_scenarios_public.json}
    ;;
  langauto_tiny)
    export ROUTES=${LANGAUTO_ROUTE_TINY:-langauto/benchmark_tiny.xml}
    export SCENARIOS=${LANGAUTO_SCENARIOS:-leaderboard/data/official/all_towns_traffic_scenarios_public.json}
    ;;
  *)
    echo "Unknown EVAL_TYPE: ${EVAL_TYPE}" >&2
    exit 1
    ;;
esac

if [ ! -f "${LMDRIVE_ROOT}/${ROUTES}" ]; then
  echo "Error: route file not found: ${LMDRIVE_ROOT}/${ROUTES}" >&2
  echo "Hint: provide LANGAUTO_ROUTE_LONG/LANGAUTO_ROUTE_SHORT/LANGAUTO_ROUTE_TINY to override route files." >&2
  exit 1
fi
if [ ! -f "${LMDRIVE_ROOT}/${SCENARIOS}" ]; then
  echo "Error: scenario file not found: ${LMDRIVE_ROOT}/${SCENARIOS}" >&2
  echo "Hint: provide LANGAUTO_SCENARIOS to override scenario file." >&2
  exit 1
fi

NATIVE_TAG=$(echo "${NATIVE_ENHANCE}" | tr ', ' '__')
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -z "${SAVE_PATH:-}" ]; then
  export SAVE_PATH="data/eval_native/${EVAL_TYPE}_${NATIVE_TAG}_${TIMESTAMP}"
fi
if [ -z "${CHECKPOINT_ENDPOINT:-}" ]; then
  mkdir -p results/native
  export CHECKPOINT_ENDPOINT="results/native/${EVAL_TYPE}_${NATIVE_TAG}_${TIMESTAMP}.json"
fi

mkdir -p "${SAVE_PATH}"

# Deploy agent after SAVE_PATH is known (required for PARALLEL_SAFE mode).
if [ "${PARALLEL_SAFE}" = "1" ]; then
  AGENT_PATH="${SAVE_PATH}/lmdriver_agent.py"
  cp "${TEAM_CODE_DIR}/lmdriver_agent_native.py" "${AGENT_PATH}"
  AGENT_DEPLOYED=1
else
  if [ -f "${TEAM_CODE_DIR}/lmdriver_agent.py" ]; then
    cp "${TEAM_CODE_DIR}/lmdriver_agent.py" "${BACKUP_DIR}/lmdriver_agent.py.bak"
  fi
  cp "${TEAM_CODE_DIR}/lmdriver_agent_native.py" "${TEAM_CODE_DIR}/lmdriver_agent.py"
  AGENT_DEPLOYED=1
fi

if [ "${PRE_CLEANUP}" = "1" ]; then
  echo "PRE_CLEANUP=1: stopping existing evaluator/CARLA processes for this run only (user=${PRE_CLEANUP_USER}, port=${PORT})..." >&2
  set +e
  if [ -n "${CHECKPOINT_ENDPOINT:-}" ]; then
    EVAL_PIDS=$(ps -u "${PRE_CLEANUP_USER}" -ww -o pid=,args= 2>/dev/null | grep -E "python3? -u .*leaderboard_evaluator(_custom)?\.py" | grep -F -- "--checkpoint=${CHECKPOINT_ENDPOINT}" | awk '{print $1}')
    if [ -n "${EVAL_PIDS}" ]; then
      kill ${EVAL_PIDS} >/dev/null 2>&1
      sleep 2
      kill -9 ${EVAL_PIDS} >/dev/null 2>&1
    fi
  fi

  if [ -n "${PORT:-}" ]; then
    CARLA_PIDS=$(ps -u "${PRE_CLEANUP_USER}" -ww -o pid=,args= 2>/dev/null | grep -F -- "--world-port=${PORT}" | grep -E "CarlaUE4-Linux-Shipping|CarlaUE4\.sh" | awk '{print $1}')
    if [ -n "${CARLA_PIDS}" ]; then
      kill ${CARLA_PIDS} >/dev/null 2>&1
      sleep 3
      kill -9 ${CARLA_PIDS} >/dev/null 2>&1
    fi
  fi
  set -e
fi

# Default SENSOR_QUEUE_TIMEOUT tuning
if [ -z "${SENSOR_QUEUE_TIMEOUT:-}" ]; then
  if [[ "${NATIVE_ENHANCE}" == *"high_fps"* ]]; then
    export SENSOR_QUEUE_TIMEOUT=90
  else
    export SENSOR_QUEUE_TIMEOUT=10
  fi
fi

EVAL_TIMEOUT=${EVAL_TIMEOUT:-600}
export CARLA_TICK_TIMEOUT=${CARLA_TICK_TIMEOUT:-${EVAL_TIMEOUT}}

cat > "${SAVE_PATH}/evaluation_metadata.json" << EOF
{
  "timestamp": "${TIMESTAMP}",
  "eval_type": "${EVAL_TYPE}",
  "native_enhance": "${NATIVE_ENHANCE}",
  "port": "${PORT}",
  "traffic_manager_port": "${TM_PORT}",
  "routes": "${ROUTES}",
  "scenarios": "${SCENARIOS}",
  "checkpoint": "${CHECKPOINT_ENDPOINT}",
  "agent": "lmdriver_agent_native.py"
}
EOF

AUTO_START_CARLA=${AUTO_START_CARLA:-0}
CARLA_ALREADY_RUNNING=0
CARLA_LAUNCH_PID=""

CARLA_LOG_DIR=${CARLA_LOG_DIR:-"${SAVE_PATH}"}
CARLA_LOG="${CARLA_LOG_DIR}/carla_server_${PORT}.log"

if [ "${AUTO_START_CARLA}" = "1" ]; then
  if [ "$(id -u)" -eq 0 ]; then
    echo "Error: AUTO_START_CARLA=1 cannot be used as root." >&2
    exit 1
  fi

  if ! ${PYTHON_BIN} -c "import carla" >/dev/null 2>&1; then
    echo "Error: cannot import 'carla' from python (${PYTHON_BIN})." >&2
    exit 1
  fi

  carla_ready_check() {
    ${PYTHON_BIN} - <<PY >/dev/null 2>&1
import sys
try:
    import carla
    client = carla.Client('localhost', int('${PORT}'))
    client.set_timeout(30.0)
    client.get_world()
except Exception:
    sys.exit(1)
sys.exit(0)
PY
  }

  if carla_ready_check; then
    CARLA_ALREADY_RUNNING=1
  else
    export SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-dummy}
    CARLA_KEEP_DISPLAY=${CARLA_KEEP_DISPLAY:-1}
    if [ "${CARLA_KEEP_DISPLAY}" != "1" ]; then
      unset DISPLAY
    else
      if [ -z "${DISPLAY:-}" ]; then
        export DISPLAY=:99
      fi
    fi

    CARLA_SDL_VIDEODRIVER=${CARLA_SDL_VIDEODRIVER:-x11}
    if [ -z "${DISPLAY:-}" ]; then
      CARLA_SDL_VIDEODRIVER=dummy
    fi

    if [ -z "${XDG_RUNTIME_DIR:-}" ]; then
      export XDG_RUNTIME_DIR="/tmp/xdg-runtime-$(id -u)"
      mkdir -p "${XDG_RUNTIME_DIR}" >/dev/null 2>&1 || true
      chmod 700 "${XDG_RUNTIME_DIR}" >/dev/null 2>&1 || true
    fi

    CARLA_EXTRA_ARGS=${CARLA_EXTRA_ARGS:-}
    CARLA_RENDER_OFFSCREEN_ARG=""
    if [ -z "${DISPLAY:-}" ]; then
      CARLA_RENDER_OFFSCREEN_ARG="-RenderOffScreen"
    fi

    CARLA_ARGS="--world-port=${PORT} -opengl ${CARLA_RENDER_OFFSCREEN_ARG} -nosound -stdout -FullStdOutLogOutput"
    if [ -n "${CARLA_EXTRA_ARGS}" ]; then
      CARLA_ARGS="${CARLA_ARGS} ${CARLA_EXTRA_ARGS}"
    fi

    mkdir -p "${CARLA_ROOT}/CarlaUE4/Saved/Logs" >/dev/null 2>&1 || true

    (
      CLEAN_CARLA_ENV=${CLEAN_CARLA_ENV:-1}
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
      cd "${CARLA_ROOT}" || exit 1
      SDL_VIDEODRIVER="${CARLA_SDL_VIDEODRIVER}" CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} bash "${CARLA_ROOT}/CarlaUE4.sh" ${CARLA_ARGS}
    ) >"${CARLA_LOG}" 2>&1 &
    CARLA_LAUNCH_PID=$!

    sleep 4
    if ! kill -0 "${CARLA_LAUNCH_PID}" >/dev/null 2>&1; then
      echo "Error: CARLA exited early (PID ${CARLA_LAUNCH_PID})." >&2
      tail -n 200 "${CARLA_LOG}" 2>/dev/null || true
      exit 1
    fi

    READY=0
    END_TS=$(( $(date +%s) + ${CARLA_READY_TIMEOUT:-180} ))
    while [ "$(date +%s)" -lt "${END_TS}" ]; do
      if carla_ready_check; then
        READY=1
        break
      fi
      sleep 2
    done

    if [ "${READY}" != "1" ]; then
      echo "Error: CARLA not reachable on localhost:${PORT}" >&2
      tail -n 200 "${CARLA_LOG}" 2>/dev/null || true
      exit 1
    fi
  fi
fi

# evaluator wrapper: patch frame_rate based on NATIVE_ENHANCE
CUSTOM_EVALUATOR="${SAVE_PATH}/leaderboard_evaluator_custom.py"
cat > "${CUSTOM_EVALUATOR}" << 'PYEOF'
#!/usr/bin/env python
import os

native_enhance = os.environ.get('NATIVE_ENHANCE', 'none')
frame_rate = 40.0 if 'high_fps' in native_enhance else 20.0
print(f"[LMDrive Native Enhancement] Setting frame rate to {frame_rate}Hz")

import leaderboard.leaderboard_evaluator as le
le.LeaderboardEvaluator.frame_rate = frame_rate

if __name__ == '__main__':
    le.main()
PYEOF

export TEAM_AGENT=${AGENT_PATH}
export TEAM_CONFIG=leaderboard/team_code/lmdriver_config.py
export DEBUG_CHALLENGE=${DEBUG_CHALLENGE:-0}
export REPETITIONS=${REPETITIONS:-1}

EVAL_LOG="${SAVE_PATH}/leaderboard_evaluator.log"

set +e
RESUME_ARGS=()
if [ -n "${RESUME:-}" ] && [ "${RESUME}" != "0" ]; then
  RESUME_ARGS=(--resume=True)
fi

PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES} ${PYTHON_BIN} -u "${CUSTOM_EVALUATOR}" \
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
  --trafficManagerPort=${TM_PORT} \
  2>&1 | tee "${EVAL_LOG}"

EVAL_EXIT_CODE=${PIPESTATUS[0]}
set -e

exit ${EVAL_EXIT_CODE}
