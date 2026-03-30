#!/bin/bash
#
# 快速清理 native 配置的进程
# Quick cleanup of native config processes
#
# 用法 / Usage:
#   bash cleanup_native_configs.sh                    # 交互式选择
#   bash cleanup_native_configs.sh high_fps           # 清理单个配置
#   bash cleanup_native_configs.sh high_fps no_noise  # 清理多个配置
#

echo "=========================================="
echo "清理 Native 配置进程"
echo "Clean up Native Config Processes"
echo "=========================================="
echo ""

# 如果没有参数，显示当前运行的 native 配置
if [ $# -eq 0 ]; then
    echo "当前运行的 native 配置 / Currently running native configs:"
    echo ""
    
    ps aux | grep -E "python.*eval_native.*leaderboard_evaluator" | grep -v grep | while read line; do
        pid=$(echo "$line" | awk '{print $2}')
        config=$(echo "$line" | grep -oP "eval_native/town05_\K[^_/]+" || echo "unknown")
        port=$(echo "$line" | grep -oP "port=\K\d+" || echo "unknown")
        checkpoint=$(echo "$line" | grep -oP "checkpoint=\K[^ ]+" || echo "unknown")
        
        echo "  配置 / Config: ${config}"
        echo "    Python PID: ${pid}"
        echo "    端口 / Port: ${port}"
        echo "    Checkpoint: ${checkpoint}"
        echo ""
    done
    
    echo "用法 / Usage:"
    echo "  $0 <config1> [config2] ..."
    echo ""
    echo "示例 / Examples:"
    echo "  $0 high_fps"
    echo "  $0 high_fps high_fps,no_noise no_noise"
    echo ""
    exit 0
fi

CONFIGS=("$@")

echo "要清理的配置 / Configs to clean:"
for config in "${CONFIGS[@]}"; do
    echo "  - ${config}"
done
echo ""

# 清理每个配置
for config in "${CONFIGS[@]}"; do
    echo "----------------------------------------"
    echo "清理 / Cleaning: ${config}"
    echo "----------------------------------------"
    
    # 转换配置名（逗号替换为下划线）
    config_pattern=$(echo "${config}" | tr ',' '_')
    
    # 1. 查找并杀死 Python 进程
    echo "查找 Python 进程 / Finding Python processes..."
    PYTHON_PIDS=$(ps aux | grep -E "python.*eval_native/town05_${config_pattern}" | grep -v grep | awk '{print $2}')
    
    if [ -n "${PYTHON_PIDS}" ]; then
        echo "找到 Python 进程 / Found Python PIDs: ${PYTHON_PIDS}"
        for pid in ${PYTHON_PIDS}; do
            # 获取端口号
            PORT=$(ps -p ${pid} -o args= | grep -oP "port=\K\d+" || echo "")
            echo "  杀死 Python PID ${pid} (端口 / port: ${PORT})"
            kill -9 ${pid} 2>/dev/null || true
            
            # 如果找到端口，杀死对应的 CARLA
            if [ -n "${PORT}" ]; then
                sleep 1
                CARLA_PIDS=$(ps aux | grep -E "CarlaUE4.*world-port=${PORT}" | grep -v grep | awk '{print $2}')
                if [ -n "${CARLA_PIDS}" ]; then
                    echo "  杀死 CARLA PID ${CARLA_PIDS} (端口 / port: ${PORT})"
                    kill -9 ${CARLA_PIDS} 2>/dev/null || true
                fi
            fi
        done
        echo "✓ 已清理 / Cleaned: ${config}"
    else
        echo "未找到进程 / No processes found for: ${config}"
    fi
    echo ""
done

echo "=========================================="
echo "清理完成 / Cleanup completed"
echo "=========================================="
echo ""

# 显示剩余的 native 进程
echo "剩余的 native 进程 / Remaining native processes:"
REMAINING=$(ps aux | grep -E "python.*eval_native.*leaderboard_evaluator" | grep -v grep | wc -l)
if [ "${REMAINING}" -gt 0 ]; then
    ps aux | grep -E "python.*eval_native.*leaderboard_evaluator" | grep -v grep | while read line; do
        pid=$(echo "$line" | awk '{print $2}')
        config=$(echo "$line" | grep -oP "eval_native/town05_\K[^_/]+" || echo "unknown")
        echo "  ${config} (PID: ${pid})"
    done
else
    echo "  无 / None"
fi
echo ""

# 显示 GPU 使用
echo "GPU 使用情况 / GPU usage:"
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader,nounits | \
    awk -F', ' '{printf "  GPU %s: %s / %s MB (%.1f%%)\n", $1, $2, $3, ($2/$3)*100}'
echo ""
