import argparse
import cv2
import numpy as np

def change_black_to_color(image_path, target_color, output_path):
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"无法加载图片: {image_path}")
    
    if img.shape[2] == 4:
        b, g, r, a = cv2.split(img)
    else:
        raise ValueError("输入图片必须包含透明通道 (RGBA)。")
    
    black_mask = (b == 0) & (g == 0) & (r == 0)
    
    b[black_mask] = target_color[0]
    g[black_mask] = target_color[1]
    r[black_mask] = target_color[2]
    
    new_img = cv2.merge((b, g, r, a))
    
    cv2.imwrite(output_path, new_img)

def parse_color(color_str):
    try:
        color = list(map(int, color_str.split(',')))
        if len(color) != 3 or not all(0 <= c <= 255 for c in color):
            raise ValueError()
        return color
    except Exception:
        raise ValueError(f"无效的颜色格式: {color_str}。请使用 'B,G,R' 格式，例如 '255,0,0'。")

if __name__ == "__main__":
    # 设置命令行参数解析器
    parser = argparse.ArgumentParser(description="将图片中的黑色部分替换为目标颜色。")
    parser.add_argument("-i", "--input", required=True, help="输入图片路径")
    parser.add_argument("-c", "--color", required=True, help="目标颜色，格式为 'B,G,R'（例如 '255,0,0' 表示蓝色）")
    parser.add_argument("-o", "--output", required=True, help="输出图片路径")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    try:
        # 解析目标颜色
        target_color = parse_color(args.color)
        
        # 调用函数修改图片
        change_black_to_color(args.input, target_color, args.output)
        print(f"图片已成功保存到: {args.output}")
    except Exception as e:
        print(f"发生错误: {e}")