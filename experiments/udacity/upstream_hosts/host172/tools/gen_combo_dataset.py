import argparse
import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime


class _GaussianNoiseProcessor:
    def __init__(self, *, sigma, seed=0):
        self.sigma = float(sigma)
        self.seed = int(seed)

    def _frame_seed(self, frame_id):
        import hashlib

        h = hashlib.md5(str(frame_id).encode("utf-8")).hexdigest()
        return (self.seed + int(h[:8], 16)) & 0xFFFFFFFF

    def process_with_id(self, img_uint8_rgb, frame_id):
        import numpy as np

        rng = np.random.default_rng(self._frame_seed(frame_id))
        noise = rng.normal(loc=0.0, scale=self.sigma, size=img_uint8_rgb.shape).astype(np.float32)
        out = img_uint8_rgb.astype(np.float32) + noise
        out = np.clip(out, 0.0, 255.0).astype(np.uint8)
        return out

    def process(self, img_uint8_rgb):
        raise RuntimeError("GaussianNoiseProcessor requires frame_id; use process_with_id")


SCRIPT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))


def _parse_frame_ids(csv_path):
    ids = []
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return ids
        for row in reader:
            if not row:
                continue
            ids.append(str(row[0]))
    return ids


def _discover_segments(input_root):
    segs = []
    pat = re.compile(r"^HMB_(\\d+)_steering\\.csv$")
    for name in sorted(os.listdir(input_root)):
        m = pat.match(name)
        if not m:
            continue
        segs.append(int(m.group(1)))
    return segs


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def _read_rgb_uint8(path):
    import cv2

    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(path)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return rgb


def _write_rgb_uint8(path, rgb_uint8):
    import cv2

    bgr = cv2.cvtColor(rgb_uint8, cv2.COLOR_RGB2BGR)
    ok = cv2.imwrite(path, bgr)
    if not ok:
        raise RuntimeError(f"Failed to write: {path}")


def _build_processors(args, tokens):
    process_method_root = os.path.abspath(args.process_method_root)
    if process_method_root not in sys.path:
        sys.path.insert(0, process_method_root)

    srgan = None
    swinir = None
    rife = None

    if "A" in tokens:
        from SRGAN.srgan_wrapper import SRGANProcessor

        srgan = SRGANProcessor(
            model_path=args.srgan_model_path,
            device=args.srgan_device,
            half_precision=args.srgan_half,
            output_scale=args.srgan_output_scale,
        )

    if "B" in tokens:
        from SwinIR.swinir_wrapper import SwinIRProcessor

        swinir = SwinIRProcessor(
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

    if "C" in tokens:
        from RIFE.rife_wrapper import RIFEProcessor

        rife = RIFEProcessor(
            model_dir=args.rife_model_dir,
            device=args.rife_device,
            scale=args.rife_scale,
            tta=args.rife_tta,
        )

    return srgan, swinir, rife


def _apply_per_frame_ops(img, per_ops):
    out = img
    for op in per_ops:
        out = op.process(out)
    return out


def _apply_per_frame_ops_with_id(img, frame_id, per_ops):
    out = img
    for op in per_ops:
        if hasattr(op, "process_with_id"):
            out = op.process_with_id(out, frame_id)
        else:
            out = op.process(out)
    return out


def _copy_labels(src_root, dst_root, seg):
    for suf in ["_steering.csv", "_steering_add.csv", "_steering_add2.csv"]:
        name = f"HMB_{seg}{suf}"
        src = os.path.join(src_root, name)
        if os.path.exists(src):
            dst = os.path.join(dst_root, name)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)


def _generate_segment_no_rife(*, seg, src_root, out_root, per_ops, force):
    seg_old_in = os.path.join(src_root, f"HMB_{seg}_old")
    steer_csv = os.path.join(src_root, f"HMB_{seg}_steering.csv")
    if not os.path.exists(seg_old_in):
        raise FileNotFoundError(seg_old_in)
    if not os.path.exists(steer_csv):
        raise FileNotFoundError(steer_csv)

    orig_ids = _parse_frame_ids(steer_csv)
    seg_old_out = os.path.join(out_root, f"HMB_{seg}_old")
    _ensure_dir(seg_old_out)

    expected = len(orig_ids)
    existing = 0
    for fid in orig_ids:
        if os.path.exists(os.path.join(seg_old_out, f"{fid}.jpg")):
            existing += 1
    if not force and expected > 0 and existing == expected:
        return

    for fid in orig_ids:
        out_path = os.path.join(seg_old_out, f"{fid}.jpg")
        if not force and os.path.exists(out_path):
            continue
        img = _read_rgb_uint8(os.path.join(seg_old_in, f"{fid}.jpg"))
        img = _apply_per_frame_ops_with_id(img, fid, per_ops)
        _write_rgb_uint8(out_path, img)


