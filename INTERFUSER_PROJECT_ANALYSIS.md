# InterFuser 项目完整分析

## 📋 项目概述

**InterFuser** 是一个基于 CARLA 模拟器的端到端自动驾驶系统，采用多模态传感器融合和 Transformer 架构进行自动驾驶决策。

### 核心功能
- **多模态感知**: 融合 RGB 相机（前/左/右）、LiDAR、GPS、IMU 等多种传感器
- **端到端控制**: 直接从传感器数据到车辆控制（转向、油门、刹车）
- **场景理解**: 预测交通参与者、识别交通信号灯、停止标志等
- **路径规划**: 预测未来轨迹点并进行安全驾驶决策

---

## 🔄 数据流架构

### 完整数据流程图

```
CARLA Simulator (模拟器)
    ↓
Sensors (传感器层)
    ├── RGB Cameras (3个相机)
    ├── LiDAR
    ├── GPS
    ├── IMU
    └── Speedometer
    ↓
CallBack (回调处理)
    ├── _parse_image_cb()      ← 图像数据解析
    ├── _parse_lidar_cb()      ← LiDAR 数据解析
    ├── _parse_gnss_cb()       ← GPS 数据解析
    └── _parse_imu_cb()        ← IMU 数据解析
    ↓
SensorInterface.update_sensor()  ← 【拦截点 1】
    ↓ (Queue)
SensorInterface.get_data()       ← 【拦截点 2】
    ↓
AutonomousAgent.__call__()
    ↓
input_data = sensor_interface.get_data()
    ↓
InterfuserAgent.run_step(input_data, timestamp)  ← 【拦截点 3】
    ↓
tick_data = self.tick(input_data)                ← 【拦截点 4】
    ↓
Model Inference (模型推理)
    ├── RGB Transform
    ├── LiDAR Processing
    ├── Feature Extraction
    └── Prediction
    ↓
Controller (控制器)
    ↓
VehicleControl (车辆控制命令)
```

---

## 🔍 关键代码模块分析

### 1. Sensor Interface (`leaderboard/leaderboard/envs/sensor_interface.py`)

**职责**: 传感器数据的收集、缓冲和分发

**关键类**:

#### `CallBack` 类
```python
class CallBack(object):
    def __call__(self, data):
        # 根据数据类型分发处理
        if isinstance(data, carla.libcarla.Image):
            self._parse_image_cb(data, self._tag)
        elif isinstance(data, carla.libcarla.LidarMeasurement):
            self._parse_lidar_cb(data, self._tag)
        # ... 其他传感器类型
```

**数据解析方法**:
- `_parse_image_cb()`: 将 CARLA 图像转换为 numpy 数组 (H, W, 4)
- `_parse_lidar_cb()`: 将 LiDAR 数据转换为点云数组 (N, 4)
- `_parse_gnss_cb()`: 提取经纬度、海拔
- `_parse_imu_cb()`: 提取加速度、角速度、罗盘方向

#### `SensorInterface` 类
```python
class SensorInterface(object):
    def update_sensor(self, tag, data, timestamp):
        # 将传感器数据放入队列
        self._new_data_buffers.put((tag, timestamp, data))
    
    def get_data(self):
        # 从队列中收集所有传感器的数据
        data_dict = {}
        while len(data_dict.keys()) < len(self._sensors_objects.keys()):
            sensor_data = self._new_data_buffers.get(True, self._queue_timeout)
            data_dict[sensor_data[0]] = ((sensor_data[1], sensor_data[2]))
        return data_dict
```

**数据格式**:
```python
{
    'rgb': (frame_id, numpy.array),      # (600, 800, 4)
    'rgb_left': (frame_id, numpy.array), # (300, 400, 4)
    'rgb_right': (frame_id, numpy.array),# (300, 400, 4)
    'lidar': (frame_id, numpy.array),    # (N, 4)
    'gps': (frame_id, numpy.array),      # (3,) [lat, lon, alt]
    'imu': (frame_id, numpy.array),      # (7,) [acc_x,y,z, gyro_x,y,z, compass]
    'speed': (frame_id, dict),           # {'speed': float}
}
```

---

### 2. Autonomous Agent (`leaderboard/leaderboard/autoagents/autonomous_agent.py`)

**职责**: Agent 基类，定义数据获取和控制接口

