#!/bin/bash
# 诊断信息收集脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "================================"
echo "CARLA Native Enhancement 诊断"
echo "================================"
echo ""

# 系统信息
echo "=== 系统信息 ==="
echo "操作系统: $(uname -s)"
echo "内核版本: $(uname -r)"
echo "架构: $(uname -m)"
echo ""

# GPU 信息
echo "=== GPU 信息 ==="
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,memory.total,driver_version,cuda_version --format=csv,noheader
else
    echo "nvidia-smi 未找到"
fi
echo ""

# Python 环境
echo "=== Python 环境 ==="
echo "Python 版本: $(python --version 2>&1)"
echo "Python 路径: $(which python)"
if [ -n "${CONDA_DEFAULT_ENV:-}" ]; then
    echo "Conda 环境: ${CONDA_DEFAULT_ENV}"
fi
echo ""

# CARLA 信息
echo "=== CARLA 信息 ==="
CARLA_ROOT="${PROJECT_ROOT}/carla"
if [ -f "${CARLA_ROOT}/VERSION" ]; then
    echo "CARLA 版本: $(cat ${CARLA_ROOT}/VERSION)"
else
    echo "CARLA VERSION 文件未找到"
fi

if [ -x "${CARLA_ROOT}/CarlaUE4.sh" ]; then
    echo "CARLA 可执行文件: 存在"
else
    echo "CARLA 可执行文件: 未找到或无执行权限"
fi
echo ""

# 最近的评估
echo "=== 最近的评估 ==="
EVAL_DIR="${PROJECT_ROOT}/data/eval_native"
if [ -d "${EVAL_DIR}" ]; then
    echo "最近 5 次评估:"
    ls -td "${EVAL_DIR}"/town05_* 2>/dev/null | head -5 | while read dir; do
        echo "  - $(basename ${dir})"
        
        # 检查 meta 目录
        META_DIRS=$(find "${dir}" -type d -name "meta" 2>/dev/null)
        if [ -n "${META_DIRS}" ]; then
            for meta_dir in ${META_DIRS}; do
                FILE_COUNT=$(ls -1 "${meta_dir}" 2>/dev/null | wc -l)
                echo "    meta 文件数: ${FILE_COUNT}"
            done
        else
            echo "    meta 目录: 未找到"
        fi
        
        # 检查日志
        if [ -f "${dir}/leaderboard_evaluator.log" ]; then
            ERROR_COUNT=$(grep -c "Error\|ERROR\|Exception\|Traceback" "${dir}/leaderboard_evaluator.log" 2>/dev/null || echo 0)
            echo "    错误数: ${ERROR_COUNT}"
            
            # 显示最后几行
            echo "    最后 3 行日志:"
            tail -3 "${dir}/leaderboard_evaluator.log" 2>/dev/null | sed 's/^/      /'
        fi
        echo ""
    done
else
    echo "评估目录不存在: ${EVAL_DIR}"
fi
echo ""

# 端口占用
echo "=== 端口占用 ==="
echo "CARLA 常用端口 (2000-2002):"
for port in 2000 2001 2002; do
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":${port} "; then
            echo "  端口 ${port}: 占用"
        else
            echo "  端口 ${port}: 空闲"
        fi
    elif command -v ss >/dev/null 2>&1; then
        if ss -tuln 2>/dev/null | grep -q ":${port} "; then
            echo "  端口 ${port}: 占用"
        else
            echo "  端口 ${port}: 空闲"
        fi
    else
        echo "  无法检查端口（netstat/ss 未找到）"
        break
    fi
done
echo ""

# CARLA 进程
echo "=== CARLA 进程 ==="
CARLA_PROCS=$(ps aux | grep -E "CarlaUE4|carla" | grep -v grep || echo "")
if [ -n "${CARLA_PROCS}" ]; then
    echo "${CARLA_PROCS}"
else
    echo "未发现 CARLA 进程"
fi
echo ""

# Python 依赖
echo "=== Python 依赖 ==="
echo "关键包版本:"
python -c "
import sys
packages = ['torch', 'torchvision', 'numpy', 'PIL', 'cv2', 'carla']
for pkg in packages:
    try:
        if pkg == 'PIL':
            import PIL
            print(f'  PIL: {PIL.__version__}')
        elif pkg == 'cv2':
            import cv2
            print(f'  opencv: {cv2.__version__}')
        else:
            mod = __import__(pkg)
            ver = getattr(mod, '__version__', 'unknown')
            print(f'  {pkg}: {ver}')
    except ImportError:
        print(f'  {pkg}: 未安装')
" 2>/dev/null || echo "  无法检查 Python 包"
echo ""

# 磁盘空间
echo "=== 磁盘空间 ==="
df -h "${PROJECT_ROOT}" | tail -1
echo ""

echo "================================"
echo "诊断完成"
echo "================================"
