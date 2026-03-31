import numpy as np

# 快速测试配置
CONFIG_FAST_TEST = {
    "enabled": True,
    "save_processed_images": False,  # 关闭保存以提升性能
    "save_path": "",
    "log_level": "INFO",  # 看到一些输出
    
    "rgb_effects": {
        "add_gaussian_noise": {"enabled": True, "mean": 0, "std": 5},
        "brightness": {"enabled": False},
        "contrast": {"enabled": False},
        "saturation": {"enabled": False},
        "gaussian_blur": {"enabled": False},
        "pixel_dropout": {"enabled": False},
        "color_shift": {"enabled": False},
    },
    "lidar_effects": {
        "add_noise": {"enabled": True, "mean": 0, "std": 0.05},
        "dropout": {"enabled": False},
        "distance_limit": {"enabled": False},
        "intensity_noise": {"enabled": False},
    },
    "gps_effects": {
        "add_drift": {"enabled": True, "mean": 0, "std_lat": 0.00005, "std_lon": 0.00005},
        "random_jump": {"enabled": False},
    },
    "other_effects": {
        "speed_error": {"enabled": True, "mean": 0, "std": 0.2, "bias": 0.0},
        "compass_error": {"enabled": True, "mean": 0, "std": np.deg2rad(1)},
    },
}

ACTIVE_CONFIG = CONFIG_FAST_TEST
