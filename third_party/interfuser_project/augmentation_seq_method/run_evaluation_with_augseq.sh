#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT=${PROJECT_ROOT:-"$(cd "${SCRIPT_DIR}/.." && pwd)"}
TEAM_CODE_DIR="${PROJECT_ROOT}/leaderboard/team_code"
BACKUP_DIR="${SCRIPT_DIR}/.backup_$(date +%Y%m%d_%H%M%S)"

EVAL_TYPE=${1:-town05}
AUGSEQ=${2:-none}
GPU_ID=${GPU_ID:-0}

DEFAULT_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-${GPU_ID}}
CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES:-${DEFAULT_VISIBLE_DEVICES}}
PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES:-${DEFAULT_VISIBLE_DEVICES}}

mkdir -p "${BACKUP_DIR}"

if [ -f "${TEAM_CODE_DIR}/interfuser_agent.py" ]; then
    cp "${TEAM_CODE_DIR}/interfuser_agent.py" "${BACKUP_DIR}/interfuser_agent.py.bak"
fi

cp "${PROJECT_ROOT}/augmentation_seq_method/interfuser_agent_augseq.py" "${TEAM_CODE_DIR}/interfuser_agent.py"

AGENT_RESTORED=0

CONDA_ENV_NAME=${CONDA_ENV_NAME:-interfuser}
if [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
    source /opt/conda/etc/profile.d/conda.sh >/dev/null 2>&1 || true
    conda activate "${CONDA_ENV_NAME}" >/dev/null 2>&1 || true
elif command -v conda >/dev/null 2>&1; then
    CONDA_BASE=$(conda info --base 2>/dev/null)
    if [ -n "${CONDA_BASE}" ] && [ -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]; then
        source "${CONDA_BASE}/etc/profile.d/conda.sh" >/dev/null 2>&1 || true
        conda activate "${CONDA_ENV_NAME}" >/dev/null 2>&1 || true
    fi
fi

cd "${PROJECT_ROOT}"

export CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES}
export PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES}
export CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES}
export PROCESS_METHOD_ROOT=${PROCESS_METHOD_ROOT:-"${PROJECT_ROOT}/process_mothod"}
export CARLA_ROOT=${PROJECT_ROOT}/carla
CARLA_SERVER_BIN="${CARLA_ROOT}/CarlaUE4/Binaries/Linux/CarlaUE4-Linux-Shipping"
if [ -x "${CARLA_SERVER_BIN}" ]; then
    export CARLA_SERVER="${CARLA_SERVER_BIN}"
    CARLA_SERVER_PROJECT=CarlaUE4
else
    export CARLA_SERVER=${CARLA_ROOT}/CarlaUE4.sh
    CARLA_SERVER_PROJECT=
fi
export SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-dummy}
CARLA_KEEP_DISPLAY=${CARLA_KEEP_DISPLAY:-1}
if [ "${CARLA_KEEP_DISPLAY}" = "1" ] && [ -z "${DISPLAY:-}" ]; then
    if [ -S "/tmp/.X11-unix/X99" ]; then
        export DISPLAY=:99
    fi
fi
CARLA_SDL_VIDEODRIVER=${CARLA_SDL_VIDEODRIVER:-x11}
if [ -z "${DISPLAY:-}" ]; then
    CARLA_SDL_VIDEODRIVER=dummy
fi
export SDL_VIDEODRIVER=${SDL_VIDEODRIVER:-${CARLA_SDL_VIDEODRIVER}}

export AUGMENT_SEQ="${AUGSEQ}"

PYTHON_BIN=${PYTHON_BIN:-python3}
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    PYTHON_BIN=python3
fi
PY_VER=$(${PYTHON_BIN} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)

CARLA_EGG=""
if [ "${PY_VER}" = "3.7" ]; then
    CARLA_EGG="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg"
elif [ "${PY_VER}" = "2.7" ]; then
    CARLA_EGG="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py2.7-linux-x86_64.egg"
fi

if [ -z "${CARLA_EGG}" ] || [ ! -f "${CARLA_EGG}" ]; then
    bash "${SCRIPT_DIR}/restore_original_agent.sh" "${BACKUP_DIR}"
    echo "Error: CARLA PythonAPI egg not available for python ${PY_VER}" >&2
    exit 1
fi

