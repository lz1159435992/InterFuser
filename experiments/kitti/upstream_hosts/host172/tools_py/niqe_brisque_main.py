import os
import sys
import time
import subprocess
import argparse
import numpy as np
from skimage import io
import piq, torch, argparse, os
from PIL import Image
import numpy as np
from piq import brisque
import torch
from pyiqa import create_metric

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(TOOLS_DIR, 'output')


def niqe_one(p):
    try:
        niqe_metric = create_metric('niqe', device='cpu')
        score = niqe_metric(p)
        return score.item()
    except Exception:
        return None

def brisque_one(p):
    try:
        # 1. 加载图像并转为 RGB
        img_pil = Image.open(p).convert('RGB')
        
        # 2. 转为 numpy array (H, W, C)
        img_np = np.array(img_pil).astype(np.float32) / 255.0  # 归一化到 [0, 1]
        
        # 3. 转为 torch tensor，并调整维度为 (1, C, H, W)
        img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0)  # (1, 3, H, W)
        
        # 4. 计算 BRISQUE 分数（无需 .score！直接调用函数）
        with torch.no_grad():
            score = brisque(img_tensor)
        
        return score.item()
    except Exception:
        return None


# def get_metrics_for_image(img_path):
#     """调用外部脚本获取 NIQE 和 BRISQUE，失败返回 (-1, -1)"""
#     try:
#         result = subprocess.run(
#             [sys.executable, './tools_py/niqe_brisque.py', '--img', img_path],
#             capture_output=True,
#             text=True,
#             timeout=30
#         )
#         if result.returncode != 0:
#             return (0, 0)
#         output = result.stdout.strip()
#         parts = output.split()
#         if len(parts) != 2:
#             return (0, 0)
#         n, b = float(parts[0]), float(parts[1])
#         return (n, b)
#     except Exception:
#         return (0, 0)

def get_metrics_for_image(img_path):
    """调用外部脚本获取 NIQE 和 BRISQUE，失败返回 (-1, -1)"""
    try:
        n, b = niqe_one(img_path), brisque_one(img_path)
        if(n!=None and b!=None):
            return (n, b)
        else:
            return (0, 0)
    except Exception:
        return (0, 0)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--img_dir', required=True)
    args=ap.parse_args()
    
    norm_path = os.path.normpath(args.img_dir)
    parts = norm_path.split(os.sep)
    parts = [p for p in parts if p]
    n = parts[-2]

    files=[f for f in os.listdir(args.img_dir) if f.lower().endswith(('.png','.jpg'))]
    niqes=[]
    brs=[]
    for f in files:
        p=os.path.join(args.img_dir,f)
        print(p)
        # time.sleep(1)
        # 尝试计算 NIQE 和 BRISQUE
        n_score, b_score = get_metrics_for_image(p)
        print(n_score,b_score)
        if (n_score != 0):
            niqes.append(n_score)
        if (b_score != 0):
            brs.append(b_score)

        with open(os.path.join(OUTPUT_DIR, "kitti_niqe_brisque_results_" + n + ".txt"), "a", encoding="utf-8") as f:
            f.write(f"{p} {n_score} {b_score}\n")
    import numpy as np
    print(f'NIQE {np.mean(niqes):.2f}±{1.96*np.std(niqes)/np.sqrt(len(niqes)):.2f} (越小越好)')
    print(f'BRISQUE {np.mean(brs):.2f}±{1.96*np.std(brs)/np.sqrt(len(brs)):.2f} (越小越好)')

    with open(os.path.join(OUTPUT_DIR, "kitti_niqe_brisque_results.txt"), "a", encoding="utf-8") as f:
        f.write(n)
        f.write(f'NIQE {np.mean(niqes):.2f}±{1.96*np.std(niqes)/np.sqrt(len(niqes)):.2f} (越小越好)')
        f.write(f'BRISQUE {np.mean(brs):.2f}±{1.96*np.std(brs)/np.sqrt(len(brs)):.2f} (越小越好)')
        f.write('\n')
