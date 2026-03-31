#!/bin/bash
# 数据处理器测试脚�?
echo "╔══════════════════════════════════════════════════════════════╗"
echo "�?        InterFuser 数据处理器测试脚�?                        �?
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 激活环�?echo "1. 激�?conda 环境..."
source /opt/conda/etc/profile.d/conda.sh
conda activate interfuser
echo "   �?环境已激�?
echo ""

# 进入工作目录（模块目录）
cd /path/to/project/sensor_data_processor_module

# 测试数据处理�?echo "2. 测试数据处理器基本功�?.."
echo "   执行: python data_processor.py"
echo "   ────────────────────────────────────────────────"
python data_processor.py
echo "   ────────────────────────────────────────────────"
echo ""

# 检查配置文�?echo "3. 检查配置文�?.."
if [ -f "data_processor_config.py" ]; then
    echo "   �?data_processor_config.py 存在"
    echo ""
    echo "   当前激活的配置:"
    echo "   ────────────────────────────────────────────────"
    python -c "from data_processor_config import ACTIVE_CONFIG; import json; print(json.dumps({'enabled': ACTIVE_CONFIG.get('enabled', False)}, indent=2))"
    echo "   ────────────────────────────────────────────────"
else
    echo "   �?data_processor_config.py 不存�?
    exit 1
fi
echo ""

# 检查示例文�?echo "4. 检查示例文�?.."
if [ -f "interfuser_agent_with_processor_example.py" ]; then
    echo "   �?interfuser_agent_with_processor_example.py 存在"
    echo "   文件大小: $(du -h interfuser_agent_with_processor_example.py | cut -f1)"
else
    echo "   �?示例文件不存�?
fi
echo ""

# 列出所有相关文�?echo "5. 相关文件列表:"
echo "   ────────────────────────────────────────────────"
ls -lh data_processor* interfuser_agent_with_processor_example.py 2>/dev/null || echo "   部分文件缺失"
echo "   ────────────────────────────────────────────────"
echo ""

# 提供下一步指�?echo "╔══════════════════════════════════════════════════════════════╗"
echo "�?                    测试完成�?                               �?
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 下一步操�?"
echo ""
echo "1. 查看使用指南:"
echo "   cd /path/to/project"
echo "   cat DATA_PROCESSOR_USAGE_GUIDE.md"
echo ""
echo "2. 查看项目分析:"
echo "   cat INTERFUSER_PROJECT_ANALYSIS.md"
echo ""
echo "3. 修改配置 (选择预设或自定义):"
echo "   cd sensor_data_processor_module"
echo "   nano data_processor_config.py"
echo "   # 修改最后一�? ACTIVE_CONFIG = CONFIG_MODERATE_NOISE"
echo ""
echo "4. 集成�?Agent:"
echo "   cd sensor_data_processor_module"
echo "   参�?interfuser_agent_with_processor_example.py"
echo "   或查�?DATA_PROCESSOR_USAGE_GUIDE.md 的集成部�?
echo ""
echo "5. 复制文件�?team_code:"
echo "   cp data_processor.py ../leaderboard/team_code/"
echo "   cp data_processor_config.py ../leaderboard/team_code/"
echo ""
echo "6. 运行评估测试:"
echo "   cd ../evaluation_scripts"
echo "   ./start_carla_server.sh  # 终端 1"
echo "   ./run_evaluation.sh town05  # 终端 2"
echo ""

