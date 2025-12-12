# 🎛️ 数据处理控制 - 快速参考

**适用于**: 需要快速开关数据处理或切换配置的用户

---

## 🚀 3 种控制方法

### ⭐ 方法 1：总开关（最简单）

**文件**: `data_processor_config.py`  
**位置**: 文件开头

```python
# 找到这一行（第 34 行左右）
ENABLE_ALL_PROCESSING = True   # ← 改为 False 关闭所有处理
```

**操作**:
- 关闭所有处理: `False`
- 开启所有处理: `True`

---

### 🎯 方法 2：切换预设配置

**文件**: `data_processor_config.py`  
**位置**: 文件末尾（第 368 行左右）

```python
# 找到这一行
ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG

# 替换为以下任一配置：
ACTIVE_CONFIG = CONFIG_NO_PROCESSING   # 无处理（原始数据）
ACTIVE_CONFIG = CONFIG_MILD_NOISE      # 轻度噪声
ACTIVE_CONFIG = CONFIG_MODERATE_NOISE  # 中度噪声
ACTIVE_CONFIG = CONFIG_SEVERE_NOISE    # 重度噪声
ACTIVE_CONFIG = CONFIG_SENSOR_FAILURE  # 传感器故障
```

**预设配置说明**:

| 配置名称 | 说明 | 适用场景 |
|---------|------|---------|
| `CONFIG_NO_PROCESSING` | 完全不处理 | 基线测试、性能对比 |
| `CONFIG_MILD_NOISE` | 轻微噪声 | 轻度鲁棒性测试 |
| `CONFIG_MODERATE_NOISE` | 中等噪声 | 一般鲁棒性测试 |
| `CONFIG_SEVERE_NOISE` | 严重噪声 | 极端场景测试 |
| `CONFIG_SENSOR_FAILURE` | 传感器故障 | 故障容忍性测试 |

---

### 🔧 方法 3：自定义单个效果

**文件**: `data_processor_config.py`  
**位置**: `DATA_PROCESSOR_CONFIG` 字典内

```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,  # 总开关
    'rgb': {
        'add_gaussian_noise': {
            'enabled': False,  # ← 改为 True 启用此效果
            'mean': 0,
            'std': 10,
        },
        'brightness': {
            'enabled': False,  # ← 改为 True 启用此效果
            'factor': 1.2,
        },
        # ... 其他效果
    },
    # ... 其他传感器
}
```

---

## 📋 快速操作步骤

### 场景 1: 完全关闭数据处理（测试基线）

```bash
# 1. 编辑配置文件
vim sensor_data_processor_module/data_processor_config.py

# 2. 修改第 34 行
ENABLE_ALL_PROCESSING = False

# 3. 保存并运行评估
./sensor_data_processor_module/quick_test.sh
```

### 场景 2: 切换到轻度噪声测试

```bash
# 1. 编辑配置文件
vim sensor_data_processor_module/data_processor_config.py

# 2. 修改文件末尾（第 368 行）
ACTIVE_CONFIG = CONFIG_MILD_NOISE

# 3. 保存并运行评估
./sensor_data_processor_module/quick_test.sh
```

### 场景 3: 只启用图像模糊

```bash
# 1. 编辑配置文件
vim sensor_data_processor_module/data_processor_config.py

# 2. 确保总开关开启
ENABLE_ALL_PROCESSING = True

# 3. 在 DATA_PROCESSOR_CONFIG 中找到并修改
'blur': {
    'enabled': True,      # ← 改为 True
    'kernel_size': 5,
},

# 4. 确保其他效果都是 enabled: False

# 5. 使用自定义配置
ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG

# 6. 保存并运行
./sensor_data_processor_module/quick_test.sh
```

---

## 🔍 验证配置是否生效

运行评估后，查看输出：

```
======================================================================
🔧 Data Processor Initialized
======================================================================
  Enabled: True                          ← 应该显示你的设置
  RGB Effects: ['blur']                  ← 显示启用的效果
  LiDAR Effects: []
  Other Effects: []
======================================================================
```

在评估结束时：

```
======================================================================
🔧 Data Processor Final Statistics
======================================================================
  Total Frames: 150
  RGB processed: 150
  Blur applied: 150                      ← 确认效果被应用
======================================================================
```

---

## 📝 常用配置组合

### 组合 1: 纯净基线（无任何处理）

```python
ENABLE_ALL_PROCESSING = False
```

### 组合 2: 雨天模拟

```python
ENABLE_ALL_PROCESSING = True

DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        'brightness': {'enabled': True, 'factor': 0.7},  # 降低亮度
        'blur': {'enabled': True, 'kernel_size': 3},     # 轻微模糊
        'pixel_dropout': {'enabled': True, 'rate': 0.02}, # 雨滴遮挡
    },
    'lidar': {
        'range_limit': {'enabled': True, 'max_range': 50.0}, # 能见度下降
    },
}

ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG
```

### 组合 3: 夜间模拟

```python
ENABLE_ALL_PROCESSING = True

DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        'brightness': {'enabled': True, 'factor': 0.3},     # 严重降低亮度
        'add_gaussian_noise': {'enabled': True, 'std': 15}, # 增加噪声
        'saturation': {'enabled': True, 'factor': 0.5},     # 降低饱和度
    },
}

ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG
```

### 组合 4: 传感器老化

```python
ENABLE_ALL_PROCESSING = True

DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        'add_gaussian_noise': {'enabled': True, 'std': 12},
        'contrast': {'enabled': True, 'factor': 0.8},
    },
    'lidar': {
        'noise': {'enabled': True, 'std': 0.05},
        'dropout': {'enabled': True, 'rate': 0.15},
    },
    'gps': {
        'drift': {'enabled': True, 'std': 0.8},
    },
}

ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG
```

---

## ⚡ 性能优化提示

如果处理速度慢，关闭调试功能：

```python
DATA_PROCESSOR_CONFIG = {
    # ... 其他配置 ...
    'advanced': {
        'log_data': False,         # ← 关闭日志
        'save_comparison': False,  # ← 关闭图像保存
        'print_stats': True,       # ← 只保留统计信息
    },
}
```

---

## 🛠️ 故障排查

| 问题 | 检查项 | 解决方法 |
|-----|--------|---------|
| 配置没生效 | `ENABLE_ALL_PROCESSING` | 确保为 `True` |
| 效果没应用 | 具体效果的 `enabled` | 改为 `True` |
| 看不到统计信息 | `print_stats` | 改为 `True` |
| 找不到配置 | `ACTIVE_CONFIG` | 检查指向正确的配置字典 |
| 处理太慢 | `save_comparison`, `log_data` | 改为 `False` |

---

## 📚 详细文档

- **扩展指南**: `HOW_TO_EXTEND.md` - 如何添加新的处理方法
- **评估指南**: `EVALUATION_GUIDE.md` - 如何运行评估
- **同步指南**: `SYNC_AND_PERFORMANCE_GUIDE.md` - 性能优化
- **快速测试**: `QUICK_TEST_GUIDE.md` - 快速验证功能

---

**快速链接**:
```bash
# 查看配置文件
cat sensor_data_processor_module/data_processor_config.py | grep -A 5 "ENABLE_ALL"

# 查看当前激活的配置
cat sensor_data_processor_module/data_processor_config.py | grep "ACTIVE_CONFIG"

# 快速测试
./sensor_data_processor_module/quick_test.sh
```

---

**最后更新**: 2025-10-07

