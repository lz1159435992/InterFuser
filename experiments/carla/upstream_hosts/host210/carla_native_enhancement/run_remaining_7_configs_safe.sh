#!/bin/bash
#
# 安全运行剩余 7 个 CARLA 原生增强配置（分阶段，避免显存溢出）
# Safe run of remaining 7 CARLA native enhancement configurations (staged to avoid OOM)
#
# 策略：分3个阶段运行，每个阶段等待完成后再启动下一阶段
# Strategy: Run in 3 stages, wait for completion before starting next stage
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo "CARLA 原生增强实验 - 安全分阶段运行"
echo "CARLA Native Enhancement - Safe Staged Run"
echo "时间 / Time: $(date)"
echo "项目根目录 / Project Root: ${PROJECT_ROOT}"
echo "=========================================="
echo ""

PRE_CLEANUP_ALL=${PRE_CLEANUP_ALL:-0}

DEFAULT_DISPLAY=${DEFAULT_DISPLAY:-":99"}
JOB_DISPLAY=${JOB_DISPLAY:-"${DEFAULT_DISPLAY}"}
JOB_SDL_VIDEODRIVER=${JOB_SDL_VIDEODRIVER:-"x11"}
JOB_CARLA_KEEP_DISPLAY=${JOB_CARLA_KEEP_DISPLAY:-"1"}
JOB_CARLA_FORCE_X99=${JOB_CARLA_FORCE_X99:-"1"}
JOB_CARLA_DISABLE_RENDER_OFFSCREEN=${JOB_CARLA_DISABLE_RENDER_OFFSCREEN:-"1"}
JOB_CARLA_EXTRA_ARGS=${JOB_CARLA_EXTRA_ARGS:-"-NoVSync -benchmark"}
JOB_SPEED_FALLBACK_ON_TIMEOUT=${JOB_SPEED_FALLBACK_ON_TIMEOUT:-"1"}
JOB_SENSOR_QUEUE_TIMEOUT=${JOB_SENSOR_QUEUE_TIMEOUT:-"60"}
if [ "${PRE_CLEANUP_ALL}" = "1" ]; then
    PRE_CLEANUP_USER=${PRE_CLEANUP_USER:-$(id -un)}
    echo "Pre-cleanup enabled: stopping existing CARLA/evaluator processes for user ${PRE_CLEANUP_USER}..." >&2
    set +e
    EVAL_PIDS=$(ps -u "${PRE_CLEANUP_USER}" -ww -o pid=,args= 2>/dev/null | grep -E "python3? -u .*leaderboard_evaluator(_custom)?\.py" | awk '{print $1}')
    TEE_PIDS=$(ps -u "${PRE_CLEANUP_USER}" -ww -o pid=,args= 2>/dev/null | grep -E "(^|[[:space:]])tee[[:space:]].*leaderboard_evaluator\.log" | awk '{print $1}')
    CARLA_PIDS=$(ps -u "${PRE_CLEANUP_USER}" -ww -o pid=,args= 2>/dev/null | grep -E "CarlaUE4-Linux-Shipping|CarlaUE4\.sh" | awk '{print $1}')

    if [ -n "${EVAL_PIDS}" ]; then
        kill ${EVAL_PIDS} >/dev/null 2>&1
        sleep 2
        kill -9 ${EVAL_PIDS} >/dev/null 2>&1
    fi
    if [ -n "${TEE_PIDS}" ]; then
        kill ${TEE_PIDS} >/dev/null 2>&1
        sleep 1
        kill -9 ${TEE_PIDS} >/dev/null 2>&1
    fi
    if [ -n "${CARLA_PIDS}" ]; then
        kill ${CARLA_PIDS} >/dev/null 2>&1
        sleep 3
        kill -9 ${CARLA_PIDS} >/dev/null 2>&1
    fi
    set -e
fi

# 切换到项目根目录
cd "${PROJECT_ROOT}"

# 激活 conda 环境（参考 augmentation_seq_method）
CONDA_ENV_NAME=${CONDA_ENV_NAME:-interfuser}
CONDA_SH_CANDIDATE="${CONDA_SH_CANDIDATE:-${HOME}/anaconda2/etc/profile.d/conda.sh}"
if [ -f "${CONDA_SH_CANDIDATE}" ]; then
    source "${CONDA_SH_CANDIDATE}" >/dev/null 2>&1 || true
    conda activate "${CONDA_ENV_NAME}" >/dev/null 2>&1 || true
