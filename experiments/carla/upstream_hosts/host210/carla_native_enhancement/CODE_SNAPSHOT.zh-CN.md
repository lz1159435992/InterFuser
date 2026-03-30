# 代码快照（Baseline 行为）�?记录�?2026-02-04

本文档描述了在实�?CARLA 原生传感器增强方法之�?`./` 中的**当前 baseline 行为**�?
## 1. Baseline 入口�?
### 1.1 主要工作�?- 目录：`leaderboard/team_code/`
- Agent：`leaderboard/team_code/interfuser_agent.py`
- 评测器：`leaderboard/leaderboard/leaderboard_evaluator.py`

### 1.2 Baseline 传感器配�?
Baseline InterfuserAgent �?`sensors()` 方法中定义传感器�?
```python
def sensors(self):
    return [
        {
            "type": "sensor.camera.rgb",
            "x": 1.3, "y": 0.0, "z": 2.3,
            "roll": 0.0, "pitch": 0.0, "yaw": 0.0,
            "width": 800,
            "height": 600,
            "fov": 100,
            "id": "rgb",
        },
        # ... rgb_left, rgb_right 类似
        {
            "type": "sensor.other.imu",
            "sensor_tick": 0.05,  # 20Hz
            "id": "imu",
        },
        {
            "type": "sensor.other.gnss",
            "sensor_tick": 0.01,  # 100Hz
            "id": "gps",
        },
        # ... lidar, speedometer
    ]
```

**关键 baseline 参数�?*
- 相机分辨率：800x600
- 相机 sensor_tick：未指定（默认使用世�?tick 速率�?- 世界 tick 速率�?0Hz（fixed_delta_seconds = 0.05�?- 无显式噪�?后处理配置（使用 CARLA 默认值）

## 2. 世界仿真配置

文件：`leaderboard/leaderboard/leaderboard_evaluator.py`

```python
def _load_and_wait_for_world(self, args, town, ego_vehicles=None):
    self.world = self.client.load_world(town)
    settings = self.world.get_settings()
    settings.fixed_delta_seconds = 1.0 / self.frame_rate  # 默认�?0Hz
    settings.synchronous_mode = True
    self.world.apply_settings(settings)
```

**Baseline 世界设置�?*
- `frame_rate`�?0（来自评测器初始化）
- `fixed_delta_seconds`�?.05�?/20�?- `synchronous_mode`：True

## 3. Agent 行为（baseline�?
### 3.1 run_step 频率

Agent �?`run_step(input_data, timestamp)` 每个世界 tick 调用一次：
- 频率：每�?20 �?- 调用间隔�?.05 �?
### 3.2 内部步数计数�?
```python
def run_step(self, input_data, timestamp):
    if not self.initialized:
        self._init()
    
    self.step += 1  # 每个世界 tick 增加一�?    
    if self.step % self.skip_frames != 0 and self.step > 4:
        return self.prev_control  # 跳过处理
    
    # ... 正常处理
```

**关键行为�?*
- `self.step` 每个世界 tick 增加一次（每秒 20 次）�?- `skip_frames` 逻辑：agent 可能在某些帧上跳过处理�?- 默认 `skip_frames`：通常�?0 �?1（处理每帧或每隔一帧）�?
### 3.3 图像预处�?
```python
# 前置相机：resize �?224x224
self.rgb_front_transform = create_carla_rgb_transform(224)

# 侧面相机：resize �?128x128
self.rgb_left_transform = create_carla_rgb_transform(128)
self.rgb_right_transform = create_carla_rgb_transform(128)
```

图像�?800x600 resize 到这些维度后再输入模型�?
## 4. 传感器数据流

```
CARLA 世界�?0Hz tick�?    �?传感器捕获数据（相机 20Hz，其他传感器不同�?    �?CallBack �?SensorInterface.update_sensor()
    �?数据存储在队列（_new_data_buffers�?    �?SensorInterface.get_data() 等待所有传感器
    �?Agent.run_step(input_data, timestamp)
    �?Agent 返回 VehicleControl
    �?控制应用到车�?```

### 4.1 SensorInterface.get_data() 行为