**关键方法**:
```python
class AutonomousAgent(object):
    def __call__(self):
        # 1. 从 sensor interface 获取数据
        input_data = self.sensor_interface.get_data()
        
        # 2. 获取当前时间戳
        timestamp = GameTime.get_time()
        
        # 3. 调用 run_step 生成控制命令
        control = self.run_step(input_data, timestamp)
        
        return control
    
    def run_step(self, input_data, timestamp):
        # 子类需要实现这个方法
        pass
```

---

### 3. InterfuserAgent (`leaderboard/team_code/interfuser_agent.py`)

**职责**: InterFuser 的具体实现

#### 传感器定义
```python
def sensors(self):
    return [
        {
            "type": "sensor.camera.rgb",
            "x": 1.3, "y": 0.0, "z": 2.3,
            "yaw": 0.0,  # 前视相机
            "width": 800, "height": 600, "fov": 100,
            "id": "rgb",
        },
        {
            "type": "sensor.camera.rgb",
            "x": 1.3, "y": 0.0, "z": 2.3,
            "yaw": -60.0,  # 左视相机
            "width": 400, "height": 300, "fov": 100,
            "id": "rgb_left",
        },
        {
            "type": "sensor.camera.rgb",
            "x": 1.3, "y": 0.0, "z": 2.3,
            "yaw": 60.0,  # 右视相机
            "width": 400, "height": 300, "fov": 100,
            "id": "rgb_right",
        },
        {
            "type": "sensor.lidar.ray_cast",
            "x": 1.3, "y": 0.0, "z": 2.5,
            "yaw": -90.0,
            "id": "lidar",
        },
        # ... GPS, IMU, Speedometer
    ]
```

#### 数据处理流程

**Step 1: `tick()` 方法** - 原始数据预处理
```python
def tick(self, input_data):
    # 1. 提取 RGB 图像（BGR → RGB 转换）
    rgb = cv2.cvtColor(input_data["rgb"][1][:, :, :3], cv2.COLOR_BGR2RGB)
    rgb_left = cv2.cvtColor(input_data["rgb_left"][1][:, :, :3], cv2.COLOR_BGR2RGB)
    rgb_right = cv2.cvtColor(input_data["rgb_right"][1][:, :, :3], cv2.COLOR_BGR2RGB)
    
    # 2. 提取定位和状态信息
    gps = input_data["gps"][1][:2]           # 经纬度
    speed = input_data["speed"][1]["speed"]  # 速度
    compass = input_data["imu"][1][-1]       # 罗盘方向
    
    # 3. 处理 LiDAR 数据
    lidar_data = input_data['lidar'][1]
    # 坐标变换
    lidar_unprocessed = lidar_data[:, :3]
    lidar_unprocessed[:, 1] *= -1  # Y轴翻转
    # 转换到全局坐标系
    full_lidar = transform_2d_points(lidar_unprocessed, ...)
    # 生成直方图特征
    lidar_processed = lidar_to_histogram_features(full_lidar, crop=224)
    
    # 4. GPS 坐标归一化
    pos = self._get_position(result)
    
    # 5. 计算目标点（相对于车辆的局部坐标）
    next_wp, next_cmd = self._route_planner.run_step(pos)
    theta = compass + np.pi / 2
    R = np.array([[np.cos(theta), -np.sin(theta)], 
                  [np.sin(theta), np.cos(theta)]])
    local_command_point = np.array([next_wp[0] - pos[0], next_wp[1] - pos[1]])
    local_command_point = R.T.dot(local_command_point)
    result["target_point"] = local_command_point
    
    return result
```