elif command -v conda >/dev/null 2>&1; then
    CONDA_BASE=$(conda info --base 2>/dev/null)
    if [ -n "${CONDA_BASE}" ] && [ -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]; then
        source "${CONDA_BASE}/etc/profile.d/conda.sh" >/dev/null 2>&1 || true
        conda activate "${CONDA_ENV_NAME}" >/dev/null 2>&1 || true
    fi
fi

# 设置 Python 解释器
PYTHON_BIN=${PYTHON_BIN:-python3}
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    PYTHON_BIN=python3
fi

# 检测 Python 版本
PY_VER=$(${PYTHON_BIN} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
echo "Python 解释器 / Interpreter: ${PYTHON_BIN}"
echo "Python 版本 / Version: ${PY_VER}"

# 验证 CARLA egg
CARLA_ROOT="${PROJECT_ROOT}/carla"
CARLA_EGG=""
if [ "${PY_VER}" = "3.7" ]; then
    CARLA_EGG="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg"
elif [ "${PY_VER}" = "2.7" ]; then
    CARLA_EGG="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py2.7-linux-x86_64.egg"
fi

if [ -z "${CARLA_EGG}" ] || [ ! -f "${CARLA_EGG}" ]; then
    echo "错误 / Error：CARLA PythonAPI egg 不可用，Python 版本 / not available for Python: ${PY_VER}" >&2
    echo "需要 Python 3.7 或 2.7 / Requires Python 3.7 or 2.7" >&2
    echo ""
    echo "提示 / Hint: 激活 interfuser conda 环境"
    echo "Example: conda activate interfuser && bash $0"
    exit 1
fi

echo "CARLA egg: ${CARLA_EGG}"
echo "✓ 环境验证通过 / Environment validated"
echo ""

EVAL_TYPES=${EVAL_TYPES:-"town05 42routes"}
WAIT_GPU_MEM_SEC=${WAIT_GPU_MEM_SEC:-60}
LAUNCH_GAP_SEC=${LAUNCH_GAP_SEC:-10}
AUTO_RESUME_SKIP=${AUTO_RESUME_SKIP:-1}
FORCE_FRESH=${FORCE_FRESH:-0}
VERBOSE_GPU_CHECK=${VERBOSE_GPU_CHECK:-1}
RESERVATION_ENABLED=${RESERVATION_ENABLED:-1}
RESERVATION_RATIO=${RESERVATION_RATIO:-1.0}
RESERVATION_CAP_MB=${RESERVATION_CAP_MB:-0}
MAX_PARALLEL=${MAX_PARALLEL:-4}

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "错误 / Error: nvidia-smi not found, cannot auto-allocate GPUs by memory." >&2
    exit 1
fi

GPU_LIST=${GPU_LIST:-""}
if [ -n "${GPU_LIST}" ]; then
    IFS=',' read -r -a GPU_IDS <<< "${GPU_LIST}"
else
    mapfile -t GPU_IDS < <(nvidia-smi --query-gpu=index --format=csv,noheader,nounits 2>/dev/null | awk '{print $1}')
fi

if [ ${#GPU_IDS[@]} -eq 0 ]; then
    echo "错误 / Error: no GPUs detected." >&2
    exit 1
fi

if [ "${MAX_PARALLEL}" -gt 0 ] && [ ${#GPU_IDS[@]} -gt "${MAX_PARALLEL}" ]; then
    GPU_IDS=("${GPU_IDS[@]:0:${MAX_PARALLEL}}")
fi

pids=()

declare -A GPU_RESERVED_MB
declare -A PID_GPU
declare -A PID_RESERVE_MB
declare -A GPU_BUSY

for gid in "${GPU_IDS[@]}"; do
    GPU_RESERVED_MB[${gid}]=0
    GPU_BUSY[${gid}]=0
done

reap_finished_jobs() {
    local still_running=()
    for pid in "${pids[@]}"; do
        if kill -0 "${pid}" >/dev/null 2>&1; then
            still_running+=("${pid}")
            continue
        fi

        gid=${PID_GPU[${pid}]:-}
        req=${PID_RESERVE_MB[${pid}]:-0}
        if [ -n "${gid}" ]; then
            GPU_BUSY[${gid}]=0
            cur=${GPU_RESERVED_MB[${gid}]:-0}
            if [ "${cur}" -ge "${req}" ]; then
                GPU_RESERVED_MB[${gid}]=$((cur - req))
            else
                GPU_RESERVED_MB[${gid}]=0
            fi
        fi

        unset PID_GPU[${pid}] >/dev/null 2>&1 || true
        unset PID_RESERVE_MB[${pid}] >/dev/null 2>&1 || true
    done
    pids=("${still_running[@]}")
}

calc_reserve_mb() {
    local req_mb="$1"
    if [ "${RESERVATION_ENABLED}" != "1" ]; then
        echo "0"
        return 0
    fi
    ${PYTHON_BIN} - <<PY 2>/dev/null
import math
req = int("${req_mb}")
ratio = float("${RESERVATION_RATIO}")
cap = int("${RESERVATION_CAP_MB}")
reserve = int(math.ceil(req * ratio))
if cap > 0:
    reserve = min(reserve, cap)
if reserve < 0:
    reserve = 0
print(reserve)
PY
}

normalize_config() {
    local cfg="$1"
    cfg="${cfg// /}"
    cfg="${cfg//gs8/gauss8}"
    cfg="${cfg//gs16/gauss16}"
    echo "${cfg}"
}

estimate_required_mem_mb() {
    local cfg="$1"
    cfg="$(normalize_config "${cfg}")"

    case "${cfg}" in
        high_fps,high_res,no_noise)
            echo "${REQ_MEM_MB_ALL:-26000}" ;;
        high_fps,high_res)
            echo "${REQ_MEM_MB_HF_HR:-24000}" ;;
        high_res,no_noise)
            echo "${REQ_MEM_MB_HR_NN:-22000}" ;;
        high_res)
            echo "${REQ_MEM_MB_HR:-20000}" ;;
        high_fps,no_noise)
            echo "${REQ_MEM_MB_HF_NN:-18000}" ;;
        high_fps)
            echo "${REQ_MEM_MB_HF:-16000}" ;;
        gauss16)
            echo "${REQ_MEM_MB_GS16:-16000}" ;;
        gauss8)
            echo "${REQ_MEM_MB_GS8:-16000}" ;;
        no_noise)
            echo "${REQ_MEM_MB_NN:-15000}" ;;
        *)
            echo "${REQ_MEM_MB_DEFAULT:-16000}" ;;
    esac
}

