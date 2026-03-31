#!/usr/bin/env python3
"""
SwinIR 使用示例

演示如何�?InterFuser 项目中使�?SwinIR 进行图像处理
"""

import sys
import os
import numpy as np
import cv2

# 添加当前目录到路径（example_usage.py 现在�?SwinIR/ 内部�?CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from swinir_wrapper import SwinIRProcessor


def example_1_basic_usage():
    """示例 1: 基本使用"""
    print("\n" + "="*70)
    print("📘 示例 1: 基本使用")
    print("="*70)
    
    # 创建测试图像
    test_image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    print(f"输入图像形状: {test_image.shape}")
    
    # 注意: 需要先下载模型文件
    model_path = os.path.join(CURRENT_DIR, 'model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth')
    
    if not os.path.exists(model_path):
        print(f"⚠️  模型文件不存�? {model_path}")
        print("请先下载模型:")
        print("  cd /path/to/project/process_mothod/SwinIR")
        print("  bash download-weights.sh")
        return
    
    # 创建处理�?    processor = SwinIRProcessor(
        model_path=model_path,
        task='sr',
        upscale=2,
        device='cuda'  # �?'cpu'
    )
    
    # 处理图像
    output = processor.process(test_image)
    print(f"输出图像形状: {output.shape}")
    
    # 获取统计信息
    stats = processor.get_stats()
    print(f"统计信息: {stats}")


def example_2_image_super_resolution():
    """示例 2: 图像超分辨率"""
    print("\n" + "="*70)
    print("📘 示例 2: 图像超分辨率�?x�?)
    print("="*70)
    
    # 读取真实图像（如果有�?    input_path = 'input_image.jpg'
    
    if os.path.exists(input_path):
        image = cv2.imread(input_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        print(f"加载图像: {input_path}, 形状: {image.shape}")
    else:
        # 创建测试图像
        image = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        print(f"使用测试图像, 形状: {image.shape}")
    
    model_path = os.path.join(CURRENT_DIR, 'model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth')
    
    if not os.path.exists(model_path):
        print("⚠️  请先下载模型")
        return
    
    # 创建 SR 处理�?    processor = SwinIRProcessor(
        model_path=model_path,
        task='sr',
        upscale=2
    )
    
    # 超分辨率处理
    sr_output = processor.process(image)
    print(f"超分辨率输出形状: {sr_output.shape}")
    
    # 保存结果
    sr_output_bgr = cv2.cvtColor(sr_output, cv2.COLOR_RGB2BGR)
    cv2.imwrite('output_sr_2x.jpg', sr_output_bgr)
    print("�?保存超分辨率结果: output_sr_2x.jpg")


def example_3_denoise():
    """示例 3: 图像去噪"""
    print("\n" + "="*70)
    print("📘 示例 3: 图像去噪")
    print("="*70)
    
    # 创建干净图像
    clean_image = np.random.randint(100, 200, (256, 256, 3), dtype=np.uint8)
    
    # 添加噪声
    noise = np.random.normal(0, 15, clean_image.shape)
    noisy_image = clean_image.astype(np.float32) + noise
    noisy_image = noisy_image.clip(0, 255).astype(np.uint8)
    
    print(f"噪声图像形状: {noisy_image.shape}")
    
    model_path = os.path.join(CURRENT_DIR, 'model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth')
    
    if not os.path.exists(model_path):
        print("⚠️  请先下载去噪模型")
        return
    
    # 创建去噪处理�?    processor = SwinIRProcessor(
        model_path=model_path,
        task='denoise'
    )
    
    # 去噪处理
    denoised = processor.process(noisy_image)
    print(f"去噪输出形状: {denoised.shape}")
    
    # 保存对比结果
    cv2.imwrite('noisy_image.jpg', cv2.cvtColor(noisy_image, cv2.COLOR_RGB2BGR))
    cv2.imwrite('denoised_image.jpg', cv2.cvtColor(denoised, cv2.COLOR_RGB2BGR))
    print("�?保存对比结果: noisy_image.jpg, denoised_image.jpg")


def example_4_batch_processing():
    """示例 4: 批量处理"""
    print("\n" + "="*70)
    print("📘 示例 4: 批量处理多张图像")
    print("="*70)
    
    # 创建多张测试图像
    images = [
        np.random.randint(0, 256, (128, 128, 3), dtype=np.uint8)
        for _ in range(5)
    ]
    print(f"图像数量: {len(images)}")
    
    model_path = os.path.join(CURRENT_DIR, 'model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth')
    
    if not os.path.exists(model_path):
        print("⚠️  请先下载模型")
        return
    
    processor = SwinIRProcessor(
        model_path=model_path,
        task='sr',
        upscale=2
    )
    
    # 批量处理
    outputs = processor.process_batch(images)
    print(f"输出数量: {len(outputs)}")
    print(f"每张输出形状: {outputs[0].shape}")


def example_5_integration_with_data_processor():
    """示例 5: 集成到数据处理器"""
    print("\n" + "="*70)
    print("📘 示例 5: 集成到数据处理器配置")
    print("="*70)
    
    print("""
# �?data_processor_config.py 中添�?

DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        # 现有效果...
        
        # SwinIR 超分辨率
        'swinir': {
            'enabled': True,
            'task': 'sr',
            'model_path': os.path.join(CURRENT_DIR, 'model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth'),
            'upscale': 2,
            'device': 'cuda',
        },
    },
}

# �?data_processor.py �?__init__ �?

from swinir_wrapper import SwinIRProcessor

class SensorDataProcessor:
    def __init__(self, config):
        # ... 现有代码 ...
        
        # 初始�?SwinIR
        self.swinir = None
        if config.get('rgb', {}).get('swinir', {}).get('enabled', False):
            cfg = config['rgb']['swinir']
            self.swinir = SwinIRProcessor(
                model_path=cfg['model_path'],
                task=cfg.get('task', 'sr'),
                upscale=cfg.get('upscale', 2),
                device=cfg.get('device', 'cuda')
            )
    
    def _apply_rgb_effects(self, image, sensor_name):
        # ... 现有效果 ...
        
        # 应用 SwinIR
        if self.swinir is not None:
            result = self.swinir.process(result)
        
        return result
    """)


def main():
    """主函�?""
    print("\n" + "="*70)
    print("🎨 SwinIR 使用示例集合")
    print("="*70)
    
    # 检�?SwinIR 是否存在
    if not os.path.exists(os.path.join(CURRENT_DIR, 'models')):
        print(f"�?SwinIR 模块不完�? {CURRENT_DIR}")
        print("请确�?SwinIR 文件夹包含完整的源代�?)
        return
    
    print(f"�?SwinIR 路径: {CURRENT_DIR}")
    
    # 运行示例
    try:
        example_1_basic_usage()
    except Exception as e:
        print(f"示例 1 失败: {e}")
    
    try:
        example_2_image_super_resolution()
    except Exception as e:
        print(f"示例 2 失败: {e}")
    
    try:
        example_3_denoise()
    except Exception as e:
        print(f"示例 3 失败: {e}")
    
    try:
        example_4_batch_processing()
    except Exception as e:
        print(f"示例 4 失败: {e}")
    
    example_5_integration_with_data_processor()
    
    print("\n" + "="*70)
    print("�?示例展示完成")
    print("="*70)
    print("\n💡 提示:")
    print("  1. 需要先下载模型文件")
    print("  2. 查看详细集成指南: SWINIR_INTEGRATION_GUIDE.md")
    print("  3. 根据实际需求调整配�?)
    print()


if __name__ == "__main__":
    main()