**Step 2: `run_step()` 方法** - 模型推理和控制
```python
@torch.no_grad()
def run_step(self, input_data, timestamp):
    # 1. 获取预处理后的数据
    tick_data = self.tick(input_data)
    
    # 2. 图像转换（Resize + Normalize）
    rgb = self.rgb_front_transform(Image.fromarray(tick_data["rgb"])).unsqueeze(0).cuda()
    rgb_left = self.rgb_left_transform(Image.fromarray(tick_data["rgb_left"])).unsqueeze(0).cuda()
    rgb_right = self.rgb_right_transform(Image.fromarray(tick_data["rgb_right"])).unsqueeze(0).cuda()
    
    # 3. 准备命令 one-hot 编码
    cmd_one_hot = [0, 0, 0, 0, 0, 0]
    cmd = command - 1
    cmd_one_hot[cmd] = 1
    cmd_one_hot.append(velocity)
    mes = torch.from_numpy(np.array(cmd_one_hot)).float().unsqueeze(0).cuda()
    
    # 4. 组装模型输入
    input_data = {
        "rgb": rgb,
        "rgb_left": rgb_left,
        "rgb_right": rgb_right,
        "rgb_center": rgb_center,
        "measurements": mes,
        "target_point": torch.from_numpy(tick_data["target_point"]).float().cuda().view(1, -1),
        "lidar": torch.from_numpy(tick_data["lidar"]).float().cuda().unsqueeze(0),
    }
    
    # 5. 模型推理
    (traffic_meta, pred_waypoints, is_junction, 
     traffic_light_state, stop_sign, bev_feature) = self.net(input_data)
    
    # 6. 后处理
    traffic_meta = traffic_meta.detach().cpu().numpy()[0]
    pred_waypoints = pred_waypoints.detach().cpu().numpy()[0]
    # ...
    
    # 7. 控制器
    steer, throttle, brake, meta_infos = self.controller.run_step(
        velocity, pred_waypoints, is_junction, 
        traffic_light_state, stop_sign, traffic_meta
    )
    
    # 8. 生成控制命令
    control = carla.VehicleControl()
    control.steer = float(steer)
    control.throttle = float(throttle)
    control.brake = float(brake)
    
    return control
```

---

## 🎯 数据拦截和编辑方案

### 方案概述

要在模拟器数据传递给 agent 时进行编辑，有 **4 个关键拦截点**，按优先级排序：

---

### 🔥 **方案 1: 在 `tick()` 方法中拦截（推荐）**

**优点**:
- ✅ 最简单直接
- ✅ 可以访问所有预处理后的数据
- ✅ 不影响其他系统组件
- ✅ 易于调试和维护

**实现方式**:

创建一个数据处理包装器类：

```python
# leaderboard/team_code/data_processor.py
import numpy as np
import cv2

class SensorDataProcessor:
    """传感器数据处理器 - 用于拦截和修改传感器数据"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        
    def process_rgb(self, rgb_image):
        """处理 RGB 图像"""
        if not self.enabled:
            return rgb_image
            
        # 示例：添加高斯噪声
        if self.config.get('add_noise', False):
            noise = np.random.normal(0, 25, rgb_image.shape).astype(np.uint8)
            rgb_image = np.clip(rgb_image + noise, 0, 255).astype(np.uint8)
        
        # 示例：调整亮度
        if self.config.get('brightness_factor'):
            factor = self.config['brightness_factor']
            rgb_image = np.clip(rgb_image * factor, 0, 255).astype(np.uint8)
        
        # 示例：模糊
        if self.config.get('blur_kernel'):
            kernel = self.config['blur_kernel']
            rgb_image = cv2.GaussianBlur(rgb_image, (kernel, kernel), 0)
            
        return rgb_image
    
    def process_lidar(self, lidar_data):
        """处理 LiDAR 数据"""
        if not self.enabled:
            return lidar_data
            
        # 示例：添加噪声
        if self.config.get('lidar_noise', 0) > 0:
            noise_level = self.config['lidar_noise']
            noise = np.random.normal(0, noise_level, lidar_data.shape)
            lidar_data = lidar_data + noise
        
        # 示例：随机删除点
        if self.config.get('lidar_dropout', 0) > 0:
            dropout_rate = self.config['lidar_dropout']
            mask = np.random.random(len(lidar_data)) > dropout_rate
            lidar_data = lidar_data[mask]
            
        return lidar_data
    
    def process_gps(self, gps):
        """处理 GPS 数据"""
        if not self.enabled:
            return gps
            
        # 示例：添加 GPS 漂移
        if self.config.get('gps_drift', 0) > 0:
            drift = self.config['gps_drift']
            gps = gps + np.random.normal(0, drift, gps.shape)
            
        return gps
    
    def process_speed(self, speed):
        """处理速度数据"""
        if not self.enabled:
            return speed
            
        # 示例：添加速度误差
        if self.config.get('speed_error', 0) > 0:
            error = self.config['speed_error']
            speed = speed + np.random.normal(0, error)
            
        return speed
    
    def process_compass(self, compass):
        """处理罗盘数据"""
        if not self.enabled:
            return compass
            
        # 示例：添加方向误差
        if self.config.get('compass_error', 0) > 0:
            error = self.config['compass_error']
            compass = compass + np.random.normal(0, error)
            
        return compass
    
    def process_all(self, input_data):
        """处理所有传感器数据"""
        result = {}
        
        # 处理图像数据
        if 'rgb' in input_data:
            result['rgb'] = self.process_rgb(input_data['rgb'].copy())
        if 'rgb_left' in input_data:
            result['rgb_left'] = self.process_rgb(input_data['rgb_left'].copy())
        if 'rgb_right' in input_data:
            result['rgb_right'] = self.process_rgb(input_data['rgb_right'].copy())
        
        # 处理其他传感器
        if 'gps' in input_data:
            result['gps'] = self.process_gps(input_data['gps'].copy())
        if 'speed' in input_data:
            result['speed'] = self.process_speed(input_data['speed'])
        if 'compass' in input_data:
            result['compass'] = self.process_compass(input_data['compass'])
        
        # 复制未处理的数据
        for key in input_data:
            if key not in result:
                result[key] = input_data[key]
                
        return result
```

