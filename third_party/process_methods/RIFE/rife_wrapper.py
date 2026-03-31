import os
import sys
import inspect

import numpy as np


class RIFEProcessor:
    def __init__(
        self,
        model_dir: str,
        *,
        device: str = "auto",
        scale: float = 1.0,
        tta: bool = False,
    ):
        self.model_dir = model_dir
        self.scale = float(scale)
        self.tta = bool(tta)

        rife_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ECCV2022-RIFE"))
        if rife_root not in sys.path:
            sys.path.insert(0, rife_root)

        import torch
        from torch.nn import functional as F

        self._torch = torch
        self._F = F

        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        torch.set_grad_enabled(False)
        if self.device.type == "cuda":
            torch.backends.cudnn.enabled = True
            torch.backends.cudnn.benchmark = True

        self.model = self._load_model(model_dir)
        self.model.eval()
        self.model.device()

    def _load_model(self, model_dir: str):
        try:
            from model.RIFE_HDv2 import Model

            model = Model()
            model.load_model(model_dir, -1)
            return model
        except Exception:
            pass

        try:
            from model.oldmodel.RIFE_HDv2 import Model

            model = Model()
            model.load_model(model_dir, -1)
            return model
        except Exception:
            pass

        try:
            from train_log.RIFE_HDv3 import Model

            model = Model()
            model.load_model(model_dir, -1)
            return model
        except Exception:
            pass

        try:
            from model.RIFE_HD import Model

            model = Model()
            model.load_model(model_dir, -1)
            return model
        except Exception:
            pass

        try:
            from model.oldmodel.RIFE_HD import Model

            model = Model()
            model.load_model(model_dir, -1)
            return model
        except Exception:
            pass

        from model.RIFE import Model

        model = Model()
        model.load_model(model_dir, -1)
        return model

    def interpolate(self, img0_rgb_uint8: np.ndarray, img1_rgb_uint8: np.ndarray, *, timestep: float = 0.5) -> np.ndarray:
        torch = self._torch
        F = self._F

        if img0_rgb_uint8.dtype != np.uint8:
            raise TypeError(f"img0 dtype must be uint8, got {img0_rgb_uint8.dtype}")
        if img1_rgb_uint8.dtype != np.uint8:
            raise TypeError(f"img1 dtype must be uint8, got {img1_rgb_uint8.dtype}")
        if img0_rgb_uint8.ndim != 3 or img0_rgb_uint8.shape[2] != 3:
            raise ValueError(f"img0 must have shape (H,W,3), got {img0_rgb_uint8.shape}")
        if img1_rgb_uint8.ndim != 3 or img1_rgb_uint8.shape[2] != 3:
            raise ValueError(f"img1 must have shape (H,W,3), got {img1_rgb_uint8.shape}")

        if img0_rgb_uint8.shape[:2] != img1_rgb_uint8.shape[:2]:
            raise ValueError(f"img0/img1 shape mismatch: {img0_rgb_uint8.shape} vs {img1_rgb_uint8.shape}")

        img0 = torch.from_numpy(img0_rgb_uint8.transpose(2, 0, 1)).to(self.device).float() / 255.0
        img1 = torch.from_numpy(img1_rgb_uint8.transpose(2, 0, 1)).to(self.device).float() / 255.0
        img0 = img0.unsqueeze(0)
        img1 = img1.unsqueeze(0)

        _, _, h, w = img0.shape
        ph = ((h - 1) // 32 + 1) * 32
        pw = ((w - 1) // 32 + 1) * 32
        padding = (0, pw - w, 0, ph - h)
        img0 = F.pad(img0, padding)
        img1 = F.pad(img1, padding)

        with torch.no_grad():
            sig = inspect.signature(self.model.inference)
            params = sig.parameters
            kwargs = {}
            if "scale" in params:
                kwargs["scale"] = self.scale
            if "TTA" in params:
                kwargs["TTA"] = self.tta
            if "timestep" in params:
                kwargs["timestep"] = float(timestep)
            out = self.model.inference(img0, img1, **kwargs)

        out = out[0].clamp(0.0, 1.0)
        out = (out * 255.0).byte().cpu().numpy().transpose(1, 2, 0)[:h, :w]
        return out
