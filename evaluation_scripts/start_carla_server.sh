#!/bin/bash
# CARLA 服务器启动脚本

echo "================================================"
echo "    启动 CARLA 服务器 (端口: 2000)"
echo "================================================"
echo ""
echo "提示: 服务器启动需要约 1-2 分钟"
echo "      看到 'Waiting for the client...' 表示启动成功"
echo "      按 Ctrl+C 停止服务器"
echo ""

cd /home/nju/InterFuser

# 设置 GPU (可选择 GPU 0-7)
GPU_ID=${1:-0}
echo "使用 GPU: $GPU_ID"
echo ""

# 启动 CARLA 服务器
CUDA_VISIBLE_DEVICES=$GPU_ID ./carla/CarlaUE4.sh --world-port=2000 -opengl

