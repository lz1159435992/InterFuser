#!/bin/bash
# InterFuser 带数据处理器的评估脚�?# 
# 此脚本会�?# 1. 自动部署数据处理器模�?# 2. 使用带处理器�?agent 运行评估
# 3. 将结果保存到独立目录
# 4. 评估结束后自动恢复原始文�?
set -e  # 遇到错误立即退�?
echo "╔══════════════════════════════════════════════════════════════╗"
echo "�?    InterFuser 带数据处理器的评估脚�?                         �?
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# 配置部分
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT=${PROJECT_ROOT:-"$(cd "${SCRIPT_DIR}/.." && pwd)"}
TEAM_CODE_DIR="${PROJECT_ROOT}/leaderboard/team_code"
BACKUP_DIR="${SCRIPT_DIR}/.backup_$(date +%Y%m%d_%H%M%S)"

# 评估参数
EVAL_TYPE=${1:-town05}
GPU_ID=${GPU_ID:-0}
CONFIG_TYPE=${2:-no_processing}  # 配置类型: no_processing, denoise15, denoise25, denoise50, sr2x, sr4x, jpeg_repair, srgan_2x, srgan_enhance, srgan_4x, custom

DEFAULT_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-${GPU_ID}}
CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES:-${DEFAULT_VISIBLE_DEVICES}}
PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES:-${DEFAULT_VISIBLE_DEVICES}}
DATA_PROCESSOR_GPU_ID=${DATA_PROCESSOR_GPU_ID:-0}

echo "📋 评估配置:"
echo "  - 评估类型: $EVAL_TYPE"
echo "  - GPU ID: $GPU_ID"
echo "  - CARLA GPUs: ${CARLA_CUDA_VISIBLE_DEVICES}"
echo "  - Python GPUs: ${PY_CUDA_VISIBLE_DEVICES}"
echo "  - Data Processor GPU ID: ${DATA_PROCESSOR_GPU_ID}"
echo "  - 数据处理配置: $CONFIG_TYPE"
echo "  - 项目根目�? $PROJECT_ROOT"
echo ""

# ============================================================
# 步骤 1: 备份原始文件
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 步骤 1/5: 备份原始文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p "${BACKUP_DIR}"

# 备份 interfuser_agent.py（如果存在）
if [ -f "${TEAM_CODE_DIR}/interfuser_agent.py" ]; then
    echo "  �?备份 interfuser_agent.py"
    cp "${TEAM_CODE_DIR}/interfuser_agent.py" "${BACKUP_DIR}/interfuser_agent.py.bak"
    BACKUP_AGENT=1
else
    echo "  �?interfuser_agent.py 不存在，跳过备份"
    BACKUP_AGENT=0
fi

# 备份数据处理器文件（如果存在�?if [ -f "${TEAM_CODE_DIR}/data_processor.py" ]; then
    echo "  �?备份 data_processor.py"
    cp "${TEAM_CODE_DIR}/data_processor.py" "${BACKUP_DIR}/data_processor.py.bak"
fi

if [ -f "${TEAM_CODE_DIR}/data_processor_config.py" ]; then
    echo "  �?备份 data_processor_config.py"
    cp "${TEAM_CODE_DIR}/data_processor_config.py" "${BACKUP_DIR}/data_processor_config.py.bak"
fi

echo "  �?备份目录: ${BACKUP_DIR}"
echo ""

# ============================================================
# 步骤 2: 部署数据处理�?# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 步骤 2/5: 部署数据处理器模�?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 复制数据处理器核心文�?echo "  �?复制 data_processor.py"
cp "${SCRIPT_DIR}/data_processor.py" "${TEAM_CODE_DIR}/data_processor.py"

echo "  �?复制 data_processor_config.py"
cp "${SCRIPT_DIR}/data_processor_config.py" "${TEAM_CODE_DIR}/data_processor_config.py"

