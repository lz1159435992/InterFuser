#!/bin/bash
# InterFuser 带数据处理器的评估脚本
# 
# 此脚本会：
# 1. 自动部署数据处理器模块
# 2. 使用带处理器的 agent 运行评估
# 3. 将结果保存到独立目录
# 4. 评估结束后自动恢复原始文件

set -e  # 遇到错误立即退出

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     InterFuser 带数据处理器的评估脚本                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# 配置部分
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/nju/InterFuser"
TEAM_CODE_DIR="${PROJECT_ROOT}/leaderboard/team_code"
BACKUP_DIR="${SCRIPT_DIR}/.backup_$(date +%Y%m%d_%H%M%S)"

# 评估参数
EVAL_TYPE=${1:-town05}
GPU_ID=${GPU_ID:-0}
CONFIG_TYPE=${2:-no_processing}  # 配置类型: no_processing, denoise15, denoise25, denoise50, sr2x, sr4x, jpeg_repair, srgan_2x, srgan_enhance, srgan_4x, custom

echo "📋 评估配置:"
echo "  - 评估类型: $EVAL_TYPE"
echo "  - GPU ID: $GPU_ID"
echo "  - 数据处理配置: $CONFIG_TYPE"
echo "  - 项目根目录: $PROJECT_ROOT"
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
    echo "  ✓ 备份 interfuser_agent.py"
    cp "${TEAM_CODE_DIR}/interfuser_agent.py" "${BACKUP_DIR}/interfuser_agent.py.bak"
    BACKUP_AGENT=1
else
    echo "  ℹ interfuser_agent.py 不存在，跳过备份"
    BACKUP_AGENT=0
fi

# 备份数据处理器文件（如果存在）
if [ -f "${TEAM_CODE_DIR}/data_processor.py" ]; then
    echo "  ✓ 备份 data_processor.py"
    cp "${TEAM_CODE_DIR}/data_processor.py" "${BACKUP_DIR}/data_processor.py.bak"
fi

if [ -f "${TEAM_CODE_DIR}/data_processor_config.py" ]; then
    echo "  ✓ 备份 data_processor_config.py"
    cp "${TEAM_CODE_DIR}/data_processor_config.py" "${BACKUP_DIR}/data_processor_config.py.bak"
fi

echo "  ✓ 备份目录: ${BACKUP_DIR}"
echo ""

# ============================================================
# 步骤 2: 部署数据处理器
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 步骤 2/5: 部署数据处理器模块"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 复制数据处理器核心文件
echo "  → 复制 data_processor.py"
cp "${SCRIPT_DIR}/data_processor.py" "${TEAM_CODE_DIR}/data_processor.py"

echo "  → 复制 data_processor_config.py"
cp "${SCRIPT_DIR}/data_processor_config.py" "${TEAM_CODE_DIR}/data_processor_config.py"

# 根据配置类型修改 ACTIVE_CONFIG
case $CONFIG_TYPE in
    no_processing)
        echo "  → 配置类型: 无处理 (CONFIG_NO_PROCESSING)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_NO_PROCESSING/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    denoise15)
        echo "  → 配置类型: 彩色去噪 noise=15 (CONFIG_COLOR_DENOISE)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_COLOR_DENOISE/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    denoise25)
        echo "  → 配置类型: 彩色去噪 noise=25 (CONFIG_COLOR_DENOISE_25)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_COLOR_DENOISE_25/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    denoise50)
        echo "  → 配置类型: 彩色去噪 noise=50 (CONFIG_COLOR_DENOISE_50)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_COLOR_DENOISE_50/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    sr2x)
        echo "  → 配置类型: 2x 超分辨率 (CONFIG_SR_2X)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_SR_2X/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    sr4x)
        echo "  → 配置类型: 4x 超分辨率 (CONFIG_SR_4X)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_SR_4X/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    jpeg_repair)
        echo "  → 配置类型: JPEG 修复 (CONFIG_JPEG_REPAIR)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_JPEG_REPAIR/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    srgan_2x)
        echo "  → 配置类型: SRGAN 2x 超分辨率 (CONFIG_SRGAN_2X) - 与原始 test.py 一致"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_SRGAN_2X/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    srgan_enhance)
        echo "  → 配置类型: SRGAN 图像增强 1x (CONFIG_SRGAN_ENHANCE)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_SRGAN_ENHANCE/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    srgan_4x)
        echo "  → 配置类型: SRGAN 4x 超分辨率 (CONFIG_SRGAN_4X)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_SRGAN_4X/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    custom)
        echo "  → 配置类型: 自定义配置 (DATA_PROCESSOR_CONFIG)"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    *)
        echo "  ✗ 错误: 未知的配置类型 '$CONFIG_TYPE'"
        echo ""
        echo "支持的类型:"
        echo "  【无处理】"
        echo "    no_processing          - 无处理"
        echo ""
        echo "  【SwinIR】"
        echo "    denoise15              - 彩色去噪 noise=15"
        echo "    denoise25              - 彩色去噪 noise=25"
        echo "    denoise50              - 彩色去噪 noise=50"
        echo "    sr2x                   - SwinIR 2x 超分辨率"
        echo "    sr4x                   - SwinIR 4x 超分辨率"
        echo "    jpeg_repair            - JPEG 修复"
        echo ""
        echo "  【SRGAN】"
        echo "    srgan_2x               - SRGAN 2x 超分辨率（与原始 test.py 一致）⭐"
        echo "    srgan_enhance          - SRGAN 图像增强 1x"
        echo "    srgan_4x               - SRGAN 4x 超分辨率"
        echo ""
        echo "  【自定义】"
        echo "    custom                 - 自定义配置"
        echo ""
        exit 1
        ;;