**修改 `interfuser_agent.py`**:

```python
# 在 InterfuserAgent 类中添加

from team_code.data_processor import SensorDataProcessor

class InterfuserAgent(autonomous_agent.AutonomousAgent):
    def setup(self, path_to_conf_file):
        # ... 原有代码 ...
        
        # 初始化数据处理器
        processor_config = {
            'enabled': True,
            'add_noise': False,
            'brightness_factor': None,
            'blur_kernel': None,
            'lidar_noise': 0.0,
            'lidar_dropout': 0.0,
            'gps_drift': 0.0,
            'speed_error': 0.0,
            'compass_error': 0.0,
        }
        self.data_processor = SensorDataProcessor(processor_config)
    
    def tick(self, input_data):
        # 原始数据提取
        rgb = cv2.cvtColor(input_data["rgb"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        rgb_left = cv2.cvtColor(input_data["rgb_left"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        rgb_right = cv2.cvtColor(input_data["rgb_right"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        gps = input_data["gps"][1][:2]
        speed = input_data["speed"][1]["speed"]
        compass = input_data["imu"][1][-1]
        
        # 组装原始数据
        raw_data = {
            "rgb": rgb,
            "rgb_left": rgb_left,
            "rgb_right": rgb_right,
            "gps": gps,
            "speed": speed,
            "compass": compass,
        }
        
        # 🔥 数据拦截和处理 🔥
        processed_data = self.data_processor.process_all(raw_data)
        
        # 使用处理后的数据
        result = {
            "rgb": processed_data["rgb"],
            "rgb_left": processed_data["rgb_left"],
            "rgb_right": processed_data["rgb_right"],
            "gps": processed_data["gps"],
            "speed": processed_data["speed"],
            "compass": processed_data["compass"],
        }
        
        # ... 后续处理（LiDAR、位置计算等）...
        
        return result
```

---

### 🔥 **方案 2: 在 SensorInterface 层拦截**

**优点**:
- ✅ 更底层，可以在数据分发前统一处理
- ✅ 对所有 agent 生效
- ✅ 可以记录原始数据

**缺点**:
- ⚠️ 修改核心框架代码
- ⚠️ 需要处理更原始的数据格式

**实现方式**:

创建一个继承的 SensorInterface：