文件：`leaderboard/leaderboard/envs/sensor_interface.py`

```python
def get_data(self):
    try: 
        data_dict = {}
        while len(data_dict.keys()) < len(self._sensors_objects.keys()):
            # 等待所有传感器（阻塞直到数据可用）
            sensor_data = self._new_data_buffers.get(True, self._queue_timeout)
            data_dict[sensor_data[0]] = ((sensor_data[1], sensor_data[2]))
    except Empty:
        raise SensorReceivedNoData("A sensor took too long to send their data")
    
    return data_dict
```

**关键行为�?*
- 阻塞直到所有传感器都为当前 tick 提供了数据�?- 使用 FIFO 队列（先进先出）�?- 超时�?0 秒（可通过 `SENSOR_QUEUE_TIMEOUT` 配置）�?
## 5. CARLA 相机后处理（默认值）

当未设置显式属性时，CARLA 相机使用这些默认值：

```python
# 来自 CARLA 文档
"bloom_intensity": 0.675,
"lens_flare_intensity": 0.1,
"motion_blur_intensity": 0.45,
"motion_blur_max_distortion": 0.35,
"chromatic_aberration_intensity": 0.0,
"lens_circle_falloff": 5.0,
"lens_circle_multiplier": 0.0,
```

这些后处理效果模拟真实的相机伪影�?
## 6. Baseline 稳定性规�?
此快照对应于 baseline InterfuserAgent 在标�?Leaderboard 路线上产生有效结果的状态。当 `NATIVE_ENHANCE=none` 时，新方法不得改变此 baseline 行为�?
## 7. 新方�?runner（隔离）

新的 CARLA 原生增强方法�?`carla_native_enhancement/` 下实现，旨在通过隔离�?runner 执行�?- `carla_native_enhancement/run_evaluation_native.sh`

�?baseline runner 的关键区别：
- 不使用默�?agent，runner 部署 `carla_native_enhancement/interfuser_agent_native.py`�?- 传感器配置根�?`NATIVE_ENHANCE` 环境变量修改�?- 世界 tick 速率可能改变（`high_fps` �?20Hz �?40Hz）�?- �?`AUTO_START_CARLA=1` 时，runner 会自动启�?CARLA 并使用适当设置�?
## 8. 关键实现注意事项

### 8.1 高帧率实�?
当启�?`high_fps` 时：
1. 世界 `fixed_delta_seconds` 必须改为 0.025�?0Hz）�?2. 相机 `sensor_tick` 应设�?0.025（或省略以使用世�?tick）�?3. Agent `run_step()` 将自动每秒调�?40 次�?4. Agent 逻辑无需更改（自动适应）�?
### 8.2 高分辨率实现

当启�?`high_res` 时：
1. 相机 `width` �?`height` 改为 1600x1200�?2. Agent 预处理仍�?resize �?224x224（或 128x128）�?3. 模型输入维度保持不变�?4. 好处：从更高分辨率下采样保留更多细节�?
### 8.3 无噪声实�?
当启�?`no_noise` 时：
1. 设置相机属性以禁用后处理：
   - `bloom_intensity`�?.0
   - `lens_flare_intensity`�?.0
   - `motion_blur_intensity`�?.0
   - `motion_blur_max_distortion`�?.0
2. 可选禁用镜头畸变：
   - `lens_circle_falloff`�?.0
   - `lens_k`�?.0
   - `lens_kcube`�?.0

## 9. �?augmentation_seq_method 的对�?
| 方面 | Baseline | augmentation_seq_method | carla_native_enhancement |
|------|----------|------------------------|-------------------------|
| **世界 tick** | 20Hz | 20Hz | 20Hz �?40Hz |
| **相机配置** | 800x600，默认�?| 800x600，默认�?| 可配�?|
| **处理** | �?| 后处理（SwinIR/SRGAN/RIFE�?| 无（原生质量�?|
| **Agent 频率** | 20Hz | 20Hz（FI 时：�?tick 2 次更新） | 20Hz �?40Hz |
| **模型输入** | 224x224 | 224x224 | 224x224 |


