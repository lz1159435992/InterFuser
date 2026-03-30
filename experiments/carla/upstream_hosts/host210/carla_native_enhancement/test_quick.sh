#!/bin/bash
# 快速测试脚本 - 使用短路线验证配置

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "================================"
echo "CARLA Native Enhancement 快速测试"
echo "================================"
echo ""

# 配置
export NATIVE_ENHANCE=${1:-none}
export AUTO_START_CARLA=1
export EVAL_TIMEOUT=300  # 5 分钟足够测试
export PORT=random
export REPETITIONS=1

# 使用短路线（如果存在）
SHORT_ROUTES="${PROJECT_ROOT}/leaderboard/data/evaluation_routes/routes_town05_short.xml"
if [ ! -f "${SHORT_ROUTES}" ]; then
    echo "⚠ 短路线文件不存在，将使用标准路线"
    SHORT_ROUTES="${PROJECT_ROOT}/leaderboard/data/evaluation_routes/routes_town05_long.xml"
fi

export CUSTOM_ROUTES="${SHORT_ROUTES}"
export CUSTOM_SCENARIOS="${PROJECT_ROOT}/leaderboard/data/scenarios/town05_all_scenarios.json"

echo "配置:"
echo "  NATIVE_ENHANCE: ${NATIVE_ENHANCE}"
echo "  ROUTES: ${CUSTOM_ROUTES}"
echo "  TIMEOUT: ${EVAL_TIMEOUT}s"
echo ""

# 运行评估
bash "${SCRIPT_DIR}/run_evaluation_native.sh" custom "${NATIVE_ENHANCE}"

EXIT_CODE=$?

if [ ${EXIT_CODE} -eq 0 ]; then
    echo ""
    echo "================================"
    echo "✓ 测试成功完成"
    echo "================================"
    
    # 显示结果
    LATEST_EVAL=$(ls -td "${PROJECT_ROOT}"/data/eval_native/custom_* 2>/dev/null | head -1)
    if [ -n "${LATEST_EVAL}" ]; then
        echo ""
        echo "评估目录: ${LATEST_EVAL}"
        
        # 检查 meta 文件
        META_FILES=$(find "${LATEST_EVAL}" -name "*.jpg" -o -name "*.png" 2>/dev/null | wc -l)
        echo "生成的图像: ${META_FILES} 个"
        
        if [ ${META_FILES} -gt 0 ]; then
            echo ""
            echo "✓ Meta 文件已成功生成！"
            echo ""
            echo "查看图像:"
            find "${LATEST_EVAL}" -name "*.jpg" | head -3 | while read img; do
                echo "  ${img}"
            done
        else
            echo ""
            echo "⚠ 警告：未生成 meta 文件"
            echo "请检查日志:"
            echo "  ${LATEST_EVAL}/leaderboard_evaluator.log"
        fi
    fi
else
    echo ""
    echo "================================"
    echo "✗ 测试失败 (退出码: ${EXIT_CODE})"
    echo "================================"
    echo ""
    echo "请运行诊断脚本:"
    echo "  bash ${SCRIPT_DIR}/collect_diagnostics.sh"
fi

exit ${EXIT_CODE}
