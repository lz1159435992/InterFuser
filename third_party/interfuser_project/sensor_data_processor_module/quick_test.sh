#!/bin/bash
# 快速测试脚�?- 测试前几个用�?# 
# 此脚本用于验证带数据处理器的 agent 是否能正常工�?# 只运�?3 条短路线，快速验证功�?
set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "�?       🧪 快速测试：带数据处理器�?Agent                       �?
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# 配置
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/path/to/project"
TEAM_CODE_DIR="${PROJECT_ROOT}/leaderboard/team_code"
BACKUP_DIR="${SCRIPT_DIR}/.backup_test_$(date +%Y%m%d_%H%M%S)"

# 测试配置
TEST_CONFIG=${1:-fast}  # fast, moderate, debug
GPU_ID=${GPU_ID:-0}

echo "📋 测试配置:"
echo "  - 测试模式: $TEST_CONFIG"
echo "  - GPU ID: $GPU_ID"
echo "  - 项目根目�? $PROJECT_ROOT"
echo "  - 测试路线: 3 条短路线"
echo ""

# ============================================================
# 步骤 1: 备份原始文件
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 步骤 1/6: 备份原始文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p "${BACKUP_DIR}"

if [ -f "${TEAM_CODE_DIR}/interfuser_agent.py" ]; then
    echo "  �?备份 interfuser_agent.py"
    cp "${TEAM_CODE_DIR}/interfuser_agent.py" "${BACKUP_DIR}/interfuser_agent.py.bak"
fi

if [ -f "${TEAM_CODE_DIR}/data_processor.py" ]; then
    cp "${TEAM_CODE_DIR}/data_processor.py" "${BACKUP_DIR}/data_processor.py.bak"
fi

if [ -f "${TEAM_CODE_DIR}/data_processor_config.py" ]; then
    cp "${TEAM_CODE_DIR}/data_processor_config.py" "${BACKUP_DIR}/data_processor_config.py.bak"
fi

echo "  �?备份目录: ${BACKUP_DIR}"
echo ""

# ============================================================
# 步骤 2: 部署数据处理�?# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 步骤 2/6: 部署数据处理�?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 复制核心文件
echo "  �?复制 data_processor.py"
cp "${SCRIPT_DIR}/data_processor.py" "${TEAM_CODE_DIR}/data_processor.py"

echo "  �?复制 data_processor_config.py"
cp "${SCRIPT_DIR}/data_processor_config.py" "${TEAM_CODE_DIR}/data_processor_config.py"

# 根据测试模式配置
case $TEST_CONFIG in
    fast)
        echo "  �?测试模式: 快速（轻度噪声 + 优化性能�?
        # 创建快速配�?        cat > "${TEAM_CODE_DIR}/data_processor_config_test.py" << 'EOF'
import numpy as np

# 快速测试配�?CONFIG_FAST_TEST = {
    "enabled": True,
    "save_processed_images": False,  # 关闭保存以提升性能
    "save_path": "",
    "log_level": "INFO",  # 看到一些输�?    
    "rgb_effects": {
        "add_gaussian_noise": {"enabled": True, "mean": 0, "std": 5},
        "brightness": {"enabled": False},
        "contrast": {"enabled": False},
        "saturation": {"enabled": False},
        "gaussian_blur": {"enabled": False},
        "pixel_dropout": {"enabled": False},
        "color_shift": {"enabled": False},
    },
    "lidar_effects": {
        "add_noise": {"enabled": True, "mean": 0, "std": 0.05},
        "dropout": {"enabled": False},
        "distance_limit": {"enabled": False},
        "intensity_noise": {"enabled": False},
    },
    "gps_effects": {
        "add_drift": {"enabled": True, "mean": 0, "std_lat": 0.00005, "std_lon": 0.00005},
        "random_jump": {"enabled": False},
    },
    "other_effects": {
        "speed_error": {"enabled": True, "mean": 0, "std": 0.2, "bias": 0.0},
        "compass_error": {"enabled": True, "mean": 0, "std": np.deg2rad(1)},
    },
}

ACTIVE_CONFIG = CONFIG_FAST_TEST
EOF
        cp "${TEAM_CODE_DIR}/data_processor_config_test.py" "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    
    moderate)
        echo "  �?测试模式: 中度噪声"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_MODERATE_NOISE/' "${TEAM_CODE_DIR}/data_processor_config.py"
        sed -i 's/"save_processed_images": True/"save_processed_images": False/' "${TEAM_CODE_DIR}/data_processor_config.py"
        sed -i 's/"log_level": "DEBUG"/"log_level": "INFO"/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    
    debug)
        echo "  �?测试模式: 调试（保存处理后的图像）"
        sed -i 's/^ACTIVE_CONFIG = .*/ACTIVE_CONFIG = CONFIG_MODERATE_NOISE/' "${TEAM_CODE_DIR}/data_processor_config.py"
        sed -i 's/"save_processed_images": False/"save_processed_images": True/' "${TEAM_CODE_DIR}/data_processor_config.py"
        sed -i 's/"log_level": "ERROR"/"log_level": "DEBUG"/' "${TEAM_CODE_DIR}/data_processor_config.py"
        ;;
    
    *)
        echo "  �?错误: 未知的测试模�?'$TEST_CONFIG'"
        echo "    支持的模�? fast, moderate, debug"
        exit 1
        ;;
esac

