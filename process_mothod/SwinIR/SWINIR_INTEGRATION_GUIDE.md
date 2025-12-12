# 🔧 SwinIR 集成指南

本指南详细说明如何将 SwinIR 图像处理模块集成到 InterFuser 数据处理器中。

---

## 📋 目录

1. [环境准备](#1-环境准备)
2. [下载预训练模型](#2-下载预训练模型)
3. [集成方法](#3-集成方法)
4. [完整示例](#4-完整示例)
5. [性能优化](#5-性能优化)
6. [故障排查](#6-故障排查)

---

## 1. 环境准备

### 检查依赖

SwinIR 需要以下 Python 包：

```bash
# 检查是否已安装
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
python3 -c "import numpy; print(f'NumPy: {numpy.__version__}')"
```

### 安装缺失的依赖（如需要）

```bash
# 激活 interfuser 环境
conda activate interfuser

# 安装依赖（如果缺失）
pip install opencv-python pillow
```

---

## 2. 下载预训练模型

### 可用模型列表

| 模型名称 | 任务 | 下载链接 |
|---------|------|---------|
| `001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth` | 2x 超分辨率 | [下载](https://github.com/JingyunLiang/SwinIR/releases) |
| `002_lightweightSR_DIV2K_s64w8_SwinIR-S_x2.pth` | 2x 轻量级 SR | [下载](https://github.com/JingyunLiang/SwinIR/releases) |
| `005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth` | 彩色图像去噪 | [下载](https://github.com/JingyunLiang/SwinIR/releases) |
| `006_CAR_DFWB_s126w7_SwinIR-M_jpeg10.pth` | JPEG 压缩修复 | [下载](https://github.com/JingyunLiang/SwinIR/releases) |

### 下载方法

```bash
cd /home/nju/InterFuser/process_mothod/SwinIR

# 方法 1: 使用提供的脚本
bash download-weights.sh

# 方法 2: 手动下载
mkdir -p model_zoo/swinir
cd model_zoo/swinir
# 从 GitHub Releases 页面下载所需模型
```

---

## 3. 集成方法

### 方法 A: 集成到现有数据处理器 ⭐ 推荐

#### 步骤 1: 创建 SwinIR 包装器

在 `process_mothod/` 目录创建 `swinir_wrapper.py`:

```python
"""
SwinIR 包装器 - 用于 InterFuser 数据处理器集成
"""

import sys
sys.path.insert(0, '/home/nju/InterFuser/process_mothod/SwinIR')

import torch
import numpy as np
from models.network_swinir import SwinIR
import cv2


class SwinIRProcessor:
    """SwinIR 图像处理器"""
    
    def __init__(self, model_path, task='sr', upscale=2, device='cuda'):
        """
        初始化 SwinIR 处理器
        
        Args:
            model_path: 预训练模型路径
            task: 任务类型 ('sr', 'denoise', 'jpeg')
            upscale: 放大倍数（仅用于 SR）
            device: 'cuda' 或 'cpu'
        """
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.task = task
        self.upscale = upscale
        
        # 根据任务类型配置模型
        if task == 'sr':
            self.model = SwinIR(
                upscale=upscale, 
                in_chans=3, 
                img_size=64, 
                window_size=8,
                img_range=1., 
                depths=[6, 6, 6, 6], 
                embed_dim=60,
                num_heads=[6, 6, 6, 6], 
                mlp_ratio=2,
                upsampler='pixelshuffledirect', 
                resi_connection='1conv'
            )
        elif task == 'denoise':
            self.model = SwinIR(
                upscale=1, 
                in_chans=3, 
                img_size=128, 
                window_size=8,
                img_range=1., 
                depths=[6, 6, 6, 6, 6, 6], 
                embed_dim=180,
                num_heads=[6, 6, 6, 6, 6, 6], 
                mlp_ratio=2,
                upsampler='', 
                resi_connection='1conv'
            )
        elif task == 'jpeg':
            self.model = SwinIR(
                upscale=1, 
                in_chans=3, 
                img_size=126, 
                window_size=7,
                img_range=255., 
                depths=[6, 6, 6, 6, 6, 6], 
                embed_dim=180,
                num_heads=[6, 6, 6, 6, 6, 6], 
                mlp_ratio=2,
                upsampler='', 
                resi_connection='1conv'
            )
        
        # 加载权重
        pretrained = torch.load(model_path)
        self.model.load_state_dict(
            pretrained['params'] if 'params' in pretrained else pretrained,
            strict=True
        )
        self.model.eval()
        self.model = self.model.to(self.device)
        
        print(f"✅ SwinIR 已加载: {task} 任务, 设备: {self.device}")
    
    def process(self, image_np):
        """
        处理图像
        
        Args:
            image_np: numpy array, shape (H, W, 3), RGB, 0-255
        
        Returns:
            processed_image: numpy array
        """
        # 预处理
        img = image_np.astype(np.float32) / 255.0
        img = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0)
        img = img.to(self.device)
        
        # 推理
        with torch.no_grad():
            output = self.model(img)
        
        # 后处理
        output = output.squeeze(0).permute(1, 2, 0).cpu().numpy()
        output = (output * 255.0).clip(0, 255).astype(np.uint8)
        
        return output
    
    def __call__(self, image):
        """允许直接调用实例"""
        return self.process(image)
```

#### 步骤 2: 修改数据处理器配置

编辑 `/home/nju/InterFuser/sensor_data_processor_module/data_processor_config.py`:

```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        # ... 现有效果 ...
        
        # 🆕 SwinIR 处理
        'swinir': {
            'enabled': False,
            'task': 'sr',  # 'sr', 'denoise', 'jpeg'
            'model_path': '/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth',
            'upscale': 2,
            'device': 'cuda',  # 'cuda' 或 'cpu'
        },
    },
}
```

#### 步骤 3: 在数据处理器中添加 SwinIR 支持

编辑 `/home/nju/InterFuser/sensor_data_processor_module/data_processor.py`:

```python
# 在文件开头导入
import sys
sys.path.insert(0, '/home/nju/InterFuser/process_mothod')
from swinir_wrapper import SwinIRProcessor

class SensorDataProcessor:
    def __init__(self, config):
        # ... 现有初始化代码 ...
        
        # 🆕 初始化 SwinIR（如果启用）
        self.swinir_processor = None
        if config.get('rgb', {}).get('swinir', {}).get('enabled', False):
            swinir_cfg = config['rgb']['swinir']
            try:
                self.swinir_processor = SwinIRProcessor(
                    model_path=swinir_cfg['model_path'],
                    task=swinir_cfg.get('task', 'sr'),
                    upscale=swinir_cfg.get('upscale', 2),
                    device=swinir_cfg.get('device', 'cuda')
                )
            except Exception as e:
                print(f"⚠️  SwinIR 初始化失败: {e}")
                self.swinir_processor = None
    
    def _apply_rgb_effects(self, image, sensor_name):
        """应用 RGB 图像效果"""
        # ... 现有代码 ...
        
        # 🆕 应用 SwinIR（放在效果链的最后）
        if self.swinir_processor is not None:
            result = self.swinir_processor.process(result)
            self.stats['swinir_count'] = self.stats.get('swinir_count', 0) + 1
        
        return result
```

---

### 方法 B: 独立处理模块

如果不想修改现有数据处理器，可以在 agent 中单独使用：

```python
# 在 interfuser_agent.py 中

from process_mothod.swinir_wrapper import SwinIRProcessor

class InterfuserAgent(autonomous_agent.AutonomousAgent):
    def setup(self, path_to_conf_file):
        # ... 现有代码 ...
        
        # 初始化 SwinIR
        self.swinir = SwinIRProcessor(
            model_path='/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/xxx.pth',
            task='sr',
            upscale=2
        )
    
    def tick(self, input_data):
        # ... 获取 RGB 图像 ...
        
        # 应用 SwinIR
        rgb = self.swinir.process(rgb)
        
        # ... 继续处理 ...
```

---

## 4. 完整示例

### 示例 1: 图像超分辨率

```python
from swinir_wrapper import SwinIRProcessor
import cv2

# 初始化处理器
swinir = SwinIRProcessor(
    model_path='/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth',
    task='sr',
    upscale=2
)

# 读取图像
image = cv2.imread('input.jpg')
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# 处理
output = swinir.process(image)

# 保存
output_bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
cv2.imwrite('output.jpg', output_bgr)
```

### 示例 2: 图像去噪

```python
swinir = SwinIRProcessor(
    model_path='/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth',
    task='denoise'
)

# 添加噪声
noisy_image = image + np.random.normal(0, 15, image.shape)
noisy_image = noisy_image.clip(0, 255).astype(np.uint8)

# 去噪
denoised = swinir.process(noisy_image)
```

### 示例 3: 在数据处理配置中使用

```python
# 配置文件
CONFIG_SWINIR_SR = {
    'enabled': True,
    'rgb': {
        'swinir': {
            'enabled': True,
            'task': 'sr',
            'model_path': '/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth',
            'upscale': 2,
            'device': 'cuda',
        },
    },
    'advanced': {
        'print_stats': True,
    },
}

ACTIVE_CONFIG = CONFIG_SWINIR_SR
```

---

## 5. 性能优化

### GPU 加速

```python
# 确保使用 GPU
swinir = SwinIRProcessor(
    model_path='...',
    task='sr',
    device='cuda'  # 使用 GPU
)
```

### 批处理

如果需要处理多张图像，可以修改包装器支持批处理：

```python
def process_batch(self, images_list):
    """批量处理图像"""
    # 将所有图像堆叠成 batch
    imgs = [torch.from_numpy(img.astype(np.float32) / 255.0).permute(2, 0, 1) 
            for img in images_list]
    batch = torch.stack(imgs).to(self.device)
    
    with torch.no_grad():
        outputs = self.model(batch)
    
    # 分离并转换
    results = []
    for output in outputs:
        out_np = output.permute(1, 2, 0).cpu().numpy()
        out_np = (out_np * 255.0).clip(0, 255).astype(np.uint8)
        results.append(out_np)
    
    return results
```

### 半精度推理（FP16）

```python
# 使用半精度加速
self.model = self.model.half()

# 在 process 中
img = img.half()  # 转换输入为 FP16
```

---

## 6. 故障排查

### 问题 1: 导入错误

```
ModuleNotFoundError: No module named 'models.network_swinir'
```

**解决方法**:
```python
import sys
sys.path.insert(0, '/home/nju/InterFuser/process_mothod/SwinIR')
```

### 问题 2: CUDA 内存不足

```
RuntimeError: CUDA out of memory
```

**解决方法**:
1. 使用 CPU: `device='cpu'`
2. 减小输入图像尺寸
3. 使用轻量级模型

### 问题 3: 模型加载失败

```
RuntimeError: Error(s) in loading state_dict
```

**解决方法**:
- 检查模型路径是否正确
- 确认任务类型与模型匹配
- 使用 `strict=False` 加载（不推荐）

### 问题 4: 处理速度慢

**优化建议**:
- 使用 GPU
- 启用 FP16 推理
- 使用轻量级模型
- 仅在关键帧处理

---

## 📚 参考资源

- [SwinIR 官方仓库](https://github.com/JingyunLiang/SwinIR)
- [SwinIR 论文](https://arxiv.org/abs/2108.10257)
- [预训练模型下载](https://github.com/JingyunLiang/SwinIR/releases)

---

**更新日期**: 2025-11-04  
**版本**: 1.0

