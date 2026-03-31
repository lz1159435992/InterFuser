"""
SRGAN Wrapper - 用于 InterFuser 数据处理器

提供简单的 API 接口来使用 SRGAN 进行图像超分辨率处理

使用方法:
    from srgan_wrapper import SRGANProcessor
    
    processor = SRGANProcessor(
        model_path='./results/checkpoint_srgan.pth',
        device='cuda'
    )
    
    output_image = processor.process(input_image)
"""

import sys
import os
import numpy as np
import torch
from PIL import Image

# 添加 SRGAN 路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from .models import Generator
from .utils import convert_image


class SRGANProcessor:
    """SRGAN 图像超分辨率处理器"""
    
    def __init__(
        self, 
        model_path=None,
        device='cuda',
        half_precision=False,
        large_kernel_size=9,
        small_kernel_size=3,
        n_channels=64,
        n_blocks=16,
        scaling_factor=4,
        output_scale=2
    ):
        """
        初始化 SRGAN 处理器
        
        Args:
            model_path: 模型文件路径，默认为 SRGAN/results/checkpoint_srgan.pth
            device: 设备 ('cuda' 或 'cpu')
            half_precision: 是否使用半精度（仅 CUDA）
            large_kernel_size: 第一层和最后一层卷积核大小
            small_kernel_size: 中间层卷积核大小
            n_channels: 中间层通道数
            n_blocks: 残差模块数量
            scaling_factor: SRGAN 内部放大比例（默认 4x）
            output_scale: 最终输出相对于输入的放大倍数
                         - 1: 缩放回原始大小（去噪/增强）
                         - 2: 输出 2x 大小（与原始 test.py 一致）⭐ 默认
                         - 4: 保持 4x 大小（完整超分辨率）
        """
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.half_precision = half_precision and self.device.type == 'cuda'
        self.scaling_factor = scaling_factor
        self.output_scale = output_scale
        
        # 设置默认模型路径
        if model_path is None:
            model_path = os.path.join(CURRENT_DIR, 'results', 'checkpoint_srgan.pth')
        
        self.model_path = model_path
        
        # 统计信息
        self.process_count = 0
        
        # 加载模型
        print(f"\n{'=' * 70}")
        print(f"📦 加载 SRGAN 模型...")
        print(f"{'=' * 70}")
        print(f"  模型路径: {model_path}")
        print(f"  设备: {self.device}")
        print(f"  内部放大: {scaling_factor}x")
        print(f"  输出放大: {output_scale}x")
        
        # 加载模型权重
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # 创建生成器
        self.model = Generator(
            large_kernel_size=large_kernel_size,
            small_kernel_size=small_kernel_size,
            n_channels=n_channels,
            n_blocks=n_blocks,
            scaling_factor=scaling_factor
        )
        
        self.model = self.model.to(self.device)
        self.model.load_state_dict(checkpoint['generator'])
        self.model.eval()
        
        # 半精度
        if self.half_precision:
            self.model = self.model.half()
            print(f"  半精度: 启用")
        
        print(f"✅ SRGAN 初始化完成")
        print(f"{'=' * 70}\n")
    
    def process(self, image):
        """
        处理图像
        
        Args:
            image: 输入图像
                   - numpy array: (H, W, 3), RGB, uint8, 0-255
                   - PIL Image
        
        Returns:
            numpy array: (H, W, 3), RGB, uint8, 0-255
        """
        # 转换输入
        if isinstance(image, np.ndarray):
            # numpy -> PIL
            pil_image = Image.fromarray(image.astype('uint8'), 'RGB')
        elif isinstance(image, Image.Image):
            pil_image = image.convert('RGB')
        else:
            raise ValueError(f"不支持的图像类型: {type(image)}")
        
        original_size = pil_image.size  # (width, height)
        
        # 图像预处理（转换为 imagenet-norm 格式）
        lr_img = convert_image(pil_image, source='pil', target='imagenet-norm')
        lr_img = lr_img.unsqueeze(0)  # (1, 3, H, W)
        
        # 转移到设备
        lr_img = lr_img.to(self.device)
        
        if self.half_precision:
            lr_img = lr_img.half()
        
        # 模型推理
        with torch.no_grad():
            sr_img = self.model(lr_img).squeeze(0).cpu()  # (3, H*scale, W*scale)
            
            # 转换回 float32（如果使用了半精度）
            if self.half_precision:
                sr_img = sr_img.float()
            
            # 转换为 PIL 图像（从 [-1, 1] 格式）
            sr_img_pil = convert_image(sr_img, source='[-1, 1]', target='pil')
        
        # 根据 output_scale 调整输出大小
        if self.output_scale != self.scaling_factor:
            # 计算目标大小
            target_width = int(original_size[0] * self.output_scale)
            target_height = int(original_size[1] * self.output_scale)
            target_size = (target_width, target_height)
            
            # 缩放到目标大小
            sr_img_pil = sr_img_pil.resize(target_size, Image.BICUBIC)
        
        # 转换为 numpy array
        output = np.array(sr_img_pil)
        
        # 更新统计
        self.process_count += 1
        
        return output
    
    def get_stats(self):
        """获取统计信息"""
        return {
            'model_path': self.model_path,
            'device': str(self.device),
            'internal_scaling': self.scaling_factor,
            'output_scale': self.output_scale,
            'half_precision': self.half_precision,
            'process_count': self.process_count
        }
    
    def __repr__(self):
        return (f"SRGANProcessor(device={self.device}, "
                f"internal={self.scaling_factor}x, "
                f"output={self.output_scale}x)")


def test_srgan_processor():
    """测试 SRGAN 处理器"""
    print("\n" + "=" * 70)
    print("🧪 测试 SRGAN 处理器")
    print("=" * 70 + "\n")
    
    # 创建测试图像
    test_image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    print(f"输入图像: shape={test_image.shape}, dtype={test_image.dtype}")
    
    # 初始化处理器
    model_path = os.path.join(CURRENT_DIR, 'results', 'checkpoint_srgan.pth')
    
    if not os.path.exists(model_path):
        print(f"\n⚠️  模型文件不存在: {model_path}")
        print("请确保模型文件在 SRGAN/results/ 目录下")
        return
    
    processor = SRGANProcessor(
        model_path=model_path,
        device='cuda',
        output_scale=2  # 2x 输出（与原始 test.py 一致）
    )
    
    # 处理图像
    print("\n处理图像...")
    import time
    start = time.time()
    output = processor.process(test_image)
    elapsed = time.time() - start
    
    print(f"输出图像: shape={output.shape}, dtype={output.dtype}")
    print(f"处理时间: {elapsed:.3f} 秒")
    
    # 统计信息
    print("\n统计信息:")
    stats = processor.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_srgan_processor()

