import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

import lpips
import piq
from pyiqa import create_metric


# 备注：
# - 这是一个独立的 GPU 加速版质量评测脚本，不会影响原来的 run_kitti_eval.py / ssim_lpips.py / niqe_brisque_main.py。
# - 加速点：NIQE/BRISQUE/LPIPS 在 GPU 上批量推理；PSNR/SSIM 仍使用 skimage（CPU）。
# - FI（插帧）相关数据集使用双端点 reference：分别与 gt_dir 和 gt_dir2 计算，再取平均。


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
DEFAULT_KITTI_ROOT = os.path.join(PROJECT_ROOT, "data", "kitti")
DEFAULT_OUT_ROOT = os.path.join(PROJECT_ROOT, "results", "raw", "rq1", "kitti_eval_gpu")

PIPELINES = [
    "DN->SR->FI",
    "DN->FI->SR",
    "SR->DN->FI",
    "SR->FI->DN",
    "FI->DN->SR",
    "FI->SR->DN",
]


@dataclass
class DatasetItem:
    dataset_id: str
    image_dir: str
    kind: str


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def _list_images(d: str) -> List[str]:
    return sorted([f for f in os.listdir(d) if f.lower().endswith((".png", ".jpg", ".jpeg"))])


def _common_image_files(dirs: List[str]) -> List[str]:
    commons: Optional[set] = None
    for d in dirs:
        if not d:
            continue
        if not os.path.isdir(d):
            return []
        s = set(_list_images(d))
        commons = s if commons is None else (commons & s)
        if commons is not None and len(commons) == 0:
            return []
    return sorted(list(commons)) if commons is not None else []


def _first_image(d: str) -> Optional[str]:
    try:
        for f in _list_images(d):
            return os.path.join(d, f)
    except Exception:
        return None
    return None


def _image_size(p: Optional[str]) -> Optional[Tuple[int, int]]:
    if not p:
        return None
    try:
        im = Image.open(p)
        return im.size
    except Exception:
        return None


def collect_datasets(*, kitti_root: str, sources: List[str], explicit: Optional[List[str]] = None) -> List[DatasetItem]:
    items: List[DatasetItem] = []
    kroot = os.path.abspath(kitti_root)

    if explicit:
        for p in explicit:
            p = os.path.abspath(p)
            if os.path.isdir(os.path.join(p, "training", "image_2")):
                dataset_id = os.path.basename(p)
                kind = "object"
                if os.path.basename(os.path.dirname(p)) == "combo" or "combo" in p:
                    dataset_id = f"combo/{os.path.basename(p)}"
                    kind = "combo_pipeline"
                items.append(DatasetItem(dataset_id=dataset_id, image_dir=os.path.join(p, "training", "image_2"), kind=kind))
        uniq: Dict[str, DatasetItem] = {}
        for it in items:
            uniq[it.dataset_id] = it
        return [uniq[k] for k in sorted(uniq.keys())]

    if "combo" in sources:
        combo_root = os.path.join(kroot, "combo")
        for pipeline in PIPELINES:
            img_dir = os.path.join(combo_root, pipeline, "training", "image_2")
            if os.path.isdir(img_dir):
                items.append(DatasetItem(dataset_id=f"combo/{pipeline}", image_dir=img_dir, kind="combo_pipeline"))

    if "objects" in sources:
        for d in sorted(os.listdir(kroot)):
            if not d.startswith("object_"):
                continue
            img_dir = os.path.join(kroot, d, "training", "image_2")
            if os.path.isdir(img_dir):
                items.append(DatasetItem(dataset_id=d, image_dir=img_dir, kind="object"))

    uniq: Dict[str, DatasetItem] = {}
    for it in items:
        uniq[it.dataset_id] = it
    return [uniq[k] for k in sorted(uniq.keys())]


def _infer_gt_dir_for_psnr(*, enh_dir: str, gt0_dir: str, gt3_dir: str) -> Tuple[str, Dict[str, object]]:
    meta: Dict[str, object] = {}

    enh_img = _first_image(enh_dir)
    gt0_img = _first_image(gt0_dir)
    gt3_img = _first_image(gt3_dir)

    meta["enh_sample"] = enh_img
    meta["gt0_sample"] = gt0_img
    meta["gt3_sample"] = gt3_img

    if not enh_img or not gt0_img:
        return gt0_dir, meta

    enh_size = _image_size(enh_img)
    gt0_size = _image_size(gt0_img) if gt0_img else None
    gt3_size = _image_size(gt3_img) if gt3_img else None

    meta["enh_size"] = enh_size
    meta["gt0_size"] = gt0_size
    meta["gt3_size"] = gt3_size

    if enh_size and gt3_size and enh_size == gt3_size:
        return gt3_dir, meta
    return gt0_dir, meta


