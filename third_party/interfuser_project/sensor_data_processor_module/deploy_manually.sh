#!/bin/bash
# 手动部署脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEAM_CODE_DIR="${SCRIPT_DIR}/../leaderboard/team_code"

echo "📦 手动部署数据处理器文件..."
echo ""

# 复制文件
echo "  → 复制 data_processor.py"
cp "${SCRIPT_DIR}/data_processor.py" "${TEAM_CODE_DIR}/data_processor.py"

echo "  → 复制 data_processor_config.py"
cp "${SCRIPT_DIR}/data_processor_config.py" "${TEAM_CODE_DIR}/data_processor_config.py"

echo ""
echo "✅ 部署完成！"
echo ""
echo "现在可以导入了："
echo "  from team_code.data_processor import SensorDataProcessor"
echo "  from team_code.data_processor_config import ACTIVE_CONFIG"
echo ""

# 测试导入
cd "${TEAM_CODE_DIR}/.."
python3 -c "from team_code.data_processor import SensorDataProcessor; from team_code.data_processor_config import ACTIVE_CONFIG; print('✅ 导入成功！')" 2>&1