esac

# 复制完整版 agent
echo "  → 部署 interfuser_agent_complete.py 为 interfuser_agent.py"
cp "${SCRIPT_DIR}/interfuser_agent_complete.py" "${TEAM_CODE_DIR}/interfuser_agent.py"

echo "  ✓ 数据处理器模块部署完成"
echo ""

# ============================================================
# 步骤 3: 设置环境变量
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  步骤 3/5: 设置环境变量"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 激活 conda 环境
source /home/nju/anaconda2/etc/profile.d/conda.sh
conda activate interfuser
echo "  ✓ 激活 conda 环境: interfuser"

# 切换到项目根目录
cd "${PROJECT_ROOT}"

# 设置基本环境变量
export CUDA_VISIBLE_DEVICES=${GPU_ID}
export CARLA_ROOT=${PROJECT_ROOT}/carla
export CARLA_SERVER=${CARLA_ROOT}/CarlaUE4.sh
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg
export PYTHONPATH=$PYTHONPATH:leaderboard
export PYTHONPATH=$PYTHONPATH:leaderboard/team_code
export PYTHONPATH=$PYTHONPATH:scenario_runner

export LEADERBOARD_ROOT=leaderboard
export CHALLENGE_TRACK_CODENAME=SENSORS
export PORT=2000
export TM_PORT=2500
export DEBUG_CHALLENGE=0
export REPETITIONS=1

# 根据评估类型设置路线和结果路径
case $EVAL_TYPE in
    town05)
        echo "  ✓ 评估类型: Town05 Long Benchmark"
        export ROUTES=leaderboard/data/evaluation_routes/routes_town05_long.xml
        export SCENARIOS=leaderboard/data/scenarios/town05_all_scenarios.json
        RESULT_BASE="town05_${CONFIG_TYPE}"
        ;;
    42routes)
        echo "  ✓ 评估类型: CARLA 42 Routes Benchmark"
        export ROUTES=leaderboard/data/42routes/42routes.xml
        export SCENARIOS=leaderboard/data/42routes/42scenarios.json
        RESULT_BASE="42routes_${CONFIG_TYPE}"
        ;;
    custom)
        echo "  ✓ 评估类型: 自定义路线"
        export ROUTES=${CUSTOM_ROUTES:-leaderboard/data/evaluation_routes/routes_town05_long.xml}
        export SCENARIOS=${CUSTOM_SCENARIOS:-leaderboard/data/scenarios/town05_all_scenarios.json}
        RESULT_BASE="custom_${CONFIG_TYPE}"
        ;;
    *)
        echo "  ✗ 错误: 未知的评估类型 '$EVAL_TYPE'"
        echo ""
        echo "用法: $0 [评估类型] [配置类型]"
        echo ""
        echo "评估类型: town05 | 42routes | custom"
        echo ""
        echo "配置类型:"
        echo "  【无处理】     no_processing"
        echo "  【SwinIR】     denoise15 | denoise25 | denoise50 | sr2x | sr4x | jpeg_repair"
        echo "  【SRGAN】      srgan_2x | srgan_enhance | srgan_4x"
        echo "  【自定义】     custom"
        echo ""
        echo "示例:"
        echo "  $0 town05 no_processing         # Town05 + 无处理（基准测试）"
        echo "  $0 town05 denoise15             # Town05 + SwinIR 彩色去噪 (noise=15)"
        echo "  $0 town05 srgan_2x              # Town05 + SRGAN 2x 超分辨率 ⭐"
        echo "  $0 42routes srgan_enhance       # 42 Routes + SRGAN 图像增强"
        echo "  GPU_ID=1 $0 town05 srgan_4x     # Town05 + SRGAN 4x (GPU 1)"
        exit 1
        ;;