def _generate_segment_with_rife(*, seg, src_root, out_root, pre_ops, post_ops, rife, force):
    seg_old_in = os.path.join(src_root, f"HMB_{seg}_old")
    steer_csv = os.path.join(src_root, f"HMB_{seg}_steering.csv")
    add_csv = os.path.join(src_root, f"HMB_{seg}_steering_add.csv")
    add2_csv = os.path.join(src_root, f"HMB_{seg}_steering_add2.csv")

    if not os.path.exists(seg_old_in):
        raise FileNotFoundError(seg_old_in)
    if not (os.path.exists(steer_csv) and os.path.exists(add_csv) and os.path.exists(add2_csv)):
        raise FileNotFoundError(f"Missing label CSVs for seg={seg}")

    orig_ids = _parse_frame_ids(steer_csv)
    add_ids = _parse_frame_ids(add_csv)
    inserted_ids = _parse_frame_ids(add2_csv)

    if len(orig_ids) < 2:
        raise ValueError(f"Not enough frames for seg={seg}")
    if len(inserted_ids) != len(orig_ids) - 1:
        raise ValueError(f"inserted_ids len mismatch seg={seg}: {len(inserted_ids)} vs {len(orig_ids) - 1}")
    if len(add_ids) != len(orig_ids) + len(inserted_ids):
        raise ValueError(f"add_ids len mismatch seg={seg}: {len(add_ids)}")

    seg_out = os.path.join(out_root, f"HMB_{seg}")
    seg_old_out = os.path.join(out_root, f"HMB_{seg}_old")
    _ensure_dir(seg_out)
    _ensure_dir(seg_old_out)

    expected_full = len(add_ids)
    existing_full = 0
    for fid in add_ids:
        if os.path.exists(os.path.join(seg_out, f"{fid}.jpg")):
            existing_full += 1
    if not force and expected_full > 0 and existing_full == expected_full:
        return

    def apply_post(img):
        return _apply_per_frame_ops_with_id(img, "__rife_post__", post_ops)

    first_id = orig_ids[0]
    prev_pre = _read_rgb_uint8(os.path.join(seg_old_in, f"{first_id}.jpg"))
    prev_pre = _apply_per_frame_ops_with_id(prev_pre, first_id, pre_ops)
    prev_id = first_id

    for i in range(1, len(orig_ids)):
        cur_id = orig_ids[i]
        cur_pre = _read_rgb_uint8(os.path.join(seg_old_in, f"{cur_id}.jpg"))
        cur_pre = _apply_per_frame_ops_with_id(cur_pre, cur_id, pre_ops)

        ins_id = inserted_ids[i - 1]
        mid_pre = rife.interpolate(prev_pre, cur_pre, timestep=0.5)

        prev_final = apply_post(prev_pre)
        mid_final = apply_post(mid_pre)

        prev_path_full = os.path.join(seg_out, f"{prev_id}.jpg")
        prev_path_old = os.path.join(seg_old_out, f"{prev_id}.jpg")
        ins_path_full = os.path.join(seg_out, f"{ins_id}.jpg")

        if force or not os.path.exists(prev_path_full):
            _write_rgb_uint8(prev_path_full, prev_final)
        if force or not os.path.exists(prev_path_old):
            _write_rgb_uint8(prev_path_old, prev_final)
        if force or not os.path.exists(ins_path_full):
            _write_rgb_uint8(ins_path_full, mid_final)

        prev_pre = cur_pre
        prev_id = cur_id

    last_final = apply_post(prev_pre)
    last_path_full = os.path.join(seg_out, f"{prev_id}.jpg")
    last_path_old = os.path.join(seg_old_out, f"{prev_id}.jpg")
    if force or not os.path.exists(last_path_full):
        _write_rgb_uint8(last_path_full, last_final)
    if force or not os.path.exists(last_path_old):
        _write_rgb_uint8(last_path_old, last_final)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", required=True)
    parser.add_argument("--segments", default="auto")
    parser.add_argument(
        "--input-root",
        default=os.path.join(REPO_ROOT, "udacity", "self-driving-car", "datasets", "CH2", "input"),
    )
    parser.add_argument(
        "--output-root",
        default=os.path.join(REPO_ROOT, "udacity", "self-driving-car", "datasets", "CH2", "input_combo"),
    )
    parser.add_argument(
        "--process-method-root",
        default=os.path.join(REPO_ROOT, "process_mothod"),
    )
    parser.add_argument("--force", action="store_true")

    parser.add_argument("--gauss-seed", type=int, default=0)

    parser.add_argument(
        "--srgan-model-path",
        default=os.path.join(REPO_ROOT, "process_mothod", "SRGAN", "results", "checkpoint_srgan.pth"),
    )
    parser.add_argument("--srgan-device", default="cuda")
    parser.add_argument("--srgan-half", action="store_true")
    parser.add_argument("--srgan-output-scale", type=int, default=2)

    parser.add_argument(
        "--swinir-model-path",
        default=os.path.join(
            REPO_ROOT,
            "process_mothod",
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

    parser.add_argument(
        "--rife-model-dir",
        default=os.path.join(REPO_ROOT, "process_mothod", "ECCV2022-RIFE", "train_log"),
    )
    parser.add_argument("--rife-device", default="auto")
    parser.add_argument("--rife-scale", type=float, default=1.0)
    parser.add_argument("--rife-tta", action="store_true")

    args = parser.parse_args()

    tokens = [t.strip() for t in args.pipeline.split("->") if t.strip()]
    if len(tokens) == 1 and tokens[0] in ("GN8", "GN16"):
        pass
    else:
        for t in tokens:
            if t not in ("A", "B", "C"):
                raise ValueError(f"Invalid token: {t}")
        if len(set(tokens)) != len(tokens):
            raise ValueError("Duplicate tokens in pipeline")

    if args.segments == "auto":
        segs = _discover_segments(args.input_root)
    else:
        segs = [int(x) for x in args.segments.split(",") if x.strip()]

    out_root = os.path.join(os.path.abspath(args.output_root), args.pipeline)
    _ensure_dir(out_root)

    _ensure_dir(out_root)

    srgan, swinir, rife = _build_processors(args, tokens)

    ops = []
    if len(tokens) == 1 and tokens[0] in ("GN8", "GN16"):
        sigma = 8.0 if tokens[0] == "GN8" else 16.0
        ops.append(_GaussianNoiseProcessor(sigma=sigma, seed=args.gauss_seed))
    else:
        for t in tokens:
            if t == "A":
                ops.append(srgan)
            elif t == "B":
                ops.append(swinir)

    has_rife = "C" in tokens
    if has_rife:
        if not os.path.exists(args.rife_model_dir):
            raise FileNotFoundError(args.rife_model_dir)
        if not os.path.exists(os.path.join(args.rife_model_dir, "flownet.pkl")):
            raise FileNotFoundError(os.path.join(args.rife_model_dir, "flownet.pkl"))

        c_idx = tokens.index("C")
        pre_ops = []
        post_ops = []
        for idx, t in enumerate(tokens):
            if t in ("A", "B"):
                if idx < c_idx:
                    pre_ops.append(srgan if t == "A" else swinir)
                else:
                    post_ops.append(srgan if t == "A" else swinir)

        for seg in segs:
            _copy_labels(args.input_root, out_root, seg)
            _generate_segment_with_rife(
                seg=seg,
                src_root=args.input_root,
                out_root=out_root,
                pre_ops=pre_ops,
                post_ops=post_ops,
                rife=rife,
                force=args.force,
            )
    else:
        for seg in segs:
            _copy_labels(args.input_root, out_root, seg)
            _generate_segment_no_rife(
                seg=seg,
                src_root=args.input_root,
                out_root=out_root,
                per_ops=ops,
                force=args.force,
            )

    manifest = {
        "pipeline": args.pipeline,
        "segments": segs,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_root": os.path.abspath(args.input_root),
        "output_root": os.path.abspath(args.output_root),
        "gaussian_noise": {
            "enabled": len(tokens) == 1 and tokens[0] in ("GN8", "GN16"),
            "sigma": (8.0 if len(tokens) == 1 and tokens[0] == "GN8" else (16.0 if len(tokens) == 1 and tokens[0] == "GN16" else None)),
            "seed": args.gauss_seed,
        },
        "srgan": {
            "enabled": "A" in tokens,
            "model_path": args.srgan_model_path,
            "device": args.srgan_device,
            "half": bool(args.srgan_half),
            "output_scale": args.srgan_output_scale,
        },
        "swinir": {
            "enabled": "B" in tokens,
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
            "enabled": has_rife,
            "model_dir": args.rife_model_dir,
            "device": args.rife_device,
            "scale": args.rife_scale,
            "tta": bool(args.rife_tta),
        },
    }

    with open(os.path.join(out_root, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    main()