```python
# leaderboard/team_code/custom_sensor_interface.py
from leaderboard.envs.sensor_interface import SensorInterface
import numpy as np

class CustomSensorInterface(SensorInterface):
    """自定义传感器接口 - 支持数据拦截和修改"""
    
    def __init__(self, data_processor=None):
        super().__init__()
        self.data_processor = data_processor
        self.raw_data_log = []  # 可选：记录原始数据
    
    def get_data(self):
        # 获取原始数据
        data_dict = super().get_data()
        
        # 如果有数据处理器，则处理数据
        if self.data_processor:
            data_dict = self._process_sensor_data(data_dict)
        
        return data_dict
    
    def _process_sensor_data(self, data_dict):
        """处理传感器数据"""
        processed_dict = {}
        
        for sensor_id, (frame, data) in data_dict.items():
            # 记录原始数据（可选）
            if self.data_processor.config.get('log_raw_data', False):
                self.raw_data_log.append({
                    'sensor_id': sensor_id,
                    'frame': frame,
                    'data_shape': data.shape if hasattr(data, 'shape') else None
                })
            
            # 根据传感器类型处理数据
            if 'rgb' in sensor_id:
                processed_data = self.data_processor.process_rgb(data[:, :, :3])
                # 保持 alpha 通道
                if data.shape[2] == 4:
                    processed_data = np.concatenate([processed_data, data[:, :, 3:4]], axis=2)
            elif sensor_id == 'lidar':
                processed_data = self.data_processor.process_lidar(data.copy())
            elif sensor_id == 'gps':
                processed_data = self.data_processor.process_gps(data.copy())
            else:
                processed_data = data
            
            processed_dict[sensor_id] = (frame, processed_data)
        
        return processed_dict
```

**使用自定义 SensorInterface**:

修改 agent 初始化：

```python
# leaderboard/team_code/interfuser_agent.py
from team_code.custom_sensor_interface import CustomSensorInterface
from team_code.data_processor import SensorDataProcessor

class InterfuserAgent(autonomous_agent.AutonomousAgent):
    def __init__(self, path_to_conf_file):
        # 不调用父类 __init__，手动初始化
        self.track = autonomous_agent.Track.SENSORS
        self._global_plan = None
        self._global_plan_world_coord = None
        
        # 🔥 使用自定义 SensorInterface 🔥
        processor_config = {...}  # 配置
        data_processor = SensorDataProcessor(processor_config)
        self.sensor_interface = CustomSensorInterface(data_processor)
        
        self.setup(path_to_conf_file)
        self.wallclock_t0 = None
```

---

### 🔥 **方案 3: 在 CallBack 层拦截（最底层）**

**优点**:
- ✅ 最早拦截，数据最原始
- ✅ 可以访问 CARLA 原生对象

**缺点**:
- ⚠️ 需要深度修改框架
- ⚠️ 处理复杂度高

**实现方式**:

```python
# leaderboard/envs/sensor_interface.py 修改 CallBack 类

class CallBack(object):
    def __init__(self, tag, sensor_type, sensor, data_provider, data_processor=None):
        self._tag = tag
        self._data_provider = data_provider
        self._data_processor = data_processor  # 新增
        self._data_provider.register_sensor(tag, sensor_type, sensor)
    
    def _parse_image_cb(self, image, tag):
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = copy.deepcopy(array)
        array = np.reshape(array, (image.height, image.width, 4))
        
        # 🔥 数据处理 🔥
        if self._data_processor and 'rgb' in tag:
            array[:, :, :3] = self._data_processor.process_rgb(array[:, :, :3])
        
        self._data_provider.update_sensor(tag, array, image.frame)
```

---

### 🔥 **方案 4: 创建代理 Agent 包装器**

**优点**:
- ✅ 不修改原始 agent 代码
- ✅ 可插拔设计

**实现方式**:

```python
# leaderboard/team_code/agent_wrapper_with_processor.py
from team_code.interfuser_agent import InterfuserAgent
from team_code.data_processor import SensorDataProcessor

class ProcessedInterfuserAgent:
    """InterfuserAgent 的包装器，添加数据处理功能"""
    
    def __init__(self, path_to_conf_file):
        # 创建原始 agent
        self.agent = InterfuserAgent(path_to_conf_file)
        
        # 创建数据处理器
        processor_config = {
            'enabled': True,
            # ... 配置项
        }
        self.data_processor = SensorDataProcessor(processor_config)
        
        # 复制必要的属性
        self.track = self.agent.track
        self.sensor_interface = self.agent.sensor_interface
        self._global_plan = None
        self._global_plan_world_coord = None
    
    def setup(self, path_to_conf_file):
        pass  # agent 已在 __init__ 中设置
    
    def sensors(self):
        return self.agent.sensors()
    
    def run_step(self, input_data, timestamp):
        # 🔥 拦截 input_data 🔥
        processed_input = self._process_input_data(input_data)
        
        # 调用原始 agent
        return self.agent.run_step(processed_input, timestamp)
    
    def _process_input_data(self, input_data):
        """处理输入数据"""
        processed = {}
        for key, (frame, data) in input_data.items():
            if 'rgb' in key and len(data.shape) >= 3:
                # 处理 RGB 数据
                processed_rgb = self.data_processor.process_rgb(
                    cv2.cvtColor(data[:, :, :3], cv2.COLOR_BGR2RGB)
                )
                processed_rgb = cv2.cvtColor(processed_rgb, cv2.COLOR_RGB2BGR)
                if data.shape[2] == 4:
                    data_processed = np.concatenate([processed_rgb, data[:, :, 3:4]], axis=2)
                else:
                    data_processed = processed_rgb
                processed[key] = (frame, data_processed)
            else:
                processed[key] = (frame, data)
        
        return processed
    
    def set_global_plan(self, global_plan_gps, global_plan_world_coord):
        self.agent.set_global_plan(global_plan_gps, global_plan_world_coord)
        self._global_plan = self.agent._global_plan
        self._global_plan_world_coord = self.agent._global_plan_world_coord
    
    def destroy(self):
        self.agent.destroy()
    
    def __call__(self):
        return self.agent()
```

