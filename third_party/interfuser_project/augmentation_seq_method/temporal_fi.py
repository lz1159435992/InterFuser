from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import os
import sys
from pathlib import Path

import numpy as np


def _validate_rgb_uint8(img: np.ndarray, name: str) -> None:
    if not isinstance(img, np.ndarray):
        raise TypeError(f"{name} must be a numpy array, got {type(img)}")
    if img.dtype != np.uint8:
        raise TypeError(f"{name} must be uint8, got {img.dtype}")
    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError(f"{name} must have shape (H, W, 3), got {img.shape}")


class FrameInterpolator:
    def interpolate(self, prev: np.ndarray, curr: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class BlendFrameInterpolator(FrameInterpolator):
    def __init__(self, alpha: float = 0.5):
        if not (0.0 < alpha < 1.0):
            raise ValueError("alpha must be in (0, 1)")
        self.alpha = float(alpha)

    def interpolate(self, prev: np.ndarray, curr: np.ndarray) -> np.ndarray:
        _validate_rgb_uint8(prev, "prev")
        _validate_rgb_uint8(curr, "curr")
        if prev.shape != curr.shape:
            raise ValueError(f"prev/curr shape mismatch: {prev.shape} vs {curr.shape}")

        a = self.alpha
        out = (prev.astype(np.float32) * (1.0 - a) + curr.astype(np.float32) * a).round()
        return out.clip(0, 255).astype(np.uint8)


class RIFEFrameInterpolator(FrameInterpolator):
    def __init__(self, model_dir: Optional[str] = None, timestep: float = 0.5):
        if not (0.0 < float(timestep) < 1.0):
            raise ValueError("timestep must be in (0, 1)")

        self.timestep = float(timestep)

        rife_root_env = os.environ.get("RIFE_ROOT", "")
        if rife_root_env:
            rife_root = Path(rife_root_env).expanduser()
        else:
            rife_root = Path(__file__).resolve().parents[1] / "process_mothod" / "ECCV2022-RIFE"
        self.rife_root = rife_root

        if not self.rife_root.exists():
            raise FileNotFoundError(f"RIFE repo root not found: {self.rife_root}")

        if model_dir is None:
            model_dir = os.environ.get("RIFE_MODEL_DIR", "")
        if model_dir:
            self.model_dir = Path(model_dir).expanduser()
        else:
            self.model_dir = self.rife_root / "train_log"

        if str(self.rife_root) not in sys.path:
            sys.path.insert(0, str(self.rife_root))

        import torch
        from torch.nn import functional as F

        self._torch = torch
        self._F = F

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = self._load_model()
        self._model.eval()
        try:
            self._model.device()
        except Exception:
            pass

    def _load_model(self):
        try:
            try:
                try:
                    from model.RIFE_HDv2 import Model

                    model = Model()
                    model.load_model(str(self.model_dir), -1)
                    return model
                except Exception:
                    from train_log.RIFE_HDv3 import Model

                    model = Model()
                    model.load_model(str(self.model_dir), -1)
                    return model
            except Exception:
                from model.RIFE_HD import Model

                model = Model()
                model.load_model(str(self.model_dir), -1)
                return model
        except Exception:
            try:
                from model.oldmodel.RIFE_HDv2 import Model

                model = Model()
                model.load_model(str(self.model_dir), -1)
                return model
            except Exception:
                try:
                    from model.oldmodel.RIFE_HD import Model

                    model = Model()
                    model.load_model(str(self.model_dir), -1)
                    return model
                except Exception:
                    from model.RIFE import Model

                    model = Model()
                    model.load_model(str(self.model_dir), -1)
                    return model

    def interpolate(self, prev: np.ndarray, curr: np.ndarray) -> np.ndarray:
        _validate_rgb_uint8(prev, "prev")
        _validate_rgb_uint8(curr, "curr")
        if prev.shape != curr.shape:
            raise ValueError(f"prev/curr shape mismatch: {prev.shape} vs {curr.shape}")

        torch = self._torch
        F = self._F

        prev_bgr = np.ascontiguousarray(prev[..., ::-1])
        curr_bgr = np.ascontiguousarray(curr[..., ::-1])

        img0 = torch.from_numpy(prev_bgr.transpose(2, 0, 1)).to(self._device).float().div(255.0).unsqueeze(0)
        img1 = torch.from_numpy(curr_bgr.transpose(2, 0, 1)).to(self._device).float().div(255.0).unsqueeze(0)

        _, _, h, w = img0.shape
        ph = ((h - 1) // 32 + 1) * 32
        pw = ((w - 1) // 32 + 1) * 32
        padding = (0, pw - w, 0, ph - h)
        img0 = F.pad(img0, padding)
        img1 = F.pad(img1, padding)

        with torch.no_grad():
            try:
                out = self._model.inference(img0, img1, timestep=self.timestep)
            except TypeError:
                out = self._model.inference(img0, img1)

        out = out[0].clamp(0.0, 1.0)[:, :h, :w]
        out_bgr = (out * 255.0).round().byte().cpu().numpy().transpose(1, 2, 0)
        out_rgb = np.ascontiguousarray(out_bgr[..., ::-1])
        return out_rgb


@dataclass
class TemporalFICache:
    apply_to: Iterable[str]
    interpolator: FrameInterpolator
    prev_raw: Optional[Dict[str, np.ndarray]] = None

    def has_prev(self) -> bool:
        return isinstance(self.prev_raw, dict) and len(self.prev_raw) > 0

    def reset(self) -> None:
        self.prev_raw = None

    def update_prev(self, curr_raw: Dict[str, np.ndarray]) -> None:
        self.prev_raw = {k: curr_raw[k] for k in self.apply_to if k in curr_raw}

    def interpolate_mid(self, curr_for_fi: Dict[str, np.ndarray]) -> Optional[Dict[str, np.ndarray]]:
        if not self.has_prev() or self.prev_raw is None:
            return None

        mid: Dict[str, np.ndarray] = {}
        for k in self.apply_to:
            if k not in self.prev_raw or k not in curr_for_fi:
                continue
            mid[k] = self.interpolator.interpolate(self.prev_raw[k], curr_for_fi[k])
        return mid
