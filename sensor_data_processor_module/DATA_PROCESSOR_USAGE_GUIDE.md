# 传感器数据处理器使用指南

## 📋 目录
- [概述](#概述)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [集成到 InterfuserAgent](#集成到-interfuseragent)
- [预设配置](#预设配置)
- [高级功能](#高级功能)
- [常见问题](#常见问题)

---

## 概述

传感器数据处理器（SensorDataProcessor）是一个用于在模拟器数据传递给 agent 之前对数据进行拦截和编辑的工具。

### 支持的传感器类型
- **RGB 相机**: 噪声、亮度、模糊、对比度、饱和度、像素丢失、色彩偏移
- **LiDAR**: 位置噪声、点云丢失、距离限制、强度噪声
- **GPS**: 位置漂移、随机跳变
- **速度传感器**: 测量误差、系统偏差
- **罗盘**: 方向误差、磁偏角

### 文件结构
```
leaderboard/team_code/
├── data_processor.py              # 数据处理器实现
├── data_processor_config.py       # 配置文件
└── interfuser_agent_with_processor_example.py  # 集成示例
```

---

## 快速开始

### 步骤 1: 测试数据处理器

```bash
cd /home/nju/InterFuser/leaderboard/team_code
source /home/nju/anaconda2/etc/profile.d/conda.sh
conda activate interfuser
python data_processor.py
```

**预期输出**:
```
Testing SensorDataProcessor...

1. Testing RGB processing...
   Original shape: (600, 800, 3), Processed shape: (600, 800, 3)

2. Testing LiDAR processing...
   Original points: 10000, Processed points: 8500

3. Testing GPS processing...
   Original GPS: [40. -75.], Processed GPS: [40.23 -74.87]

...
✅ All tests completed successfully!
```

### 步骤 2: 选择配置

编辑 `data_processor_config.py` 文件，选择配置：

```python
# 在文件末尾修改
ACTIVE_CONFIG = CONFIG_MODERATE_NOISE  # 使用中度噪声配置
```

可选配置：
- `DATA_PROCESSOR_CONFIG` - 默认（所有处理关闭）
- `CONFIG_MILD_NOISE` - 轻度噪声
- `CONFIG_MODERATE_NOISE` - 中度噪声
- `CONFIG_SEVERE_NOISE` - 严重噪声
- `CONFIG_SENSOR_FAILURE` - 传感器故障模拟

### 步骤 3: 集成到 Agent

#### 方法 A: 修改现有的 interfuser_agent.py

```bash
# 备份原文件
cp interfuser_agent.py interfuser_agent_backup.py

# 然后按照下面的说明修改
```

**关键修改**:

1. **导入模块**（文件顶部）:
```python
from team_code.data_processor import SensorDataProcessor
from team_code.data_processor_config import ACTIVE_CONFIG
```

2. **初始化处理器**（`setup()` 方法中，约第 210 行）:
```python
def setup(self, path_to_conf_file):
    # ... 现有代码 ...
    
    # 初始化数据处理器
    self.data_processor = SensorDataProcessor(ACTIVE_CONFIG)
    print("=" * 60)
    print("Data Processor Enabled:")
    summary = self.data_processor.get_config_summary()
    for key, value in summary.items():
        if value and (not isinstance(value, list) or value):
            print(f"  {key}: {value}")
    print("=" * 60)
```

3. **处理数据**（`tick()` 方法中，约第 320-365 行）:

**修改前**:
```python
def tick(self, input_data):
    rgb = cv2.cvtColor(input_data["rgb"][1][:, :, :3], cv2.COLOR_BGR2RGB)
    rgb_left = cv2.cvtColor(input_data["rgb_left"][1][:, :, :3], cv2.COLOR_BGR2RGB)
    rgb_right = cv2.cvtColor(input_data["rgb_right"][1][:, :, :3], cv2.COLOR_BGR2RGB)
    gps = input_data["gps"][1][:2]
    speed = input_data["speed"][1]["speed"]
    compass = input_data["imu"][1][-1]
```

**修改后**:
```python
def tick(self, input_data):
    # 提取原始数据
    rgb = cv2.cvtColor(input_data["rgb"][1][:, :, :3], cv2.COLOR_BGR2RGB)
    rgb_left = cv2.cvtColor(input_data["rgb_left"][1][:, :, :3], cv2.COLOR_BGR2RGB)
    rgb_right = cv2.cvtColor(input_data["rgb_right"][1][:, :, :3], cv2.COLOR_BGR2RGB)
    gps = input_data["gps"][1][:2]
    speed = input_data["speed"][1]["speed"]
    compass = input_data["imu"][1][-1]
    
    if math.isnan(compass):
        compass = 0.0
    
    # 🔥 处理数据 🔥
    rgb = self.data_processor.process_rgb(rgb, 'rgb')
    rgb_left = self.data_processor.process_rgb(rgb_left, 'rgb_left')
    rgb_right = self.data_processor.process_rgb(rgb_right, 'rgb_right')
    gps = self.data_processor.process_gps(gps)
    speed = self.data_processor.process_speed(speed)
    compass = self.data_processor.process_compass(compass)
```

**LiDAR 处理**（在 `tick()` 方法的 LiDAR 部分，约第 346-360 行）:

**在坐标转换前添加**:
```python
# 提取 LiDAR 数据
lidar_data = input_data['lidar'][1]
result['raw_lidar'] = lidar_data

lidar_unprocessed = lidar_data[:, :3]
lidar_unprocessed[:, 1] *= -1

# 🔥 处理 LiDAR 🔥
if lidar_data.shape[1] >= 4:
    lidar_with_intensity = np.column_stack([lidar_unprocessed, lidar_data[:, 3:]])
    lidar_with_intensity = self.data_processor.process_lidar(lidar_with_intensity)
    lidar_unprocessed = lidar_with_intensity[:, :3]
else:
    lidar_with_dummy = np.column_stack([lidar_unprocessed, np.ones((len(lidar_unprocessed), 1))])
    lidar_with_dummy = self.data_processor.process_lidar(lidar_with_dummy)
    lidar_unprocessed = lidar_with_dummy[:, :3]

# 继续坐标转换
full_lidar = transform_2d_points(...)
```

4. **帧计数**（`run_step()` 方法中，约第 385 行）:
```python
@torch.no_grad()
def run_step(self, input_data, timestamp):
    if not self.initialized:
        self._init()
    
    self.step += 1
    
    # 🔥 更新帧计数 🔥
    if self.step % self.skip_frames == 0 or self.step <= 4:
        self.data_processor.next_frame()
    
    if self.step % self.skip_frames != 0 and self.step > 4:
        return self.prev_control
    
    # ... 继续 ...
```

#### 方法 B: 使用示例文件（推荐用于测试）

```bash
cd /home/nju/InterFuser/leaderboard/team_code

# 查看示例文件
cat interfuser_agent_with_processor_example.py
```

### 步骤 4: 运行评估

```bash
cd /home/nju/InterFuser/evaluation_scripts

# 启动 CARLA 服务器（终端 1）
./start_carla_server.sh

# 运行评估（终端 2）
./run_evaluation.sh town05
```

---

## 配置说明

### 配置结构

```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,  # 全局开关
    
    'rgb': {
        'add_gaussian_noise': {
            'enabled': False,
            'mean': 0,
            'std': 10,
        },
        # ... 更多 RGB 处理
    },
    
    'lidar': {
        'noise': {...},
        'dropout': {...},
        # ... 更多 LiDAR 处理
    },
    
    # ... 其他传感器
}
```

### RGB 相机配置

| 参数 | 说明 | 取值范围 |
|------|------|----------|
| `add_gaussian_noise.std` | 高斯噪声标准差 | 0-50（推荐 5-25） |
| `brightness.factor` | 亮度系数 | 0.5-2.0（1.0=不变） |
| `blur.kernel_size` | 模糊核大小 | 3, 5, 7, 9（奇数） |
| `contrast.factor` | 对比度系数 | 0.5-2.0（1.0=不变） |
| `saturation.factor` | 饱和度系数 | 0.0-2.0（1.0=不变） |
| `pixel_dropout.rate` | 像素丢失率 | 0.0-0.1（0.01=1%） |
| `color_shift.r/g/b_shift` | RGB 通道偏移 | -50 到 50 |

### LiDAR 配置

| 参数 | 说明 | 取值范围 |
|------|------|----------|
| `noise.std` | 位置噪声标准差 | 0.0-0.2（米） |
| `dropout.rate` | 点云丢失率 | 0.0-0.5（0.1=10%） |
| `range_limit.max_range` | 最大有效距离 | 10-100（米） |
| `range_limit.min_range` | 最小有效距离 | 0.0-5.0（米） |
| `intensity_noise.std` | 强度噪声标准差 | 0.0-0.5 |

### GPS 配置

| 参数 | 说明 | 取值范围 |
|------|------|----------|
| `drift.std` | 漂移噪声标准差 | 0.0-5.0（米） |
| `random_jump.probability` | 跳变概率 | 0.0-0.1（每帧） |
| `random_jump.max_distance` | 最大跳变距离 | 0.0-20.0（米） |

### 速度传感器配置

| 参数 | 说明 | 取值范围 |
|------|------|----------|
| `error.std` | 测量误差标准差 | 0.0-1.0（m/s） |
| `bias.value` | 系统偏差 | -2.0 到 2.0（m/s） |

### 罗盘配置

| 参数 | 说明 | 取值范围 |
|------|------|----------|
| `error.std` | 方向误差标准差 | 0.0-0.2（弧度） |
| `declination.value` | 磁偏角 | -π 到 π（弧度） |

---

## 预设配置

### 1. 轻度噪声 (CONFIG_MILD_NOISE)

模拟良好天气和传感器状态：
```python
ACTIVE_CONFIG = CONFIG_MILD_NOISE
```

**效果**:
- RGB 噪声 std=5
- LiDAR 噪声 std=0.01m
- GPS 漂移 std=0.3m

**适用场景**: 测试模型对轻微噪声的鲁棒性

### 2. 中度噪声 (CONFIG_MODERATE_NOISE)

模拟一般条件：
```python
ACTIVE_CONFIG = CONFIG_MODERATE_NOISE
```

**效果**:
- RGB 噪声 std=15 + 模糊 kernel=3
- LiDAR 噪声 std=0.03m + 5% 点云丢失
- GPS 漂移 std=1.0m
- 速度误差 std=0.2m/s

**适用场景**: 真实世界条件模拟

### 3. 严重噪声 (CONFIG_SEVERE_NOISE)

模拟恶劣条件：
```python
ACTIVE_CONFIG = CONFIG_SEVERE_NOISE
```

**效果**:
- RGB 噪声 std=25 + 亮度 0.7 + 模糊 kernel=5
- LiDAR 噪声 std=0.08m + 20% 点云丢失
- GPS 漂移 std=2.0m
- 速度误差 std=0.5m/s
- 罗盘误差 std=0.1 rad

**适用场景**: 压力测试

### 4. 传感器故障 (CONFIG_SENSOR_FAILURE)

模拟传感器故障：
```python
ACTIVE_CONFIG = CONFIG_SENSOR_FAILURE
```

**效果**:
- RGB 5% 像素丢失
- LiDAR 30% 点云丢失 + 距离限制 30m
- GPS 随机跳变（5% 概率）

**适用场景**: 故障恢复能力测试

---

## 高级功能

### 1. 保存对比图像

在配置中启用：
```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    # ... 其他配置 ...
    'advanced': {
        'save_comparison': True,
        'comparison_path': './data_comparison',
    },
}
```

**结果**: 在 `./data_comparison/` 目录下保存原始图像和处理后图像的对比。

### 2. 数据日志

```python
DATA_PROCESSOR_CONFIG = {
    'advanced': {
        'log_data': True,
        'log_path': './data_logs',
    },
}
```

### 3. 统计信息

```python
DATA_PROCESSOR_CONFIG = {
    'advanced': {
        'print_stats': True,
        'stats_interval': 100,  # 每 100 帧打印一次
    },
}
```

**输出示例**:
```
==================================================
Sensor Data Processor Statistics
==================================================
Total Frames:     500
RGB Processed:    1500  (3 cameras)
LiDAR Processed:  500
GPS Processed:    500
==================================================
```

### 4. 自定义配置

创建完全自定义的配置：
```python
MY_CUSTOM_CONFIG = {
    'enabled': True,
    'rgb': {
        'add_gaussian_noise': {
            'enabled': True,
            'mean': 0,
            'std': 20,  # 自定义噪声级别
        },
        'brightness': {
            'enabled': True,
            'factor': 0.8,  # 降低亮度 20%
        },
    },
    'lidar': {
        'dropout': {
            'enabled': True,
            'rate': 0.15,  # 15% 点云丢失
        },
        'range_limit': {
            'enabled': True,
            'max_range': 40.0,  # 限制到 40 米
            'min_range': 0.5,
        },
    },
    'gps': {
        'drift': {
            'enabled': True,
            'std': 1.5,  # 1.5 米漂移
        },
    },
    'advanced': {
        'save_comparison': True,
        'comparison_path': './my_comparison',
        'print_stats': True,
        'stats_interval': 50,
    },
}

# 使用自定义配置
ACTIVE_CONFIG = MY_CUSTOM_CONFIG
```

---

## 常见问题

### Q1: 如何临时禁用数据处理？

**A**: 将配置的 `enabled` 设为 `False`:
```python
ACTIVE_CONFIG = {
    'enabled': False,
    # ... 其他配置会被忽略
}
```

### Q2: 如何只处理某些传感器？

**A**: 在配置中只启用需要处理的传感器：
```python
ACTIVE_CONFIG = {
    'enabled': True,
    'rgb': {
        'add_gaussian_noise': {'enabled': True, 'mean': 0, 'std': 15},
    },
    # lidar, gps 等不配置，则不会被处理
}
```

### Q3: 处理后的数据是否会影响性能？

**A**: 
- RGB 处理: 轻微影响（~1-5ms/帧）
- LiDAR 处理: 几乎无影响（<1ms）
- 总体影响小于 5%

### Q4: 如何查看处理效果？

**A**: 启用对比图像保存：
```python
'advanced': {
    'save_comparison': True,
    'comparison_path': './comparison',
}
```

然后查看生成的对比图像：
```bash
ls ./comparison/
# rgb_000001.jpg, rgb_left_000001.jpg, ...
```

### Q5: 如何在评估中使用不同的配置？

**A**: 
1. 修改 `data_processor_config.py` 中的 `ACTIVE_CONFIG`
2. 重新运行评估脚本
3. 无需重启 CARLA 服务器

### Q6: 处理后评估结果变差了，如何分析原因？

**A**: 
1. 启用统计信息和对比图像
2. 逐个传感器测试（只启用一个传感器的处理）
3. 调整噪声级别，从轻度到重度逐步测试
4. 查看对比图像，确认处理效果是否符合预期

### Q7: 如何添加新的处理方法？

**A**: 编辑 `data_processor.py`，在相应的处理方法中添加新逻辑：
```python
def process_rgb(self, rgb_image, sensor_id='rgb'):
    # ... 现有代码 ...
    
    # 添加新的处理
    if rgb_config.get('my_new_effect', {}).get('enabled', False):
        cfg = rgb_config['my_new_effect']
        # 你的处理逻辑
        processed = my_processing_function(processed, cfg)
        has_changes = True
    
    # ... 后续代码 ...
```

然后在配置中添加相应配置项。

---

## 完整工作流程示例

### 场景：测试模型对相机噪声的鲁棒性

#### 步骤 1: 配置
```python
# data_processor_config.py
TEST_CONFIG = {
    'enabled': True,
    'rgb': {
        'add_gaussian_noise': {
            'enabled': True,
            'mean': 0,
            'std': 20,  # 中等噪声
        },
    },
    'advanced': {
        'save_comparison': True,
        'comparison_path': './camera_noise_test',
        'print_stats': True,
        'stats_interval': 100,
    },
}

ACTIVE_CONFIG = TEST_CONFIG
```

#### 步骤 2: 集成到 Agent
（按照上述"集成到 Agent"部分的说明修改 `interfuser_agent.py`）

#### 步骤 3: 运行评估
```bash
# 终端 1
cd /home/nju/InterFuser/evaluation_scripts
./start_carla_server.sh

# 终端 2
cd /home/nju/InterFuser/evaluation_scripts
./run_evaluation.sh town05
```

#### 步骤 4: 查看结果
```bash
# 查看统计信息
cat results/interfuser_town05_result.json

# 查看对比图像
ls camera_noise_test/
# rgb_000001.jpg, rgb_000002.jpg, ...

# 查看处理器统计
cat data_logs/processor_stats.json
```

#### 步骤 5: 分析
- 对比有噪声和无噪声的评估结果
- 查看对比图像，确认噪声级别
- 根据结果调整配置，重新测试

---

## 参考资料

### 相关文件
- `INTERFUSER_PROJECT_ANALYSIS.md` - 项目完整分析文档
- `data_processor.py` - 数据处理器实现
- `data_processor_config.py` - 配置文件
- `interfuser_agent_with_processor_example.py` - 集成示例

### 数据流图
```
CARLA → Sensors → CallBack → SensorInterface → Agent → tick() 
                                                          ↓
                                                    DataProcessor
                                                          ↓
                                                   Processed Data
                                                          ↓
                                                    Model Inference
                                                          ↓
                                                      Control
```

---

## 技术支持

如有问题或建议，请查看：
- `INTERFUSER_PROJECT_ANALYSIS.md` - 详细的技术分析
- `interfuser_agent_with_processor_example.py` - 代码示例和注释