---

## 🎯 推荐实现方案

### **最佳方案组合**: 方案 1 + 配置文件

**实现步骤**:

#### 步骤 1: 创建配置文件
```python
# leaderboard/team_code/data_processor_config.py
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    
    # RGB 图像处理
    'rgb': {
        'add_gaussian_noise': {
            'enabled': False,
            'mean': 0,
            'std': 10,
        },
        'brightness': {
            'enabled': False,
            'factor': 1.2,  # 1.0 = 不变, >1 变亮, <1 变暗
        },
        'blur': {
            'enabled': False,
            'kernel_size': 5,
        },
        'contrast': {
            'enabled': False,
            'factor': 1.1,
        },
    },
    
    # LiDAR 处理
    'lidar': {
        'noise': {
            'enabled': False,
            'std': 0.02,  # 2cm 标准差
        },
        'dropout': {
            'enabled': False,
            'rate': 0.1,  # 10% 点云丢失
        },
        'range_limit': {
            'enabled': False,
            'max_range': 50.0,  # 米
        },
    },
    
    # GPS 处理
    'gps': {
        'drift': {
            'enabled': False,
            'std': 0.5,  # 0.5米标准差
        },
    },
    
    # 速度传感器
    'speed': {
        'error': {
            'enabled': False,
            'std': 0.1,  # m/s
        },
    },
    
    # 罗盘
    'compass': {
        'error': {
            'enabled': False,
            'std': 0.05,  # 弧度
        },
    },
    
    # 高级功能
    'advanced': {
        'log_data': False,  # 记录处理前后的数据
        'save_comparison': False,  # 保存对比图像
        'comparison_path': './data_comparison',
    },
}
```

