from lmdriver_config import GlobalConfig as BaseConfig


class GlobalConfig(BaseConfig):
    # Enable external sensor data processor for LMDrive evaluation
    use_data_processor = True