get_gpu_free_mb() {
    local gid="$1"
    nvidia-smi -i "${gid}" --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -n 1 | awk '{print $1}'
}

dump_gpu_memory_status() {
    local req_mb="$1"
    echo "  --- GPU memory status (req_free_mem_mb=${req_mb}) ---"
    for gid in "${GPU_IDS[@]}"; do
        free_mb=$(get_gpu_free_mb "${gid}")
        reserved_mb=${GPU_RESERVED_MB[${gid}]:-0}
        if [ "${RESERVATION_ENABLED}" != "1" ]; then
            reserved_mb=0
        fi
        if [ -z "${free_mb}" ]; then
            echo "  GPU ${gid}: free_mb=<N/A> reserved_mb=${reserved_mb} effective_free_mb=<N/A>"
        else
            effective_free=$((free_mb - reserved_mb))
            if [ "${effective_free}" -lt 0 ]; then
                effective_free=0
            fi
            echo "  GPU ${gid}: free_mb=${free_mb} reserved_mb=${reserved_mb} effective_free_mb=${effective_free}"
        fi
    done
    echo "  -----------------------------------------"
}

find_latest_checkpoint() {
    local eval_type="$1"
    local native_tag="$2"

    local direct="results/native/${eval_type}_${native_tag}.json"
    if [ -f "${direct}" ]; then
        echo "${direct}"
        return 0
    fi

    local latest
    latest=$(${PYTHON_BIN} - <<PY 2>/dev/null
import glob, os, re
eval_type = "${eval_type}"
native_tag = "${native_tag}"
pattern = f"results/native/{eval_type}_{native_tag}_*.json"
paths = sorted(glob.glob(pattern), key=lambda p: os.path.getmtime(p), reverse=True)
for p in paths:
    bn = os.path.basename(p)
    m = re.match(rf"^{re.escape(eval_type)}_{re.escape(native_tag)}_(\\d{{8}}_\\d{{6}})\\.json$", bn)
    if m:
        print(p)
        break
PY
)
    if [ -n "${latest}" ]; then
        echo "${latest}"
        return 0
    fi

    echo ""
}