export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla
export PYTHONPATH=$PYTHONPATH:${CARLA_EGG}
export PYTHONPATH=$PYTHONPATH:leaderboard
export PYTHONPATH=$PYTHONPATH:leaderboard/team_code
export PYTHONPATH=$PYTHONPATH:scenario_runner

export LEADERBOARD_ROOT=leaderboard
export CHALLENGE_TRACK_CODENAME=SENSORS
export PORT=${PORT:-2000}

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
else
    set +e
    TM_PORT_FALLBACK=$(${PYTHON_BIN} - <<PY 2>/dev/null
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', 0))
print(s.getsockname()[1])
s.close()
PY
)
    set -e
    if [ -n "${TM_PORT_FALLBACK}" ]; then
        TM_PORT=${TM_PORT_FALLBACK}
    fi
fi

export TM_PORT=${TM_PORT}
export DEBUG_CHALLENGE=0
export REPETITIONS=1
EVAL_TIMEOUT=${EVAL_TIMEOUT:-600}
export CARLA_TICK_TIMEOUT=${CARLA_TICK_TIMEOUT:-${EVAL_TIMEOUT}}
export CARLA_TM_READY_TIMEOUT=${CARLA_TM_READY_TIMEOUT:-60}

echo "CARLA RPC port: ${PORT}"
echo "Traffic Manager port: ${TM_PORT}"

case $EVAL_TYPE in
    town05)
        export ROUTES=leaderboard/data/evaluation_routes/routes_town05_long.xml
        export SCENARIOS=leaderboard/data/scenarios/town05_all_scenarios.json
        ;;
    42routes)
        export ROUTES=leaderboard/data/42routes/42routes.xml
        export SCENARIOS=leaderboard/data/42routes/42scenarios.json
        ;;
    custom)
        export ROUTES=${CUSTOM_ROUTES:-leaderboard/data/evaluation_routes/routes_town05_long.xml}
        export SCENARIOS=${CUSTOM_SCENARIOS:-leaderboard/data/scenarios/town05_all_scenarios.json}
        ;;
    *)
        bash "${SCRIPT_DIR}/restore_original_agent.sh" "${BACKUP_DIR}"
        echo "Error: unknown eval type '${EVAL_TYPE}'" >&2
        exit 1
        ;;
esac

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
AUGSEQ_TAG=$(echo "${AUGSEQ}" | tr ', ' '__')
if [ -z "${SAVE_PATH:-}" ]; then
    export SAVE_PATH="data/eval_augseq/${EVAL_TYPE}_${AUGSEQ_TAG}_${TIMESTAMP}"
fi
if [ -z "${CHECKPOINT_ENDPOINT:-}" ]; then
    export CHECKPOINT_ENDPOINT="results/augseq/${EVAL_TYPE}_${AUGSEQ_TAG}_${TIMESTAMP}.json"
fi
EVAL_LOG="${SAVE_PATH}/leaderboard_evaluator.log"

export TEAM_AGENT=leaderboard/team_code/interfuser_agent.py
export TEAM_CONFIG=leaderboard/team_code/interfuser_config.py
export RESUME=${RESUME:-True}

mkdir -p "results/augseq"
mkdir -p "${SAVE_PATH}"

cat > "${SAVE_PATH}/evaluation_metadata.json" << EOF
{
    "timestamp": "${TIMESTAMP}",
    "eval_type": "${EVAL_TYPE}",
    "augment_seq": "${AUGSEQ}",
    "fi_apply_to": "${FI_APPLY_TO:-}",
    "port": "${PORT}",
    "traffic_manager_port": "${TM_PORT}",
    "routes": "${ROUTES}",
    "scenarios": "${SCENARIOS}",
    "checkpoint": "${CHECKPOINT_ENDPOINT}",
    "agent": "interfuser_agent_augseq.py"
}
EOF

