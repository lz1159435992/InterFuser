#!/bin/bash
# CARLA 服务器启动脚本

echo "================================================"
PORT=${2:-${PORT:-2000}}
echo "    启动 CARLA 服务器 (端口: ${PORT})"
echo "================================================"
echo ""
echo "提示: 服务器启动需要约 1-2 分钟"
echo "      看到 'Waiting for the client...' 表示启动成功"
echo "      按 Ctrl+C 停止服务器"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# 设置 GPU (可选择 GPU 0-7)
GPU_ID=${1:-0}
echo "使用 GPU: $GPU_ID"
echo ""

# 启动 CARLA 服务器
CUDA_VISIBLE_DEVICES=$GPU_ID "${PROJECT_ROOT}/carla/CarlaUE4.sh" --world-port=${PORT} -opengl
