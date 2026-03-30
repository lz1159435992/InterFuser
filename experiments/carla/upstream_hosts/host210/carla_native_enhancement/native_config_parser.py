"""
Configuration parser for CARLA native sensor enhancements.

Parses NATIVE_ENHANCE environment variable into sensor configuration parameters.
"""

import os
from dataclasses import dataclass
from typing import Tuple


_ALLOWED_TOKENS = {"none", "high_fps", "high_res", "no_noise", "gauss8", "gauss16"}


@dataclass(frozen=True)
class NativeEnhanceConfig:
    """Configuration for native sensor enhancements."""
    tokens: Tuple[str, ...]
    high_fps: bool
    high_res: bool
    no_noise: bool
    gaussian_noise_sigma: int
    
    # Derived parameters
    frame_rate: int  # 20 or 40
    fixed_delta_seconds: float  # 0.05 or 0.025
    camera_width: int  # 800 or 1600
    camera_height: int  # 600 or 1200
    sensor_tick: float  # 0.05 or 0.025
    
    # Noise parameters
    motion_blur_intensity: float
    motion_blur_max_distortion: float
    bloom_intensity: float
    lens_flare_intensity: float
    lens_circle_falloff: float
    lens_k: float
    lens_kcube: float


def _normalize_token(tok: str) -> str:
    """Normalize a token to lowercase and strip whitespace."""
    return tok.strip().lower()


def parse_native_enhance(enhance_str: str = None) -> Tuple[str, ...]:
    """
    Parse NATIVE_ENHANCE string into a tuple of tokens.
    
    Args:
        enhance_str: Comma-separated enhancement tokens (e.g., "high_fps,high_res").
                    If None, reads from NATIVE_ENHANCE environment variable.
    
    Returns:
        Tuple of normalized tokens.
    
    Raises:
        ValueError: If unknown token or invalid combination is found.
    """
    if enhance_str is None:
        enhance_str = os.environ.get("NATIVE_ENHANCE", "")
    
    s = enhance_str.strip()
    if not s:
        return ("none",)
    
    tokens = [_normalize_token(t) for t in s.split(",") if _normalize_token(t)]
    if not tokens:
        return ("none",)
    
    # Validate tokens
    for t in tokens:
        if t not in _ALLOWED_TOKENS:
            raise ValueError(f"Unknown NATIVE_ENHANCE token: {t}")
    
    # Check for conflicts
    if "none" in tokens and len(tokens) > 1:
        raise ValueError("NATIVE_ENHANCE contains 'none' with other tokens")

    gauss_tokens = [t for t in tokens if t in {"gauss8", "gauss16"}]
    if len(gauss_tokens) > 1:
        raise ValueError("NATIVE_ENHANCE contains multiple gaussian noise tokens")
    if len(gauss_tokens) == 1 and len(tokens) > 1:
        raise ValueError("Gaussian noise tokens cannot be combined with other tokens")
    
    return tuple(tokens)


def build_config(tokens: Tuple[str, ...] = None) -> NativeEnhanceConfig:
    """
    Build NativeEnhanceConfig from tokens.
    
    Args:
        tokens: Tuple of enhancement tokens. If None, parses from environment.
    
    Returns:
        NativeEnhanceConfig with all parameters set.
    """
    if tokens is None:
        tokens = parse_native_enhance()
    
    # Parse flags
    high_fps = "high_fps" in tokens
    high_res = "high_res" in tokens
    no_noise = "no_noise" in tokens

    if "gauss8" in tokens:
        gaussian_noise_sigma = 8
    elif "gauss16" in tokens:
        gaussian_noise_sigma = 16
    else:
        gaussian_noise_sigma = 0
    
    # Derive frame rate parameters
    if high_fps:
        frame_rate = 40
        fixed_delta_seconds = 0.025
        sensor_tick = 0.025
    else:
        frame_rate = 20
        fixed_delta_seconds = 0.05
        sensor_tick = 0.05
    
    # Derive resolution parameters
    if high_res:
        camera_width = 1600
        camera_height = 1200
    else:
        camera_width = 800
        camera_height = 600
    
    # Derive noise parameters
    if no_noise:
        motion_blur_intensity = 0.0
        motion_blur_max_distortion = 0.0
        bloom_intensity = 0.0
        lens_flare_intensity = 0.0
        lens_circle_falloff = 0.0
        lens_k = 0.0
        lens_kcube = 0.0
    else:
        # CARLA defaults
        motion_blur_intensity = 0.45
        motion_blur_max_distortion = 0.35
        bloom_intensity = 0.675
        lens_flare_intensity = 0.1
        lens_circle_falloff = 5.0
        lens_k = -1.0
        lens_kcube = 0.0
    
    return NativeEnhanceConfig(
        tokens=tokens,
        high_fps=high_fps,
        high_res=high_res,
        no_noise=no_noise,
        gaussian_noise_sigma=gaussian_noise_sigma,
        frame_rate=frame_rate,
        fixed_delta_seconds=fixed_delta_seconds,
        camera_width=camera_width,
        camera_height=camera_height,
        sensor_tick=sensor_tick,
        motion_blur_intensity=motion_blur_intensity,
        motion_blur_max_distortion=motion_blur_max_distortion,
        bloom_intensity=bloom_intensity,
        lens_flare_intensity=lens_flare_intensity,
        lens_circle_falloff=lens_circle_falloff,
        lens_k=lens_k,
        lens_kcube=lens_kcube,
    )


def load_config_from_env() -> NativeEnhanceConfig:
    """
    Load configuration from NATIVE_ENHANCE environment variable.
    
    Returns:
        NativeEnhanceConfig with all parameters set.
    """
    tokens = parse_native_enhance()
    return build_config(tokens)
