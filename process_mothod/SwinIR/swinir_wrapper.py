"""
SwinIR 包装器 - 用于 InterFuser 数据处理器集成

提供简单的接口来使用 SwinIR 进行图像处理
支持的任务：
  - sr: 超分辨率
  - denoise: 去噪
  - jpeg: JPEG 压缩伪影去除
"""

import sys
import os

# 添加当前目录到路径（swinir_wrapper.py 现在在 SwinIR/ 内部）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import torch
import numpy as np
import cv2
from contextlib import nullcontext

try:
    from .models.network_swinir import SwinIR
except ImportError as e:
    try:
        # 允许直接 `python swinir_wrapper.py` 或 `python example_usage.py` 运行
        from models.network_swinir import SwinIR
    except ImportError:
        print(f"⚠️  无法导入 SwinIR: {e}")
        print(f"请确保在正确的目录: {CURRENT_DIR}")
        print(f"swinir_wrapper.py 应该在 SwinIR/ 文件夹内部")
        raise


class SwinIRProcessor:
    """
    SwinIR 图像处理器包装类
    
    使用示例:
        processor = SwinIRProcessor(
            model_path='model_zoo/swinir/xxx.pth',
            task='sr',
            upscale=2
        )
        
        output = processor.process(input_image)
    """
    
    # 预定义的模型配置
    MODEL_CONFIGS = {
        'sr_x2': {
            'upscale': 2,
            'in_chans': 3,
            'img_size': 64,
            'window_size': 8,
            'img_range': 1.,
            'depths': [6, 6, 6, 6],
            'embed_dim': 60,
            'num_heads': [6, 6, 6, 6],
            'mlp_ratio': 2,
            'upsampler': 'pixelshuffledirect',
            'resi_connection': '1conv'
        },
        'sr_x4': {
            'upscale': 4,
            'in_chans': 3,
            'img_size': 64,
            'window_size': 8,
            'img_range': 1.,
            'depths': [6, 6, 6, 6, 6, 6],
            'embed_dim': 180,
            'num_heads': [6, 6, 6, 6, 6, 6],
            'mlp_ratio': 2,
            'upsampler': 'pixelshuffle',
            'resi_connection': '1conv'
        },
        'denoise': {
            'upscale': 1,
            'in_chans': 3,
            'img_size': 128,
            'window_size': 8,
            'img_range': 1.,
            'depths': [6, 6, 6, 6, 6, 6],
            'embed_dim': 180,
            'num_heads': [6, 6, 6, 6, 6, 6],
            'mlp_ratio': 2,
            'upsampler': '',
            'resi_connection': '1conv'
        },
        'jpeg': {
            'upscale': 1,
            'in_chans': 3,
            'img_size': 126,
            'window_size': 7,
            'img_range': 255.,
            'depths': [6, 6, 6, 6, 6, 6],
            'embed_dim': 180,
            'num_heads': [6, 6, 6, 6, 6, 6],
            'mlp_ratio': 2,
            'upsampler': '',
            'resi_connection': '1conv'
        }
    }
    
    def __init__(self, model_path, task='color_dn', upscale=1, device='cuda', half_precision=False,
                 noise=15, jpeg=40, training_patch_size=128, tile=None, tile_overlap=32):
        """
        初始化 SwinIR 处理器
        
        Args:
            model_path: 预训练模型路径
            task: 任务类型
                  - 'classical_sr': 经典超分辨率
                  - 'lightweight_sr': 轻量级超分辨率
                  - 'real_sr': 真实世界超分辨率
                  - 'gray_dn': 灰度图像去噪
                  - 'color_dn': 彩色图像去噪 (默认)
                  - 'jpeg_car': JPEG 压缩伪影去除
                  - 'color_jpeg_car': 彩色 JPEG 压缩伪影去除
                  - 'sr' or 'sr_x2': 2x 超分辨率（兼容旧版）
                  - 'sr_x4': 4x 超分辨率（兼容旧版）
            upscale: 放大倍数（SR 任务使用，默认 1）
            device: 'cuda' 或 'cpu'
            half_precision: 是否使用半精度（FP16）
            noise: 噪声等级，用于去噪任务 (15, 25, 50)，默认 15
            jpeg: JPEG 质量，用于 JPEG 修复任务 (10, 20, 30, 40)，默认 40
            training_patch_size: 训练时使用的 patch 大小，默认 128
            tile: 瓦片大小，None 表示整图处理，默认 None
            tile_overlap: 瓦片重叠大小，默认 32
        """
        _wants_cuda = str(device).startswith('cuda')
        self.device = device if (_wants_cuda and torch.cuda.is_available()) else 'cpu'
        if _wants_cuda and not torch.cuda.is_available():
            print("⚠️  CUDA 不可用，使用 CPU")
            self.device = 'cpu'
        if str(self.device).startswith('cuda'):
            try:
                torch.backends.cudnn.benchmark = True
            except Exception:
                pass
        
        self.task = task
        self.upscale = upscale
        self.half_precision = half_precision and str(self.device).startswith('cuda')
        self.noise = noise
        self.jpeg = jpeg
        self.training_patch_size = training_patch_size
        self.tile = tile
        self.tile_overlap = tile_overlap
        
        # 根据任务选择配置
        if task in ['sr', 'sr_x2', 'classical_sr', 'lightweight_sr', 'real_sr']:
            if upscale == 2:
                config_key = 'sr_x2'
            elif upscale == 4:
                config_key = 'sr_x4'
            else:
                config_key = 'sr_x2'  # 默认
        elif task in ['denoise', 'gray_dn', 'color_dn']:
            config_key = 'denoise'
        elif task in ['jpeg', 'jpeg_car', 'color_jpeg_car']:
            config_key = 'jpeg'
        else:
            raise ValueError(f"未知任务类型: {task}. 支持: classical_sr, lightweight_sr, real_sr, "
                           f"gray_dn, color_dn, jpeg_car, color_jpeg_car, sr, sr_x2, sr_x4")
        
        model_config = self.MODEL_CONFIGS[config_key].copy()
        
        # 对于 SR 任务，使用指定的 upscale
        if 'sr' in task:
            model_config['upscale'] = upscale
        
        # 创建模型
        print(f"📦 创建 SwinIR 模型: 任务={task}, 配置={config_key}")
        self.model = SwinIR(**model_config)
        
        # 加载权重
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        print(f"📂 加载模型权重: {model_path}")
        try:
            pretrained = torch.load(model_path, map_location='cpu')
            
            # 处理不同的权重格式
            if 'params' in pretrained:
                state_dict = pretrained['params']
            elif 'model' in pretrained:
                state_dict = pretrained['model']
            else:
                state_dict = pretrained
            
            self.model.load_state_dict(state_dict, strict=True)
            print("✅ 权重加载成功")
        except Exception as e:
            raise RuntimeError(f"加载模型权重失败: {e}")
        
        # 设置为评估模式
        self.model.eval()
        
        # 移动到指定设备
        self.model = self.model.to(self.device)
        
        # 半精度
        if self.half_precision:
            self.model = self.model.half()
            print("⚡ 启用半精度 (FP16)")
        
        # 统计信息
        self.process_count = 0
        
        print(f"✅ SwinIR 初始化完成")
        print(f"   任务: {task}")
        print(f"   设备: {self.device}")
        print(f"   放大倍数: {model_config['upscale']}")
        if task in ['denoise', 'gray_dn', 'color_dn']:
            print(f"   噪声等级: {noise}")
        if task in ['jpeg', 'jpeg_car', 'color_jpeg_car']:
            print(f"   JPEG 质量: {jpeg}")
        if tile is not None:
            print(f"   瓦片大小: {tile}")
            print(f"   瓦片重叠: {tile_overlap}")
    
    def process(self, image_np):
        """
        处理单张图像
        
        Args:
            image_np: numpy array, shape (H, W, 3), RGB, 0-255
        
        Returns:
            processed_image: numpy array, shape (H', W', 3), RGB, 0-255
                            对于 SR: H'=H*upscale, W'=W*upscale
                            对于其他任务: H'=H, W'=W
        """
        if not isinstance(image_np, np.ndarray):
            raise TypeError(f"输入必须是 numpy array，实际类型: {type(image_np)}")
        
        if image_np.ndim != 3 or image_np.shape[2] != 3:
            raise ValueError(f"输入图像必须是 (H, W, 3)，实际形状: {image_np.shape}")
        
        # 预处理
        img = image_np.astype(np.float32)
        
        # 根据任务调整输入范围
        if self.task == 'jpeg':
            # JPEG 任务使用 0-255 范围
            img_range = 255.0
        else:
            img_range = 1.0
            img = img / 255.0
        
        # 转换为 tensor: (H, W, 3) -> (1, 3, H, W)
        img_tensor = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0)
        img_tensor = img_tensor.to(self.device)
        
        if self.half_precision:
            img_tensor = img_tensor.half()
        
        def _forward_with_tile(x, tile_size, overlap):
            b, c, h, w = x.shape
            stride = tile_size - overlap
            # Determine scale factor
            if self.task in ['denoise', 'gray_dn', 'color_dn', 'jpeg', 'jpeg_car', 'color_jpeg_car']:
                s = 1  # no spatial scaling for denoise/jpeg tasks
            else:
                # For SR tasks, detect scale once using a small center crop
                yc = min(tile_size, h)
                xc = min(tile_size, w)
                y0c = (h - yc) // 2
                x0c = (w - xc) // 2
                with torch.no_grad():
                    test_out = self.model(x[:, :, y0c:y0c+yc, x0c:x0c+xc])
                sh = test_out.shape[-2] // yc
                s = max(1, sh)  # assume isotropic scale
            Hs, Ws = h * s, w * s
            out = torch.zeros((b, c, Hs, Ws), device=x.device, dtype=x.dtype)
            wei = torch.zeros((b, c, Hs, Ws), device=x.device, dtype=x.dtype)
            ys = list(range(0, max(h - tile_size + stride, 1), stride)) if h > tile_size else [0]
            xs = list(range(0, max(w - tile_size + stride, 1), stride)) if w > tile_size else [0]
            tile_batch = os.environ.get('DATA_PROCESSOR_TILE_BATCH', '').strip()
            try:
                tile_batch = int(tile_batch) if tile_batch else 4
            except Exception:
                tile_batch = 4
            tile_batch = max(1, tile_batch)

            positions = []
            for y in ys:
                y0 = min(y, max(h - tile_size, 0))
                y1 = min(y0 + tile_size, h)
                for x_ in xs:
                    x0 = min(x_, max(w - tile_size, 0))
                    x1 = min(x0 + tile_size, w)
                    positions.append((y0, y1, x0, x1))

            for i in range(0, len(positions), tile_batch):
                batch_pos = positions[i:i + tile_batch]
                patches = torch.cat([x[:, :, y0:y1, x0:x1] for (y0, y1, x0, x1) in batch_pos], dim=0)
                out_patches = self.model(patches)
                for j, (y0, y1, x0, x1) in enumerate(batch_pos):
                    ph = y1 - y0
                    pw = x1 - x0
                    Y0 = y0 * s
                    X0 = x0 * s
                    Y1 = Y0 + ph * s
                    X1 = X0 + pw * s
                    out[:, :, Y0:Y1, X0:X1] += out_patches[j:j+1]
                    wei[:, :, Y0:Y1, X0:X1] += 1
            wei = wei.clamp(min=1)
            return out / wei

        amp_enabled = bool(self.half_precision and str(self.device).startswith('cuda'))
        amp_ctx = torch.cuda.amp.autocast(enabled=amp_enabled) if str(self.device).startswith('cuda') else nullcontext()
        with torch.no_grad():
            with amp_ctx:
                if self.tile is not None and (img_tensor.shape[-2] > int(self.tile) or img_tensor.shape[-1] > int(self.tile)):
                    output_tensor = _forward_with_tile(img_tensor, int(self.tile), int(self.tile_overlap))
                else:
                    try:
                        output_tensor = self.model(img_tensor)
                    except RuntimeError as e:
                        if 'out of memory' in str(e).lower() and str(self.device).startswith('cuda'):
                            try:
                                torch.cuda.empty_cache()
                            except Exception:
                                pass
                            output_tensor = _forward_with_tile(img_tensor, 512, 32)
                        else:
                            raise
        
        # 后处理: (1, 3, H', W') -> (H', W', 3)
        output = output_tensor.squeeze(0).permute(1, 2, 0)
        
        # 转换回 numpy
        if self.half_precision:
            output = output.float()
        
        output = output.cpu().numpy()
        
        # 根据任务调整输出范围
        if self.task != 'jpeg':
            output = output * 255.0
        
        output = output.clip(0, 255).astype(np.uint8)
        
        # 更新统计
        self.process_count += 1
        
        return output
    
    def process_batch(self, images_list):
        """
        批量处理多张图像
        
        Args:
            images_list: list of numpy arrays, each (H, W, 3), RGB, 0-255
        
        Returns:
            results: list of numpy arrays
        """
        if not images_list:
            return []
        
        # 检查所有图像尺寸是否一致
        shapes = [img.shape for img in images_list]
        if len(set(shapes)) > 1:
            # 尺寸不一致，逐个处理
            return [self.process(img) for img in images_list]
        
        # 批量处理
        # 预处理
        imgs = []
        for img_np in images_list:
            img = img_np.astype(np.float32)
            if self.task != 'jpeg':
                img = img / 255.0
            imgs.append(torch.from_numpy(img).permute(2, 0, 1))
        
        batch = torch.stack(imgs).to(self.device)
        if self.half_precision:
            batch = batch.half()
        
        # 推理
        with torch.no_grad():
            outputs = self.model(batch)
        
        # 后处理
        results = []
        for output_tensor in outputs:
            output = output_tensor.permute(1, 2, 0)
            if self.half_precision:
                output = output.float()
            output = output.cpu().numpy()
            if self.task != 'jpeg':
                output = output * 255.0
            output = output.clip(0, 255).astype(np.uint8)
            results.append(output)
        
        self.process_count += len(images_list)
        
        return results
    
    def get_stats(self):
        """获取处理统计信息"""
        stats = {
            'task': self.task,
            'device': self.device,
            'upscale': self.upscale,
            'half_precision': self.half_precision,
            'process_count': self.process_count,
            'training_patch_size': self.training_patch_size,
        }
        
        # 添加任务特定的参数
        if self.task in ['denoise', 'gray_dn', 'color_dn']:
            stats['noise'] = self.noise
        if self.task in ['jpeg', 'jpeg_car', 'color_jpeg_car']:
            stats['jpeg'] = self.jpeg
        if self.tile is not None:
            stats['tile'] = self.tile
            stats['tile_overlap'] = self.tile_overlap
        
        return stats
    
    def __call__(self, image):
        """允许直接调用实例"""
        return self.process(image)
    
    def __repr__(self):
        base = f"SwinIRProcessor(task={self.task}, upscale={self.upscale}, device={self.device}"
        
        if self.task in ['denoise', 'gray_dn', 'color_dn']:
            base += f", noise={self.noise}"
        if self.task in ['jpeg', 'jpeg_car', 'color_jpeg_car']:
            base += f", jpeg={self.jpeg}"
        if self.tile is not None:
            base += f", tile={self.tile}"
        
        base += f", processed={self.process_count})"
        return base


