import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .path_utils import ensure_process_method_on_path, get_process_method_root


@dataclass
class SpatialPipelineConfig:
    ops: Tuple[str, ...]
    device: str
    half_precision: bool
    swinir_tile: Optional[int]
    swinir_tile_overlap: int


def _infer_device() -> str:
    device = os.environ.get("DATA_PROCESSOR_DEVICE", "").strip()
    if device:
        return device

    gpu_id = os.environ.get("DATA_PROCESSOR_GPU_ID", "").strip()
    if gpu_id:
        return f"cuda:{gpu_id}"

    return "cuda"


def _infer_half_precision() -> bool:
    v = os.environ.get("DATA_PROCESSOR_HALF", "").strip().lower()
    return v in {"1", "true", "yes", "y", "on"}


def _infer_tile() -> Optional[int]:
    v = os.environ.get("DATA_PROCESSOR_TILE", "").strip().lower()
    if not v:
        return 256
    if v in {"none", "null", "-1"}:
        return None
    try:
        return int(v)
    except Exception:
        return 256


def _infer_tile_overlap() -> int:
    v = os.environ.get("DATA_PROCESSOR_TILE_OVERLAP", "").strip()
    try:
        return int(v) if v else 32
    except Exception:
        return 32


def _default_dn15_model_path() -> str:
    root = get_process_method_root()
    return str(root / "SwinIR" / "model_zoo" / "swinir" / "005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth")


def _default_srgan_model_path() -> str:
    root = get_process_method_root()
    return str(root / "SRGAN" / "results" / "checkpoint_srgan.pth")


class SpatialPipeline:
    def __init__(self, ops: Sequence[str]):
        self.ops = tuple([op for op in ops if op not in {"none", "fi"}])

        self.config = SpatialPipelineConfig(
            ops=self.ops,
            device=_infer_device(),
            half_precision=_infer_half_precision(),
            swinir_tile=_infer_tile(),
            swinir_tile_overlap=_infer_tile_overlap(),
        )

        self._swinir_dn15 = None
        self._srgan_2x = None

        ensure_process_method_on_path()

    def _get_swinir_dn15(self):
        if self._swinir_dn15 is not None:
            return self._swinir_dn15

        from SwinIR.swinir_wrapper import SwinIRProcessor

        self._swinir_dn15 = SwinIRProcessor(
            model_path=_default_dn15_model_path(),
            task="color_dn",
            upscale=1,
            device=self.config.device,
            half_precision=self.config.half_precision,
            noise=15,
            tile=self.config.swinir_tile,
            tile_overlap=self.config.swinir_tile_overlap,
        )
        return self._swinir_dn15

    def _get_srgan_2x(self):
        if self._srgan_2x is not None:
            return self._srgan_2x

        from SRGAN.srgan_wrapper import SRGANProcessor

        self._srgan_2x = SRGANProcessor(
            model_path=_default_srgan_model_path(),
            device=self.config.device,
            half_precision=self.config.half_precision,
            output_scale=2,
        )
        return self._srgan_2x

    def process_rgb_batch(self, images: Sequence[np.ndarray]) -> List[np.ndarray]:
        imgs: List[np.ndarray] = list(images)
        for op in self.ops:
            if op == "dn15":
                proc = self._get_swinir_dn15()
                imgs = proc.process_batch(imgs)
            elif op == "srgan_2x":
                proc = self._get_srgan_2x()
                imgs = [proc.process(img) for img in imgs]
            else:
                raise ValueError(f"Unsupported spatial op: {op}")
        return imgs

    def process_cameras(self, images_by_id: Dict[str, np.ndarray], apply_to: Iterable[str]) -> Dict[str, np.ndarray]:
        keys = [k for k in apply_to if k in images_by_id]
        batch = [images_by_id[k] for k in keys]
        if not batch:
            return dict(images_by_id)

        processed = self.process_rgb_batch(batch)
        out = dict(images_by_id)
        for k, img in zip(keys, processed):
            out[k] = img
        return out
