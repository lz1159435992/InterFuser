# 这是一个将jpg合成gif的py脚本


from PIL import Image
import os
import sys


def create_gif_from_folder(image_folder, duration=500, loop=0):
    """
    将文件夹中的 JPEG 文件制作成动态 GIF。
    
    :param image_folder: 包含 JPEG 文件的文件夹路径
    :param output_path: 输出的 GIF 文件路径（如果为 None，则默认保存到输入文件夹）
    :param duration: 每帧之间的间隔时间（毫秒）
    :param loop: 循环次数（0 表示无限循环）
    """
    # 获取文件夹中的所有 JPEG 文件
    image_files = [
        f for f in os.listdir(image_folder)
        if os.path.isfile(os.path.join(image_folder, f)) and f.lower().endswith(('.jpg'))
    ]
    
    if not image_files:
        print("未找到任何 JPEG 文件！")
        return
    
    # 自定义排序：按文件名中的数字大小排序
    image_files.sort(key=lambda x: int(os.path.splitext(x)[0]))  # 提取文件名中的数字部分并排序

    # 打开所有图片并加载到内存中
    images = [Image.open(os.path.join(image_folder, file)) for file in image_files]

    # 如果未指定输出路径，默认保存到输入文件夹
    output_path = image_folder + ".gif"
    # 保存为 GIF 动图
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=loop
    )
    print(f"GIF 文件已成功保存到 '{output_path}'")

# main
if len(sys.argv) != 2:
    print("用法: python3 jpg_to_gif.py /path/to/jpg/dir/")
    exit()

# 获取文件夹路径
image_folder = sys.argv[1]

# 调用函数生成 GIF
create_gif_from_folder(image_folder, 1000, 0)
