#!/bin/bash
#
# 运行剩余 7 个 CARLA 原生增强配置
# Run remaining 7 CARLA native enhancement configurations
#
# 参考 augmentation_seq_method 的 Python 解释器设置
# Reference augmentation_seq_method for Python interpreter setup
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo "CARLA 原生增强实验 - 剩余 7 个配置"
echo "CARLA Native Enhancement - Remaining 7 Configs"
echo "时间 / Time: $(date)"
echo "项目根目录 / Project Root: ${PROJECT_ROOT}"
echo "=========================================="
echo ""

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

# 验证 CARLA egg 是否存在
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

# 配置列表（跳过 none）
# Configuration list (skip none - already completed)
configs=(
    "1:high_fps"
    "1:high_fps,no_noise"
    "2:high_res"
    "2:high_res,no_noise"
    "3:no_noise"
    "3:high_fps,high_res"
    "3:high_fps,high_res,no_noise"
)

echo "将运行以下配置 / Will run the following configurations:"
for i in "${!configs[@]}"; do
    item="${configs[$i]}"
    GPU_ID="${item%%:*}"
    CONFIG="${item#*:}"
    NUM=$((i + 1))
    echo "  [${NUM}/7] GPU ${GPU_ID}: ${CONFIG}"
done
echo ""

# 运行每个配置
# Run each configuration
for i in "${!configs[@]}"; do
    item="${configs[$i]}"
    GPU_ID="${item%%:*}"
    CONFIG="${item#*:}"
    
    NUM=$((i + 1))
    echo "=========================================="
    echo "[${NUM}/7] 启动 / Starting: GPU ${GPU_ID} - ${CONFIG}"
    echo "=========================================="
    
    # 使用相同的 PYTHON_BIN
    # Use the same PYTHON_BIN
    PYTHON_BIN="${PYTHON_BIN}" GPU_ID=${GPU_ID} PORT=random AUTO_START_CARLA=1 \
    bash carla_native_enhancement/run_evaluation_native.sh town05 "${CONFIG}" &
    
    PID=$!
    echo "  ✓ 进程已启动 / Process started, PID: ${PID}"
    echo "  等待 10 秒后启动下一个 / Waiting 10 seconds before next..."
    echo ""
    sleep 10
done

echo ""
echo "=========================================="
echo "所有 7 个配置已启动！"
echo "All 7 configurations started!"
echo "=========================================="
echo ""
echo "GPU 分配 / GPU Allocation:"
echo "  GPU 1: high_fps, high_fps,no_noise"
echo "  GPU 2: high_res, high_res,no_noise"
echo "  GPU 3: no_noise, high_fps,high_res, high_fps,high_res,no_noise"
echo ""
echo "监控命令 / Monitoring commands:"
echo "  watch -n 1 nvidia-smi"
echo "  ps aux | grep CarlaUE4"
echo ""
echo "查看日志 / View logs:"
echo "  ls -lh data/eval_native/"
echo "  tail -f data/eval_native/town05_*/leaderboard_evaluator.log"
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
echo "  cat results/native/town05_*.json"
echo ""
