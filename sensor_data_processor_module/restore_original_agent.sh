#!/bin/bash
# 恢复原始 agent 文件的脚本

set -e

TEAM_CODE_DIR="/home/nju/InterFuser/leaderboard/team_code"
BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "用法: $0 <备份目录>"
    echo ""
    echo "查找最近的备份:"
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    LATEST_BACKUP=$(ls -dt ${SCRIPT_DIR}/.backup_* 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        echo "  最近备份: $LATEST_BACKUP"
        read -p "是否使用此备份恢复? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            BACKUP_DIR="$LATEST_BACKUP"
        else
            exit 1
        fi
    else
        echo "  未找到备份文件"
        exit 1
    fi
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "错误: 备份目录不存在: $BACKUP_DIR"
    exit 1
fi

echo "从备份恢复文件: $BACKUP_DIR"
echo ""

# 恢复 interfuser_agent.py
if [ -f "${BACKUP_DIR}/interfuser_agent.py.bak" ]; then
    echo "  ✓ 恢复 interfuser_agent.py"
    cp "${BACKUP_DIR}/interfuser_agent.py.bak" "${TEAM_CODE_DIR}/interfuser_agent.py"
else
    echo "  ℹ 删除 interfuser_agent.py (原本不存在)"
    rm -f "${TEAM_CODE_DIR}/interfuser_agent.py"
fi

# 恢复或删除数据处理器文件
if [ -f "${BACKUP_DIR}/data_processor.py.bak" ]; then
    echo "  ✓ 恢复 data_processor.py"
    cp "${BACKUP_DIR}/data_processor.py.bak" "${TEAM_CODE_DIR}/data_processor.py"
else
    echo "  ℹ 删除 data_processor.py (原本不存在)"
    rm -f "${TEAM_CODE_DIR}/data_processor.py"
fi

if [ -f "${BACKUP_DIR}/data_processor_config.py.bak" ]; then
    echo "  ✓ 恢复 data_processor_config.py"
    cp "${BACKUP_DIR}/data_processor_config.py.bak" "${TEAM_CODE_DIR}/data_processor_config.py"
else
    echo "  ℹ 删除 data_processor_config.py (原本不存在)"
    rm -f "${TEAM_CODE_DIR}/data_processor_config.py"
fi

# 清理 __pycache__
echo "  → 清理 Python 缓存"
rm -rf "${TEAM_CODE_DIR}/__pycache__"

echo ""
echo "✅ 恢复完成！"
echo ""
echo "备份目录: $BACKUP_DIR"
echo "（如需保留备份，请勿删除此目录）"
echo ""

