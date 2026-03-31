# single_image_metrics.py
import sys
import argparse
import numpy as np
from skimage import io
import piq, torch, argparse, os
from PIL import Image
import numpy as np
from piq import brisque
import torch
from pyiqa import create_metric

def niqe_one(p):
    try:
        niqe_metric = create_metric('niqe', device='cpu')
        score = niqe_metric(p)
        return score
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--img', required=True)
    args = parser.parse_args()

    n_score = niqe_one(args.img)
    b_score = brisque_one(args.img)

    n_out = -1 if n_score is None else n_score
    b_out = -1 if b_score is None else b_score

    # 输出格式：NIQE BRISQUE（空格分隔，便于主脚本解析）
    print(f"{n_out} {b_out}")
    sys.exit(0)