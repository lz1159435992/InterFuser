import os
import sys
import cv2
import numpy as np
from pathlib import Path

def add_gaussian_noise(image, mean=0, sigma=25):
    """
    给图像添加高斯噪声
    :param image: 输入图像 (numpy array)
    :param mean: 噪声均值
    :param sigma: 噪声标准差
    :return: 添加噪声后的图像 (uint8)
    """
    gauss = np.random.normal(mean, sigma, image.shape)
    noisy = image.astype(np.float32) + gauss
    noisy = np.clip(noisy, 0, 255).astype(np.uint8)
    return noisy

def process_directory(input_dir, output_dir, sigma):
    """
    处理整个文件夹中的 PNG 图像
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)

    # 获取所有 .png 文件（不区分大小写）
    png_files = list(input_path.glob("*.png")) + list(input_path.glob("*.PNG"))

    if not png_files:
        print(f"❌ 在 {input_dir} 中没有找到 .png 文件！")
        return

    print(f"📁 找到 {len(png_files)} 个 PNG 文件，开始添加高斯噪声 (sigma={sigma})...")

    for img_path in png_files:
        # 读取图像
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"⚠️  跳过无效图像: {img_path.name}")
            continue

        # 添加噪声
        noisy_img = add_gaussian_noise(img, sigma=sigma)

        # 保存到输出目录，保持原文件名
        output_file = output_path / img_path.name
        cv2.imwrite(str(output_file), noisy_img)

        print(f"✅ 已保存: {output_file.name}")

    print("🎉 所有图像处理完成！")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python3 add_noise.py <输入文件夹> <输出文件夹>")
        print("示例: python3 add_noise.py ./input ./output")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    # 可选：在这里修改 方差 值 
    SIGMA = 8  # <- 你可以根据需要修改这个值

    process_directory(input_dir, output_dir, sigma=SIGMA)