esac

# 设置结果保存路径（带时间戳和配置标识）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
export CHECKPOINT_ENDPOINT="results/with_processor/${RESULT_BASE}_${TIMESTAMP}.json"
export SAVE_PATH="data/eval_with_processor/${RESULT_BASE}_${TIMESTAMP}"
EVAL_LOG="${SAVE_PATH}/leaderboard_evaluator.log"

export TEAM_AGENT=leaderboard/team_code/interfuser_agent.py
export TEAM_CONFIG=leaderboard/team_code/interfuser_config.py
export RESUME=${RESUME:-True}

# 创建结果目录
mkdir -p "results/with_processor"
mkdir -p "${SAVE_PATH}"

echo "  ✓ 结果将保存到: ${CHECKPOINT_ENDPOINT}"
echo ""

# ============================================================
# 步骤 4: 检查 CARLA 服务器
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 步骤 4/5: 检查 CARLA 服务器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

timeout 5 bash -c "echo > /dev/tcp/localhost/2000" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✓ CARLA 服务器已连接 (端口 2000)"
    echo ""
else
    echo "  ✗ 警告: 无法连接到 CARLA 服务器 (端口 2000)"
    echo ""
    echo "请在另一个终端运行以下命令启动 CARLA 服务器:"
    echo "  cd /home/nju/InterFuser/evaluation_scripts"
    echo "  ./start_carla_server.sh"
    echo ""
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "评估已取消。正在恢复原始文件..."
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
echo "  • GPU: $CUDA_VISIBLE_DEVICES"
echo "  • 路线: $ROUTES"
echo "  • 场景: $SCENARIOS"
echo "  • 数据处理: ${CONFIG_TYPE}"
echo "  • 结果: $CHECKPOINT_ENDPOINT"
echo "  • 恢复模式: $RESUME"
echo ""
echo "开始评估..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 保存评估元数据
cat > "${SAVE_PATH}/evaluation_metadata.json" << EOF
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

# 运行评估（捕获退出码）
set +e
python3 ${LEADERBOARD_ROOT}/leaderboard/leaderboard_evaluator.py \
    --scenarios=${SCENARIOS}  \
    --routes=${ROUTES} \
    --repetitions=${REPETITIONS} \
    --track=${CHALLENGE_TRACK_CODENAME} \
    --checkpoint=${CHECKPOINT_ENDPOINT} \
    --agent=${TEAM_AGENT} \
    --agent-config=${TEAM_CONFIG} \
    --debug=${DEBUG_CHALLENGE} \
    --resume=${RESUME} \
    --port=${PORT} \
    --trafficManagerPort=${TM_PORT} \
    2>&1 | tee "${EVAL_LOG}"

EVAL_EXIT_CODE=${PIPESTATUS[0]}
set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $EVAL_EXIT_CODE -eq 0 ]; then
    echo "✅ 评估成功完成！"
else
    echo "⚠️  评估结束 (退出码: $EVAL_EXIT_CODE)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================
# 清理和恢复
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 清理和恢复"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 自动恢复原始文件（不询问）
echo "  → 自动恢复原始文件..."
bash "${SCRIPT_DIR}/restore_original_agent.sh" "${BACKUP_DIR}"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 全部完成！                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 评估结果:"
echo "  • JSON 结果: ${CHECKPOINT_ENDPOINT}"
echo "  • 评估数据: ${SAVE_PATH}"
echo "  • 元数据: ${SAVE_PATH}/evaluation_metadata.json"
echo ""
echo "📖 查看结果:"
echo "  bash /home/nju/InterFuser/evaluation_scripts/view_results.sh ${CHECKPOINT_ENDPOINT}"
echo ""
echo "🔧 备份位置: ${BACKUP_DIR}"
echo ""

exit $EVAL_EXIT_CODE