#### 步骤 2: 创建完整的数据处理器
```python
# leaderboard/team_code/data_processor.py
import numpy as np
import cv2
import os
from pathlib import Path

class SensorDataProcessor:
    def __init__(self, config):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.frame_count = 0
        
        # 创建日志目录
        if config.get('advanced', {}).get('save_comparison', False):
            self.comparison_path = Path(config['advanced']['comparison_path'])
            self.comparison_path.mkdir(parents=True, exist_ok=True)
    
    def process_rgb(self, rgb_image, sensor_id='rgb'):
        """处理 RGB 图像"""
        if not self.enabled:
            return rgb_image
        
        original = rgb_image.copy() if self.config.get('advanced', {}).get('save_comparison', False) else None
        processed = rgb_image.copy()
        
        rgb_config = self.config.get('rgb', {})
        
        # 高斯噪声
        if rgb_config.get('add_gaussian_noise', {}).get('enabled', False):
            noise_cfg = rgb_config['add_gaussian_noise']
            noise = np.random.normal(noise_cfg['mean'], noise_cfg['std'], processed.shape)
            processed = np.clip(processed.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        
        # 亮度调整
        if rgb_config.get('brightness', {}).get('enabled', False):
            factor = rgb_config['brightness']['factor']
            processed = np.clip(processed.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        
        # 模糊
        if rgb_config.get('blur', {}).get('enabled', False):
            kernel = rgb_config['blur']['kernel_size']
            if kernel % 2 == 0:
                kernel += 1  # 确保是奇数
            processed = cv2.GaussianBlur(processed, (kernel, kernel), 0)
        
        # 对比度
        if rgb_config.get('contrast', {}).get('enabled', False):
            factor = rgb_config['contrast']['factor']
            mean = processed.mean()
            processed = np.clip((processed - mean) * factor + mean, 0, 255).astype(np.uint8)
        
        # 保存对比图
        if original is not None and not np.array_equal(original, processed):
            self._save_comparison(original, processed, sensor_id)
        
        return processed
    
    def process_lidar(self, lidar_data):
        """处理 LiDAR 点云数据"""
        if not self.enabled or len(lidar_data) == 0:
            return lidar_data
        
        processed = lidar_data.copy()
        lidar_config = self.config.get('lidar', {})
        
        # 添加噪声
        if lidar_config.get('noise', {}).get('enabled', False):
            std = lidar_config['noise']['std']
            noise = np.random.normal(0, std, processed[:, :3].shape)
            processed[:, :3] += noise
        
        # 点云丢失（dropout）
        if lidar_config.get('dropout', {}).get('enabled', False):
            rate = lidar_config['dropout']['rate']
            keep_mask = np.random.random(len(processed)) > rate
            processed = processed[keep_mask]
        
        # 距离限制
        if lidar_config.get('range_limit', {}).get('enabled', False):
            max_range = lidar_config['range_limit']['max_range']
            distances = np.linalg.norm(processed[:, :3], axis=1)
            range_mask = distances <= max_range
            processed = processed[range_mask]
        
        return processed
    
    def process_gps(self, gps):
        """处理 GPS 数据"""
        if not self.enabled:
            return gps
        
        gps_config = self.config.get('gps', {})
        processed = gps.copy()
        
        # GPS 漂移
        if gps_config.get('drift', {}).get('enabled', False):
            std = gps_config['drift']['std']
            drift = np.random.normal(0, std, gps.shape)
            processed += drift
        
        return processed
    
    def process_speed(self, speed):
        """处理速度数据"""
        if not self.enabled:
            return speed
        
        speed_config = self.config.get('speed', {})
        
        # 速度误差
        if speed_config.get('error', {}).get('enabled', False):
            std = speed_config['error']['std']
            error = np.random.normal(0, std)
            speed += error
        
        return max(0, speed)  # 速度不能为负
    
    def process_compass(self, compass):
        """处理罗盘数据"""
        if not self.enabled:
            return compass
        
        compass_config = self.config.get('compass', {})
        
        # 罗盘误差
        if compass_config.get('error', {}).get('enabled', False):
            std = compass_config['error']['std']
            error = np.random.normal(0, std)
            compass += error
        
        # 归一化到 [-pi, pi]
        while compass > np.pi:
            compass -= 2 * np.pi
        while compass < -np.pi:
            compass += 2 * np.pi
        
        return compass
    
    def _save_comparison(self, original, processed, sensor_id):
        """保存原始图像和处理后图像的对比"""
        comparison = np.hstack([original, processed])
        filename = f"{sensor_id}_{self.frame_count:06d}.jpg"
        cv2.imwrite(str(self.comparison_path / filename), cv2.cvtColor(comparison, cv2.COLOR_RGB2BGR))
    
    def next_frame(self):
        """移动到下一帧"""
        self.frame_count += 1
```

