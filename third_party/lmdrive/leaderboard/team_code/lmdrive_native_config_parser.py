import os
from dataclasses import dataclass
from typing import Tuple


_ALLOWED_TOKENS = {"none", "high_fps", "high_res", "no_noise", "gauss8", "gauss16"}


@dataclass(frozen=True)
class NativeEnhanceConfig:
    tokens: Tuple[str, ...]
    high_fps: bool
    high_res: bool
    no_noise: bool
    gaussian_noise_sigma: int

    frame_rate: int
    fixed_delta_seconds: float
    sensor_tick: float

    camera_front_width: int
    camera_front_height: int
    camera_side_width: int
    camera_side_height: int

    motion_blur_intensity: float
    motion_blur_max_distortion: float
    bloom_intensity: float
    lens_flare_intensity: float
    lens_circle_falloff: float
    lens_k: float
    lens_kcube: float


def _normalize_token(tok: str) -> str:
    return tok.strip().lower()


def parse_native_enhance(enhance_str: str = None) -> Tuple[str, ...]:
    if enhance_str is None:
        enhance_str = os.environ.get("NATIVE_ENHANCE", "")

    s = enhance_str.strip()
    if not s:
        return ("none",)

    tokens = [_normalize_token(t) for t in s.split(",") if _normalize_token(t)]
    if not tokens:
        return ("none",)

    for t in tokens:
        if t not in _ALLOWED_TOKENS:
            raise ValueError(f"Unknown NATIVE_ENHANCE token: {t}")

    if "none" in tokens and len(tokens) > 1:
        raise ValueError("NATIVE_ENHANCE contains 'none' with other tokens")

    gauss_tokens = [t for t in tokens if t in {"gauss8", "gauss16"}]
    if len(gauss_tokens) > 1:
        raise ValueError("NATIVE_ENHANCE contains multiple gaussian noise tokens")
    if len(gauss_tokens) == 1 and len(tokens) > 1:
        raise ValueError("Gaussian noise tokens cannot be combined with other tokens")

    return tuple(tokens)


def build_config(tokens: Tuple[str, ...] = None) -> NativeEnhanceConfig:
    if tokens is None:
        tokens = parse_native_enhance()

    high_fps = "high_fps" in tokens
    high_res = "high_res" in tokens
    no_noise = "no_noise" in tokens

    if "gauss8" in tokens:
        gaussian_noise_sigma = 8
    elif "gauss16" in tokens:
        gaussian_noise_sigma = 16
    else:
        gaussian_noise_sigma = 0

    if high_fps:
        frame_rate = 40
        fixed_delta_seconds = 0.025
        sensor_tick = 0.025
    else:
        frame_rate = 20
        fixed_delta_seconds = 0.05
        sensor_tick = 0.05

    if high_res:
        camera_front_width = 2400
        camera_front_height = 1800
        camera_side_width = 800
        camera_side_height = 600
    else:
        camera_front_width = 1200
        camera_front_height = 900
        camera_side_width = 400
        camera_side_height = 300

    if no_noise:
        motion_blur_intensity = 0.0
        motion_blur_max_distortion = 0.0
        bloom_intensity = 0.0
        lens_flare_intensity = 0.0
        lens_circle_falloff = 0.0
        lens_k = 0.0
        lens_kcube = 0.0
    else:
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
        sensor_tick=sensor_tick,
        camera_front_width=camera_front_width,
        camera_front_height=camera_front_height,
        camera_side_width=camera_side_width,
        camera_side_height=camera_side_height,
        motion_blur_intensity=motion_blur_intensity,
        motion_blur_max_distortion=motion_blur_max_distortion,
        bloom_intensity=bloom_intensity,
        lens_flare_intensity=lens_flare_intensity,
        lens_circle_falloff=lens_circle_falloff,
        lens_k=lens_k,
        lens_kcube=lens_kcube,
    )


def load_config_from_env() -> NativeEnhanceConfig:
    tokens = parse_native_enhance()
    return build_config(tokens)
