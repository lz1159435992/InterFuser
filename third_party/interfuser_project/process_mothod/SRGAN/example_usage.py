"""
SRGAN 使用示例

展示如何在不同场景下使用 SRGAN 处理�?"""

import sys
import os
import numpy as np
from PIL import Image

# 添加 SRGAN 路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from srgan_wrapper import SRGANProcessor


def example_1_basic_usage():
    """示例 1: 基本使用 - 图像去噪/修复"""
    print("\n" + "=" * 70)
    print("示例 1: 基本使用 - 图像去噪/修复")
    print("=" * 70 + "\n")
    
    # 创建测试图像
    test_image = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
    print(f"输入图像: {test_image.shape}")
    
    # 初始化处理器（输出缩放回原始大小�?    processor = SRGANProcessor(
        model_path=os.path.join(CURRENT_DIR, 'results', 'checkpoint_srgan.pth'),
        device='cuda',
        downscale_output=True  # 缩放回原始大�?    )
    
    # 处理图像
    output = processor.process(test_image)
    print(f"输出图像: {output.shape}")
    print(f"�?处理完成\n")


def example_2_super_resolution():
    """示例 2: 超分辨率 - 保持 4x 放大"""
    print("\n" + "=" * 70)
    print("示例 2: 超分辨率 - 保持 4x 放大")
    print("=" * 70 + "\n")
    
    # 创建测试图像
    test_image = np.random.randint(0, 256, (128, 128, 3), dtype=np.uint8)
    print(f"输入图像: {test_image.shape}")
    
    # 初始化处理器（不缩放输出�?    processor = SRGANProcessor(
        model_path=os.path.join(CURRENT_DIR, 'results', 'checkpoint_srgan.pth'),
        device='cuda',
        downscale_output=False  # 保持 4x 放大
    )
    
    # 处理图像
    output = processor.process(test_image)
    print(f"输出图像: {output.shape}")
    print(f"放大倍数: {output.shape[0] / test_image.shape[0]:.1f}x")
    print(f"�?处理完成\n")


def example_3_pil_image():
    """示例 3: 使用 PIL 图像"""
    print("\n" + "=" * 70)
    print("示例 3: 使用 PIL 图像")
    print("=" * 70 + "\n")
    
    # 创建 PIL 图像
    pil_image = Image.new('RGB', (200, 200), color='red')
    print(f"输入图像: PIL Image, size={pil_image.size}")
    
    # 初始化处理器
    processor = SRGANProcessor(
        model_path=os.path.join(CURRENT_DIR, 'results', 'checkpoint_srgan.pth'),
        device='cuda',
        downscale_output=True
    )
    
    # 处理图像
    output = processor.process(pil_image)
    print(f"输出图像: numpy array, shape={output.shape}")
    print(f"�?处理完成\n")


def example_4_half_precision():
    """示例 4: 使用半精度加�?""
    print("\n" + "=" * 70)
    print("示例 4: 使用半精度加速（FP16�?)
    print("=" * 70 + "\n")
    
    test_image = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
    
    # FP32（默认）
    print("FP32 模式:")
    processor_fp32 = SRGANProcessor(
        model_path=os.path.join(CURRENT_DIR, 'results', 'checkpoint_srgan.pth'),
        device='cuda',
        half_precision=False,
        downscale_output=True
    )
    
    import time
    start = time.time()
    output_fp32 = processor_fp32.process(test_image)
    time_fp32 = time.time() - start
    print(f"  处理时间: {time_fp32:.3f} 秒\n")
    
    # FP16（半精度�?    print("FP16 模式:")
    processor_fp16 = SRGANProcessor(
        model_path=os.path.join(CURRENT_DIR, 'results', 'checkpoint_srgan.pth'),
        device='cuda',
        half_precision=True,
        downscale_output=True
    )
    
    start = time.time()
    output_fp16 = processor_fp16.process(test_image)
    time_fp16 = time.time() - start
    print(f"  处理时间: {time_fp16:.3f} �?)
    print(f"  加速比: {time_fp32 / time_fp16:.2f}x")
    print(f"�?处理完成\n")


def example_5_batch_processing():
    """示例 5: 批量处理多张图像"""
    print("\n" + "=" * 70)
    print("示例 5: 批量处理多张图像")
    print("=" * 70 + "\n")
    
    # 初始化处理器
    processor = SRGANProcessor(
        model_path=os.path.join(CURRENT_DIR, 'results', 'checkpoint_srgan.pth'),
        device='cuda',
        downscale_output=True
    )
    
    # 批量处理
    num_images = 5
    print(f"处理 {num_images} 张图�?..")
    
    import time
    start = time.time()
    
    for i in range(num_images):
        test_image = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
        output = processor.process(test_image)
    
    elapsed = time.time() - start
    avg_time = elapsed / num_images
    
    print(f"总时�? {elapsed:.3f} �?)
    print(f"平均每张: {avg_time:.3f} �?)
    print(f"吞吐�? {1/avg_time:.2f} �?�?)
    
    # 统计信息
    stats = processor.get_stats()
    print(f"\n处理总数: {stats['process_count']} �?)
    print(f"�?批量处理完成\n")


def example_6_integration_with_data_processor():
    """示例 6: 集成到数据处理器"""
    print("\n" + "=" * 70)
    print("示例 6: 集成到数据处理器的示例代�?)
    print("=" * 70 + "\n")
    
    code = '''
# �?data_processor_config.py 中添�?SRGAN 配置:

DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'srgan': {
        'enabled': True,
        'model_path': '/path/to/project/process_mothod/SRGAN/results/checkpoint_srgan.pth',
        'device': 'cuda',
        'half_precision': False,
        'downscale_output': True,  # 缩放回原始大小（去噪模式�?    },
}


# �?data_processor.py 中使�?

from srgan_wrapper import SRGANProcessor

class SensorDataProcessor:
    def __init__(self, config):
        # 初始�?SRGAN
        srgan_config = config.get('srgan', {})
        if srgan_config.get('enabled', False):
            self.srgan_processor = SRGANProcessor(
                model_path=srgan_config.get('model_path'),
                device=srgan_config.get('device', 'cuda'),
                half_precision=srgan_config.get('half_precision', False),
                downscale_output=srgan_config.get('downscale_output', True)
            )
    
    def process_rgb(self, rgb_image):
        # 使用 SRGAN 处理
        processed = self.srgan_processor.process(rgb_image)
        return processed
'''
    
    print(code)
    print("\n�?示例代码显示完成\n")


def main():
    """运行所有示�?""
    print("\n" + "�? + "=" * 68 + "�?)
    print("�? + " " * 20 + "SRGAN 使用示例" + " " * 34 + "�?)
    print("�? + "=" * 68 + "�?)
    
    # 检查模型文�?    model_path = os.path.join(CURRENT_DIR, 'results', 'checkpoint_srgan.pth')
    if not os.path.exists(model_path):
        print(f"\n⚠️  模型文件不存�? {model_path}")
        print("请确保模型文件在 SRGAN/results/ 目录�?)
        return
    
    # 运行示例
    try:
        example_1_basic_usage()
        example_2_super_resolution()
        example_3_pil_image()
        example_4_half_precision()
        example_5_batch_processing()
        example_6_integration_with_data_processor()
        
        print("\n" + "=" * 70)
        print("🎉 所有示例运行完成！")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n�?错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