def _to_tensor_01(paths: List[str], *, device: str) -> torch.Tensor:
    imgs: List[torch.Tensor] = []
    for p in paths:
        arr = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32) / 255.0
        t = torch.from_numpy(arr).permute(2, 0, 1)  # C,H,W
        imgs.append(t)
    x = torch.stack(imgs, dim=0).to(device=device)
    return x


def _to_tensor_m11(paths: List[str], *, device: str) -> torch.Tensor:
    x01 = _to_tensor_01(paths, device=device)
    return x01 * 2.0 - 1.0


def _psnr_ssim_one(gt_p: str, out_p: str) -> Tuple[float, float]:
    gt = np.array(Image.open(gt_p).convert("RGB"))
    out = np.array(Image.open(out_p).convert("RGB"))
    psnr = peak_signal_noise_ratio(gt, out, data_range=255)
    ssim = structural_similarity(gt, out, channel_axis=2, data_range=255)
    return float(psnr), float(ssim)


@torch.no_grad()
def _lpips_batch(loss_fn: lpips.LPIPS, gt_paths: List[str], out_paths: List[str], *, device: str) -> List[float]:
    try:
        gt = _to_tensor_m11(gt_paths, device=device)
        out = _to_tensor_m11(out_paths, device=device)
        d = loss_fn(gt, out)
        if d.ndim == 0:
            return [float(d.item())] * len(gt_paths)
        return [float(x) for x in d.view(-1).detach().cpu().numpy().tolist()]
    except RuntimeError:
        vals: List[float] = []
        for gp, op in zip(gt_paths, out_paths):
            gt1 = _to_tensor_m11([gp], device=device)
            out1 = _to_tensor_m11([op], device=device)
            d1 = loss_fn(gt1, out1)
            vals.append(float(d1.view(-1)[0].detach().cpu().item()))
        return vals


@torch.no_grad()
def _niqe_batch(metric, out_paths: List[str], *, device: str) -> List[float]:
    try:
        x = _to_tensor_01(out_paths, device=device)
        s = metric(x)
        if isinstance(s, torch.Tensor):
            s = s.view(-1)
            return [float(v) for v in s.detach().cpu().numpy().tolist()]
        return [float(s)] * len(out_paths)
    except RuntimeError:
        vals: List[float] = []
        for p in out_paths:
            x1 = _to_tensor_01([p], device=device)
            s1 = metric(x1)
            if isinstance(s1, torch.Tensor):
                vals.append(float(s1.view(-1)[0].detach().cpu().item()))
            else:
                vals.append(float(s1))
        return vals


@torch.no_grad()
def _brisque_batch(out_paths: List[str], *, device: str) -> List[float]:
    try:
        x = _to_tensor_01(out_paths, device=device)
        s = piq.brisque(x)
        if isinstance(s, torch.Tensor):
            s = s.view(-1)
            return [float(v) for v in s.detach().cpu().numpy().tolist()]
        return [float(s)] * len(out_paths)
    except RuntimeError:
        vals: List[float] = []
        for p in out_paths:
            x1 = _to_tensor_01([p], device=device)
            s1 = piq.brisque(x1)
            if isinstance(s1, torch.Tensor):
                vals.append(float(s1.view(-1)[0].detach().cpu().item()))
            else:
                vals.append(float(s1))
        return vals


def _summary_stats(vals: List[float]) -> Tuple[float, float]:
    m = float(np.mean(vals)) if vals else 0.0
    ci = float(1.96 * np.std(vals) / np.sqrt(len(vals))) if len(vals) > 1 else 0.0
    return m, ci