# 根据配置类型修改 ACTIVE_CONFIG
case $CONFIG_TYPE in
    no_processing)
        echo "  �?配置类型: 无处�?(CONFIG_NO_PROCESSING)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_NO_PROCESSING/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    denoise15)
        echo "  �?配置类型: 彩色去噪 noise=15 (CONFIG_COLOR_DENOISE)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_COLOR_DENOISE/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    denoise25)
        echo "  �?配置类型: 彩色去噪 noise=25 (CONFIG_COLOR_DENOISE_25)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_COLOR_DENOISE_25/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    denoise50)
        echo "  �?配置类型: 彩色去噪 noise=50 (CONFIG_COLOR_DENOISE_50)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_COLOR_DENOISE_50/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    sr2x)
        echo "  �?配置类型: 2x 超分辨率 (CONFIG_SR_2X)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_SR_2X/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    sr4x)
        echo "  �?配置类型: 4x 超分辨率 (CONFIG_SR_4X)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_SR_4X/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    jpeg_repair)
        echo "  �?配置类型: JPEG 修复 (CONFIG_JPEG_REPAIR)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_JPEG_REPAIR/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    srgan_2x)
        echo "  �?配置类型: SRGAN 2x 超分辨率 (CONFIG_SRGAN_2X) - 与原�?test.py 一�?
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_SRGAN_2X/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    srgan_enhance)
        echo "  �?配置类型: SRGAN 图像增强 1x (CONFIG_SRGAN_ENHANCE)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_SRGAN_ENHANCE/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    srgan_4x)
        echo "  �?配置类型: SRGAN 4x 超分辨率 (CONFIG_SRGAN_4X)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_SRGAN_4X/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    custom)
        echo "  �?配置类型: 自定义配�?(DATA_PROCESSOR_CONFIG)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    *)
        echo "  �?错误: 未知的配置类�?'$CONFIG_TYPE'"
        echo ""
        echo "支持的类�?"
        echo "  【无处理�?
        echo "    no_processing          - 无处�?
        echo ""
        echo "  【SwinIR�?
        echo "    denoise15              - 彩色去噪 noise=15"
        echo "    denoise25              - 彩色去噪 noise=25"
        echo "    denoise50              - 彩色去噪 noise=50"
        echo "    sr2x                   - SwinIR 2x 超分辨率"
        echo "    sr4x                   - SwinIR 4x 超分辨率"
        echo "    jpeg_repair            - JPEG 修复"
        echo ""
        echo "  【SRGAN�?
        echo "    srgan_2x               - SRGAN 2x 超分辨率（与原始 test.py 一致）�?
        echo "    srgan_enhance          - SRGAN 图像增强 1x"
        echo "    srgan_4x               - SRGAN 4x 超分辨率"
        echo ""
        echo "  【自定义�?
        echo "    custom                 - 自定义配�?
        echo ""
        exit 1
        ;;
esac

# 复制完整�?agent
echo "  �?部署 interfuser_agent_complete.py �?interfuser_agent.py"
cp "${SCRIPT_DIR}/interfuser_agent_complete.py" "${TEAM_CODE_DIR}/interfuser_agent.py"

echo "  �?数据处理器模块部署完�?
echo ""

# ============================================================
# 步骤 3: 设置环境变量
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  步骤 3/5: 设置环境变量"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 激�?conda 环境
CONDA_ENV_NAME=${CONDA_ENV_NAME:-interfuser}
if [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
    source /opt/conda/etc/profile.d/conda.sh >/dev/null 2>&1 || true
    if conda activate "${CONDA_ENV_NAME}" >/dev/null 2>&1; then
        echo "  �?激�?conda 环境: ${CONDA_ENV_NAME}"
    else
        echo "  ⚠️  conda 环境不存�? ${CONDA_ENV_NAME}，继续使用当前环�?
    fi
elif command -v conda >/dev/null 2>&1; then
    CONDA_BASE=$(conda info --base 2>/dev/null)
    if [ -n "${CONDA_BASE}" ] && [ -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]; then
        source "${CONDA_BASE}/etc/profile.d/conda.sh" >/dev/null 2>&1 || true
        if conda activate "${CONDA_ENV_NAME}" >/dev/null 2>&1; then
            echo "  �?激�?conda 环境: ${CONDA_ENV_NAME}"
        else
            echo "  ⚠️  conda 环境不存�? ${CONDA_ENV_NAME}，继续使用当前环�?
        fi
    else
        echo "  ⚠️  conda.sh 不存在，跳过 conda 激�?
    fi
else
    echo "  ⚠️  conda 不存在，跳过 conda 激�?
fi

# 切换到项目根目录
cd "${PROJECT_ROOT}"

# 设置基本环境变量
export CARLA_CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES}
export PY_CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES}
export CUDA_VISIBLE_DEVICES=${PY_CUDA_VISIBLE_DEVICES}
export DATA_PROCESSOR_GPU_ID=${DATA_PROCESSOR_GPU_ID}
export PROCESS_METHOD_ROOT=${PROCESS_METHOD_ROOT:-"${PROJECT_ROOT}/process_mothod"}
export CARLA_ROOT=${PROJECT_ROOT}/carla
export CARLA_SERVER=${CARLA_ROOT}/CarlaUE4.sh
export SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-dummy}
if [ -z "${SDL_VIDEODRIVER:-}" ]; then
    if [ -n "${DISPLAY:-}" ]; then
        export SDL_VIDEODRIVER=x11
    else
        export SDL_VIDEODRIVER=dummy
    fi