# 部署完整�?agent
echo "  �?部署 interfuser_agent_complete.py"
cp "${SCRIPT_DIR}/interfuser_agent_complete.py" "${TEAM_CODE_DIR}/interfuser_agent.py"

echo "  �?数据处理器部署完�?
echo ""

# ============================================================
# 步骤 3: 设置环境
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  步骤 3/6: 设置环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

source /opt/conda/etc/profile.d/conda.sh
conda activate interfuser
echo "  �?激�?conda 环境: interfuser"

cd "${PROJECT_ROOT}"

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

# 测试路线
export ROUTES="${SCRIPT_DIR}/test_routes_short.xml"
export SCENARIOS=leaderboard/data/scenarios/town05_all_scenarios.json

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
export CHECKPOINT_ENDPOINT="results/test/quick_test_${TEST_CONFIG}_${TIMESTAMP}.json"
export SAVE_PATH="data/test/quick_test_${TEST_CONFIG}_${TIMESTAMP}"

export TEAM_AGENT=leaderboard/team_code/interfuser_agent.py
export TEAM_CONFIG=leaderboard/team_code/interfuser_config.py
export RESUME=False

mkdir -p "results/test"
mkdir -p "${SAVE_PATH}"

echo "  �?测试路线: ${ROUTES}"
echo "  �?结果文件: ${CHECKPOINT_ENDPOINT}"
echo ""

# ============================================================
# 步骤 4: 检�?CARLA 服务�?# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 步骤 4/6: 检�?CARLA 服务�?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

timeout 5 bash -c "echo > /dev/tcp/localhost/2000" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  �?CARLA 服务器已连接 (端口 2000)"
    echo ""
else
    echo "  �?警告: 无法连接�?CARLA 服务�?(端口 2000)"
    echo ""
    echo "请在另一个终端运�?"
    echo "  cd /path/to/project/evaluation_scripts"
    echo "  ./start_carla_server.sh"
    echo ""
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "测试已取消。正在恢复原始文�?.."
        bash "${SCRIPT_DIR}/restore_original_agent.sh" "${BACKUP_DIR}"
        exit 1
    fi
    echo ""
fi

# ============================================================
# 步骤 5: 运行快速测�?# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 步骤 5/6: 运行快速测�?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "测试配置:"
echo "  �?GPU: $CUDA_VISIBLE_DEVICES"
echo "  �?路线�? 3 �?
echo "  �?测试模式: ${TEST_CONFIG}"
echo "  �?场景: Town05"
echo ""
echo "开始测�?.."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 保存测试元数�?cat > "${SAVE_PATH}/test_metadata.json" << EOF
{
    "timestamp": "${TIMESTAMP}",
    "test_mode": "${TEST_CONFIG}",
    "gpu_id": ${GPU_ID},
    "routes": "${ROUTES}",
    "num_routes": 3,
    "scenarios": "${SCENARIOS}",
    "checkpoint": "${CHECKPOINT_ENDPOINT}",
    "data_processor": "enabled"
}
EOF

# 运行测试
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
    --trafficManagerPort=${TM_PORT}

TEST_EXIT_CODE=$?
set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "�?测试成功完成�?
else
    echo "⚠️  测试结束 (退出码: $TEST_EXIT_CODE)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================
# 步骤 6: 显示结果
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 步骤 6/6: 测试结果"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "${CHECKPOINT_ENDPOINT}" ]; then
    echo "📄 结果文件已生�?"
    echo "  �?${CHECKPOINT_ENDPOINT}"
    echo ""
    
    # 快速分析结�?    echo "🔍 快速分�?"
    python3 << EOF
import json
import sys

try:
    with open("${CHECKPOINT_ENDPOINT}", 'r') as f:
        data = json.load(f)
    
    if '_checkpoint' in data and 'records' in data['_checkpoint']:
        records = data['_checkpoint']['records']
        total = len(records)
        completed = sum(1 for r in records if r.get('status') == 'Completed')
        
        print(f"  �?总路线数: {total}")
        print(f"  �?完成�? {completed}")
        print(f"  �?成功�? {completed/total*100:.1f}%")
        
        if records:
            avg_score = sum(r['scores'].get('score_route', 0) for r in records) / len(records)
            print(f"  �?平均分数: {avg_score:.2f}")
        
        print("")
        print("  详细路线结果:")
        for i, r in enumerate(records):
            status = r.get('status', 'Unknown')
            score = r['scores'].get('score_route', 0)
            icon = "�? if status == 'Completed' else "�?
            print(f"    {icon} 路线 {i}: {status} (分数: {score:.2f})")
    else:
        print("  ⚠️  结果数据格式异常")
except Exception as e:
    print(f"  ⚠️  无法解析结果: {e}")
EOF
else
    echo "  ⚠️  未找到结果文�?
fi

echo ""
echo "📂 测试数据保存位置:"
echo "  �?JSON 结果: ${CHECKPOINT_ENDPOINT}"
echo "  �?测试数据: ${SAVE_PATH}"
echo "  �?备份文件: ${BACKUP_DIR}"
echo ""

# ============================================================
# 恢复选项
# ============================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 恢复选项"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 自动恢复原始文件（不询问�?echo "  �?自动恢复原始文件..."
bash "${SCRIPT_DIR}/restore_original_agent.sh" "${BACKUP_DIR}"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "�?                 🎉 测试完成�?                                �?
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📖 查看详细结果:"
echo "  python3 ${SCRIPT_DIR}/analyze_results.py ${CHECKPOINT_ENDPOINT}"
echo ""

exit $TEST_EXIT_CODE

