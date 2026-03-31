import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
DEFAULT_KITTI_ROOT = os.path.join(PROJECT_ROOT, "data", "kitti")
DEFAULT_PROCESS_METHOD_ROOT = os.path.join(PROJECT_ROOT, "third_party", "process_methods")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _iter_image_files(root: str):
    p = Path(root)
    exts = ["*.png", "*.PNG", "*.jpg", "*.JPG", "*.jpeg", "*.JPEG"]
    out = []
    for pat in exts:
        out.extend(p.glob(pat))
    out = sorted(out, key=lambda x: x.name)
    return out


def _read_rgb_uint8(path: str):
    import cv2

    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(path)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def _write_rgb_uint8(path: str, rgb_uint8):
    import cv2

    bgr = cv2.cvtColor(rgb_uint8, cv2.COLOR_RGB2BGR)
    ok = cv2.imwrite(path, bgr)
    if not ok:
        raise RuntimeError(f"Failed to write: {path}")


def _build_processors(args):
    process_method_root = os.path.abspath(args.process_method_root)
    if process_method_root not in sys.path:
        sys.path.insert(0, process_method_root)

    sr = None
    dn = None
    fi = None

    if args.enable_sr:
        try:
            from SRGAN.srgan_wrapper import SRGANProcessor
        except ModuleNotFoundError as e:
            if getattr(e, "name", None) == "torchvision":
                raise ModuleNotFoundError(
                    "Missing dependency 'torchvision' required by SRGAN. "
                    "Install a torchvision build that matches your torch version, e.g. `pip install torchvision`, "
                    "then re-run."
                ) from e
            raise

        sr = SRGANProcessor(
            model_path=args.srgan_model_path,
            device=args.srgan_device,
            half_precision=args.srgan_half,
            output_scale=args.srgan_output_scale,
        )

    if args.enable_dn:
        from SwinIR.swinir_wrapper import SwinIRProcessor

        dn = SwinIRProcessor(
            model_path=args.swinir_model_path,
            task=args.swinir_task,
            upscale=args.swinir_upscale,
            device=args.swinir_device,
            half_precision=args.swinir_half,
            noise=args.swinir_noise,
            jpeg=args.swinir_jpeg,
            tile=args.swinir_tile,
            tile_overlap=args.swinir_tile_overlap,
        )

    if args.enable_fi:
        from RIFE.rife_wrapper import RIFEProcessor

        fi = RIFEProcessor(
            model_dir=args.rife_model_dir,
            device=args.rife_device,
            scale=args.rife_scale,
            tta=args.rife_tta,
        )

    return sr, dn, fi


def _apply_ops(img, ops, fid: str):
    out = img
    for op in ops:
        if hasattr(op, "process_with_id"):
            out = op.process_with_id(out, fid)
        else:
            out = op.process(out)
    return out


def _parse_pipeline(pipeline: str):
    tokens = [t.strip() for t in pipeline.split("->") if t.strip()]
    for t in tokens:
        if t not in ("DN", "SR", "FI"):
            raise ValueError(f"Invalid token in pipeline: {t}")
    if len(tokens) != 3 or len(set(tokens)) != 3:
        raise ValueError(f"Pipeline must be a permutation of DN,SR,FI, got: {pipeline}")
    return tokens


def _generate_pipeline(*, pipeline: str, left_root: str, right_root: str, out_root: str, sr, dn, fi, force: bool):
    tokens = _parse_pipeline(pipeline)
    if "FI" not in tokens:
        raise RuntimeError("This generator expects FI to be present in all pipelines.")

    left_files = _iter_image_files(left_root)
    right_files = _iter_image_files(right_root)

    left_map = {p.name: str(p) for p in left_files}
    right_map = {p.name: str(p) for p in right_files}
    names = sorted(set(left_map.keys()) & set(right_map.keys()))
    if not names:
        raise RuntimeError(f"No overlapping image files between {left_root} and {right_root}")

    out_dir = os.path.join(out_root, pipeline, "training", "image_2")
    _ensure_dir(out_dir)

    expected = len(names)
    existing = 0
    for name in names:
        if os.path.exists(os.path.join(out_dir, name)):
            existing += 1
    if not force and expected > 0 and existing == expected:
        return

    # Split ops relative to FI.
    fi_idx = tokens.index("FI")
    pre = tokens[:fi_idx]
    post = tokens[fi_idx + 1 :]

    def token_to_op(t):
        if t == "DN":
            if dn is None:
                raise RuntimeError("DN requested but dn processor is None")
            return dn
        if t == "SR":
            if sr is None:
                raise RuntimeError("SR requested but sr processor is None")
            return sr
        raise RuntimeError(f"Unexpected token: {t}")

    pre_ops = [token_to_op(t) for t in pre]
    post_ops = [token_to_op(t) for t in post]

    for name in names:
        out_path = os.path.join(out_dir, name)
        if not force and os.path.exists(out_path):
            continue

        left = _read_rgb_uint8(left_map[name])
        right = _read_rgb_uint8(right_map[name])

        left = _apply_ops(left, pre_ops, name)
        right = _apply_ops(right, pre_ops, name)

        if fi is None:
            raise RuntimeError("FI requested but fi processor is None")
        mid = fi.interpolate(left, right, timestep=0.5)

        mid = _apply_ops(mid, post_ops, name)
        _write_rgb_uint8(out_path, mid)


