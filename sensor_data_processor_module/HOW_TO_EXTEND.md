# 🔧 数据处理器扩展指南

本文档详细说明如何在现有的数据处理系统中添加新的处理方法。

---

## 📋 目录

1. [快速开关所有处理](#1-快速开关所有处理)
2. [添加新的 RGB 图像处理](#2-添加新的-rgb-图像处理)
3. [添加新的 LiDAR 处理](#3-添加新的-lidar-处理)
4. [添加新的传感器类型](#4-添加新的传感器类型)
5. [创建新的预设配置](#5-创建新的预设配置)
6. [完整示例](#6-完整示例)

---

## 1. 快速开关所有处理

### 方法 1：使用总开关（最简单）⭐

编辑 `data_processor_config.py`：

```python
# 在文件顶部找到这一行
ENABLE_ALL_PROCESSING = True  # ← 改为 False 即可关闭所有处理！
```

**关闭处理：**
```python
ENABLE_ALL_PROCESSING = False
```

**开启处理：**
```python
ENABLE_ALL_PROCESSING = True
```

### 方法 2：使用预设配置

编辑 `data_processor_config.py` 文件末尾：

```python
# 关闭所有处理
ACTIVE_CONFIG = CONFIG_NO_PROCESSING

# 或使用其他预设
ACTIVE_CONFIG = CONFIG_MILD_NOISE      # 轻度噪声
ACTIVE_CONFIG = CONFIG_MODERATE_NOISE  # 中度噪声
ACTIVE_CONFIG = CONFIG_SEVERE_NOISE    # 重度噪声
```

### 方法 3：单独控制每个效果

在 `DATA_PROCESSOR_CONFIG` 中修改各个效果的 `enabled` 参数：

```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,  # 保持总开关开启
    'rgb': {
        'add_gaussian_noise': {
            'enabled': False,  # ← 关闭此效果
            # ...
        },
        'brightness': {
            'enabled': True,   # ← 开启此效果
            # ...
        },
    },
}
```

---

## 2. 添加新的 RGB 图像处理

### 步骤 1：在配置文件中添加新效果

编辑 `data_processor_config.py`：

```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        # ... 现有效果 ...
        
        # 🆕 添加你的新效果
        'my_new_effect': {
            'enabled': False,  # 默认关闭
            'param1': 1.0,     # 自定义参数
            'param2': 'value', # 可以是任何类型
        },
    },
}
```

### 步骤 2：在处理器中实现效果

编辑 `data_processor.py`，找到 `_apply_rgb_effects` 方法：

```python
def _apply_rgb_effects(self, image, sensor_name):
    """应用 RGB 图像效果"""
    if not isinstance(image, np.ndarray):
        return image
    
    rgb_config = self.config.get('rgb', {})
    result = image.copy()
    
    # ... 现有效果处理 ...
    
    # 🆕 添加你的新效果处理
    if rgb_config.get('my_new_effect', {}).get('enabled', False):
        cfg = rgb_config['my_new_effect']
        result = self._apply_my_new_effect(result, cfg, sensor_name)
    
    return result
```

### 步骤 3：实现具体的处理函数

在 `data_processor.py` 中添加新方法：

```python
def _apply_my_new_effect(self, image, config, sensor_name):
    """
    应用自定义效果
    
    Args:
        image: numpy array, shape (H, W, 3)
        config: dict, 配置参数
        sensor_name: str, 传感器名称
    
    Returns:
        processed_image: numpy array
    """
    param1 = config.get('param1', 1.0)
    param2 = config.get('param2', 'default')
    
    # 实现你的处理逻辑
    processed = image.copy()
    
    # 例如：简单的缩放
    processed = (processed * param1).clip(0, 255).astype(np.uint8)
    
    # 如果启用了对比保存，记录原始图像
    if self.config.get('advanced', {}).get('save_comparison', False):
        self.comparison_data['my_new_effect'].append({
            'frame': self.frame_count,
            'sensor': sensor_name,
            'original': image.copy(),
            'processed': processed.copy()
        })
    
    return processed
```

### 步骤 4（可选）：添加统计信息

如果需要统计效果使用情况，在 `__init__` 中初始化：

```python
def __init__(self, config):
    # ... 现有初始化代码 ...
    
    # 添加到对比数据字典
    self.comparison_data = {
        # ... 现有键 ...
        'my_new_effect': [],
    }
```

---

## 3. 添加新的 LiDAR 处理

### 步骤 1：配置文件

```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'lidar': {
        # ... 现有效果 ...
        
        # 🆕 新的 LiDAR 效果
        'intensity_noise': {
            'enabled': False,
            'std': 0.1,  # 强度噪声标准差
        },
    },
}
```

### 步骤 2：实现处理

编辑 `data_processor.py` 中的 `process_lidar` 方法：

```python
def process_lidar(self, lidar_data):
    """
    处理 LiDAR 点云数据
    
    Args:
        lidar_data: numpy array, shape (N, 4) [x, y, z, intensity]
    
    Returns:
        processed_lidar: numpy array
    """
    if not self.config.get('enabled', True):
        return lidar_data
    
    lidar_config = self.config.get('lidar', {})
    result = lidar_data.copy()
    
    # ... 现有效果 ...
    
    # 🆕 强度噪声
    if lidar_config.get('intensity_noise', {}).get('enabled', False):
        std = lidar_config['intensity_noise'].get('std', 0.1)
        if result.shape[1] >= 4:  # 确保有强度通道
            noise = np.random.normal(0, std, result[:, 3].shape)
            result[:, 3] = np.clip(result[:, 3] + noise, 0, 1)
            self.stats['lidar_intensity_noise_count'] += 1
    
    return result
```

---

## 4. 添加新的传感器类型

假设你想添加一个新的传感器类型（如深度相机）：

### 步骤 1：配置文件

```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    # ... rgb, lidar 等 ...
    
    # 🆕 新传感器类型
    'depth': {
        'noise': {
            'enabled': False,
            'std': 0.05,  # 深度噪声（米）
        },
        'missing_depth': {
            'enabled': False,
            'rate': 0.1,  # 10% 深度值缺失
        },
    },
}
```

### 步骤 2：添加处理方法

在 `data_processor.py` 中添加新方法：

```python
def process_depth(self, depth_data, sensor_name='depth'):
    """
    处理深度图数据
    
    Args:
        depth_data: numpy array, shape (H, W) or (H, W, 1)
        sensor_name: str
    
    Returns:
        processed_depth: numpy array
    """
    if not self.config.get('enabled', True):
        return depth_data
    
    depth_config = self.config.get('depth', {})
    result = depth_data.copy()
    
    # 深度噪声
    if depth_config.get('noise', {}).get('enabled', False):
        std = depth_config['noise'].get('std', 0.05)
        noise = np.random.normal(0, std, result.shape)
        result += noise
        self.stats['depth_noise_count'] += 1
    
    # 深度缺失
    if depth_config.get('missing_depth', {}).get('enabled', False):
        rate = depth_config['missing_depth'].get('rate', 0.1)
        mask = np.random.random(result.shape) < rate
        result[mask] = 0  # 或 np.nan
        self.stats['depth_missing_count'] += 1
    
    return result
```

### 步骤 3：在 agent 中使用

在 `interfuser_agent_complete.py` 的 `tick` 方法中：

```python
def tick(self, input_data):
    # ... 现有代码 ...
    
    # 🆕 处理深度数据（如果有）
    if 'depth' in input_data:
        depth = input_data['depth'][1]
        depth = self.data_processor.process_depth(depth, 'depth_front')
        result['depth'] = depth
    
    return result
```

---

## 5. 创建新的预设配置

在 `data_processor_config.py` 末尾添加：

```python
# ============================================================
# 🆕 你的自定义预设
# ============================================================

CONFIG_CUSTOM_WEATHER = {
    'enabled': True,
    'rgb': {
        'brightness': {
            'enabled': True,
            'factor': 0.6,  # 模拟阴天
        },
        'blur': {
            'enabled': True,
            'kernel_size': 3,  # 轻微雾化
        },
        'saturation': {
            'enabled': True,
            'factor': 0.8,  # 降低饱和度
        },
    },
    'lidar': {
        'range_limit': {
            'enabled': True,
            'max_range': 50.0,  # 恶劣天气能见度下降
        },
    },
    'gps': {
        'drift': {
            'enabled': True,
            'std': 1.0,  # 信号干扰
        },
    },
    'advanced': {
        'log_data': False,
        'save_comparison': False,
        'print_stats': True,
    },
}

# 使用新配置
# ACTIVE_CONFIG = CONFIG_CUSTOM_WEATHER
```

---

## 6. 完整示例：添加"运动模糊"效果

### 步骤 1：配置（data_processor_config.py）

```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        # ... 其他效果 ...
        
        # 🆕 运动模糊
        'motion_blur': {
            'enabled': False,
            'kernel_size': 15,  # 模糊核大小
            'angle': 0,         # 模糊角度（度）
        },
    },
}
```

### 步骤 2：实现效果（data_processor.py）

在 `_apply_rgb_effects` 中添加：

```python
def _apply_rgb_effects(self, image, sensor_name):
    """应用 RGB 图像效果"""
    if not isinstance(image, np.ndarray):
        return image
    
    rgb_config = self.config.get('rgb', {})
    result = image.copy()
    
    # ... 其他效果 ...
    
    # 🆕 运动模糊
    if rgb_config.get('motion_blur', {}).get('enabled', False):
        cfg = rgb_config['motion_blur']
        result = self._apply_motion_blur(result, cfg, sensor_name)
    
    return result

def _apply_motion_blur(self, image, config, sensor_name):
    """
    应用运动模糊效果
    
    Args:
        image: numpy array, shape (H, W, 3)
        config: dict
        sensor_name: str
    
    Returns:
        blurred_image: numpy array
    """
    import cv2
    
    kernel_size = config.get('kernel_size', 15)
    angle = config.get('angle', 0)
    
    # 创建运动模糊核
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size - 1) / 2), :] = np.ones(kernel_size)
    kernel = kernel / kernel_size
    
    # 旋转核
    if angle != 0:
        M = cv2.getRotationMatrix2D(
            (kernel_size / 2, kernel_size / 2), 
            angle, 
            1
        )
        kernel = cv2.warpAffine(kernel, M, (kernel_size, kernel_size))
    
    # 应用模糊
    blurred = cv2.filter2D(image, -1, kernel)
    
    # 统计
    self.stats['motion_blur_count'] = self.stats.get('motion_blur_count', 0) + 1
    
    # 保存对比（如果启用）
    if self.config.get('advanced', {}).get('save_comparison', False):
        self.comparison_data['motion_blur'].append({
            'frame': self.frame_count,
            'sensor': sensor_name,
            'original': image.copy(),
            'processed': blurred.copy(),
            'kernel_size': kernel_size,
            'angle': angle,
        })
    
    return blurred
```

### 步骤 3：初始化统计（data_processor.py）

在 `__init__` 方法中：

```python
def __init__(self, config):
    # ... 现有代码 ...
    
    self.comparison_data = {
        # ... 现有键 ...
        'motion_blur': [],
    }
```

### 步骤 4：测试新效果

修改 `data_processor_config.py`：

```python
ENABLE_ALL_PROCESSING = True

DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        'motion_blur': {
            'enabled': True,   # ← 开启测试
            'kernel_size': 15,
            'angle': 45,
        },
    },
    'advanced': {
        'print_stats': True,  # 查看统计信息
    },
}
```

### 步骤 5：创建预设配置

```python
# 高速运动场景预设
CONFIG_HIGH_SPEED = {
    'enabled': True,
    'rgb': {
        'motion_blur': {
            'enabled': True,
            'kernel_size': 21,
            'angle': 0,  # 水平运动模糊
        },
    },
    'gps': {
        'update_delay': {
            'enabled': True,
            'frames': 2,  # 延迟更新
        },
    },
}

# 使用预设
# ACTIVE_CONFIG = CONFIG_HIGH_SPEED
```

---

## 📝 最佳实践

### 1. 命名规范

- **配置键名**：使用 `snake_case`，清晰描述效果
- **函数名**：`_apply_效果名`，保持一致性
- **参数名**：使用常见术语（如 `std`, `rate`, `factor`）

### 2. 默认值

- 所有新效果默认 `'enabled': False`
- 提供合理的默认参数值
- 在函数中使用 `.get()` 提供备用默认值

### 3. 性能考虑

```python
# ✅ 好的做法：提前检查是否启用
if config.get('my_effect', {}).get('enabled', False):
    result = self._apply_my_effect(result, config['my_effect'])

# ❌ 避免：无条件处理
result = self._apply_my_effect(result, config)  # 即使未启用也会执行
```

### 4. 参数验证

```python
def _apply_my_effect(self, image, config, sensor_name):
    # 参数验证
    param = config.get('param', 1.0)
    if param < 0 or param > 10:
        print(f"Warning: param {param} out of range [0, 10], using default")
        param = 1.0
    
    # 处理逻辑
    # ...
```

### 5. 统计和日志

```python
# 添加计数统计
self.stats[f'{effect_name}_count'] += 1

# 记录参数信息（用于调试）
if self.config.get('advanced', {}).get('log_data', False):
    print(f"Applied {effect_name} with param={param}")
```

---

## 🔍 调试技巧

### 1. 启用详细日志

```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'advanced': {
        'log_data': True,        # 打印处理信息
        'print_stats': True,     # 打印统计信息
        'save_comparison': True, # 保存对比图像
    },
}
```

### 2. 逐步测试

```python
# 只启用一个效果进行测试
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        'my_new_effect': {'enabled': True, ...},
        # 其他都设为 enabled: False
    },
}
```

### 3. 使用打印调试

```python
def _apply_my_effect(self, image, config, sensor_name):
    print(f"[DEBUG] Processing {sensor_name}")
    print(f"[DEBUG] Input shape: {image.shape}")
    print(f"[DEBUG] Config: {config}")
    
    # ... 处理逻辑 ...
    
    print(f"[DEBUG] Output shape: {result.shape}")
    return result
```

---

## 📚 参考资源

- **OpenCV 文档**: https://docs.opencv.org/
- **NumPy 文档**: https://numpy.org/doc/
- **CARLA 传感器参考**: https://carla.readthedocs.io/en/latest/ref_sensors/

---

## ❓ 常见问题

### Q1: 修改配置后没有生效？

**A**: 确保：
1. `ENABLE_ALL_PROCESSING = True`
2. 具体效果的 `'enabled': True`
3. 修改了正确的 `ACTIVE_CONFIG`

### Q2: 如何临时关闭某个效果？

**A**: 在配置中将该效果的 `enabled` 设为 `False`，或使用 `CONFIG_NO_PROCESSING`。

### Q3: 处理速度太慢？

**A**: 
1. 关闭 `save_comparison` 和 `log_data`
2. 减少图像处理操作（如大核模糊）
3. 使用优化的 NumPy 操作代替循环

### Q4: 如何保存处理后的数据供分析？

**A**: 启用 `save_comparison`，处理后的数据会保存在 `comparison_data` 中，可在 `destroy()` 时导出。

---

**更新日期**: 2025-10-07  
**版本**: 1.0  
**维护者**: InterFuser Project