AUTO_START_CARLA=${AUTO_START_CARLA:-0}
CARLA_STARTUP_WAIT_SEC=${CARLA_STARTUP_WAIT_SEC:-180}
CARLA_STARTUP_CHECK_INTERVAL=${CARLA_STARTUP_CHECK_INTERVAL:-2}
CARLA_EXTRA_ARGS=${CARLA_EXTRA_ARGS:-}
CARLA_READY_TIMEOUT=${CARLA_READY_TIMEOUT:-${CARLA_STARTUP_WAIT_SEC}}
KILL_EXISTING_CARLA=${KILL_EXISTING_CARLA:-0}
CLEAN_CARLA_ENV=${CLEAN_CARLA_ENV:-1}
CLEANUP_KILL_PYTHON_ON_EXIT=${CLEANUP_KILL_PYTHON_ON_EXIT:-1}
CLEANUP_KILL_EXISTING_CARLA_ON_ABORT=${CLEANUP_KILL_EXISTING_CARLA_ON_ABORT:-0}
ABORTED=0
CARLA_ALREADY_RUNNING=0
CARLA_LAUNCH_PID=""
CARLA_LOG="${SAVE_PATH}/carla_server_${PORT}.log"

cleanup() {
    EXIT_CODE=$?
    set +e

    if [ "${CLEANUP_KILL_PYTHON_ON_EXIT}" = "1" ] && [ -n "${CHECKPOINT_ENDPOINT:-}" ]; then
        EVAL_PIDS=$(ps -ww -eo pid=,args= 2>/dev/null | grep -F "leaderboard_evaluator.py" | grep -F -- "--checkpoint=${CHECKPOINT_ENDPOINT}" | awk '{print $1}')
        if [ -n "${EVAL_PIDS}" ]; then
            kill ${EVAL_PIDS} >/dev/null 2>&1 || true
            sleep 2
            kill -9 ${EVAL_PIDS} >/dev/null 2>&1 || true
        fi
    fi

    KILL_CARLA_BY_PORT=0
    if [ "${AUTO_START_CARLA}" = "1" ] && [ "${CARLA_ALREADY_RUNNING}" != "1" ]; then
        KILL_CARLA_BY_PORT=1
    fi
    if [ "${ABORTED}" = "1" ] && [ "${CLEANUP_KILL_EXISTING_CARLA_ON_ABORT}" = "1" ]; then
        KILL_CARLA_BY_PORT=1
    fi

    if [ "${KILL_CARLA_BY_PORT}" = "1" ] && [ -n "${PORT:-}" ]; then
        CARLA_PIDS=$(ps -ww -eo pid=,args= 2>/dev/null | grep -F -- "--world-port=${PORT}" | grep -E "CarlaUE4-Linux-Shipping|CarlaUE4.sh" | awk '{print $1}')
        if [ -n "${CARLA_PIDS}" ]; then
            kill ${CARLA_PIDS} >/dev/null 2>&1 || true
            sleep 3
            kill -9 ${CARLA_PIDS} >/dev/null 2>&1 || true
        fi
    elif [ -n "${CARLA_LAUNCH_PID}" ]; then
        kill "${CARLA_LAUNCH_PID}" >/dev/null 2>&1 || true
        sleep 3
        kill -9 "${CARLA_LAUNCH_PID}" >/dev/null 2>&1 || true
    fi

    if [ "${AGENT_RESTORED}" != "1" ]; then
        bash "${SCRIPT_DIR}/restore_original_agent.sh" "${BACKUP_DIR}" >/dev/null 2>&1 || true
        AGENT_RESTORED=1
    fi

    return ${EXIT_CODE}
}

on_abort() {
    ABORTED=1
    exit 130
}

trap on_abort INT TERM HUP QUIT
trap cleanup EXIT

