#!/bin/bash
# InterFuser 评估脚本

echo "================================================"
echo "    InterFuser 模型评估"
echo "================================================"
echo ""

# 激活 conda 环境
source /home/nju/anaconda2/etc/profile.d/conda.sh
conda activate interfuser

cd /home/nju/InterFuser

# 设置基本环境变量
export CUDA_VISIBLE_DEVICES=${GPU_ID:-0}
export CARLA_ROOT=/home/nju/InterFuser/carla
export CARLA_SERVER=${CARLA_ROOT}/CarlaUE4.sh
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla
export PYTHONPATH=$PYTHONPATH:$CARLA_ROOT/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg
export PYTHONPATH=$PYTHONPATH:leaderboard
export PYTHONPATH=$PYTHONPATH:leaderboard/team_code
export PYTHONPATH=$PYTHONPATH:scenario_runner

export LEADERBOARD_ROOT=leaderboard
export CHALLENGE_TRACK_CODENAME=SENSORS
export PORT=2000
export TM_PORT=2500
export DEBUG_CHALLENGE=0
export REPETITIONS=1

# 评估类型选择
EVAL_TYPE=${1:-town05}

case $EVAL_TYPE in
    town05)
        echo "评估类型: Town05 Long Benchmark"
        export ROUTES=leaderboard/data/evaluation_routes/routes_town05_long.xml
        export SCENARIOS=leaderboard/data/scenarios/town05_all_scenarios.json
        export CHECKPOINT_ENDPOINT=results/interfuser_town05_result.json
        ;;
    42routes)
        echo "评估类型: CARLA 42 Routes Benchmark"
        export ROUTES=leaderboard/data/42routes/42routes.xml
        export SCENARIOS=leaderboard/data/42routes/42scenarios.json
        export CHECKPOINT_ENDPOINT=results/interfuser_42routes_result.json
        ;;
    custom)
        echo "评估类型: 自定义路线"
        export ROUTES=${CUSTOM_ROUTES:-leaderboard/data/evaluation_routes/routes_town05_long.xml}
        export SCENARIOS=${CUSTOM_SCENARIOS:-leaderboard/data/scenarios/town05_all_scenarios.json}
        export CHECKPOINT_ENDPOINT=${CUSTOM_RESULT:-results/interfuser_custom_result.json}
        ;;
    *)
        echo "错误: 未知的评估类型 '$EVAL_TYPE'"
        echo ""
        echo "用法: $0 [评估类型] [GPU_ID]"
        echo ""
        echo "评估类型:"
        echo "  town05    - Town05 Long Benchmark (默认)"
        echo "  42routes  - CARLA 42 Routes Benchmark"
        echo "  custom    - 自定义路线 (需设置 CUSTOM_ROUTES, CUSTOM_SCENARIOS)"
        echo ""
        echo "示例:"
        echo "  $0 town05         # Town05 评估，使用 GPU 0"
        echo "  $0 42routes       # 42 Routes 评估，使用 GPU 0"
        echo "  GPU_ID=1 $0 town05  # Town05 评估，使用 GPU 1"
        exit 1
        ;;
esac

export TEAM_AGENT=leaderboard/team_code/interfuser_agent.py
export TEAM_CONFIG=leaderboard/team_code/interfuser_config.py
export SAVE_PATH=data/eval
export RESUME=${RESUME:-True}

# 创建结果目录
mkdir -p results data/eval

echo ""
echo "配置信息:"
echo "  - GPU: $CUDA_VISIBLE_DEVICES"
echo "  - 路线文件: $ROUTES"
echo "  - 场景文件: $SCENARIOS"
echo "  - 结果文件: $CHECKPOINT_ENDPOINT"
echo "  - 模型路径: leaderboard/team_code/interfuser.pth.tar"
echo "  - 恢复模式: $RESUME"
echo ""

# 检查 CARLA 服务器是否运行
echo "检查 CARLA 服务器连接..."
timeout 5 bash -c "echo > /dev/tcp/localhost/2000" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ CARLA 服务器已连接"
    echo ""
else
    echo "✗ 警告: 无法连接到 CARLA 服务器 (端口 2000)"
    echo "  请先在另一个终端运行: ./start_carla_server.sh"
    echo ""
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "开始评估..."
echo "================================================"
echo ""

# 运行评估
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

echo ""
echo "================================================"
echo "评估完成！"
echo "结果保存在: $CHECKPOINT_ENDPOINT"
echo "================================================"