select_checkpoint_action() {
    local eval_type="$1"
    local native_tag="$2"

    local direct="results/native/${eval_type}_${native_tag}.json"
    local -a candidates=()

    while IFS= read -r line; do
        [ -n "${line}" ] || continue
        candidates+=("${line}")
    done < <(${PYTHON_BIN} - <<PY 2>/dev/null
import glob, os, re
eval_type = "${eval_type}"
native_tag = "${native_tag}"
paths = []
direct = f"results/native/{eval_type}_{native_tag}.json"
if os.path.isfile(direct):
    paths.append(direct)
for p in glob.glob(f"results/native/{eval_type}_{native_tag}_*.json"):
    bn=os.path.basename(p)
    # require exact timestamp after native_tag_ to avoid prefix collisions
    if re.match(rf"^{re.escape(eval_type)}_{re.escape(native_tag)}_(\\d{{8}}_\\d{{6}})\\.json$", bn):
        paths.append(p)
paths = sorted(set(paths), key=lambda p: os.path.getmtime(p), reverse=True)
for p in paths:
    print(p)
PY
)

    if [ ${#candidates[@]} -eq 0 ]; then
        echo "NEW:"
        return 0
    fi

    for ckpt in "${candidates[@]}"; do
        if [ "$(checkpoint_is_completed "${ckpt}")" = "1" ]; then
            echo "SKIP:${ckpt}"
            return 0
        fi
    done

    local best_ckpt=""
    local best_ratio="-1"
    local best_cur="-1"
    local idx=0
    local valid_count=0
    for ckpt in "${candidates[@]}"; do
        out=$(${PYTHON_BIN} - <<PY 2>/dev/null
import json
p = "${ckpt}"
cur, total = 0, 0
try:
    with open(p, 'r') as f:
        d = json.load(f)
    prog = d.get('_checkpoint', {}).get('progress', None)
    if isinstance(prog, list) and len(prog) >= 2:
        cur = int(prog[0])
        total = int(prog[1])
except Exception:
    pass
ratio = (float(cur) / float(total)) if total > 0 else 0.0
print(f"{ratio} {cur} {total}")
PY
)
        ratio=$(echo "${out}" | awk '{print $1}')
        cur=$(echo "${out}" | awk '{print $2}')
        total=$(echo "${out}" | awk '{print $3}')

        if [ -z "${total}" ] || [ "${total}" -le 0 ]; then
            idx=$((idx + 1))
            continue
        fi
        valid_count=$((valid_count + 1))

        better=$(${PYTHON_BIN} - <<PY 2>/dev/null
import sys
r = float("${ratio}" or 0)
c = int("${cur}" or 0)
br = float("${best_ratio}" or -1)
bc = int("${best_cur}" or -1)
print(1 if (r > br or (r == br and c > bc)) else 0)
PY
)
        if [ "${better}" = "1" ]; then
            best_ratio="${ratio}"
            best_cur="${cur}"
            best_ckpt="${ckpt}"
        fi
        idx=$((idx + 1))
    done

    if [ "${valid_count}" -le 0 ]; then
        echo "NEW:"
        return 0
    fi

    echo "RESUME:${best_ckpt}"
}

checkpoint_is_completed() {
    local ckpt="$1"
    if [ ! -f "${ckpt}" ]; then
        echo "0"
        return 0
    fi

    ${PYTHON_BIN} - <<PY 2>/dev/null
import json, sys
path = "${ckpt}"
try:
    with open(path, 'r') as f:
        data = json.load(f)
    ck = data.get('_checkpoint', {})
    prog = ck.get('progress', None)
    if isinstance(prog, list) and len(prog) >= 2:
        cur = int(prog[0])
        total = int(prog[1])
        sys.exit(0 if cur >= total else 1)
except Exception:
    sys.exit(1)
sys.exit(1)
PY
    if [ "$?" -eq 0 ]; then
        echo "1"
    else
        echo "0"
    fi
}

resolve_save_path_from_checkpoint() {
    local ckpt="$1"
    local eval_type="$2"
    local native_tag="$3"

    if [[ "${ckpt}" =~ ^results/native/${eval_type}_${native_tag}_[0-9]{8}_[0-9]{6}\.json$ ]]; then
        local base
        base=$(basename "${ckpt}" .json)
        echo "data/eval_native/${base}"
        return 0
    fi

    local found
    found=$(grep -R --line-number -F "\"checkpoint\": \"${ckpt}\"" data/eval_native 2>/dev/null | head -n 1 | awk -F: '{print $1}')
    if [ -n "${found}" ]; then
        echo "$(dirname "${found}")"
        return 0
    fi

    echo ""
}

select_gpu_for_job() {
    local req_mb="$1"
    local best_gid=""
    local best_free=-1

    for gid in "${GPU_IDS[@]}"; do
        if [ "${GPU_BUSY[${gid}]:-0}" = "1" ]; then
            continue
        fi
        free_mb=$(get_gpu_free_mb "${gid}")
        if [ -z "${free_mb}" ]; then
            continue
        fi
        reserved_mb=${GPU_RESERVED_MB[${gid}]:-0}
        if [ "${RESERVATION_ENABLED}" != "1" ]; then
            reserved_mb=0
        fi
        effective_free=$((free_mb - reserved_mb))
        if [ "${effective_free}" -lt 0 ]; then
            effective_free=0
        fi
        if [ "${effective_free}" -ge "${req_mb}" ] && [ "${effective_free}" -gt "${best_free}" ]; then
            best_free="${effective_free}"
            best_gid="${gid}"
        fi
    done

    echo "${best_gid}"
}

configs=(
    "high_fps"
    "high_fps,no_noise"
    "high_res"
    "high_res,no_noise"
    "no_noise"
    "high_fps,high_res"
    "high_fps,high_res,no_noise"
    "gauss8"
    "gauss16"
)

SKIP_CONFIGS=${SKIP_CONFIGS:-""}

should_skip_config() {
    local cfg="$1"
    local skip

    if [ -z "${SKIP_CONFIGS}" ]; then
        return 1
    fi

    cfg="$(normalize_config "${cfg}")"
    for skip in ${SKIP_CONFIGS}; do
        skip="$(normalize_config "${skip}")"
        if [ "${cfg}" = "${skip}" ]; then
            return 0
        fi
    done
    return 1
}

jobs=()
for eval_type in ${EVAL_TYPES}; do
    for cfg in "${configs[@]}"; do
        if should_skip_config "${cfg}"; then
            continue
        fi
        CONFIG_ITEM_NORM="$(normalize_config "${cfg}")"
        if [ "${AUTO_RESUME_SKIP}" = "1" ] && [ "${FORCE_FRESH}" != "1" ]; then
            NATIVE_TAG_ITEM=$(echo "${CONFIG_ITEM_NORM}" | tr ', ' '__')
            ACTION=$(select_checkpoint_action "${eval_type}" "${NATIVE_TAG_ITEM}")
            ACTION_KIND="${ACTION%%:*}"
            if [ "${ACTION_KIND}" = "SKIP" ]; then
                continue
            fi
        fi
        jobs+=("${eval_type}:${CONFIG_ITEM_NORM}")
    done
done

echo "将运行以下任务 / Will run the following jobs:"
NUM_JOBS=${#jobs[@]}
for i in "${!jobs[@]}"; do
    item="${jobs[$i]}"
    EVAL_TYPE_ITEM="${item%%:*}"
    CONFIG_ITEM="${item#*:}"
    REQ_MB=$(estimate_required_mem_mb "${CONFIG_ITEM}")
    NUM=$((i + 1))

    if [ "${AUTO_RESUME_SKIP}" = "1" ] && [ "${FORCE_FRESH}" != "1" ]; then
        NATIVE_TAG_ITEM=$(echo "${CONFIG_ITEM}" | tr ', ' '__')
        ACTION=$(select_checkpoint_action "${EVAL_TYPE_ITEM}" "${NATIVE_TAG_ITEM}")
        ACTION_KIND="${ACTION%%:*}"
        ACTION_CKPT="${ACTION#*:}"
        if [ "${ACTION_KIND}" = "SKIP" ]; then
            echo "  [${NUM}/${NUM_JOBS}] ${EVAL_TYPE_ITEM} - ${CONFIG_ITEM} (SKIP completed, req_free_mem_mb≈${REQ_MB})"
        elif [ "${ACTION_KIND}" = "RESUME" ]; then
            echo "  [${NUM}/${NUM_JOBS}] ${EVAL_TYPE_ITEM} - ${CONFIG_ITEM} (RESUME ${ACTION_CKPT}, req_free_mem_mb≈${REQ_MB})"
        else
            echo "  [${NUM}/${NUM_JOBS}] ${EVAL_TYPE_ITEM} - ${CONFIG_ITEM} (NEW, req_free_mem_mb≈${REQ_MB})"
        fi
    else
        echo "  [${NUM}/${NUM_JOBS}] ${EVAL_TYPE_ITEM} - ${CONFIG_ITEM} (req_free_mem_mb≈${REQ_MB})"
    fi
done
echo ""
echo "可用 GPU / Available GPUs: ${GPU_IDS[*]}"
echo "EVAL_TYPES: ${EVAL_TYPES}"
echo "MAX_PARALLEL: ${MAX_PARALLEL}"
echo ""

for i in "${!jobs[@]}"; do
    item="${jobs[$i]}"
    EVAL_TYPE_ITEM="${item%%:*}"
    CONFIG_ITEM="${item#*:}"
    REQ_MB=$(estimate_required_mem_mb "${CONFIG_ITEM}")

    EXPORT_SAVE_PATH=""
    EXPORT_CKPT=""
    EXPORT_RESUME="True"
    SKIP_JOB=0
    if [ "${AUTO_RESUME_SKIP}" = "1" ] && [ "${FORCE_FRESH}" != "1" ]; then
        NATIVE_TAG_ITEM=$(echo "${CONFIG_ITEM}" | tr ', ' '__')
        ACTION=$(select_checkpoint_action "${EVAL_TYPE_ITEM}" "${NATIVE_TAG_ITEM}")
        ACTION_KIND="${ACTION%%:*}"
        ACTION_CKPT="${ACTION#*:}"
        if [ "${ACTION_KIND}" = "SKIP" ]; then
            SKIP_JOB=1
            EXPORT_CKPT="${ACTION_CKPT}"
        elif [ "${ACTION_KIND}" = "RESUME" ]; then
            EXPORT_CKPT="${ACTION_CKPT}"
            EXPORT_SAVE_PATH=$(resolve_save_path_from_checkpoint "${EXPORT_CKPT}" "${EVAL_TYPE_ITEM}" "${NATIVE_TAG_ITEM}")
            EXPORT_RESUME="True"
        fi
    fi

    NUM=$((i + 1))
    echo "=========================================="
    echo "[${NUM}/${NUM_JOBS}] 准备启动 / Preparing: ${EVAL_TYPE_ITEM} - ${CONFIG_ITEM}"
    echo "需要空闲显存 / Required free mem (MB): ${REQ_MB}"
    if [ "${SKIP_JOB}" = "1" ]; then
        echo "跳过 / Skip: detected completed checkpoint"
    elif [ -n "${EXPORT_CKPT}" ] && [ -n "${EXPORT_SAVE_PATH}" ]; then
        echo "恢复 / Resume: checkpoint=${EXPORT_CKPT}"
        echo "恢复 / Resume: save_path=${EXPORT_SAVE_PATH}"
    elif [ -n "${EXPORT_CKPT}" ]; then
        echo "恢复 / Resume: checkpoint=${EXPORT_CKPT}"
        echo "恢复 / Resume: save_path not found, will fallback to runner default"
    else
        echo "新跑 / New run"
    fi
    echo "=========================================="

    if [ "${SKIP_JOB}" = "1" ]; then
        echo "  ✓ 已完成，跳过 / Completed, skipped"
        echo ""
        continue
    fi

    while true; do
        reap_finished_jobs
        if [ "${MAX_PARALLEL}" -gt 0 ] && [ "${#pids[@]}" -ge "${MAX_PARALLEL}" ]; then
            sleep 2
            continue
        fi
        GPU_ID=$(select_gpu_for_job "${REQ_MB}")
        if [ -n "${GPU_ID}" ]; then
            FREE_MB=$(get_gpu_free_mb "${GPU_ID}")
            RESERVED_MB=${GPU_RESERVED_MB[${GPU_ID}]:-0}
            EFFECTIVE_FREE_MB=$((FREE_MB - RESERVED_MB))
            echo "  ✓ 选择 GPU ${GPU_ID} (free_mb=${FREE_MB}, reserved_mb=${RESERVED_MB}, effective_free_mb=${EFFECTIVE_FREE_MB})"
            break
        fi
        echo "  ⚠ 当前无 GPU 满足需求 (req_free_mem_mb=${REQ_MB})，${WAIT_GPU_MEM_SEC}s 后重试..."
        if [ "${VERBOSE_GPU_CHECK}" = "1" ]; then
            dump_gpu_memory_status "${REQ_MB}"
        fi
        sleep "${WAIT_GPU_MEM_SEC}"
    done

    CMD_ENV=(
        "PYTHON_BIN=${PYTHON_BIN}"
        "GPU_ID=${GPU_ID}"
        "PORT=random"
        "AUTO_START_CARLA=1"
        "RESUME=${EXPORT_RESUME}"
        "PRE_CLEANUP_ALL=0"
        "DISPLAY=${JOB_DISPLAY}"
        "CARLA_KEEP_DISPLAY=${JOB_CARLA_KEEP_DISPLAY}"
        "CARLA_FORCE_X99=${JOB_CARLA_FORCE_X99}"
        "SDL_VIDEODRIVER=${JOB_SDL_VIDEODRIVER}"
        "CARLA_DISABLE_RENDER_OFFSCREEN=${JOB_CARLA_DISABLE_RENDER_OFFSCREEN}"
        "CARLA_EXTRA_ARGS=${JOB_CARLA_EXTRA_ARGS}"
        "SPEED_FALLBACK_ON_TIMEOUT=${JOB_SPEED_FALLBACK_ON_TIMEOUT}"
        "SENSOR_QUEUE_TIMEOUT=${JOB_SENSOR_QUEUE_TIMEOUT}"
    )
    if [ -n "${EXPORT_CKPT}" ]; then
        CMD_ENV+=("CHECKPOINT_ENDPOINT=${EXPORT_CKPT}")
    fi
    if [ -n "${EXPORT_SAVE_PATH}" ]; then
        CMD_ENV+=("SAVE_PATH=${EXPORT_SAVE_PATH}")
    fi

    env "${CMD_ENV[@]}" bash carla_native_enhancement/run_evaluation_native.sh "${EVAL_TYPE_ITEM}" "${CONFIG_ITEM}" &
    PID=$!
    pids+=("${PID}")

    RESERVE_MB=$(calc_reserve_mb "${REQ_MB}")

    PID_GPU[${PID}]="${GPU_ID}"
    PID_RESERVE_MB[${PID}]="${RESERVE_MB}"
    GPU_BUSY[${GPU_ID}]=1
    GPU_RESERVED_MB[${GPU_ID}]=$(( ${GPU_RESERVED_MB[${GPU_ID}]:-0} + RESERVE_MB ))

    echo "  ✓ 进程已启动 / Process started, PID: ${PID} (reserve_mb=${RESERVE_MB})"
    echo "  等待 ${LAUNCH_GAP_SEC} 秒后启动下一个 / Waiting ${LAUNCH_GAP_SEC}s before next..."
    echo ""
    sleep "${LAUNCH_GAP_SEC}"
done

echo ""
echo "=========================================="
echo "所有任务已启动！"
echo "All jobs started!"
echo "=========================================="
echo ""
echo "实际 GPU 分配为动态分配（根据显存空闲） / GPU allocation is dynamic (by free memory)"
echo ""
echo "监控命令 / Monitoring commands:"
echo "  watch -n 1 nvidia-smi"
echo "  ps aux | grep CarlaUE4"
echo ""
echo "查看日志 / View logs:"
echo "  ls -lh data/eval_native/"
echo "  tail -f data/eval_native/*_*/leaderboard_evaluator.log"
echo ""
echo "等待所有评估完成 / Waiting for all evaluations to complete..."
echo "预计时间 / Estimated time: 2-4 hours"
echo ""

# 等待所有后台进程完成
# Wait for all background processes to complete
wait

echo ""
echo "=========================================="
echo "所有配置评估完成！"
echo "All configuration evaluations completed!"
echo "完成时间 / Completion time: $(date)"
echo "=========================================="
echo ""
echo "查看结果 / View results:"
echo "  ls -lh results/native/"
echo "  cat results/native/*.json"
echo ""