def test_swinir_processor():
    """测试 SwinIR 处理器"""
    print("="*70)
    print("🧪 测试 SwinIR 处理器")
    print("="*70)
    
    # 创建测试图像
    test_image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    print(f"\n📸 测试图像形状: {test_image.shape}")
    
    # 测试不同任务（需要相应的模型文件）
    # 这里只演示如何使用
    print("\n示例用法:")
    print("""
    # 1. 彩色图像去噪（默认配置）
    processor_dn = SwinIRProcessor(
        model_path='model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth',
        task='color_dn',      # 默认
        noise=15,             # 默认
        training_patch_size=128  # 默认
    )
    output_dn = processor_dn.process(test_image)
    
    # 2. 超分辨率（2x）
    processor_sr = SwinIRProcessor(
        model_path='model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth',
        task='classical_sr',
        upscale=2
    )
    output_sr = processor_sr.process(test_image)
    
    # 3. JPEG 压缩伪影去除
    processor_jpeg = SwinIRProcessor(
        model_path='model_zoo/swinir/006_CAR_DFWB_s126w7_SwinIR-M_jpeg40.pth',
        task='jpeg_car',
        jpeg=40               # 默认
    )
    output_jpeg = processor_jpeg.process(test_image)
    
    # 4. 使用瓦片处理大图像
    processor_tile = SwinIRProcessor(
        model_path='model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth',
        task='classical_sr',
        upscale=2,
        tile=512,             # 使用 512x512 瓦片
        tile_overlap=32       # 默认重叠
    )
    output_tile = processor_tile.process(large_image)
    """)
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_swinir_processor()

