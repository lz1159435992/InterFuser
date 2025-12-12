#!/bin/bash
# 数据处理器测试脚本

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         InterFuser 数据处理器测试脚本                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 激活环境
echo "1. 激活 conda 环境..."
source /home/nju/anaconda2/etc/profile.d/conda.sh
conda activate interfuser
echo "   ✓ 环境已激活"
echo ""

# 进入工作目录（模块目录）
cd /home/nju/InterFuser/sensor_data_processor_module

# 测试数据处理器
echo "2. 测试数据处理器基本功能..."
echo "   执行: python data_processor.py"
echo "   ────────────────────────────────────────────────"
python data_processor.py
echo "   ────────────────────────────────────────────────"
echo ""

# 检查配置文件
echo "3. 检查配置文件..."
if [ -f "data_processor_config.py" ]; then
    echo "   ✓ data_processor_config.py 存在"
    echo ""
    echo "   当前激活的配置:"
    echo "   ────────────────────────────────────────────────"
    python -c "from data_processor_config import ACTIVE_CONFIG; import json; print(json.dumps({'enabled': ACTIVE_CONFIG.get('enabled', False)}, indent=2))"
    echo "   ────────────────────────────────────────────────"
else
    echo "   ✗ data_processor_config.py 不存在"
    exit 1
fi
echo ""

# 检查示例文件
echo "4. 检查示例文件..."
if [ -f "interfuser_agent_with_processor_example.py" ]; then
    echo "   ✓ interfuser_agent_with_processor_example.py 存在"
    echo "   文件大小: $(du -h interfuser_agent_with_processor_example.py | cut -f1)"
else
    echo "   ✗ 示例文件不存在"
fi
echo ""

# 列出所有相关文件
echo "5. 相关文件列表:"
echo "   ────────────────────────────────────────────────"
ls -lh data_processor* interfuser_agent_with_processor_example.py 2>/dev/null || echo "   部分文件缺失"
echo "   ────────────────────────────────────────────────"
echo ""

# 提供下一步指引
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     测试完成！                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 下一步操作:"
echo ""
echo "1. 查看使用指南:"
echo "   cd /home/nju/InterFuser"
echo "   cat DATA_PROCESSOR_USAGE_GUIDE.md"
echo ""
echo "2. 查看项目分析:"
echo "   cat INTERFUSER_PROJECT_ANALYSIS.md"
echo ""
echo "3. 修改配置 (选择预设或自定义):"
echo "   cd sensor_data_processor_module"
echo "   nano data_processor_config.py"
echo "   # 修改最后一行: ACTIVE_CONFIG = CONFIG_MODERATE_NOISE"
echo ""
echo "4. 集成到 Agent:"
echo "   cd sensor_data_processor_module"
echo "   参考 interfuser_agent_with_processor_example.py"
echo "   或查看 DATA_PROCESSOR_USAGE_GUIDE.md 的集成部分"
echo ""
echo "5. 复制文件到 team_code:"
echo "   cp data_processor.py ../leaderboard/team_code/"
echo "   cp data_processor_config.py ../leaderboard/team_code/"
echo ""
echo "6. 运行评估测试:"
echo "   cd ../evaluation_scripts"
echo "   ./start_carla_server.sh  # 终端 1"
echo "   ./run_evaluation.sh town05  # 终端 2"
echo ""

