#!/bin/bash
# 查看评估结果脚本

echo "================================================"
echo "    InterFuser 评估结果查看器"
echo "================================================"
echo ""

cd /home/nju/InterFuser

# 检查结果文件
RESULT_FILE=${1:-results/interfuser_town05_result.json}

if [ ! -f "$RESULT_FILE" ]; then
    echo "错误: 结果文件不存在: $RESULT_FILE"
    echo ""
    echo "可用的结果文件:"
    ls -lh results/*.json 2>/dev/null || echo "  (暂无结果文件)"
    echo ""
    echo "用法: $0 [结果文件路径]"
    echo "示例: $0 results/interfuser_town05_result.json"
    exit 1
fi

echo "结果文件: $RESULT_FILE"
echo "文件大小: $(du -h $RESULT_FILE | cut -f1)"
echo ""
echo "================================================"
echo ""

# 激活环境
source /home/nju/anaconda2/etc/profile.d/conda.sh
conda activate interfuser

# 使用 Python 解析并美化显示结果
python3 << 'EOF'
import json
import sys
from pathlib import Path

result_file = sys.argv[1] if len(sys.argv) > 1 else 'results/interfuser_town05_result.json'

try:
    with open(result_file, 'r') as f:
        data = json.load(f)
    
    print("📊 评估统计摘要")
    print("=" * 60)
    
    if '_checkpoint' in data:
        checkpoint = data['_checkpoint']
        
        # 总体统计
        if 'global_record' in checkpoint:
            gr = checkpoint['global_record']
            print(f"\n🎯 总体表现:")
            print(f"  - 总分 (Score):              {gr.get('scores', {}).get('score', 'N/A'):.2f}")
            print(f"  - 路线完成度:                 {gr.get('scores', {}).get('route_completion', 'N/A'):.2f}%")
            print(f"  - 违规惩罚:                   {gr.get('scores', {}).get('infraction_penalty', 'N/A'):.2f}")
        
        # 路线统计
        if 'records' in checkpoint:
            records = checkpoint['records']
            print(f"\n📍 路线详情: (共 {len(records)} 条路线)")
            print("-" * 60)
            
            completed = sum(1 for r in records if r.get('scores', {}).get('route_completion', 0) >= 99)
            print(f"  - 完成路线数: {completed}/{len(records)}")
            
            avg_score = sum(r.get('scores', {}).get('score', 0) for r in records) / len(records) if records else 0
            print(f"  - 平均分数:   {avg_score:.2f}")
            
            # 违规统计
            infractions = {}
            for record in records:
                for inf_type, inf_data in record.get('infractions', {}).items():
                    if inf_type not in infractions:
                        infractions[inf_type] = 0
                    infractions[inf_type] += len(inf_data)
            
            if infractions:
                print(f"\n⚠️  违规统计:")
                for inf_type, count in sorted(infractions.items(), key=lambda x: x[1], reverse=True):
                    print(f"  - {inf_type}: {count}")
    
    print("\n" + "=" * 60)
    print("\n💡 提示: 完整 JSON 数据请查看原文件")
    print(f"   文件位置: {result_file}")
    print()

except FileNotFoundError:
    print(f"❌ 错误: 找不到文件 {result_file}")
except json.JSONDecodeError:
    print(f"❌ 错误: 无法解析 JSON 文件 {result_file}")
except Exception as e:
    print(f"❌ 错误: {str(e)}")

EOF

echo ""
echo "================================================"
echo "是否查看完整 JSON 数据? (y/N)"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 -m json.tool "$RESULT_FILE" | less
fi

