"""
快速评估配置（性能优化版本）

这个配置文件针对日常评估进行了优化：
- 关闭所有调试功能
- 使用轻度噪声
- 最小化性能开销

使用方法：
1. 将此文件重命名为 data_processor_config.py
2. 或在 data_processor_config.py 中导入: from data_processor_config_fast import FAST_CONFIG
"""

import numpy as np

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 快速轻度噪声配置（推荐用于日常评估）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONFIG_FAST_MILD = {
    "enabled": True,
    
    # ⚡ 性能优化设置
    "save_processed_images": False,  # ← 关键！节省 50-100ms/帧
    "save_path": "",
    "log_level": "ERROR",            # ← 关键！只记录错误，节省 5-10ms/帧
    
    # RGB 相机效果（轻度）
    "rgb_effects": {
        "add_gaussian_noise": {
            "enabled": True,
            "mean": 0,
            "std": 5,  # 轻度噪声
        },
        # 其他效果全部禁用以提升性能
        "brightness": {"enabled": False},
        "contrast": {"enabled": False},
        "saturation": {"enabled": False},
        "gaussian_blur": {"enabled": False},
        "pixel_dropout": {"enabled": False},
        "color_shift": {"enabled": False},
    },
    
    # LiDAR 效果（轻度）
    "lidar_effects": {
        "add_noise": {
            "enabled": True,
            "mean": 0,
            "std": 0.05,  # 轻度位置噪声
        },
        "dropout": {"enabled": False},
        "distance_limit": {"enabled": False},
        "intensity_noise": {"enabled": False},
    },
    
    # GPS 效果（轻度）
    "gps_effects": {
        "add_drift": {
            "enabled": True,
            "mean": 0,
            "std_lat": 0.00005,  # 轻度漂移
            "std_lon": 0.00005,
        },
        "random_jump": {"enabled": False},
    },
    
    # 其他传感器效果（轻度）
    "other_effects": {
        "speed_error": {
            "enabled": True,
            "mean": 0,
            "std": 0.2,  # 轻度速度误差
            "bias": 0.0,
        },
        "compass_error": {
            "enabled": True,
            "mean": 0,
            "std": np.deg2rad(1),  # 轻度方向误差（1 度）
        },
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 超快速配置（仅核心噪声）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONFIG_ULTRA_FAST = {
    "enabled": True,
    "save_processed_images": False,
    "save_path": "",
    "log_level": "CRITICAL",  # 几乎不记录日志
    
    # 只启用最关键的噪声
    "rgb_effects": {
        "add_gaussian_noise": {"enabled": True, "mean": 0, "std": 3},
        "brightness": {"enabled": False},
        "contrast": {"enabled": False},
        "saturation": {"enabled": False},
        "gaussian_blur": {"enabled": False},
        "pixel_dropout": {"enabled": False},
        "color_shift": {"enabled": False},
    },
    "lidar_effects": {
        "add_noise": {"enabled": True, "mean": 0, "std": 0.03},
        "dropout": {"enabled": False},
        "distance_limit": {"enabled": False},
        "intensity_noise": {"enabled": False},
    },
    "gps_effects": {
        "add_drift": {"enabled": False},
        "random_jump": {"enabled": False},
    },
    "other_effects": {
        "speed_error": {"enabled": False},
        "compass_error": {"enabled": False},
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 仅调试模式（评估少量路线）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONFIG_DEBUG = {
    "enabled": True,
    "save_processed_images": True,   # 保存图像用于调试
    "save_path": "debug_sensor_data",
    "log_level": "DEBUG",            # 详细日志
    
    "rgb_effects": {
        "add_gaussian_noise": {"enabled": True, "mean": 0, "std": 10},
        "brightness": {"enabled": False},
        "contrast": {"enabled": False},
        "saturation": {"enabled": False},
        "gaussian_blur": {"enabled": False},
        "pixel_dropout": {"enabled": False},
        "color_shift": {"enabled": False},
    },
    "lidar_effects": {
        "add_noise": {"enabled": True, "mean": 0, "std": 0.1},
        "dropout": {"enabled": False},
        "distance_limit": {"enabled": False},
        "intensity_noise": {"enabled": False},
    },
    "gps_effects": {
        "add_drift": {"enabled": True, "mean": 0, "std_lat": 0.0001, "std_lon": 0.0001},
        "random_jump": {"enabled": False},
    },
    "other_effects": {
        "speed_error": {"enabled": True, "mean": 0, "std": 0.5, "bias": 0.0},
        "compass_error": {"enabled": True, "mean": 0, "std": np.deg2rad(2)},
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 性能对比配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 预期性能（基于 PERFORMANCE_ANALYSIS.md）:
PERFORMANCE_TABLE = """
┌────────────────┬────────────────┬─────────────┬──────────┐
│ 配置           │ 额外开销       │ 总处理时间  │ 帧率     │
├────────────────┼────────────────┼─────────────┼──────────┤
│ 无处理         │ 0ms            │ ~52ms       │ 19.2 FPS │
│ ULTRA_FAST     │ +1-2ms         │ ~53-54ms    │ 18.5 FPS │
│ FAST_MILD      │ +3-5ms         │ ~55-57ms    │ 17.5 FPS │
│ MILD           │ +4-6ms         │ ~56-58ms    │ 17.0 FPS │
│ MODERATE       │ +5-10ms        │ ~57-62ms    │ 16.1 FPS │
│ SEVERE         │ +15-28ms       │ ~67-80ms    │ 12.5 FPS │
│ DEBUG          │ +50-150ms      │ ~102-202ms  │ 5-9 FPS  │
└────────────────┴────────────────┴─────────────┴──────────┘

推荐：
  • 日常评估: FAST_MILD 或 ULTRA_FAST
  • 鲁棒性测试: MILD 或 MODERATE
  • 压力测试: SEVERE
  • 调试分析: DEBUG (仅用于少量路线)
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 使用指南
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

USAGE_GUIDE = """
使用方法：

1. 在 data_processor_config.py 中设置活动配置：
   
   from data_processor_config_fast import CONFIG_FAST_MILD
   ACTIVE_CONFIG = CONFIG_FAST_MILD

2. 或直接重命名此文件：
   
   mv data_processor_config_fast.py data_processor_config.py
   # 然后设置: ACTIVE_CONFIG = CONFIG_FAST_MILD

3. 运行评估：
   
   ./run_evaluation_with_processor.sh town05 custom

性能优化技巧：

✅ 必做（节省 50-110ms/帧）：
   • save_processed_images = False
   • log_level = "ERROR" 或 "CRITICAL"

✅ 推荐：
   • 使用 FAST_MILD 或 ULTRA_FAST 配置
   • 只启用必要的效果

⚠️ 避免：
   • save_processed_images = True（除非调试）
   • log_level = "DEBUG"（除非调试）
   • 同时启用太多效果
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 默认配置（快速模式）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 如果使用此文件，默认使用快速轻度配置
ACTIVE_CONFIG = CONFIG_FAST_MILD

if __name__ == "__main__":
    print(PERFORMANCE_TABLE)
    print(USAGE_GUIDE)