def _print_torch_device_info():
    try:
        import torch
    except Exception:
        return
    if not torch.cuda.is_available():
        return
    try:
        idx = torch.cuda.current_device()
        name = torch.cuda.get_device_name(idx)
        count = torch.cuda.device_count()
        print(f"[gen_kitti_combo_dataset] torch.cuda is available: device_count={count}, current_device=cuda:{idx} ({name})")
    except Exception:
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pipelines",
        default="all",
        help="Comma-separated list of pipelines or 'all'. Supported: permutations of DN->SR->FI.",
    )
    parser.add_argument(
        "--kitti-root",
        default=DEFAULT_KITTI_ROOT,
        help="KITTI root containing object_*/training/image_2",
    )
    parser.add_argument(
        "--fi-left-object",
        type=int,
        default=0,
        help="Left input object id for FI (default: object_0)",
    )
    parser.add_argument(
        "--fi-right-object",
        type=int,
        default=2,
        help="Right input object id for FI (default: object_2)",
    )
    parser.add_argument(
        "--output-root",
        default=os.path.join(DEFAULT_KITTI_ROOT, "combo"),
        help="Output root: <output-root>/<pipeline>/training/image_2",
    )
    parser.add_argument("--force", action="store_true")

    parser.add_argument(
        "--process-method-root",
        default=DEFAULT_PROCESS_METHOD_ROOT,
    )

    # SRGAN
    parser.add_argument(
        "--srgan-model-path",
        default=os.path.join(DEFAULT_PROCESS_METHOD_ROOT, "SRGAN", "results", "checkpoint_srgan.pth"),
    )
    parser.add_argument("--srgan-device", default="cuda")
    parser.add_argument("--srgan-half", action="store_true")
    parser.add_argument("--srgan-output-scale", type=int, default=2)

    # SwinIR (DN)
    parser.add_argument(
        "--swinir-model-path",
        default=os.path.join(
            PROJECT_ROOT,
            "third_party",
            "process_methods",
            "SwinIR",
            "model_zoo",
            "swinir",
            "005_colorDN_DFWB_s128w8_SwinIR-M_noise15.pth",
        ),
    )
    parser.add_argument("--swinir-task", default="color_dn")
    parser.add_argument("--swinir-upscale", type=int, default=1)
    parser.add_argument("--swinir-device", default="cuda")
    parser.add_argument("--swinir-half", action="store_true")
    parser.add_argument("--swinir-noise", type=int, default=15)
    parser.add_argument("--swinir-jpeg", type=int, default=40)
    parser.add_argument("--swinir-tile", default=None)
    parser.add_argument("--swinir-tile-overlap", type=int, default=32)

    # RIFE (FI)
    parser.add_argument(
        "--rife-model-dir",
        default=os.path.join(DEFAULT_PROCESS_METHOD_ROOT, "ECCV2022-RIFE", "train_log"),
    )
    parser.add_argument("--rife-device", default="auto")
    parser.add_argument("--rife-scale", type=float, default=1.0)
    parser.add_argument("--rife-tta", action="store_true")

    args = parser.parse_args()

    all_pipelines = [
        "DN->SR->FI",
        "DN->FI->SR",
        "SR->DN->FI",
        "SR->FI->DN",
        "FI->DN->SR",
        "FI->SR->DN",
    ]

    if args.pipelines == "all":
        pipelines = list(all_pipelines)
    else:
        pipelines = [p.strip() for p in args.pipelines.split(",") if p.strip()]

    # Determine which processors we need based on requested pipelines.
    tokens_needed = set()
    for p in pipelines:
        tokens_needed.update(_parse_pipeline(p))

    args.enable_sr = "SR" in tokens_needed
    args.enable_dn = "DN" in tokens_needed
    args.enable_fi = "FI" in tokens_needed

    left_root = os.path.join(args.kitti_root, f"object_{args.fi_left_object}", "training", "image_2")
    right_root = os.path.join(args.kitti_root, f"object_{args.fi_right_object}", "training", "image_2")
    if not os.path.isdir(left_root):
        raise FileNotFoundError(left_root)
    if not os.path.isdir(right_root):
        raise FileNotFoundError(right_root)

    sr, dn, fi = _build_processors(args)
    _print_torch_device_info()

    # Generate
    for pipeline in pipelines:
        _generate_pipeline(
            pipeline=pipeline,
            left_root=left_root,
            right_root=right_root,
            out_root=os.path.abspath(args.output_root),
            sr=sr,
            dn=dn,
            fi=fi,
            force=args.force,
        )

    # Write a manifest for reproducibility.
    manifest = {
        "pipelines": pipelines,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "kitti_root": os.path.abspath(args.kitti_root),
        "fi_left_object": args.fi_left_object,
        "fi_right_object": args.fi_right_object,
        "output_root": os.path.abspath(args.output_root),
        "srgan": {
            "enabled": bool(args.enable_sr),
            "model_path": args.srgan_model_path,
            "device": args.srgan_device,
            "half": bool(args.srgan_half),
            "output_scale": args.srgan_output_scale,
        },
        "swinir": {
            "enabled": bool(args.enable_dn),
            "model_path": args.swinir_model_path,
            "task": args.swinir_task,
            "upscale": args.swinir_upscale,
            "device": args.swinir_device,
            "half": bool(args.swinir_half),
            "noise": args.swinir_noise,
            "jpeg": args.swinir_jpeg,
            "tile": args.swinir_tile,
            "tile_overlap": args.swinir_tile_overlap,
        },
        "rife": {
            "enabled": bool(args.enable_fi),
            "model_dir": args.rife_model_dir,
            "device": args.rife_device,
            "scale": args.rife_scale,
            "tta": bool(args.rife_tta),
        },
    }

    _ensure_dir(os.path.abspath(args.output_root))
    with open(os.path.join(os.path.abspath(args.output_root), "manifest_kitti_combo.json"), "w") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    main()
