#!/bin/bash
#
# 清理特定配置的进程，不影响其他实验
# Clean up specific config processes without affecting other experiments
#
# 用法 / Usage:
#   bash cleanup_specific_configs.sh high_fps high_fps,no_noise no_noise
#   bash cleanup_specific_configs.sh high_res
#

set -e

if [ $# -eq 0 ]; then
    echo "用法 / Usage: $0 <config1> [config2] [config3] ..."
    echo ""
    echo "示例 / Examples:"
    echo "  $0 high_fps"
    echo "  $0 high_fps high_fps,no_noise no_noise"
    echo "  $0 high_res high_res,no_noise"
    echo ""
    exit 1
fi

CONFIGS=("$@")

echo "=========================================="
echo "清理特定配置的进程"
echo "Clean up specific config processes"
echo "=========================================="
echo ""
echo "要清理的配置 / Configs to clean:"
for config in "${CONFIGS[@]}"; do
    echo "  - ${config}"
done
echo ""
read -p "确认清理这些配置？(y/N) / Confirm cleanup? (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消 / Cancelled"
    exit 0
fi

echo ""
echo "开始清理 / Starting cleanup..."
echo ""

# 清理每个配置
for config in "${CONFIGS[@]}"; do
    echo "----------------------------------------"
    echo "清理配置 / Cleaning config: ${config}"
    echo "----------------------------------------"
    
    # 转换配置名为文件名格式（用下划线替换逗号）
    config_tag=$(echo "${config}" | tr ',' '_')
    
    # 1. 查找并杀死 Python 评估进程
    echo "1. 查找 Python 评估进程 / Finding Python evaluator processes..."
    PYTHON_PIDS=$(ps aux | grep -E "python.*leaderboard_evaluator.*town05_${config_tag}" | grep -v grep | awk '{print $2}')
    
    if [ -n "${PYTHON_PIDS}" ]; then
        echo "   找到 Python 进程 / Found Python processes: ${PYTHON_PIDS}"
        for pid in ${PYTHON_PIDS}; do
            echo "   杀死进程 / Killing process: ${pid}"
            kill -9 ${pid} 2>/dev/null || true
        done
    else
        echo "   未找到 Python 进程 / No Python processes found"
    fi
    
    # 2. 查找并杀死对应的 CARLA 服务器
    echo "2. 查找 CARLA 服务器进程 / Finding CARLA server processes..."
    
    # 从 checkpoint 文件中获取端口号
    CHECKPOINT_FILES=$(ls -t results/native/town05_${config_tag}_*.json 2>/dev/null || true)
    
    if [ -n "${CHECKPOINT_FILES}" ]; then
        for checkpoint in ${CHECKPOINT_FILES}; do
            # 从日志目录中查找端口
            TIMESTAMP=$(basename "${checkpoint}" .json | sed "s/town05_${config_tag}_//")
            LOG_DIR="data/eval_native/town05_${config_tag}_${TIMESTAMP}"
            
            if [ -d "${LOG_DIR}" ]; then
                # 从日志中提取端口号
                PORT=$(grep -oP "world-port=\K\d+" "${LOG_DIR}/leaderboard_evaluator.log" 2>/dev/null | head -1 || echo "")
                
                if [ -n "${PORT}" ]; then
                    echo "   找到端口 / Found port: ${PORT}"
                    
                    # 查找使用该端口的 CARLA 进程
                    CARLA_PIDS=$(ps aux | grep -E "CarlaUE4.*world-port=${PORT}" | grep -v grep | awk '{print $2}')
                    
                    if [ -n "${CARLA_PIDS}" ]; then
                        echo "   找到 CARLA 进程 / Found CARLA processes: ${CARLA_PIDS}"
                        for pid in ${CARLA_PIDS}; do
                            echo "   杀死进程 / Killing process: ${pid}"
                            kill -9 ${pid} 2>/dev/null || true
                        done
                    fi
                fi
            fi
        done
    else
        echo "   未找到 checkpoint 文件 / No checkpoint files found"
    fi
    
    # 3. 清理可能的孤儿 CARLA 进程（通过 checkpoint 文件名匹配）
    echo "3. 清理孤儿进程 / Cleaning orphan processes..."
    ORPHAN_CARLA=$(ps aux | grep "CarlaUE4" | grep -v grep | while read line; do
        pid=$(echo "$line" | awk '{print $2}')
        port=$(echo "$line" | grep -oP "world-port=\K\d+" || echo "")
        
        if [ -n "${port}" ]; then
            # 检查是否有对应的 Python 进程使用这个端口
            python_count=$(ps aux | grep -E "python.*leaderboard.*port=${port}" | grep -v grep | wc -l)
            
            if [ "${python_count}" -eq 0 ]; then
                # 检查这个端口是否属于我们要清理的配置
                for cfg in "${CONFIGS[@]}"; do
                    cfg_tag=$(echo "${cfg}" | tr ',' '_')
                    log_count=$(ls -d data/eval_native/town05_${cfg_tag}_* 2>/dev/null | xargs -I {} grep -l "world-port=${port}" {}/leaderboard_evaluator.log 2>/dev/null | wc -l)
                    
                    if [ "${log_count}" -gt 0 ]; then
                        echo "${pid}"
                        break
                    fi
                done
            fi
        fi
    done)
    
    if [ -n "${ORPHAN_CARLA}" ]; then
        echo "   找到孤儿 CARLA 进程 / Found orphan CARLA processes: ${ORPHAN_CARLA}"
        for pid in ${ORPHAN_CARLA}; do
            echo "   杀死进程 / Killing process: ${pid}"
            kill -9 ${pid} 2>/dev/null || true
        done
    else
        echo "   未找到孤儿进程 / No orphan processes found"
    fi
    
    echo "✓ 配置清理完成 / Config cleanup completed: ${config}"
    echo ""
done

echo "=========================================="
echo "所有指定配置已清理 / All specified configs cleaned"
echo "=========================================="
echo ""

# 显示剩余的进程
echo "剩余的 CARLA 和评估进程 / Remaining CARLA and evaluator processes:"
echo ""
ps aux | grep -E "CarlaUE4|python.*leaderboard" | grep -v grep | grep -v "cleanup_specific_configs" || echo "无 / None"
echo ""

# 显示 GPU 使用情况
echo "GPU 使用情况 / GPU usage:"
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader,nounits | \
    awk -F', ' '{printf "GPU %s: %s / %s MB (%.1f%%)\n", $1, $3, $4, ($3/$4)*100}'
echo ""