fi
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
    echo "Error: CARLA PythonAPI egg not available for python ${PY_VER}." >&2
    echo "Expected one of: py3.7 or py2.7 under ${CARLA_ROOT}/PythonAPI/carla/dist" >&2
    echo "Tip: create/activate a Python 3.7 environment, then re-run with CONDA_ENV_NAME=<env> or PYTHON_BIN=<python3.7>." >&2
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

# 根据评估类型设置路线和结果路�?case $EVAL_TYPE in
    town05)
        echo "  �?评估类型: Town05 Long Benchmark"
        export ROUTES=leaderboard/data/evaluation_routes/routes_town05_long.xml
        export SCENARIOS=leaderboard/data/scenarios/town05_all_scenarios.json
        RESULT_BASE="town05_${CONFIG_TYPE}"
        ;;
    42routes)
        echo "  �?评估类型: CARLA 42 Routes Benchmark"
        export ROUTES=leaderboard/data/42routes/42routes.xml
        export SCENARIOS=leaderboard/data/42routes/42scenarios.json
        RESULT_BASE="42routes_${CONFIG_TYPE}"
        ;;
    custom)
        echo "  �?评估类型: 自定义路�?
        export ROUTES=${CUSTOM_ROUTES:-leaderboard/data/evaluation_routes/routes_town05_long.xml}
        export SCENARIOS=${CUSTOM_SCENARIOS:-leaderboard/data/scenarios/town05_all_scenarios.json}
        RESULT_BASE="custom_${CONFIG_TYPE}"
        ;;
    *)
        echo "  �?错误: 未知的评估类�?'$EVAL_TYPE'"
        echo ""
        echo "用法: $0 [评估类型] [配置类型]"
        echo ""
        echo "评估类型: town05 | 42routes | custom"
        echo ""
        echo "配置类型:"
        echo "  【无处理�?    no_processing"
        echo "  【SwinIR�?    denoise15 | denoise25 | denoise50 | sr2x | sr4x | jpeg_repair"
        echo "  【SRGAN�?     srgan_2x | srgan_enhance | srgan_4x"
        echo "  【自定义�?    custom"
        echo ""
        echo "示例:"
        echo "  $0 town05 no_processing         # Town05 + 无处理（基准测试�?
        echo "  $0 town05 denoise15             # Town05 + SwinIR 彩色去噪 (noise=15)"
        echo "  $0 town05 srgan_2x              # Town05 + SRGAN 2x 超分辨率 �?
        echo "  $0 42routes srgan_enhance       # 42 Routes + SRGAN 图像增强"
        echo "  GPU_ID=1 $0 town05 srgan_4x     # Town05 + SRGAN 4x (GPU 1)"
        exit 1
        ;;
esac

# 设置结果保存路径（带时间戳和配置标识�?# 若外部已指定 SAVE_PATH/CHECKPOINT_ENDPOINT（用于断点续跑），则沿用�?TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -z "${SAVE_PATH:-}" ]; then
    export SAVE_PATH="data/eval_with_processor/${RESULT_BASE}_${TIMESTAMP}"
fi
if [ -z "${CHECKPOINT_ENDPOINT:-}" ]; then
    export CHECKPOINT_ENDPOINT="results/with_processor/${RESULT_BASE}_${TIMESTAMP}.json"
