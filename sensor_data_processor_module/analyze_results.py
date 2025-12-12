#!/usr/bin/env python3
"""
评估结果分析脚本

用于分析和比较不同数据处理配置下的评估结果
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import argparse
from datetime import datetime

def load_result(result_file: Path) -> Dict[str, Any]:
    """加载评估结果 JSON 文件"""
    if not result_file.exists():
        raise FileNotFoundError(f"结果文件不存在: {result_file}")
    
    with open(result_file, 'r') as f:
        return json.load(f)

def load_metadata(eval_dir: Path) -> Dict[str, Any]:
    """加载评估元数据"""
    metadata_file = eval_dir / "evaluation_metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    return {}

def calculate_statistics(result_data: Dict[str, Any]) -> Dict[str, Any]:
    """计算评估统计信息"""
    stats = {
        'total_routes': 0,
        'completed_routes': 0,
        'failed_routes': 0,
        'avg_driving_score': 0.0,
        'avg_route_completion': 0.0,
        'avg_infraction_penalty': 0.0,
        'total_infractions': 0,
        'infraction_breakdown': {},
    }
    
    if '_checkpoint' not in result_data:
        return stats
    
    checkpoint = result_data['_checkpoint']
    records = checkpoint.get('records', [])
    
    stats['total_routes'] = len(records)
    
    driving_scores = []
    route_completions = []
    infraction_penalties = []
    
    for record in records:
        status = record.get('status', 'Failed')
        scores = record.get('scores', {})
        
        if status == 'Completed':
            stats['completed_routes'] += 1
        else:
            stats['failed_routes'] += 1
        
        # 提取分数
        driving_score = scores.get('score_route', 0.0)
        route_completion = scores.get('score_composed', 0.0)
        infraction_penalty = scores.get('score_penalty', 0.0)
        
        driving_scores.append(driving_score)
        route_completions.append(route_completion)
        infraction_penalties.append(infraction_penalty)
        
        # 违规统计
        infractions = record.get('infractions', {})
        for infraction_type, infraction_list in infractions.items():
            if infraction_type not in stats['infraction_breakdown']:
                stats['infraction_breakdown'][infraction_type] = 0
            stats['infraction_breakdown'][infraction_type] += len(infraction_list)
            stats['total_infractions'] += len(infraction_list)
    
    # 计算平均值
    if driving_scores:
        stats['avg_driving_score'] = sum(driving_scores) / len(driving_scores)
    if route_completions:
        stats['avg_route_completion'] = sum(route_completions) / len(route_completions)
    if infraction_penalties:
        stats['avg_infraction_penalty'] = sum(infraction_penalties) / len(infraction_penalties)
    
    return stats

def print_single_result(result_file: Path, detailed: bool = False):
    """打印单个结果的分析"""
    print("=" * 70)
    print(f"📊 评估结果分析: {result_file.name}")
    print("=" * 70)
    print()
    
    # 加载数据
    result_data = load_result(result_file)
    stats = calculate_statistics(result_data)
    
    # 尝试加载元数据
    eval_dir = result_file.parent.parent / "data" / "eval_with_processor" / result_file.stem
    metadata = load_metadata(eval_dir)
    
    if metadata:
        print("🔧 评估配置:")
        print(f"  • 时间戳: {metadata.get('timestamp', 'N/A')}")
        print(f"  • 评估类型: {metadata.get('eval_type', 'N/A')}")
        print(f"  • 数据处理配置: {metadata.get('config_type', 'N/A')}")
        print(f"  • GPU ID: {metadata.get('gpu_id', 'N/A')}")
        print()
    
    print("📈 总体统计:")
    print(f"  • 总路线数: {stats['total_routes']}")
    print(f"  • 完成路线数: {stats['completed_routes']}")
    print(f"  • 失败路线数: {stats['failed_routes']}")
    print(f"  • 完成率: {stats['completed_routes']/stats['total_routes']*100:.2f}%" if stats['total_routes'] > 0 else "  • 完成率: N/A")
    print()
    
    print("🎯 性能指标:")
    print(f"  • 平均驾驶分数: {stats['avg_driving_score']:.2f}")
    print(f"  • 平均路线完成度: {stats['avg_route_completion']:.2f}")
    print(f"  • 平均违规惩罚: {stats['avg_infraction_penalty']:.2f}")
    print()
    
    print("⚠️  违规统计:")
    print(f"  • 总违规次数: {stats['total_infractions']}")
    if stats['infraction_breakdown']:
        print("  • 违规详情:")
        for infraction_type, count in sorted(stats['infraction_breakdown'].items(), key=lambda x: x[1], reverse=True):
            print(f"    - {infraction_type}: {count} 次")
    else:
        print("  • 无违规记录")
    print()
    
    if detailed and '_checkpoint' in result_data:
        print("📋 详细路线结果:")
        print("-" * 70)
        records = result_data['_checkpoint'].get('records', [])
        for i, record in enumerate(records, 1):
            route_id = record.get('route_id', f'Route {i}')
            status = record.get('status', 'Unknown')
            scores = record.get('scores', {})
            
            print(f"\n  路线 {route_id}:")
            print(f"    状态: {status}")
            print(f"    驾驶分数: {scores.get('score_route', 0.0):.2f}")
            print(f"    完成度: {scores.get('score_composed', 0.0):.2f}")
            print(f"    违规惩罚: {scores.get('score_penalty', 0.0):.2f}")
            
            infractions = record.get('infractions', {})
            total_route_infractions = sum(len(v) for v in infractions.values())
            if total_route_infractions > 0:
                print(f"    违规次数: {total_route_infractions}")
        print()

def compare_results(result_files: List[Path]):
    """比较多个结果"""
    print("=" * 70)
    print("📊 评估结果对比")
    print("=" * 70)
    print()
    
    results = []
    for result_file in result_files:
        try:
            result_data = load_result(result_file)
            stats = calculate_statistics(result_data)
            
            # 尝试加载元数据
            eval_dir = result_file.parent.parent / "data" / "eval_with_processor" / result_file.stem
            metadata = load_metadata(eval_dir)
            
            results.append({
                'file': result_file,
                'stats': stats,
                'metadata': metadata
            })
        except Exception as e:
            print(f"⚠️  跳过 {result_file.name}: {e}")
    
    if not results:
        print("没有有效的结果可供比较")
        return
    
    # 打印对比表格
    print(f"{'配置类型':<15} {'完成率':<10} {'驾驶分数':<12} {'完成度':<12} {'违规次数':<10}")
    print("-" * 70)
    
    for result in results:
        config_type = result['metadata'].get('config_type', 'Unknown')
        stats = result['stats']
        
        completion_rate = f"{stats['completed_routes']/stats['total_routes']*100:.1f}%" if stats['total_routes'] > 0 else "N/A"
        
        print(f"{config_type:<15} {completion_rate:<10} {stats['avg_driving_score']:<12.2f} "
              f"{stats['avg_route_completion']:<12.2f} {stats['total_infractions']:<10}")
    
    print()
    
    # 性能对比分析
    print("🔍 性能对比分析:")
    print()
    
    if len(results) >= 2:
        # 找到基准（通常是无处理或轻度处理）
        baseline = None
        for result in results:
            config_type = result['metadata'].get('config_type', '')
            if config_type in ['mild', 'baseline', 'no_processing']:
                baseline = result
                break
        
        if not baseline:
            baseline = results[0]
        
        baseline_name = baseline['metadata'].get('config_type', 'baseline')
        print(f"  基准配置: {baseline_name}")
        print()
        
        for result in results:
            if result == baseline:
                continue
            
            config_type = result['metadata'].get('config_type', 'Unknown')
            
            # 计算相对变化
            driving_score_diff = result['stats']['avg_driving_score'] - baseline['stats']['avg_driving_score']
            completion_diff = result['stats']['avg_route_completion'] - baseline['stats']['avg_route_completion']
            infraction_diff = result['stats']['total_infractions'] - baseline['stats']['total_infractions']
            
            print(f"  {config_type} vs {baseline_name}:")
            print(f"    驾驶分数变化: {driving_score_diff:+.2f}")
            print(f"    完成度变化: {completion_diff:+.2f}")
            print(f"    违规次数变化: {infraction_diff:+d}")
            print()

def main():
    parser = argparse.ArgumentParser(
        description='分析 InterFuser 评估结果',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 分析单个结果
  %(prog)s results/with_processor/town05_moderate_20250101_120000.json
  
  # 详细分析
  %(prog)s -d results/with_processor/town05_moderate_20250101_120000.json
  
  # 对比多个结果
  %(prog)s -c results/with_processor/town05_mild_*.json results/with_processor/town05_moderate_*.json
  
  # 分析目录中的所有结果
  %(prog)s -c results/with_processor/*.json
        '''
    )
    
    parser.add_argument('files', nargs='+', type=Path, help='结果文件路径（支持通配符）')
    parser.add_argument('-d', '--detailed', action='store_true', help='显示详细信息（每条路线）')
    parser.add_argument('-c', '--compare', action='store_true', help='对比模式（比较多个结果）')
    
    args = parser.parse_args()
    
    # 展开通配符
    result_files = []
    for pattern in args.files:
        if pattern.exists() and pattern.is_file():
            result_files.append(pattern)
        else:
            # 尝试作为通配符匹配
            parent = pattern.parent
            if parent.exists():
                result_files.extend(parent.glob(pattern.name))
    
    result_files = sorted(set(result_files))  # 去重并排序
    
    if not result_files:
        print("错误: 未找到结果文件")
        sys.exit(1)
    
    if args.compare or len(result_files) > 1:
        compare_results(result_files)
    else:
        print_single_result(result_files[0], detailed=args.detailed)

if __name__ == '__main__':
    main()

