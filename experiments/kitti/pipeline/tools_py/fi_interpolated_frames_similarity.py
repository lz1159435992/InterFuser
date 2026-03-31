# scripts/metrics/fi_temporal_smoothness.py
# 评估图像序列的时序平滑度 —— 所有输出写入单个 output.txt 文件
import cv2, os, argparse
import numpy as np
from pathlib import Path
import json

def compute_frame_difference(frame1, frame2):
    """计算两帧之间的平均绝对差"""
    diff = cv2.absdiff(frame1, frame2)
    return np.mean(diff)

def evaluate_temporal_smoothness(frame_dir, output_file_path):
    """
    评估图像序列的时序平滑度
    输入：图像帧目录（如 ./HMB_1_old）
    输出：
      - 所有结果写入 output.txt（包含每帧差异 + 汇总统计 + JSON 结构）
      - 终端仅打印进度和完成提示
    """
    # 加载并排序所有图像帧（支持 .png, .jpg, .jpeg）
    frame_paths = sorted(
        list(Path(frame_dir).glob("*.png")) +
        list(Path(frame_dir).glob("*.jpg")) +
        list(Path(frame_dir).glob("*.jpeg"))
    )
    if not frame_paths:
        raise FileNotFoundError(f"目录 {frame_dir} 中未找到图像帧（支持 .png/.jpg/.jpeg）")

    total_frames = len(frame_paths)
    print(f"📁 加载成功: {total_frames} 帧")

    # 存储每帧差异值（从第2帧开始）
    frame_diffs = []
    prev_gray = None

    # 准备输出内容列表
    output_lines = [
        f"=== 时序平滑度评估报告 ===",
        f"目录: {frame_dir}",
        f"总帧数: {total_frames}",
        "",
        "=== 每帧差异值（从第2帧开始） ===",
        "frame_index,prev_frame,current_frame,diff_value"
    ]

    print("\n📊 正在计算帧间差异...")
    for idx, path in enumerate(frame_paths):
        frame = cv2.imread(str(path))
        if frame is None:
            raise RuntimeError(f"无法读取图像: {path}")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_gray is not None:
            diff = compute_frame_difference(prev_gray, gray)
            frame_diffs.append(diff)
            output_lines.append(f"{idx+1},{Path(frame_paths[idx-1]).name},{Path(path).name},{diff:.6f}")
        else:
            output_lines.append(f"{idx+1},N/A,{Path(path).name},N/A")

        prev_gray = gray

        if (idx + 1) % 100 == 0:
            print(f"  进度: {idx + 1}/{total_frames}")

    # 如果帧数不足2，则无法计算差异
    if len(frame_diffs) < 1:
        output_lines.extend([
            "",
            "⚠️ 警告: 帧数不足（<2），无法计算平滑度",
            ""
        ])
        result = {
            'frame_dir': str(frame_dir),
            'total_frames': total_frames,
            'mean_diff': float('nan'),
            'std_diff': float('nan'),
            'cv': float('nan'),
            'abrupt_changes': 0,
            'abrupt_ratio': 0.0
        }
    else:
        # 统计分析
        diffs_mean = np.mean(frame_diffs)
        diffs_std = np.std(frame_diffs, ddof=1)
        diffs_cv = diffs_std / diffs_mean if diffs_mean > 0 else float('inf')
        threshold = diffs_mean + 2 * diffs_std
        abrupt_changes = sum(1 for d in frame_diffs if d > threshold)
        abrupt_ratio = abrupt_changes / len(frame_diffs)

        # 汇总报告
        output_lines.extend([
            "",
            "=== 汇总统计 ===",
            f"有效差异帧数:   {len(frame_diffs)}",
            f"平均帧间差异:   {diffs_mean:.6f}",
            f"标准差:         {diffs_std:.6f}",
            f"变异系数 (CV):  {diffs_cv:.6f}",
            f"突变帧数:       {abrupt_changes} / {len(frame_diffs)} ({abrupt_ratio*100:.2f}%)",
            "",
            "📌 解读:",
            "  - CV < 0.5: 非常平滑",
            "  - CV < 1.0: 较平滑",
            "  - CV > 1.5: 存在明显抖动",
            "  - 突变率 < 5%: 良好",
            "",
            "=== 结构化数据（JSON 格式） ==="
        ])

        result = {
            'frame_dir': str(frame_dir),
            'total_frames': total_frames,
            'effective_diff_frames': len(frame_diffs),
            'mean_diff': float(diffs_mean),
            'std_diff': float(diffs_std),
            'cv': float(diffs_cv),
            'abrupt_changes': int(abrupt_changes),
            'abrupt_ratio': float(abrupt_ratio),
            'threshold_for_abrupt': float(threshold)
        }

        output_lines.append(json.dumps(result, indent=2, ensure_ascii=False))

    # 写入文件
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines))

    print(f"\n✅ 完成！所有结果已保存至: {output_file_path}")

    return result

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='评估图像序列的时序平滑度（所有输出写入单个 output.txt）')
    ap.add_argument('--frame_dir', required=True, help='图像帧所在目录（如 ./udacity/input/HMB_1_old）')
    ap.add_argument('--output_dir', required=True, help='输出结果目录（如 ./results/HMB_1_old）')
    args = ap.parse_args()

    evaluate_temporal_smoothness(args.frame_dir, args.output_dir)