#### 步骤 3: 修改 InterfuserAgent
```python
# leaderboard/team_code/interfuser_agent.py 中添加

from team_code.data_processor import SensorDataProcessor
from team_code.data_processor_config import DATA_PROCESSOR_CONFIG

class InterfuserAgent(autonomous_agent.AutonomousAgent):
    def setup(self, path_to_conf_file):
        # ... 原有代码 ...
        
        # 🔥 初始化数据处理器 🔥
        self.data_processor = SensorDataProcessor(DATA_PROCESSOR_CONFIG)
    
    def tick(self, input_data):
        # 提取原始数据
        rgb = cv2.cvtColor(input_data["rgb"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        rgb_left = cv2.cvtColor(input_data["rgb_left"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        rgb_right = cv2.cvtColor(input_data["rgb_right"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        gps = input_data["gps"][1][:2]
        speed = input_data["speed"][1]["speed"]
        compass = input_data["imu"][1][-1]
        
        # 🔥 数据处理 🔥
        rgb = self.data_processor.process_rgb(rgb, 'rgb')
        rgb_left = self.data_processor.process_rgb(rgb_left, 'rgb_left')
        rgb_right = self.data_processor.process_rgb(rgb_right, 'rgb_right')
        gps = self.data_processor.process_gps(gps)
        speed = self.data_processor.process_speed(speed)
        compass = self.data_processor.process_compass(compass)
        
        # ... 继续原有处理 ...
        
        result = {
            "rgb": rgb,
            "rgb_left": rgb_left,
            "rgb_right": rgb_right,
            "gps": gps,
            "speed": speed,
            "compass": compass,
        }
        
        # 处理 LiDAR
        lidar_data = input_data['lidar'][1]
        result['raw_lidar'] = lidar_data
        
        lidar_unprocessed = lidar_data[:, :3]
        lidar_unprocessed[:, 1] *= -1
        
        # 🔥 LiDAR 数据处理（在坐标转换前）🔥
        lidar_unprocessed_points = np.column_stack([lidar_unprocessed, lidar_data[:, 3:]])
        lidar_unprocessed_points = self.data_processor.process_lidar(lidar_unprocessed_points)
        lidar_unprocessed = lidar_unprocessed_points[:, :3]
        
        # 继续原有的坐标转换和特征提取
        full_lidar = transform_2d_points(lidar_unprocessed, ...)
        lidar_processed = lidar_to_histogram_features(full_lidar, crop=224)
        
        # ...
        
        # 帧计数
        self.data_processor.next_frame()
        
        return result
```

---

## 📝 使用示例

### 示例 1: 添加相机噪声
```python
# data_processor_config.py
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        'add_gaussian_noise': {
            'enabled': True,
            'mean': 0,
            'std': 15,  # 添加 std=15 的高斯噪声
        },
    },
}
```

### 示例 2: 模拟 LiDAR 点云丢失
```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'lidar': {
        'dropout': {
            'enabled': True,
            'rate': 0.2,  # 20% 点云丢失
        },
    },
}
```

### 示例 3: 模拟 GPS 漂移
```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'gps': {
        'drift': {
            'enabled': True,
            'std': 1.0,  # 1米标准差的 GPS 漂移
        },
    },
}
```

### 示例 4: 组合多种效果
```python
DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        'add_gaussian_noise': {
            'enabled': True,
            'mean': 0,
            'std': 10,
        },
        'brightness': {
            'enabled': True,
            'factor': 0.8,  # 降低亮度
        },
        'blur': {
            'enabled': True,
            'kernel_size': 3,
        },
    },
    'lidar': {
        'noise': {
            'enabled': True,
            'std': 0.05,
        },
        'dropout': {
            'enabled': True,
            'rate': 0.15,
        },
    },
    'gps': {
        'drift': {
            'enabled': True,
            'std': 0.5,
        },
    },
    'advanced': {
        'save_comparison': True,
        'comparison_path': './data_comparison',
    },
}
```

---

## 🚀 完整工作流程

```
1. CARLA Simulator 产生数据
   ↓
2. Sensor Callbacks 解析数据
   ↓
3. SensorInterface 收集数据
   ↓
4. Agent.__call__() 获取数据
   ↓
5. InterfuserAgent.tick(input_data)
   ↓
6. 🔥 SensorDataProcessor 处理数据 🔥
   ├── process_rgb()
   ├── process_lidar()
   ├── process_gps()
   ├── process_speed()
   └── process_compass()
   ↓
7. 数据转换和特征提取
   ↓
8. 模型推理
   ↓
9. 控制器生成命令
   ↓
10. VehicleControl 应用到车辆
```

---

## 🎯 总结

### 推荐方案
- **最佳**: 方案 1 - 在 `tick()` 方法中拦截
- **优点**: 简单、不侵入式、易维护、灵活配置
- **实现**: 创建 `SensorDataProcessor` 类 + 配置文件

### 关键要点
1. **数据流理解**: CARLA → Callback → SensorInterface → Agent → tick() → Model
2. **拦截位置**: `tick()` 方法是最佳拦截点
3. **可扩展性**: 配置文件 + 处理器类的设计便于扩展
4. **调试友好**: 可以记录处理前后的数据，便于对比分析

### 下一步
1. 实现 `SensorDataProcessor` 类
2. 修改 `interfuser_agent.py`
3. 创建配置文件
4. 测试不同的数据处理效果
5. 分析对模型性能的影响