fi
EVAL_LOG="${SAVE_PATH}/leaderboard_evaluator.log"

export TEAM_AGENT=leaderboard/team_code/interfuser_agent.py
export TEAM_CONFIG=leaderboard/team_code/interfuser_config.py
export RESUME=${RESUME:-True}

# 创建结果目录
mkdir -p "results/with_processor"
mkdir -p "${SAVE_PATH}"

echo "  �?结果将保存到: ${CHECKPOINT_ENDPOINT}"
echo ""

# ============================================================
# 步骤 4: 检�?CARLA 服务�?# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 步骤 4/5: 检�?CARLA 服务�?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CARLA_READY_TIMEOUT=${CARLA_READY_TIMEOUT:-60}
echo "  �?等待 CARLA ready (timeout: ${CARLA_READY_TIMEOUT}s)"
READY=0
END_TS=$(( $(date +%s) + CARLA_READY_TIMEOUT ))
while [ "$(date +%s)" -lt "${END_TS}" ]; do
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

if [ "${READY}" = "1" ]; then
    echo "  �?CARLA 服务器已连接 (端口 ${PORT})"
    echo ""
else
    echo "  �?警告: CARLA 服务器不可用或无响应 (端口 ${PORT})"
    echo ""
    echo "请在另一个终端运行以下命令启�?CARLA 服务�?"
    echo "  cd ${PROJECT_ROOT}/evaluation_scripts"
    echo "  CUDA_VISIBLE_DEVICES=${CARLA_CUDA_VISIBLE_DEVICES} ./start_carla_server.sh"
    echo ""
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "评估已取消。正在恢复原始文�?.."
        bash "${SCRIPT_DIR}/restore_original_agent.sh" "${BACKUP_DIR}"
        exit 1
    fi
    echo ""
fi

# ============================================================
# 步骤 5: 运行评估
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 步骤 5/5: 运行评估"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "评估配置摘要:"
echo "  �?CARLA GPUs: ${CARLA_CUDA_VISIBLE_DEVICES}"
echo "  �?Python GPUs: ${PY_CUDA_VISIBLE_DEVICES}"
echo "  �?Data Processor GPU ID: ${DATA_PROCESSOR_GPU_ID}"
echo "  �?Traffic Manager Port: ${TM_PORT}"
echo "  �?路线: $ROUTES"
echo "  �?场景: $SCENARIOS"
echo "  �?数据处理: ${CONFIG_TYPE}"
echo "  �?结果: $CHECKPOINT_ENDPOINT"
echo "  �?恢复模式: $RESUME"
echo ""
echo "开始评�?.."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 保存评估元数�?cat > "${SAVE_PATH}/evaluation_metadata.json" << EOF
{
    "timestamp": "${TIMESTAMP}",
    "eval_type": "${EVAL_TYPE}",
    "config_type": "${CONFIG_TYPE}",
    "gpu_id": ${GPU_ID},
    "routes": "${ROUTES}",
    "scenarios": "${SCENARIOS}",
    "checkpoint": "${CHECKPOINT_ENDPOINT}",
    "agent": "interfuser_agent_complete.py",
    "data_processor": "enabled"
}
EOF

# 运行评估（捕获退出码�?set +e
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

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $EVAL_EXIT_CODE -eq 0 ]; then
    echo "�?评估成功完成�?
else
    echo "⚠️  评估结束 (退出码: $EVAL_EXIT_CODE)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================
# 清理和恢�?# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 清理和恢�?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 自动恢复原始文件（不询问�?echo "  �?自动恢复原始文件..."
bash "${SCRIPT_DIR}/restore_original_agent.sh" "${BACKUP_DIR}"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "�?                   🎉 全部完成�?                              �?
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 评估结果:"
echo "  �?JSON 结果: ${CHECKPOINT_ENDPOINT}"
echo "  �?评估数据: ${SAVE_PATH}"
echo "  �?元数�? ${SAVE_PATH}/evaluation_metadata.json"
echo ""
echo "📖 查看结果:"
echo "  bash ${PROJECT_ROOT}/evaluation_scripts/view_results.sh ${CHECKPOINT_ENDPOINT}"
echo ""
echo "🔧 备份位置: ${BACKUP_DIR}"
echo ""

exit $EVAL_EXIT_CODE

