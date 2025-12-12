"""
数据处理器配置文件 - 图像处理模块

支持多种图像处理方法:
  • SwinIR - 基于 Swin Transformer 的图像修复（去噪、超分辨率、JPEG 修复）
  • SRGAN - 基于 GAN 的 4x 超分辨率 / 图像增强

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 快速控制指南：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

方法 1: 完全关闭所有数据处理（推荐）⭐
  修改下面的 ENABLE_ALL_PROCESSING = False

方法 2: 使用预设配置
  修改最后一行: ACTIVE_CONFIG = CONFIG_NO_PROCESSING  # 不处理
                ACTIVE_CONFIG = CONFIG_SWINIR_DENOISE  # SwinIR 彩色去噪
                ACTIVE_CONFIG = CONFIG_SRGAN_ENHANCE   # SRGAN 图像增强
                ACTIVE_CONFIG = CONFIG_SRGAN_SR        # SRGAN 超分辨率

方法 3: 自定义处理
  修改下面 DATA_PROCESSOR_CONFIG 中的参数

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os

# ============================================================
# 🎛️ 总开关 - 最简单的控制方法
# ============================================================

ENABLE_ALL_PROCESSING = True  # ← 改为 False 即可关闭所有数据处理！

# ============================================================
# 📝 基础配置 - 图像处理
# ============================================================

DATA_PROCESSOR_CONFIG = {
    # 全局开关
    'enabled': ENABLE_ALL_PROCESSING,
    
    # ========== 处理方法选择 ==========
    # 注意: 同时只能启用一种处理方法！
    'processor_type': 'none',  # 可选: 'none', 'swinir', 'srgan'
    
    # ========== SwinIR 配置 ==========
    'swinir': {
        'enabled': False,  # 是否启用 SwinIR（需要先下载模型）
        
        # 模型路径（必需）
        'model_path': '/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth',
        
        # 任务类型（与 main_test_swinir.py 一致）
        # 可选: 'classical_sr', 'lightweight_sr', 'real_sr', 
        #       'gray_dn', 'color_dn', 'jpeg_car', 'color_jpeg_car'
        'task': 'color_dn',  # 默认: 彩色图像去噪
        
        # 放大倍数（用于超分辨率任务）
        'upscale': 1,  # 默认: 1 (去噪任务), SR 任务使用 2, 4, 8
        
        # 噪声等级（用于去噪任务）
        'noise': 15,  # 默认: 15, 可选: 15, 25, 50
        
        # JPEG 质量（用于 JPEG 修复任务）
        'jpeg': 40,  # 默认: 40, 可选: 10, 20, 30, 40
        
        # 训练时的 patch 大小
        'training_patch_size': 128,  # 默认: 128
        
        # 瓦片处理（用于大图像）
        'tile': None,  # 默认: None (整图处理), 可设为 512, 1024 等
        'tile_overlap': 32,  # 默认: 32
        
        # 设备
        'device': 'cuda',  # 'cuda' 或 'cpu'
        
        # 半精度（FP16）
        'half_precision': False,  # True 可加速，但可能降低精度
    },
    
    # ========== SRGAN 配置 ==========
    'srgan': {
        'enabled': False,  # 是否启用 SRGAN
        
        # 模型路径（必需）
        'model_path': '/home/nju/InterFuser/process_mothod/SRGAN/results/checkpoint_srgan.pth',
        
        # 设备
        'device': 'cpu',  # 'cuda' 或 'cpu'
        
        # 半精度（FP16）
        'half_precision': False,  # True 可加速，但可能降低精度
        
        # 输出放大倍数（相对于输入）
        'output_scale': 2,  # 1: 原始大小（增强）
                            # 2: 2x 大小（与原始 test.py 一致）⭐ 默认
                            # 4: 4x 大小（完整超分辨率）
        
        # 模型参数（通常不需要修改）
        'large_kernel_size': 9,
        'small_kernel_size': 3,
        'n_channels': 64,
        'n_blocks': 16,
        'scaling_factor': 4,  # SRGAN 内部放大倍数
    },
}


# ============================================================
# 🚫 无处理配置 - 直接传递原始数据
# ============================================================

CONFIG_NO_PROCESSING = {
    'enabled': False,
    'swinir': {
        'enabled': False,
    },
}


# ============================================================
# 🎨 预设配置 1: 彩色图像去噪（噪声等级 15）
# ============================================================

CONFIG_COLOR_DENOISE = {
    'enabled': True,
    'swinir': {
        'enabled': True,
        'model_path': '/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth',
        'task': 'color_dn',
        'upscale': 1,
        'noise': 15,
        'training_patch_size': 128,
        'device': 'cuda',
        'half_precision': False,
        'tile': 256,
        'tile_overlap': 32,
    },
}


# ============================================================
# 🎨 预设配置 2: 彩色图像去噪（噪声等级 25）
# ============================================================

CONFIG_COLOR_DENOISE_25 = {
    'enabled': True,
    'swinir': {
        'enabled': True,
        'model_path': '/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise25.pth',
        'task': 'color_dn',
        'upscale': 1,
        'noise': 25,
        'training_patch_size': 128,
        'device': 'cuda',
        'half_precision': False,
    },
}


# ============================================================
# 🎨 预设配置 3: 彩色图像去噪（噪声等级 50）
# ============================================================

CONFIG_COLOR_DENOISE_50 = {
    'enabled': True,
    'swinir': {
        'enabled': True,
        'model_path': '/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise50.pth',
        'task': 'color_dn',
        'upscale': 1,
        'noise': 50,
        'training_patch_size': 128,
        'device': 'cuda',
        'half_precision': False,
    },
}


# ============================================================
# 🔍 预设配置 4: 2x 超分辨率
# ============================================================

CONFIG_SR_2X = {
    'enabled': True,
    'swinir': {
        'enabled': True,
        'model_path': '/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x2.pth',
        'task': 'classical_sr',
        'upscale': 2,
        'training_patch_size': 128,
        'device': 'cuda',
        'half_precision': False,
    },
}


# ============================================================
# 🔍 预设配置 5: 4x 超分辨率
# ============================================================

CONFIG_SR_4X = {
    'enabled': True,
    'swinir': {
        'enabled': True,
        'model_path': '/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth',
        'task': 'classical_sr',
        'upscale': 4,
        'training_patch_size': 128,
        'device': 'cuda',
        'half_precision': False,
    },
}


# ============================================================
# 📷 预设配置 6: JPEG 压缩伪影修复（质量 40）
# ============================================================

CONFIG_JPEG_REPAIR = {
    'enabled': True,
    'processor_type': 'swinir',
    'swinir': {
        'enabled': True,
        'model_path': '/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/006_CAR_DFWB_s126w7_SwinIR-M_jpeg40.pth',
        'task': 'jpeg_car',
        'upscale': 1,
        'jpeg': 40,
        'training_patch_size': 128,
        'device': 'cuda',
        'half_precision': False,
    },
    'srgan': {'enabled': False},
}


# ============================================================
# 🖼️ 预设配置 7: SRGAN 2x 超分辨率（与原始 test.py 一致）
# ============================================================

CONFIG_SRGAN_2X = {
    'enabled': True,
    'processor_type': 'srgan',
    'swinir': {'enabled': False},
    'srgan': {
        'enabled': True,
        'model_path': '/home/nju/InterFuser/process_mothod/SRGAN/results/checkpoint_srgan.pth',
        'device': 'cpu',
        'half_precision': False,
        'output_scale': 2,  # 2x 输出（与原始 test.py 一致）⭐
    },
}


# ============================================================
# 📈 预设配置 8: SRGAN 图像增强（缩放回原始大小）
# ============================================================

CONFIG_SRGAN_ENHANCE = {
    'enabled': True,
    'processor_type': 'srgan',
    'swinir': {'enabled': False},
    'srgan': {
        'enabled': True,
        'model_path': '/home/nju/InterFuser/process_mothod/SRGAN/results/checkpoint_srgan.pth',
        'device': 'cpu',
        'half_precision': False,
        'output_scale': 1,  # 1x 输出（增强模式）
    },
}


# ============================================================
# 🔍 预设配置 9: SRGAN 4x 超分辨率（完整放大）
# ============================================================

CONFIG_SRGAN_4X = {
    'enabled': True,
    'processor_type': 'srgan',
    'swinir': {'enabled': False},
    'srgan': {
        'enabled': True,
        'model_path': '/home/nju/InterFuser/process_mothod/SRGAN/results/checkpoint_srgan.pth',
        'device': 'cpu',
        'half_precision': False,
        'output_scale': 4,  # 4x 输出（完整超分辨率）
    },
}


# ============================================================
# 🎯 激活配置选择
# ============================================================
# 
# 可选配置：
#
# 【无处理】
#   - CONFIG_NO_PROCESSING      : 无处理（原始数据）⭐ 推荐测试用
#
# 【SwinIR】
#   - CONFIG_COLOR_DENOISE      : 彩色去噪 (noise=15) ✅ 模型已下载
#   - CONFIG_COLOR_DENOISE_25   : 彩色去噪 (noise=25) ⚠️ 需下载模型
#   - CONFIG_COLOR_DENOISE_50   : 彩色去噪 (noise=50) ⚠️ 需下载模型
#   - CONFIG_SR_2X              : 2x 超分辨率 ⚠️ 需下载模型
#   - CONFIG_SR_4X              : 4x 超分辨率 ⚠️ 需下载模型
#   - CONFIG_JPEG_REPAIR        : JPEG 修复 ⚠️ 需下载模型
#
# 【SRGAN】
#   - CONFIG_SRGAN_2X           : 2x 超分辨率（与原始 test.py 一致）✅ 模型已存在 ⭐ 推荐
#   - CONFIG_SRGAN_ENHANCE      : 图像增强（1x，缩放回原始大小）✅ 模型已存在
#   - CONFIG_SRGAN_4X           : 4x 超分辨率（完整放大）✅ 模型已存在
#
# 【自定义】
#   - DATA_PROCESSOR_CONFIG     : 自定义配置
#
# 使用方法：取消注释下面某一行，或修改最后的 ACTIVE_CONFIG
#
# ============================================================

# 无处理
# ACTIVE_CONFIG = CONFIG_NO_PROCESSING

# SwinIR
# ACTIVE_CONFIG = CONFIG_COLOR_DENOISE     # 彩色去噪 (noise=15)
# ACTIVE_CONFIG = CONFIG_COLOR_DENOISE_25  # 彩色去噪 (noise=25)
# ACTIVE_CONFIG = CONFIG_COLOR_DENOISE_50  # 彩色去噪 (noise=50)
# ACTIVE_CONFIG = CONFIG_SR_2X             # 2x 超分辨率
# ACTIVE_CONFIG = CONFIG_SR_4X             # 4x 超分辨率
# ACTIVE_CONFIG = CONFIG_JPEG_REPAIR       # JPEG 修复

# SRGAN
# ACTIVE_CONFIG = CONFIG_SRGAN_2X          # SRGAN 2x 超分辨率（与原始 test.py 一致）⭐
# ACTIVE_CONFIG = CONFIG_SRGAN_ENHANCE     # SRGAN 图像增强（1x）
# ACTIVE_CONFIG = CONFIG_SRGAN_4X          # SRGAN 4x 超分辨率

# 默认使用无处理配置（可被环境变量 DATA_PROCESSOR_CONFIG_TYPE 覆盖）
ACTIVE_CONFIG = CONFIG_NO_PROCESSING

# 允许通过环境变量选择不同的预设配置，保持对旧逻辑的兼容：
# - 如果 DATA_PROCESSOR_CONFIG_TYPE 未设置或为空，则沿用上面的 ACTIVE_CONFIG
# - 如果设置为支持的字符串，则覆盖 ACTIVE_CONFIG
CONFIG_TYPE = os.environ.get("DATA_PROCESSOR_CONFIG_TYPE", "").strip()

if CONFIG_TYPE:
    if CONFIG_TYPE == "no_processing":
        ACTIVE_CONFIG = CONFIG_NO_PROCESSING
    elif CONFIG_TYPE == "denoise15":
        ACTIVE_CONFIG = CONFIG_COLOR_DENOISE
    elif CONFIG_TYPE == "denoise25":
        ACTIVE_CONFIG = CONFIG_COLOR_DENOISE_25
    elif CONFIG_TYPE == "denoise50":
        ACTIVE_CONFIG = CONFIG_COLOR_DENOISE_50
    elif CONFIG_TYPE == "sr2x":
        ACTIVE_CONFIG = CONFIG_SR_2X
    elif CONFIG_TYPE == "sr4x":
        ACTIVE_CONFIG = CONFIG_SR_4X
    elif CONFIG_TYPE == "jpeg_repair":
        ACTIVE_CONFIG = CONFIG_JPEG_REPAIR
    elif CONFIG_TYPE == "srgan_2x":
        ACTIVE_CONFIG = CONFIG_SRGAN_2X
    elif CONFIG_TYPE == "srgan_enhance":
        ACTIVE_CONFIG = CONFIG_SRGAN_ENHANCE
    elif CONFIG_TYPE == "srgan_4x":
        ACTIVE_CONFIG = CONFIG_SRGAN_4X
    elif CONFIG_TYPE == "custom":
        ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG
    # 未知值时保持原有 ACTIVE_CONFIG 不变，以避免意外崩溃