if [ "${AUTO_START_CARLA}" = "1" ]; then
    if [ "$(id -u)" -eq 0 ]; then
        echo "Error: AUTO_START_CARLA=1 cannot be used as root (CARLA refuses to run with root privileges)." >&2
        exit 1
    fi

    if ! ${PYTHON_BIN} -c "import carla" >/dev/null 2>&1; then
        echo "Error: cannot import 'carla' from the runner Python environment (${PYTHON_BIN})." >&2
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

    if [ "${KILL_EXISTING_CARLA}" = "1" ] && [ -n "${PORT:-}" ]; then
        CARLA_PIDS=$(ps -u "$(id -u)" -ww -o pid=,args= 2>/dev/null | grep -F -- "--world-port=${PORT}" | grep -E "CarlaUE4-Linux-Shipping|CarlaUE4\.sh" | awk '{print $1}')
        if [ -n "${CARLA_PIDS}" ]; then
            echo "Detected existing CARLA processes on port ${PORT} for user $(id -un). Stopping them..."
            kill ${CARLA_PIDS} >/dev/null 2>&1 || true
            sleep 3
            kill -9 ${CARLA_PIDS} >/dev/null 2>&1 || true
            sleep 1
        fi
    fi

    if [ "${CARLA_KEEP_DISPLAY}" != "1" ]; then
        unset DISPLAY
    fi

    if [ -z "${XDG_RUNTIME_DIR:-}" ]; then
        export XDG_RUNTIME_DIR="/tmp/xdg-runtime-$(id -u)"
        mkdir -p "${XDG_RUNTIME_DIR}" >/dev/null 2>&1 || true
        chmod 700 "${XDG_RUNTIME_DIR}" >/dev/null 2>&1 || true
    fi

    CARLA_START_TS=$(date +%s)

    if carla_ready_check; then
        CARLA_ALREADY_RUNNING=1
    else
        echo "Starting CARLA server on port ${PORT} (log: ${CARLA_LOG})"

        CARLA_ARGS="--world-port=${PORT} -opengl -RenderOffScreen -nosound -stdout -FullStdOutLogOutput"
        if [ -n "${CARLA_EXTRA_ARGS}" ]; then
            CARLA_ARGS="${CARLA_ARGS} ${CARLA_EXTRA_ARGS}"
        fi

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
            cd "${CARLA_ROOT}" || exit 1
            if [[ "${CARLA_SERVER}" == *"CarlaUE4.sh" ]]; then
                SDL_VIDEODRIVER="${CARLA_SDL_VIDEODRIVER}" CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} bash "${CARLA_SERVER}" ${CARLA_ARGS}
            else
                SDL_VIDEODRIVER="${CARLA_SDL_VIDEODRIVER}" CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} "${CARLA_SERVER}" ${CARLA_SERVER_PROJECT} ${CARLA_ARGS}
            fi
        ) >"${CARLA_LOG}" 2>&1 &
        CARLA_LAUNCH_PID=$!

        sleep 4
        if ! kill -0 "${CARLA_LAUNCH_PID}" >/dev/null 2>&1; then
            echo "Error: CARLA server exited early (PID ${CARLA_LAUNCH_PID})." >&2
            set +e
            wait "${CARLA_LAUNCH_PID}" >/dev/null 2>&1
            CARLA_EXIT_CODE=$?
            set -e
            echo "CARLA exit code: ${CARLA_EXIT_CODE}" >&2
            tail -n 200 "${CARLA_LOG}" 2>/dev/null || true
            tail_unreal_log
            exit 1
        fi

        READY=0
        END_TS=$(( $(date +%s) + CARLA_READY_TIMEOUT ))
        while [ "$(date +%s)" -lt "${END_TS}" ]; do
            if ! kill -0 "${CARLA_LAUNCH_PID}" >/dev/null 2>&1; then
                echo "Error: CARLA server exited during startup (PID ${CARLA_LAUNCH_PID})." >&2
                tail -n 200 "${CARLA_LOG}" 2>/dev/null || true
                tail_unreal_log
                exit 1
            fi
            if carla_ready_check; then
                READY=1
                break
            fi
            sleep ${CARLA_STARTUP_CHECK_INTERVAL}
        done

        if [ "${READY}" != "1" ]; then
            echo "Error: CARLA not reachable on localhost:${PORT}" >&2
            tail -n 200 "${CARLA_LOG}" 2>/dev/null || true
            tail_unreal_log
            exit 1
        fi
    fi
fi

set +e
PYTHONUNBUFFERED=1 ${PYTHON_BIN} -u ${LEADERBOARD_ROOT}/leaderboard/leaderboard_evaluator.py \
    --scenarios=${SCENARIOS}  \
    --routes=${ROUTES} \
    --repetitions=${REPETITIONS} \
    --track=${CHALLENGE_TRACK_CODENAME} \
    --checkpoint=${CHECKPOINT_ENDPOINT} \
    --agent=${TEAM_AGENT} \
    --agent-config=${TEAM_CONFIG} \
    --debug=${DEBUG_CHALLENGE} \
    --resume=${RESUME} \
    --timeout=${EVAL_TIMEOUT} \
    --port=${PORT} \
    --trafficManagerPort=${TM_PORT} \
    2>&1 | tee "${EVAL_LOG}"

EVAL_EXIT_CODE=${PIPESTATUS[0]}
set -e

bash "${SCRIPT_DIR}/restore_original_agent.sh" "${BACKUP_DIR}"
AGENT_RESTORED=1

exit $EVAL_EXIT_CODE