def _write_summary_csv(out_root: str, rows: List[Dict[str, object]]) -> None:
    csv_path = os.path.join(out_root, "summary.csv")
    keys: List[str] = []
    for row in rows:
        for k in row.keys():
            if k not in keys:
                keys.append(k)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kitti-root", default=DEFAULT_KITTI_ROOT)
    ap.add_argument(
        "--sources",
        default="combo,objects",
        help="Comma-separated. Supported: combo,objects. Use with --datasets for custom paths.",
    )
    ap.add_argument(
        "--datasets",
        default=None,
        help="Comma-separated dataset roots to evaluate. For object: <kitti_root>/object_6 ; for combo pipeline: <kitti_root>/combo/DN->SR->FI",
    )

    ap.add_argument("--run-niqe-brisque", action="store_true")
    ap.add_argument("--run-psnr-ssim-lpips", action="store_true")

    ap.add_argument("--gt0-dir", default=os.path.join(DEFAULT_KITTI_ROOT, "object_0", "training", "image_2"))
    ap.add_argument("--gt3-dir", default=os.path.join(DEFAULT_KITTI_ROOT, "object_3", "training", "image_2"))

    ap.add_argument("--fi-gt0-dir", default=os.path.join(DEFAULT_KITTI_ROOT, "object_0", "training", "image_2"))
    ap.add_argument("--fi-gt2-dir", default=os.path.join(DEFAULT_KITTI_ROOT, "object_2", "training", "image_2"))
    ap.add_argument("--fi-gt0-x2-dir", default=os.path.join(DEFAULT_KITTI_ROOT, "object_3", "training", "image_2"))
    ap.add_argument("--fi-gt2-x2-dir", default="")

    ap.add_argument("--device", default="cuda")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lpips-net", default="vgg")

    ap.add_argument("--out-root", default=DEFAULT_OUT_ROOT)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--run-tag", default="")

    args = ap.parse_args()

    if not args.run_niqe_brisque and not args.run_psnr_ssim_lpips:
        raise SystemExit("No task enabled. Use --run-niqe-brisque and/or --run-psnr-ssim-lpips")

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    explicit = [s.strip() for s in args.datasets.split(",") if s.strip()] if args.datasets else None

    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = (args.run_tag or "").strip()
    safe_tag = "".join([c if (c.isalnum() or c in "-_.") else "_" for c in tag])
    out_dir_name = run_id + ("__" + safe_tag if safe_tag else "")

    out_root = os.path.join(os.path.abspath(args.out_root), out_dir_name)
    _ensure_dir(out_root)

    items = collect_datasets(kitti_root=args.kitti_root, sources=sources, explicit=explicit)

    # meta for reproducibility
    try:
        with open(os.path.join(out_root, "run_meta.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "run_id": run_id,
                    "run_tag": tag,
                    "device": args.device,
                    "batch_size": args.batch_size,
                    "lpips_net": args.lpips_net,
                    "kitti_root": os.path.abspath(args.kitti_root),
                    "sources": sources,
                    "datasets": explicit,
                    "gt0_dir": args.gt0_dir,
                    "gt3_dir": args.gt3_dir,
                    "fi_gt0_dir": args.fi_gt0_dir,
                    "fi_gt2_dir": args.fi_gt2_dir,
                    "fi_gt0_x2_dir": args.fi_gt0_x2_dir,
                    "fi_gt2_x2_dir": args.fi_gt2_x2_dir,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
    except Exception:
        pass

    device = args.device
    if device.startswith("cuda") and not torch.cuda.is_available():
        print("[warn] cuda not available, falling back to cpu")
        device = "cpu"

    niqe_metric = create_metric("niqe", device=device) if args.run_niqe_brisque else None
    lpips_fn = lpips.LPIPS(net=args.lpips_net).to(device) if args.run_psnr_ssim_lpips else None

    summary_rows: List[Dict[str, object]] = []

    for it in items:
        ds_out_dir = os.path.join(out_root, it.dataset_id.replace("/", "__"))
        _ensure_dir(ds_out_dir)

        metrics_path = os.path.join(ds_out_dir, "metrics.json")
        if os.path.isfile(metrics_path):
            try:
                with open(metrics_path, "r", encoding="utf-8") as f:
                    record = json.load(f)
                summary_rows.append(record)
                print(f"[skip] {it.dataset_id} (metrics.json exists)")
                continue
            except Exception:
                pass

        record: Dict[str, object] = {
            "dataset_id": it.dataset_id,
            "kind": it.kind,
            "image_dir": it.image_dir,
            "run_id": run_id,
            "run_tag": tag,
            "device": device,
            "batch_size": args.batch_size,
        }

        # NIQE / BRISQUE (no-reference)
        if args.run_niqe_brisque and niqe_metric is not None:
            files = _list_images(it.image_dir)
            niqe_vals: List[float] = []
            brisque_vals: List[float] = []
            for i in range(0, len(files), args.batch_size):
                batch = files[i : i + args.batch_size]
                paths = [os.path.join(it.image_dir, f) for f in batch]
                niqe_vals.extend(_niqe_batch(niqe_metric, paths, device=device))
                brisque_vals.extend(_brisque_batch(paths, device=device))
                if (i // args.batch_size + 1) % 20 == 0:
                    print(f"[niqe/brisque] {it.dataset_id} {i+len(batch)}/{len(files)}")

            m, ci = _summary_stats(niqe_vals)
            mb, cib = _summary_stats(brisque_vals)
            record["NIQE_mean"] = m
            record["NIQE_ci95"] = ci
            record["BRISQUE_mean"] = mb
            record["BRISQUE_ci95"] = cib

        # PSNR / SSIM / LPIPS (full-reference / surrogate)
        if args.run_psnr_ssim_lpips and lpips_fn is not None:
            use_dual = False
            if it.kind == "combo_pipeline":
                use_dual = True
            elif it.kind == "object" and it.dataset_id.startswith("object_"):
                try:
                    oid = int(it.dataset_id.split("_")[-1])
                    if oid in [1, 11, 12, 8, 10]:
                        use_dual = True
                except Exception:
                    pass

            # decide GT dirs
            if use_dual:
                enh_img = _first_image(it.image_dir)
                enh_size = _image_size(enh_img) if enh_img else None
                if enh_size and enh_size[0] >= 2000:
                    if not args.fi_gt2_x2_dir:
                        raise SystemExit("--fi-gt2-x2-dir is required for 2x FI evaluation")
                    gt_dir = args.fi_gt0_x2_dir
                    gt_dir2 = args.fi_gt2_x2_dir
                else:
                    gt_dir = args.fi_gt0_dir
                    gt_dir2 = args.fi_gt2_dir
                record["gt_dir"] = gt_dir
                record["gt_dir2"] = gt_dir2
            else:
                gt_dir, gt_meta = _infer_gt_dir_for_psnr(enh_dir=it.image_dir, gt0_dir=args.gt0_dir, gt3_dir=args.gt3_dir)
                record["gt_dir"] = gt_dir
                record["gt_infer"] = gt_meta
                gt_dir2 = ""

            common_dirs = [gt_dir, it.image_dir]
            if use_dual:
                common_dirs.append(gt_dir2)
            files = _common_image_files(common_dirs)
            psnr_vals: List[float] = []
            ssim_vals: List[float] = []
            lpips_vals: List[float] = []

            # PSNR/SSIM per-image (CPU)
            for idx, f in enumerate(files):
                gt_p = os.path.join(gt_dir, f)
                en_p = os.path.join(it.image_dir, f)
                if use_dual:
                    gt2_p = os.path.join(gt_dir2, f)
                    p1, s1 = _psnr_ssim_one(gt_p, en_p)
                    p2, s2 = _psnr_ssim_one(gt2_p, en_p)
                    psnr_vals.append((p1 + p2) / 2.0)
                    ssim_vals.append((s1 + s2) / 2.0)
                else:
                    p, s = _psnr_ssim_one(gt_p, en_p)
                    psnr_vals.append(p)
                    ssim_vals.append(s)

                if (idx + 1) % 500 == 0:
                    print(f"[psnr/ssim] {it.dataset_id} {idx+1}/{len(files)}")

            # LPIPS batched (GPU)
            for i in range(0, len(files), args.batch_size):
                batch = files[i : i + args.batch_size]
                out_paths = [os.path.join(it.image_dir, f) for f in batch]
                gt_paths = [os.path.join(gt_dir, f) for f in batch]
                if use_dual:
                    gt2_paths = [os.path.join(gt_dir2, f) for f in batch]
                    d1 = _lpips_batch(lpips_fn, gt_paths, out_paths, device=device)
                    d2 = _lpips_batch(lpips_fn, gt2_paths, out_paths, device=device)
                    lpips_vals.extend([(a + b) / 2.0 for a, b in zip(d1, d2)])
                else:
                    lpips_vals.extend(_lpips_batch(lpips_fn, gt_paths, out_paths, device=device))

                if (i // args.batch_size + 1) % 20 == 0:
                    print(f"[lpips] {it.dataset_id} {i+len(batch)}/{len(files)}")

            m, ci = _summary_stats(psnr_vals)
            ms, cis = _summary_stats(ssim_vals)
            ml, cil = _summary_stats(lpips_vals)
            record["PSNR_mean"] = m
            record["PSNR_ci95"] = ci
            record["SSIM_mean"] = ms
            record["SSIM_ci95"] = cis
            record["LPIPS_mean"] = ml
            record["LPIPS_ci95"] = cil

        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        summary_rows.append(record)

    _write_summary_csv(out_root, summary_rows)
    print(out_root)


if __name__ == "__main__":
    main()
