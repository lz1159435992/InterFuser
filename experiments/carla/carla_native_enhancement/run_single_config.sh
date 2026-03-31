#!/bin/bash
#
# 运行单个 CARLA 原生增强配置
# 用法: ./run_single_config.sh <GPU_ID> <CONFIG>
# 示例: ./run_single_config.sh 1 high_fps
#

set -e

if [ $# -lt 2 ]; then
    echo "用法: $0 <GPU_ID> <CONFIG>"
    echo ""
    echo "示例:"
    echo "  $0 1 high_fps"
    echo "  $0 2 high_res"
    echo "  $0 3 high_fps,high_res,no_noise"
    echo ""
    echo "可用配置:"
    echo "  - none"
    echo "  - high_fps"
    echo "  - high_res"
    echo "  - no_noise"
    echo "  - high_fps,high_res"
    echo "  - high_fps,no_noise"
    echo "  - high_res,no_noise"
    echo "  - high_fps,high_res,no_noise"
    exit 1
fi

GPU_ID=$1
CONFIG=$2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo "CARLA 原生增强实验 - 单配置运�?
echo "=========================================="
echo "GPU ID: ${GPU_ID}"
echo "配置: ${CONFIG}"
echo "时间: $(date)"
echo "项目根目�? ${PROJECT_ROOT}"
echo ""

# 切换到项目根目录
cd "${PROJECT_ROOT}"

# 激�?conda 环境（参�?augmentation_seq_method�?CONDA_ENV_NAME=${CONDA_ENV_NAME:-interfuser}
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

# 设置 Python 解释�?PYTHON_BIN=${PYTHON_BIN:-python3}
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    PYTHON_BIN=python3
fi

# 检�?Python 版本
PY_VER=$(${PYTHON_BIN} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
echo "Python 解释�? ${PYTHON_BIN}"
echo "Python 版本: ${PY_VER}"

# 验证 CARLA egg 是否存在
CARLA_ROOT="${PROJECT_ROOT}/carla"
CARLA_EGG=""
if [ "${PY_VER}" = "3.7" ]; then
    CARLA_EGG="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg"
elif [ "${PY_VER}" = "2.7" ]; then
    CARLA_EGG="${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py2.7-linux-x86_64.egg"
fi

if [ -z "${CARLA_EGG}" ] || [ ! -f "${CARLA_EGG}" ]; then
    echo "错误：CARLA PythonAPI egg 不可用，Python 版本: ${PY_VER}" >&2
    echo "需�?Python 3.7 �?2.7" >&2
    echo ""
    echo "提示: 激�?interfuser conda 环境"
    echo "Example: conda activate interfuser && bash $0"
    exit 1
fi

echo "CARLA egg: ${CARLA_EGG}"
echo "�?环境验证通过"
echo ""

# 运行评估
echo "启动评估..."
PYTHON_BIN="${PYTHON_BIN}" GPU_ID=${GPU_ID} PORT=random AUTO_START_CARLA=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 "${CONFIG}"

echo ""
echo "评估完成�?
