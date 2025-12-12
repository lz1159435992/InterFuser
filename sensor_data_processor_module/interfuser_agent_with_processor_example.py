"""
InterfuserAgent 数据处理集成示例

此文件展示如何将 SensorDataProcessor 集成到 InterfuserAgent 中

使用方法：
1. 将此文件的修改应用到 interfuser_agent.py
2. 或者复制此文件并重命名，然后在评估时使用新的 agent

关键修改点：
- 在 setup() 中初始化 SensorDataProcessor
- 在 tick() 中调用数据处理方法
- 在 run_step() 中进行帧计数
"""

# ========== 关键修改 1: 导入数据处理器 ==========
from team_code.data_processor import SensorDataProcessor
from team_code.data_processor_config import ACTIVE_CONFIG

# ... 其他 import 保持不变 ...


class InterfuserAgent(autonomous_agent.AutonomousAgent):
    
    # ========== 关键修改 2: 在 setup() 中初始化处理器 ==========
    def setup(self, path_to_conf_file):
        # ... 原有代码保持不变 ...
        
        self._hic = DisplayInterface()
        self.lidar_processed = list()
        self.track = autonomous_agent.Track.SENSORS
        self.step = -1
        # ...
        
        # 🔥 新增：初始化数据处理器 🔥
        self.data_processor = SensorDataProcessor(ACTIVE_CONFIG)
        print("=" * 60)
        print("Data Processor initialized with configuration:")
        config_summary = self.data_processor.get_config_summary()
        for key, value in config_summary.items():
            if value and (not isinstance(value, list) or value):
                print(f"  {key}: {value}")
        print("=" * 60)
        
        # ... 后续代码保持不变 ...
    
    # ========== 关键修改 3: 在 tick() 中处理数据 ==========
    def tick(self, input_data):
        """
        处理传感器数据
        
        修改要点：
        1. 提取原始数据后立即进行处理
        2. 使用处理后的数据进行后续计算
        """
        
        # 1. 提取原始 RGB 图像
        rgb = cv2.cvtColor(input_data["rgb"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        rgb_left = cv2.cvtColor(input_data["rgb_left"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        rgb_right = cv2.cvtColor(input_data["rgb_right"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        
        # 🔥 处理 RGB 图像 🔥
        rgb = self.data_processor.process_rgb(rgb, 'rgb')
        rgb_left = self.data_processor.process_rgb(rgb_left, 'rgb_left')
        rgb_right = self.data_processor.process_rgb(rgb_right, 'rgb_right')
        
        # 2. 提取原始传感器数据
        gps = input_data["gps"][1][:2]
        speed = input_data["speed"][1]["speed"]
        compass = input_data["imu"][1][-1]
        
        # 检查 NaN
        if math.isnan(compass):
            compass = 0.0
        
        # 🔥 处理传感器数据 🔥
        gps = self.data_processor.process_gps(gps)
        speed = self.data_processor.process_speed(speed)
        compass = self.data_processor.process_compass(compass)
        
        # 3. 组装处理后的数据
        result = {
            "rgb": rgb,
            "rgb_left": rgb_left,
            "rgb_right": rgb_right,
            "gps": gps,
            "speed": speed,
            "compass": compass,
        }
        
        # 4. 计算位置
        pos = self._get_position(result)
        
        # 5. 处理 LiDAR 数据
        lidar_data = input_data['lidar'][1]
        result['raw_lidar'] = lidar_data
        
        # 提取 x, y, z 坐标
        lidar_unprocessed = lidar_data[:, :3]
        lidar_unprocessed[:, 1] *= -1  # Y 轴翻转
        
        # 🔥 处理 LiDAR（在坐标转换前）🔥
        # 重新组装完整的 LiDAR 数据（包括强度信息）
        if lidar_data.shape[1] >= 4:
            lidar_with_intensity = np.column_stack([
                lidar_unprocessed, 
                lidar_data[:, 3:]
            ])
            lidar_with_intensity = self.data_processor.process_lidar(lidar_with_intensity)
            lidar_unprocessed = lidar_with_intensity[:, :3]
        else:
            # 如果没有强度信息，添加虚拟强度列以便处理
            lidar_with_dummy = np.column_stack([
                lidar_unprocessed,
                np.ones((len(lidar_unprocessed), 1))
            ])
            lidar_with_dummy = self.data_processor.process_lidar(lidar_with_dummy)
            lidar_unprocessed = lidar_with_dummy[:, :3]
        
        # 6. 坐标转换和特征提取（使用处理后的数据）
        full_lidar = transform_2d_points(
            lidar_unprocessed,
            np.pi / 2 - compass,
            -pos[0],
            -pos[1],
            np.pi / 2 - compass,
            -pos[0],
            -pos[1],
        )
        lidar_processed = lidar_to_histogram_features(full_lidar, crop=224)
        
        if self.step % 2 == 0 or self.step < 4:
            self.prev_lidar = lidar_processed
        result["lidar"] = self.prev_lidar
        
        # 7. 后续处理（保持不变）
        result["gps"] = pos
        next_wp, next_cmd = self._route_planner.run_step(pos)
        result["next_command"] = next_cmd.value
        result['measurements'] = [pos[0], pos[1], compass, speed]
        
        theta = compass + np.pi / 2
        R = np.array([[np.cos(theta), -np.sin(theta)], 
                      [np.sin(theta), np.cos(theta)]])
        
        local_command_point = np.array([next_wp[0] - pos[0], next_wp[1] - pos[1]])
        local_command_point = R.T.dot(local_command_point)
        result["target_point"] = local_command_point
        
        return result
    
    # ========== 关键修改 4: 在 run_step() 中更新帧计数 ==========
    @torch.no_grad()
    def run_step(self, input_data, timestamp):
        if not self.initialized:
            self._init()
        
        self.step += 1
        
        # 🔥 更新数据处理器帧计数 🔥
        if self.step % self.skip_frames == 0 or self.step <= 4:
            self.data_processor.next_frame()
        
        if self.step % self.skip_frames != 0 and self.step > 4:
            return self.prev_control
        
        # ... 后续代码保持不变 ...
        tick_data = self.tick(input_data)
        
        # ... 模型推理、控制器等代码保持不变 ...
        
        return control
    
    # ========== 关键修改 5（可选）: 在 destroy() 中保存统计信息 ==========
    def destroy(self):
        """清理资源"""
        # 保存数据处理器统计信息
        if hasattr(self, 'data_processor'):
            print("\n" + "=" * 60)
            print("Data Processor Final Statistics:")
            self.data_processor.print_stats()
            self.data_processor.save_stats('processor_stats.json')
            print("=" * 60 + "\n")
        
        # 原有清理代码
        if self.ensemble:
            del self.nets
        else:
            del self.net


# ========== 完整的修改步骤总结 ==========
"""
修改 interfuser_agent.py 的步骤：

1. 在文件顶部添加导入：
   ```python
   from team_code.data_processor import SensorDataProcessor
   from team_code.data_processor_config import ACTIVE_CONFIG
   ```

2. 在 InterfuserAgent.setup() 方法中添加（第 160 行附近）：
   ```python
   # 初始化数据处理器
   self.data_processor = SensorDataProcessor(ACTIVE_CONFIG)
   print("Data Processor initialized")
   print(self.data_processor.get_config_summary())
   ```

3. 在 InterfuserAgent.tick() 方法中修改（第 320-365 行）：
   - 提取 RGB 后立即调用 process_rgb()
   - 提取 GPS/速度/罗盘后立即调用对应的处理方法
   - 在 LiDAR 坐标转换前调用 process_lidar()

4. 在 InterfuserAgent.run_step() 方法中添加（第 384 行附近）：
   ```python
   self.data_processor.next_frame()
   ```

5. （可选）在 InterfuserAgent.destroy() 方法中添加：
   ```python
   if hasattr(self, 'data_processor'):
       self.data_processor.print_stats()
       self.data_processor.save_stats()
   ```
"""

# ========== 配置切换示例 ==========
"""
在 data_processor_config.py 中切换配置：

# 默认配置（所有处理关闭）
ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG

# 轻度噪声
ACTIVE_CONFIG = CONFIG_MILD_NOISE

# 中度噪声
ACTIVE_CONFIG = CONFIG_MODERATE_NOISE

# 严重噪声
ACTIVE_CONFIG = CONFIG_SEVERE_NOISE

# 传感器故障
ACTIVE_CONFIG = CONFIG_SENSOR_FAILURE

# 自定义配置
ACTIVE_CONFIG = {
    'enabled': True,
    'rgb': {
        'add_gaussian_noise': {'enabled': True, 'mean': 0, 'std': 20},
        'blur': {'enabled': True, 'kernel_size': 5},
    },
    'lidar': {
        'dropout': {'enabled': True, 'rate': 0.15},
    },
}
"""

