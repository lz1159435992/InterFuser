import argparse
import csv
import json
import os
import re
import subprocess
import sys
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
DEFAULT_OUT_ROOT = os.path.join(TOOLS_DIR, "output", "kitti_eval")
DEFAULT_KITTI_OBJECT_ROOT = os.path.abspath(os.path.join(TOOLS_DIR, "..", "kitti_test", "kitti_object"))


PIPELINES = [
    "DN->SR->FI",
    "DN->FI->SR",
    "SR->DN->FI",
    "SR->FI->DN",
    "FI->DN->SR",
    "FI->SR->DN",
]


@dataclass(frozen=True)
class DatasetItem:
    dataset_id: str
    image_dir: str
    kind: str  # combo_pipeline | object


def _is_image_file(name: str) -> bool:
    n = name.lower()
    return n.endswith(".png") or n.endswith(".jpg") or n.endswith(".jpeg")


def _first_image(path: str) -> Optional[str]:
    try:
        for name in sorted(os.listdir(path)):
            if _is_image_file(name):
                return os.path.join(path, name)
    except FileNotFoundError:
        return None
    return None


def _image_size(path: str) -> Optional[Tuple[int, int]]:
    try:
        from PIL import Image

        with Image.open(path) as im:
            return im.size  # (w, h)
    except Exception:
        return None


def _first_image_path(path: str) -> Optional[str]:
    return _first_image(path)


def _read_image_size(path: str) -> Optional[Tuple[int, int]]:
    return _image_size(path)


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def _run(cmd: List[str], *, cwd: Optional[str] = None) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _run_env(
    cmd: List[str],
    *,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[int, str, str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    p = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=full_env,
    )
    return p.returncode, p.stdout, p.stderr


def _parse_metric_line(prefix: str, text: str) -> Optional[Tuple[float, float]]:
    # e.g. "PSNR 28.12±0.34"
    m = re.search(rf"{re.escape(prefix)}\s+([0-9.]+)±([0-9.]+)", text)
    if not m:
        return None
    return float(m.group(1)), float(m.group(2))


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


def collect_datasets(*, kitti_root: str, sources: List[str], explicit: Optional[List[str]] = None) -> List[DatasetItem]:
    items: List[DatasetItem] = []
    kroot = os.path.abspath(kitti_root)

    if explicit:
        for p in explicit:
            p = os.path.abspath(p)
            if os.path.isdir(p) and os.path.isdir(os.path.join(p, "training", "image_2")):
                dataset_id = os.path.basename(p)
                items.append(DatasetItem(dataset_id=dataset_id, image_dir=os.path.join(p, "training", "image_2"), kind="object"))
            elif os.path.isdir(p) and "combo" in os.path.basename(os.path.dirname(p)) and os.path.isdir(os.path.join(p, "training", "image_2")):
                dataset_id = f"combo/{os.path.basename(p)}"
                items.append(DatasetItem(dataset_id=dataset_id, image_dir=os.path.join(p, "training", "image_2"), kind="combo_pipeline"))
            elif os.path.isdir(p) and os.path.isdir(p) and os.path.basename(p) in PIPELINES and os.path.isdir(os.path.join(p, "training", "image_2")):
                dataset_id = f"combo/{os.path.basename(p)}"
                items.append(DatasetItem(dataset_id=dataset_id, image_dir=os.path.join(p, "training", "image_2"), kind="combo_pipeline"))
            else:
                raise FileNotFoundError(f"Unsupported dataset path: {p}")

        # If explicit datasets are provided, do not auto-expand sources.
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

    # de-dup
    uniq: Dict[str, DatasetItem] = {}
    for it in items:
        uniq[it.dataset_id] = it
    return [uniq[k] for k in sorted(uniq.keys())]


def eval_niqe_brisque(*, img_dir: str, python_bin: str = sys.executable) -> Dict[str, object]:
    script = os.path.join(SCRIPT_DIR, "niqe_brisque_main.py")
    cmd = [python_bin, script, "--img_dir", img_dir]
    rc, out, err = _run(cmd)
    res: Dict[str, object] = {"returncode": rc, "stdout": out, "stderr": err}

    niqe = _parse_metric_line("NIQE", out)
    brisque = _parse_metric_line("BRISQUE", out)
    if niqe:
        res["NIQE_mean"] = niqe[0]
        res["NIQE_ci95"] = niqe[1]
    if brisque:
        res["BRISQUE_mean"] = brisque[0]
        res["BRISQUE_ci95"] = brisque[1]
    return res


def _link_or_copy_dir(src: str, dst: str) -> None:
    if os.path.lexists(dst):
        if os.path.islink(dst) or os.path.isfile(dst):
            os.unlink(dst)
        else:
            # directory
            subprocess.run(["rm", "-rf", dst], check=False)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.symlink(os.path.abspath(src), dst)


def _resize_kitti_depth_dense_dir(
    *,
    src_depth_dir: str,
    dst_depth_dir: str,
    dst_size_wh: Tuple[int, int],
    max_frames: Optional[int] = None,
) -> None:
    """Resize KITTI dense depth pngs to match SR image resolution.

    DID-M3D expects 16-bit PNG depth maps where depth is stored as value*256.
    We keep the depth scale unchanged and only resize spatially.
    """

    _ensure_dir(dst_depth_dir)
    try:
        import cv2 as cv
    except Exception as e:
        raise RuntimeError("cv2 is required to resize dense depth maps") from e

    dst_w, dst_h = int(dst_size_wh[0]), int(dst_size_wh[1])
    names = [n for n in sorted(os.listdir(src_depth_dir)) if n.lower().endswith(".png")]
    if max_frames is not None and max_frames > 0:
        names = names[: int(max_frames)]

    for n in names:
        src_p = os.path.join(src_depth_dir, n)
        dst_p = os.path.join(dst_depth_dir, n)
        if os.path.isfile(dst_p):
            continue
        d = cv.imread(src_p, cv.IMREAD_UNCHANGED)
        if d is None:
            continue
        if d.shape[1] == dst_w and d.shape[0] == dst_h:
            cv.imwrite(dst_p, d)
            continue
        d2 = cv.resize(d, (dst_w, dst_h), interpolation=cv.INTER_NEAREST)
        cv.imwrite(dst_p, d2)


def _didm3d_depth_cache_key(*, src_depth_dir: str, dst_size_wh: Tuple[int, int], max_frames: Optional[int]) -> str:
    key = "|".join(
        [
            os.path.realpath(os.path.abspath(src_depth_dir)),
            str(int(dst_size_wh[0])),
            str(int(dst_size_wh[1])),
            str(int(max_frames)) if (max_frames is not None and max_frames > 0) else "all",
        ]
    )
    return hashlib.md5(key.encode("utf-8", errors="ignore")).hexdigest()  # nosec - used only for path naming


def _didm3d_get_depth_cache_dir(
    *,
    cache_root: str,
    src_depth_dir: str,
    dst_size_wh: Tuple[int, int],
    max_frames: Optional[int],
) -> str:
    h = _didm3d_depth_cache_key(src_depth_dir=src_depth_dir, dst_size_wh=dst_size_wh, max_frames=max_frames)
    w, h2 = int(dst_size_wh[0]), int(dst_size_wh[1])
    return os.path.join(os.path.abspath(cache_root), f"depth_{w}x{h2}_{h}")


def _didm3d_prepare_depth_cache(
    *,
    cache_dir: str,
    src_depth_dir: str,
    dst_size_wh: Tuple[int, int],
    max_frames: Optional[int],
) -> None:
    """Create/complete cache_dir containing resized depth_dense PNGs."""

    _ensure_dir(cache_dir)
    marker = os.path.join(cache_dir, "_COMPLETE")
    if os.path.isfile(marker):
        return

    _resize_kitti_depth_dense_dir(
        src_depth_dir=src_depth_dir,
        dst_depth_dir=cache_dir,
        dst_size_wh=dst_size_wh,
        max_frames=max_frames,
    )
    # Mark complete.
    try:
        with open(marker, "w", encoding="utf-8") as f:
            f.write("ok\n")
    except Exception:
        pass


def stage_did_m3d_dataset(
    *,
    dataset_image_dir: str,
    stage_dir: str,
    did_m3d_root: str,
    kitti_gt_root: str,
    dense_depth_src_dir: str,
    depth_cache_root: str,
    did_m3d_max_frames: Optional[int] = None,
) -> Dict[str, object]:
    """Stage DID-M3D expected data/KITTI3D with SR-aware calib and depth_dense."""

    res: Dict[str, object] = {
        "stage_dir": os.path.abspath(stage_dir),
        "did_m3d_root": os.path.abspath(did_m3d_root),
        "kitti_gt_root": os.path.abspath(kitti_gt_root),
        "dataset_image_dir": os.path.abspath(dataset_image_dir),
        "dense_depth_src_dir": os.path.abspath(dense_depth_src_dir),
        "depth_cache_root": os.path.abspath(depth_cache_root),
    }

    stage_dir = os.path.abspath(stage_dir)
    did_m3d_root = os.path.abspath(did_m3d_root)

    staged_root = os.path.join(stage_dir, "data", "KITTI3D")
    staged_train = os.path.join(staged_root, "training")
    _ensure_dir(staged_train)

    # Stage image_2
    _link_or_copy_dir(dataset_image_dir, os.path.join(staged_train, "image_2"))

    # Determine SR scale relative to GT KITTI image size
    gt_root = os.path.abspath(kitti_gt_root)
    gt_train = os.path.join(gt_root, "training")
    src_gt_img_dir = os.path.join(gt_train, "image_2")
    dst_img_dir = os.path.join(staged_train, "image_2")
    sx = 1.0
    sy = 1.0
    dst_size = None
    try:
        p_new = _first_image_path(dst_img_dir)
        p_old = _first_image_path(src_gt_img_dir)
        if p_new and p_old:
            sz_new = _read_image_size(p_new)
            sz_old = _read_image_size(p_old)
            if sz_new and sz_old and sz_old[0] > 0 and sz_old[1] > 0:
                sx = float(sz_new[0]) / float(sz_old[0])
                sy = float(sz_new[1]) / float(sz_old[1])
                dst_size = sz_new
    except Exception:
        sx = 1.0
        sy = 1.0
        dst_size = None

    res["sr_scale"] = {"sx": sx, "sy": sy}
    if dst_size:
        res["sr_image_size"] = {"w": dst_size[0], "h": dst_size[1]}

    # Stage calib (scaled if SR)
    src_calib = os.path.join(gt_train, "calib")
    if os.path.isdir(src_calib):
        dst_calib = os.path.join(staged_train, "calib")
        if abs(sx - 1.0) < 1e-6 and abs(sy - 1.0) < 1e-6:
            _link_or_copy_dir(src_calib, dst_calib)
        else:
            _write_scaled_calib_dir(src_calib_dir=src_calib, dst_calib_dir=dst_calib, sx=sx, sy=sy)

    # Stage labels
    src_label = os.path.join(gt_train, "label_2")
    if os.path.isdir(src_label):
        _link_or_copy_dir(src_label, os.path.join(staged_train, "label_2"))

    # Stage ImageSets: DID-M3D reads cfg['data_dir']/ImageSets/{split}.txt
    imagesets_dir = os.path.join(staged_root, "ImageSets")
    _ensure_dir(imagesets_dir)
    img_dir = os.path.join(staged_train, "image_2")
    ids: List[str] = []
    try:
        for fn in sorted(os.listdir(img_dir)):
            if _is_image_file(fn):
                stem = os.path.splitext(fn)[0]
                if stem.isdigit() and len(stem) == 6:
                    ids.append(stem)
        if not ids:
            # fallback: assume contiguous ids
            image_count = sum(1 for n in os.listdir(img_dir) if _is_image_file(n))
            ids = [f"{i:06d}" for i in range(image_count)]
    except Exception:
        ids = []
    if did_m3d_max_frames is not None and did_m3d_max_frames > 0:
        ids = ids[: int(did_m3d_max_frames)]
    for split_name in ["train", "val", "trainval", "test"]:
        p = os.path.join(imagesets_dir, f"{split_name}.txt")
        with open(p, "w", encoding="utf-8") as f:
            for s in ids:
                f.write(s + "\n")

    # Stage depth_dense (global cache bucketed by target size)
    if dst_size and os.path.isdir(dense_depth_src_dir):
        cache_dir = _didm3d_get_depth_cache_dir(
            cache_root=depth_cache_root,
            src_depth_dir=dense_depth_src_dir,
            dst_size_wh=dst_size,
            max_frames=did_m3d_max_frames,
        )
        _didm3d_prepare_depth_cache(
            cache_dir=cache_dir,
            src_depth_dir=dense_depth_src_dir,
            dst_size_wh=dst_size,
            max_frames=did_m3d_max_frames,
        )
        res["depth_dense_cache_dir"] = cache_dir
        _link_or_copy_dir(cache_dir, os.path.join(staged_train, "depth_dense"))

    # Make DID-M3D use staged data/KITTI3D
    _ensure_dir(os.path.join(did_m3d_root, "data"))
    _link_or_copy_dir(staged_root, os.path.join(did_m3d_root, "data", "KITTI3D"))

    return res


def _scale_kitti_P_line(vals: List[float], *, sx: float, sy: float) -> List[float]:
    # KITTI projection matrix is 3x4 flattened row-major.
    if len(vals) != 12:
        return vals
    out = list(vals)
    # Apply image scaling transform S * P, where S = [[sx,0,0],[0,sy,0],[0,0,1]]
    for j in range(4):
        out[j] *= sx
    for j in range(4, 8):
        out[j] *= sy
    return out


def _write_scaled_calib_dir(*, src_calib_dir: str, dst_calib_dir: str, sx: float, sy: float) -> None:
    if os.path.lexists(dst_calib_dir):
        subprocess.run(["rm", "-rf", dst_calib_dir], check=False)
    os.makedirs(dst_calib_dir, exist_ok=True)

    for name in sorted(os.listdir(src_calib_dir)):
        src_path = os.path.join(src_calib_dir, name)
        if not os.path.isfile(src_path):
            continue
        dst_path = os.path.join(dst_calib_dir, name)

        with open(src_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        out_lines: List[str] = []
        for ln in lines:
            parts = ln.strip().split()
            if not parts:
                out_lines.append(ln)
                continue

            key = parts[0]
            if key in {"P2:", "P3:"} and len(parts) == 13:
                try:
                    vals = [float(x) for x in parts[1:]]
                except Exception:
                    out_lines.append(ln)
                    continue
                vals2 = _scale_kitti_P_line(vals, sx=sx, sy=sy)
                out_lines.append(key + " " + " ".join(f"{v:.12e}" for v in vals2) + "\n")
            else:
                out_lines.append(ln if ln.endswith("\n") else (ln + "\n"))

        with open(dst_path, "w", encoding="utf-8") as f:
            f.writelines(out_lines)


def _kitti_native_eval(*, eval_bin: str, gt_label_dir: str, pred_dir: str, cwd: Optional[str] = None) -> Dict[str, object]:
    cmd = [eval_bin, gt_label_dir, pred_dir]
    rc, out, err = _run(cmd, cwd=cwd)
    return {"returncode": rc, "stdout": out, "stderr": err, "cmd": cmd}


def _safe_pred_dir_for_native_eval(*, pred_dir: str, work_dir: str) -> str:
    """KITTI native eval scripts/binaries may call shell commands internally.

    If the path contains special characters like '>', it can be interpreted as shell
    redirection and crash. Use a safe symlink path for eval.
    """

    if ">" not in pred_dir and ">" not in work_dir:
        return pred_dir

    # IMPORTANT: work_dir itself may contain '>' (e.g., combo__DN->SR->FI), so we must
    # create the safe path under a global directory that never contains such chars.
    safe_root = "/tmp/virconv_pred_safe"
    _ensure_dir(safe_root)

    # Stable name so reruns overwrite/update the same symlink.
    key = os.path.realpath(os.path.abspath(pred_dir)).encode("utf-8", errors="ignore")
    h = hashlib.md5(key).hexdigest()  # nosec - used only for path naming
    safe_dir = os.path.join(safe_root, f"pred_{h}")

    try:
        if os.path.islink(safe_dir):
            # Ensure it points to the current pred_dir.
            try:
                cur = os.readlink(safe_dir)
                if os.path.realpath(cur) == os.path.realpath(pred_dir):
                    return safe_dir
            except Exception:
                pass
            try:
                os.unlink(safe_dir)
            except Exception:
                return safe_dir

        if os.path.exists(safe_dir) and not os.path.islink(safe_dir):
            return safe_dir

        os.symlink(pred_dir, safe_dir)
        return safe_dir
    except Exception:
        # Fallback: if symlink is not permitted, just pass the original path.
        return pred_dir


def _virconv_find_result_pkl(*, virconv_root: str, eval_tag: str) -> Optional[str]:
    cand_roots: List[str] = []
    cand_roots.append(os.path.join(os.path.abspath(virconv_root), "output"))
    cand_roots.append(os.path.join(PROJECT_ROOT, "data", "virconv", "output"))

    seen: set[str] = set()
    out_roots: List[str] = []
    for p in cand_roots:
        rp = os.path.realpath(os.path.abspath(p))
        if rp in seen:
            continue
        seen.add(rp)
        if os.path.isdir(rp):
            out_roots.append(rp)

    matches: List[str] = []
    for out_root in out_roots:
        for root, _dirs, files in os.walk(out_root):
            if "result.pkl" in files and eval_tag in root:
                matches.append(os.path.join(root, "result.pkl"))
    if not matches:
        return None
    matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return matches[0]


def eval_virconv(
    *,
    dataset_image_dir: str,
    stage_dir: str,
    virconv_root: str,
    virconv_python: str,
    virconv_cfg_file: str,
    virconv_ckpt: str,
    virconv_gpus: str,
    virconv_launcher: str,
    virconv_nproc_per_node: int,
    virconv_eval_tag: str,
    virconv_create_infos: bool,
    virconv_max_frames: Optional[int],
    kitti_gt_root: str,
    kitti_native_eval_bin: str,
    gt_label_dir: str,
) -> Dict[str, object]:
    """Run VirConv inference on a staged KITTI folder.

    This runner stages a minimal KITTI folder under `stage_dir/data/kitti/training` by
    linking `image_2` to the evaluated dataset images, and linking other KITTI assets
    (calib/velodyne/label_2/ImageSets/...) from `kitti_gt_root`.
    """
    res: Dict[str, object] = {
        "virconv_root": virconv_root,
        "stage_dir": stage_dir,
        "eval_tag": virconv_eval_tag,
        "python": virconv_python,
    }

    virconv_root = os.path.abspath(virconv_root)
    stage_dir = os.path.abspath(stage_dir)
    staged_kitti = os.path.join(stage_dir, "data", "kitti")
    staged_train = os.path.join(staged_kitti, "training")
    _ensure_dir(staged_train)

    gt_root = os.path.abspath(kitti_gt_root)
    gt_train = os.path.join(gt_root, "training")
    # stage links
    _link_or_copy_dir(dataset_image_dir, os.path.join(staged_train, "image_2"))

    # If the evaluated images were geometrically resized (e.g., SR 2x), we must
    # scale camera intrinsics accordingly (P2/P3) or 3D evaluation will be inconsistent.
    src_gt_img_dir = os.path.join(gt_train, "image_2")
    dst_img_dir = os.path.join(staged_train, "image_2")
    sx = 1.0
    sy = 1.0
    try:
        p_new = _first_image_path(dst_img_dir)
        p_old = _first_image_path(src_gt_img_dir)
        if p_new and p_old:
            sz_new = _read_image_size(p_new)
            sz_old = _read_image_size(p_old)
            if sz_new and sz_old and sz_old[0] > 0 and sz_old[1] > 0:
                sx = float(sz_new[0]) / float(sz_old[0])
                sy = float(sz_new[1]) / float(sz_old[1])
    except Exception:
        sx = 1.0
        sy = 1.0

    for sub in ["velodyne", "label_2", "velodyne_depth", "planes"]:
        src = os.path.join(gt_train, sub)
        if os.path.isdir(src):
            _link_or_copy_dir(src, os.path.join(staged_train, sub))

    # calib: symlink if no resize, else write scaled copies.
    src_calib = os.path.join(gt_train, "calib")
    if os.path.isdir(src_calib):
        dst_calib = os.path.join(staged_train, "calib")
        if abs(sx - 1.0) < 1e-6 and abs(sy - 1.0) < 1e-6:
            _link_or_copy_dir(src_calib, dst_calib)
        else:
            _write_scaled_calib_dir(src_calib_dir=src_calib, dst_calib_dir=dst_calib, sx=sx, sy=sy)
    src_imagesets = os.path.join(gt_root, "ImageSets")
    if os.path.isdir(src_imagesets):
        _link_or_copy_dir(src_imagesets, os.path.join(staged_kitti, "ImageSets"))
    else:
        # Some KITTI copies don't include ImageSets. Generate a minimal one.
        img_dir = os.path.join(staged_train, "image_2")
        test_img_dir = os.path.join(staged_kitti, "testing", "image_2")
        image_count = 0
        test_count = 0
        try:
            image_count = sum(1 for n in os.listdir(img_dir) if _is_image_file(n))
        except Exception:
            image_count = 0
        try:
            test_count = sum(1 for n in os.listdir(test_img_dir) if _is_image_file(n))
        except Exception:
            test_count = 0

        imagesets_dir = os.path.join(staged_kitti, "ImageSets")
        _ensure_dir(imagesets_dir)

        def _write_set(name: str, count: int) -> None:
            p = os.path.join(imagesets_dir, name)
            with open(p, "w", encoding="utf-8") as f:
                for i in range(count):
                    f.write(f"{i:06d}\n")

        def _write_empty_set(name: str) -> None:
            p = os.path.join(imagesets_dir, name)
            with open(p, "w", encoding="utf-8") as f:
                f.write("")

        # For quick evaluation, we mirror train->val.
        if virconv_max_frames is not None and virconv_max_frames > 0:
            image_count = min(image_count, virconv_max_frames)
            test_count = min(test_count, virconv_max_frames)
        _write_set("train.txt", image_count)
        _write_set("val.txt", image_count)
        _write_set("trainval.txt", image_count)
        _write_set("test.txt", test_count)

        # VirConv's KittiDatasetSemi expects ImageSets/semi.txt for 'trainsemi' and
        # 'trainvalsemi' splits. For smoke tests without a dedicated semi split,
        # create an empty semi.txt to avoid failures in create_kitti_infos.
        _write_empty_set("semi.txt")

        # Optional convenience for some configs/scripts.
        _write_set("trainsemi.txt", image_count)
        _write_set("trainvalsemi.txt", image_count)

    # make VirConv use staged data/kitti
    _ensure_dir(os.path.join(virconv_root, "data"))
    _link_or_copy_dir(staged_kitti, os.path.join(virconv_root, "data", "kitti"))

    # VirConv evaluation configs typically require precomputed KITTI info pkls.
    # When running with a fresh virconv_root (e.g., parallel copies), these pkls
    # may be missing and the dataset length becomes 0, causing failures.
    info_val = os.path.join(virconv_root, "data", "kitti", "kitti_infos_val.pkl")
    info_trainsemi = os.path.join(virconv_root, "data", "kitti", "kitti_infos_trainsemi.pkl")
    need_infos = not (os.path.isfile(info_val) and os.path.isfile(info_trainsemi))
    if need_infos:
        virconv_create_infos = True

    env = {"CUDA_VISIBLE_DEVICES": virconv_gpus} if virconv_gpus else {}

    if virconv_create_infos:
        cmd_infos_1 = [
            virconv_python,
            "-m",
            "pcdet.datasets.kitti.kitti_dataset_mm",
            "create_kitti_infos",
            "tools/cfgs/dataset_configs/kitti_dataset.yaml",
        ]
        rc, out, err = _run_env(cmd_infos_1, cwd=virconv_root, env=env)
        res["create_infos_mm"] = {"returncode": rc, "stdout": out, "stderr": err, "cmd": cmd_infos_1}

        cmd_infos_2 = [
            virconv_python,
            "-m",
            "pcdet.datasets.kitti.kitti_datasetsemi",
            "create_kitti_infos",
            "tools/cfgs/dataset_configs/kitti_dataset.yaml",
        ]
        rc, out, err = _run_env(cmd_infos_2, cwd=virconv_root, env=env)
        res["create_infos_semi"] = {"returncode": rc, "stdout": out, "stderr": err, "cmd": cmd_infos_2}

    # VirConv config files often use relative _BASE_CONFIG_ paths like
    # 'cfgs/dataset_configs/kitti_dataset.yaml', which are resolved relative to
    # the current working directory. Run test from virconv_root/tools to match
    # upstream scripts.
    virconv_tools_dir = os.path.join(virconv_root, "tools")
    cfg_for_tools = virconv_cfg_file
    if not os.path.isabs(cfg_for_tools) and cfg_for_tools.startswith("tools/"):
        cfg_for_tools = cfg_for_tools[len("tools/") :]

    launcher = (virconv_launcher or "none").strip()
    if launcher not in ["none", "pytorch"]:
        raise ValueError(f"Unsupported virconv launcher: {launcher}")

    test_args = [
        "test.py",
        "--cfg_file",
        cfg_for_tools,
        "--ckpt",
        virconv_ckpt,
        "--launcher",
        launcher,
        "--save_to_file",
        "--eval_tag",
        virconv_eval_tag,
    ]

    if launcher == "pytorch":
        nproc = int(virconv_nproc_per_node) if int(virconv_nproc_per_node) > 0 else 0
        if nproc <= 0:
            gpus = [g.strip() for g in (virconv_gpus or "").split(",") if g.strip()]
            nproc = len(gpus) if gpus else 1
        cmd_test = [
            virconv_python,
            "-m",
            "torch.distributed.launch",
            "--nproc_per_node",
            str(nproc),
        ] + test_args
    else:
        cmd_test = [virconv_python] + test_args
    rc, out, err = _run_env(cmd_test, cwd=virconv_tools_dir, env=env)
    res["test"] = {"returncode": rc, "stdout": out, "stderr": err, "cmd": cmd_test}

    pkl_path = _virconv_find_result_pkl(virconv_root=virconv_root, eval_tag=virconv_eval_tag)
    res["result_pkl"] = pkl_path
    if not pkl_path or not os.path.isfile(pkl_path):
        return res

    # convert to KITTI txt predictions
    pred_root = os.path.join(stage_dir, "virconv_pred")
    pred_data_dir = os.path.join(pred_root, "data")
    _ensure_dir(pred_data_dir)
    pkl_to_dir = os.path.join(TOOLS_DIR, "v100", "tools", "py", "pkl_to_dir.py")
    cmd_conv = [sys.executable, pkl_to_dir, pkl_path, pred_data_dir]
    rc, out, err = _run(cmd_conv)
    res["pkl_to_dir"] = {"returncode": rc, "stdout": out, "stderr": err, "cmd": cmd_conv}

    # native eval
    pred_for_eval = _safe_pred_dir_for_native_eval(pred_dir=pred_root, work_dir=stage_dir)
    res["kitti_native_eval"] = _kitti_native_eval(
        eval_bin=kitti_native_eval_bin,
        gt_label_dir=gt_label_dir,
        pred_dir=pred_for_eval,
        cwd=os.path.dirname(kitti_native_eval_bin),
    )
    return res


def _parse_didm3d_ap(text: str) -> Optional[str]:
    m = re.search(r"Car AP\(Average Precision\)@0\.70, 0\.70, 0\.70:(.*)", text)
    if not m:
        return None
    return m.group(0).strip()


def _parse_didm3d_list_line(text: str, prefix: str) -> Optional[List[float]]:
    # Example:
    # bbox@0.70 [94.9, 85.5, 80.6]
    m = re.search(rf"^{re.escape(prefix)}\s*\[([^\]]+)\]", text.strip())
    if not m:
        return None
    parts = [p.strip() for p in m.group(1).split(",")]
    vals: List[float] = []
    for p in parts:
        if not p:
            continue
        vals.append(float(p))
    return vals if vals else None


def _parse_didm3d_metrics(text: str) -> Dict[str, object]:
    """Parse DID-M3D eval stdout into structured metrics.

    The repo prints an 'AP40 evaluation' block with lines such as:
      bbox@0.70 [easy, mod, hard]
      bev@0.70 [...]
      3d@0.70 [...]
      aos [...]
      bev@0.50 [...]
      3d@0.50 [...]
      bev@0.30 [...]
      3d@0.30 [...]
    """
    res: Dict[str, object] = {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return res

    # Keep a compact textual marker for debugging.
    if "AP40 evaluation" in text:
        res["has_ap40_block"] = True

    # Extract lists.
    keys = {
        "bbox@0.70": "bbox_ap70",
        "bev@0.70": "bev_ap70",
        "3d@0.70": "ap3d_70",
        "aos": "aos",
        "bev@0.50": "bev_ap50",
        "3d@0.50": "ap3d_50",
        "bev@0.30": "bev_ap30",
        "3d@0.30": "ap3d_30",
    }

    for ln in lines:
        for prefix, out_name in keys.items():
            vals = _parse_didm3d_list_line(ln, prefix)
            if vals is None:
                continue
            res[out_name] = vals

            # Also flatten easy/mod/hard.
            if len(vals) >= 1:
                res[f"{out_name}_easy"] = vals[0]
            if len(vals) >= 2:
                res[f"{out_name}_mod"] = vals[1]
            if len(vals) >= 3:
                res[f"{out_name}_hard"] = vals[2]

    return res


def eval_did_m3d(
    *,
    did_m3d_root: str,
    did_m3d_config: str,
    did_m3d_gpus: str,
) -> Dict[str, object]:
    did_m3d_root = os.path.abspath(did_m3d_root)
    env = {"CUDA_VISIBLE_DEVICES": did_m3d_gpus} if did_m3d_gpus else {}
    cmd = [sys.executable, "tools/train_val.py", "--config", did_m3d_config, "-e"]
    rc, out, err = _run_env(cmd, cwd=did_m3d_root, env=env)
    res: Dict[str, object] = {"returncode": rc, "stdout": out, "stderr": err, "cmd": cmd}
    ap_line = _parse_didm3d_ap(out + "\n" + err)
    if ap_line:
        res["car_ap_line"] = ap_line
    metrics = _parse_didm3d_metrics(out + "\n" + err)
    if metrics:
        res["metrics"] = metrics
    return res


def eval_psnr_ssim_lpips(*, gt_dir: str, enh_dir: str, python_bin: str = sys.executable) -> Dict[str, object]:
    script = os.path.join(SCRIPT_DIR, "ssim_lpips.py")
    cmd = [python_bin, script, "--gt_dir", gt_dir, "--enh_dir", enh_dir]
    rc, out, err = _run(cmd)
    res: Dict[str, object] = {"returncode": rc, "stdout": out, "stderr": err}

    psnr = _parse_metric_line("PSNR", out)
    ssim = _parse_metric_line("SSIM", out)
    lpips = _parse_metric_line("LPIPS", out)

    if psnr:
        res["PSNR_mean"] = psnr[0]
        res["PSNR_ci95"] = psnr[1]
    if ssim:
        res["SSIM_mean"] = ssim[0]
        res["SSIM_ci95"] = ssim[1]
    if lpips:
        res["LPIPS_mean"] = lpips[0]
        res["LPIPS_ci95"] = lpips[1]
    return res


def eval_psnr_ssim_lpips_dual(
    *,
    gt_dir: str,
    gt_dir2: str,
    enh_dir: str,
    python_bin: str = sys.executable,
) -> Dict[str, object]:
    script = os.path.join(SCRIPT_DIR, "ssim_lpips.py")
    cmd = [
        python_bin,
        script,
        "--gt_dir",
        gt_dir,
        "--gt_dir2",
        gt_dir2,
        "--enh_dir",
        enh_dir,
    ]
    rc, out, err = _run(cmd)
    res: Dict[str, object] = {"returncode": rc, "stdout": out, "stderr": err}

    psnr = _parse_metric_line("PSNR", out)
    ssim = _parse_metric_line("SSIM", out)
    lpips = _parse_metric_line("LPIPS", out)

    if psnr:
        res["PSNR_mean"] = psnr[0]
        res["PSNR_ci95"] = psnr[1]
    if ssim:
        res["SSIM_mean"] = ssim[0]
        res["SSIM_ci95"] = ssim[1]
    if lpips:
        res["LPIPS_mean"] = lpips[0]
        res["LPIPS_ci95"] = lpips[1]
    return res


def _flatten_summary_row(record: Dict[str, object]) -> Dict[str, object]:
    flat: Dict[str, object] = {
        "dataset_id": record.get("dataset_id", ""),
        "kind": record.get("kind", ""),
        "image_dir": record.get("image_dir", ""),
        "gt_dir": record.get("gt_dir", ""),
    }

    nb = record.get("niqe_brisque", {})
    psl = record.get("psnr_ssim_lpips", {})
    for k in ["NIQE_mean", "NIQE_ci95", "BRISQUE_mean", "BRISQUE_ci95"]:
        if isinstance(nb, dict) and k in nb:
            flat[k] = nb[k]
    for k in [
        "PSNR_mean",
        "PSNR_ci95",
        "SSIM_mean",
        "SSIM_ci95",
        "LPIPS_mean",
        "LPIPS_ci95",
    ]:
        if isinstance(psl, dict) and k in psl:
            flat[k] = psl[k]

    vc = record.get("virconv", {})
    if isinstance(vc, dict):
        kn = vc.get("kitti_native_eval", {}) if isinstance(vc.get("kitti_native_eval", {}), dict) else {}
        if isinstance(kn, dict):
            flat["virconv_kitti_eval_rc"] = kn.get("returncode", "")

    dm = record.get("did_m3d", {})
    if isinstance(dm, dict):
        if "car_ap_line" in dm:
            flat["did_m3d_car_ap_line"] = dm["car_ap_line"]
        m = dm.get("metrics", {}) if isinstance(dm.get("metrics", {}), dict) else {}
        if isinstance(m, dict):
            for k in [
                "bbox_ap70_easy",
                "bbox_ap70_mod",
                "bbox_ap70_hard",
                "bev_ap70_easy",
                "bev_ap70_mod",
                "bev_ap70_hard",
                "ap3d_70_easy",
                "ap3d_70_mod",
                "ap3d_70_hard",
            ]:
                if k in m:
                    flat[f"did_m3d_{k}"] = m[k]
    return flat


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


def backfill_virconv_out_root(
    *,
    out_root: str,
    kitti_native_eval_bin: str,
    gt_label_dir: str,
) -> None:
    out_root = os.path.abspath(out_root)
    t0 = datetime.now()
    summary_rows: List[Dict[str, object]] = []

    ds_names: List[str] = []
    try:
        ds_names = [n for n in sorted(os.listdir(out_root)) if os.path.isdir(os.path.join(out_root, n))]
    except Exception:
        ds_names = []
    total = len(ds_names)
    done = 0
    skipped = 0
    updated = 0

    print(f"[backfill] out_root={out_root}")
    print(f"[backfill] total_subdirs={total}")

    for idx, name in enumerate(ds_names, start=1):
        ds_dir = os.path.join(out_root, name)
        metrics_path = os.path.join(ds_dir, "metrics.json")
        if not os.path.isfile(metrics_path):
            skipped += 1
            print(f"[backfill] [{idx}/{total}] {name}: skip (no metrics.json)")
            continue

        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                record: Dict[str, object] = json.load(f)
        except Exception:
            skipped += 1
            print(f"[backfill] [{idx}/{total}] {name}: skip (failed to read metrics.json)")
            continue

        vc = record.get("virconv", {})
        if isinstance(vc, dict):
            kn = vc.get("kitti_native_eval")
            pkl_path = vc.get("result_pkl")
            eval_tag = vc.get("eval_tag")
            virconv_root = vc.get("virconv_root")
            stage_dir = vc.get("stage_dir")

            need_backfill = True
            if isinstance(kn, dict):
                try:
                    need_backfill = int(kn.get("returncode", 1)) != 0
                except Exception:
                    need_backfill = True
            if not need_backfill:
                skipped += 1
                print(f"[backfill] [{idx}/{total}] {name}: skip (already has kitti_native_eval)")
            elif need_backfill and isinstance(virconv_root, str) and isinstance(eval_tag, str) and isinstance(stage_dir, str):
                print(f"[backfill] [{idx}/{total}] {name}: start eval_tag={eval_tag}")
                if not isinstance(pkl_path, str) or not os.path.isfile(pkl_path):
                    pkl_path2 = _virconv_find_result_pkl(virconv_root=virconv_root, eval_tag=eval_tag)
                    if pkl_path2 and os.path.isfile(pkl_path2):
                        vc["result_pkl"] = pkl_path2
                        pkl_path = pkl_path2

                if isinstance(pkl_path, str):
                    print(f"[backfill] [{idx}/{total}] {name}: result_pkl={pkl_path}")

                if isinstance(pkl_path, str) and os.path.isfile(pkl_path):
                    pred_root = os.path.join(stage_dir, "virconv_pred")
                    pred_data_dir = os.path.join(pred_root, "data")
                    _ensure_dir(pred_data_dir)
                    pkl_to_dir = os.path.join(TOOLS_DIR, "v100", "tools", "py", "pkl_to_dir.py")
                    cmd_conv = [sys.executable, pkl_to_dir, pkl_path, pred_data_dir]
                    rc, out, err = _run(cmd_conv)
                    vc["pkl_to_dir"] = {"returncode": rc, "stdout": out, "stderr": err, "cmd": cmd_conv}
                    print(f"[backfill] [{idx}/{total}] {name}: pkl_to_dir rc={rc}")

                    pred_for_eval = _safe_pred_dir_for_native_eval(pred_dir=pred_root, work_dir=ds_dir)
                    vc["kitti_native_eval"] = _kitti_native_eval(
                        eval_bin=os.path.abspath(kitti_native_eval_bin),
                        gt_label_dir=os.path.abspath(gt_label_dir),
                        pred_dir=pred_for_eval,
                        cwd=os.path.dirname(os.path.abspath(kitti_native_eval_bin)),
                    )
                    if isinstance(vc.get("kitti_native_eval"), dict):
                        print(
                            f"[backfill] [{idx}/{total}] {name}: kitti_native_eval rc={vc['kitti_native_eval'].get('returncode', '')}"
                        )
                    record["virconv"] = vc
                    updated += 1
                else:
                    print(f"[backfill] [{idx}/{total}] {name}: FAIL (result.pkl not found)")
            else:
                skipped += 1
                print(f"[backfill] [{idx}/{total}] {name}: skip (virconv metadata incomplete)")

        done += 1
        if done % 1 == 0:
            dt = datetime.now() - t0
            print(f"[backfill] progress done={done}/{total} updated={updated} skipped={skipped} elapsed={dt}")

        try:
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        summary_rows.append(_flatten_summary_row(record))

    _write_summary_csv(out_root, summary_rows)
    dt = datetime.now() - t0
    print(f"[backfill] DONE out_root={out_root} updated={updated} skipped={skipped} elapsed={dt}")
    print(out_root)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--backfill-virconv-out-root",
        default=None,
        help="Existing run output directory to backfill VirConv pkl_to_dir + KITTI native eval into metrics.json and summary.csv.",
    )
    ap.add_argument("--kitti-root", default=os.path.join(PROJECT_ROOT, "data", "kitti"))
    ap.add_argument(
        "--quality-python",
        default=sys.executable,
        help="Python interpreter used to run image quality metric scripts (niqe/brisque/psnr/ssim/lpips).",
    )
    ap.add_argument(
        "--sources",
        default="combo,objects",
        help="Comma-separated. Supported: combo,objects. Use with --datasets for custom paths.",
    )
    ap.add_argument(
        "--datasets",
        default=None,
        help="Comma-separated dataset roots to evaluate. For object: ./data/kitti/object_6 ; for combo pipeline: ./data/kitti/combo/DN->SR->FI",
    )

    ap.add_argument("--run-niqe-brisque", action="store_true")
    ap.add_argument("--run-psnr-ssim-lpips", action="store_true")

    ap.add_argument("--run-virconv", action="store_true")
    ap.add_argument("--virconv-root", default=os.path.join(PROJECT_ROOT, "data", "virconv"))
    ap.add_argument("--virconv-python", default=sys.executable)
    ap.add_argument(
        "--virconv-cfg-file",
        default=os.path.join(TOOLS_DIR, "..", "kitti_test", "virconv_models", "VirConv-L", "default", "VirConv-L.yaml"),
    )
    ap.add_argument(
        "--virconv-ckpt",
        default=os.path.join(
            TOOLS_DIR,
            "..",
            "kitti_test",
            "virconv_models",
            "VirConv-L",
            "default",
            "ckpt",
            "checkpoint_epoch_50.pth",
        ),
    )
    ap.add_argument("--virconv-gpus", default="0")
    ap.add_argument(
        "--virconv-launcher",
        default="none",
        help="VirConv launcher mode. Supported: none, pytorch. Use pytorch to enable multi-GPU via torch.distributed.launch.",
    )
    ap.add_argument(
        "--virconv-nproc-per-node",
        type=int,
        default=0,
        help="When --virconv-launcher pytorch, number of processes per node. If 0, inferred from --virconv-gpus.",
    )
    ap.add_argument("--virconv-create-infos", action="store_true")
    ap.add_argument("--virconv-max-frames", type=int, default=0)

    ap.add_argument("--run-did-m3d", action="store_true")
    ap.add_argument("--did-m3d-root", default=os.path.join(TOOLS_DIR, "..", "kitti_test", "did_m3d"))
    ap.add_argument("--did-m3d-config", default="config/kitti.yaml")
    ap.add_argument("--did-m3d-gpus", default="0")
    ap.add_argument(
        "--did-m3d-dense-depth-src-dir",
        default="",
        help="Source depth_dense directory to resize/stage for SR evaluation. Default uses <did_m3d_root>/data/KITTI3D/training/depth_dense.",
    )
    ap.add_argument(
        "--did-m3d-max-frames",
        type=int,
        default=0,
        help="Optional limit for staging depth_dense and ImageSets in DID-M3D.",
    )
    ap.add_argument(
        "--did-m3d-depth-cache-root",
        default=os.path.join(TOOLS_DIR, "output", "_didm3d_depth_cache"),
        help="Global cache root for resized DID-M3D depth_dense, bucketed by target size.",
    )

    ap.add_argument("--kitti-native-eval-bin", default=os.path.join(TOOLS_DIR, "..", "kitti_test", "kitti_native_evaluation", "evaluate_object_3d_offline"))
    ap.add_argument("--det-gt-root", default=DEFAULT_KITTI_OBJECT_ROOT)
    ap.add_argument("--det-gt-label-dir", default="")

    ap.add_argument("--gt0-dir", default=os.path.join(PROJECT_ROOT, "data", "kitti", "object_0", "training", "image_2"))
    ap.add_argument("--gt3-dir", default=os.path.join(PROJECT_ROOT, "data", "kitti", "object_3", "training", "image_2"))

    ap.add_argument("--fi-gt0-dir", default=os.path.join(PROJECT_ROOT, "data", "kitti", "object_0", "training", "image_2"))
    ap.add_argument("--fi-gt2-dir", default=os.path.join(PROJECT_ROOT, "data", "kitti", "object_2", "training", "image_2"))
    ap.add_argument("--fi-gt0-x2-dir", default=os.path.join(PROJECT_ROOT, "data", "kitti", "object_3", "training", "image_2"))
    ap.add_argument("--fi-gt2-x2-dir", default="")

    ap.add_argument("--out-root", default=DEFAULT_OUT_ROOT)
    ap.add_argument("--run-id", default=None)
    ap.add_argument(
        "--run-tag",
        default="",
        help="Optional label added to output directory name and recorded in metrics.json/run_meta.json.",
    )

    args = ap.parse_args()

    det_gt_root = os.path.abspath(args.det_gt_root) if args.det_gt_root else os.path.abspath(os.path.join(args.kitti_root, "object"))
    det_gt_label_dir = args.det_gt_label_dir or os.path.join(det_gt_root, "training", "label_2")

    if args.backfill_virconv_out_root:
        backfill_virconv_out_root(
            out_root=args.backfill_virconv_out_root,
            kitti_native_eval_bin=os.path.abspath(args.kitti_native_eval_bin),
            gt_label_dir=os.path.abspath(det_gt_label_dir),
        )
        return

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    explicit = [s.strip() for s in args.datasets.split(",") if s.strip()] if args.datasets else None

    if not args.run_niqe_brisque and not args.run_psnr_ssim_lpips and not args.run_virconv and not args.run_did_m3d:
        raise SystemExit(
            "No task enabled. Use --run-niqe-brisque, --run-psnr-ssim-lpips, --run-virconv and/or --run-did-m3d"
        )

    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = (args.run_tag or "").strip()
    safe_tag = "".join([c if (c.isalnum() or c in "-_.") else "_" for c in tag])
    out_dir_name = run_id + ("__" + safe_tag if safe_tag else "")
    out_root = os.path.join(os.path.abspath(args.out_root), out_dir_name)
    _ensure_dir(out_root)

    items = collect_datasets(kitti_root=args.kitti_root, sources=sources, explicit=explicit)

    try:
        with open(os.path.join(out_root, "run_meta.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "run_id": run_id,
                    "run_tag": tag,
                    "quality_python": os.path.abspath(args.quality_python) if args.quality_python else "",
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

    summary_rows: List[Dict[str, object]] = []

    for it in items:
        ds_out_dir = os.path.join(out_root, it.dataset_id.replace("/", "__"))
        _ensure_dir(ds_out_dir)

        record: Dict[str, object] = {
            "dataset_id": it.dataset_id,
            "kind": it.kind,
            "image_dir": it.image_dir,
            "run_id": run_id,
            "run_tag": tag,
            "quality_python": args.quality_python,
        }

        if args.run_niqe_brisque:
            record["niqe_brisque"] = eval_niqe_brisque(img_dir=it.image_dir, python_bin=args.quality_python)

        if args.run_psnr_ssim_lpips:
            use_dual = False
            dual_gt1 = ""
            dual_gt2 = ""
            if it.kind == "combo_pipeline":
                use_dual = True
            elif it.kind == "object":
                if it.dataset_id.startswith("object_"):
                    try:
                        oid = int(it.dataset_id.split("_")[-1])
                        if oid in [1, 11, 12, 8, 10]:
                            use_dual = True
                    except Exception:
                        pass

            if use_dual:
                enh_img = _first_image(it.image_dir)
                enh_size = _image_size(enh_img) if enh_img else None
                if enh_size and enh_size[0] >= 2000:
                    if not args.fi_gt2_x2_dir:
                        raise SystemExit("--fi-gt2-x2-dir is required for 2x FI evaluation")
                    dual_gt1 = args.fi_gt0_x2_dir
                    dual_gt2 = args.fi_gt2_x2_dir
                else:
                    dual_gt1 = args.fi_gt0_dir
                    dual_gt2 = args.fi_gt2_dir

                record["gt_dir"] = dual_gt1
                record["gt_dir2"] = dual_gt2
                record["psnr_ssim_lpips"] = eval_psnr_ssim_lpips_dual(
                    gt_dir=dual_gt1,
                    gt_dir2=dual_gt2,
                    enh_dir=it.image_dir,
                    python_bin=args.quality_python,
                )
            else:
                gt_dir, gt_meta = _infer_gt_dir_for_psnr(enh_dir=it.image_dir, gt0_dir=args.gt0_dir, gt3_dir=args.gt3_dir)
                record["gt_dir"] = gt_dir
                record["gt_infer"] = gt_meta
                record["psnr_ssim_lpips"] = eval_psnr_ssim_lpips(gt_dir=gt_dir, enh_dir=it.image_dir, python_bin=args.quality_python)

        if args.run_virconv:
            if not args.virconv_ckpt:
                record["virconv"] = {"error": "--virconv-ckpt is required when --run-virconv is set"}
            else:
                record["virconv"] = eval_virconv(
                    dataset_image_dir=it.image_dir,
                    stage_dir=os.path.join(ds_out_dir, "_virconv_stage"),
                    virconv_root=args.virconv_root,
                    virconv_python=args.virconv_python,
                    virconv_cfg_file=args.virconv_cfg_file,
                    virconv_ckpt=args.virconv_ckpt,
                    virconv_gpus=args.virconv_gpus,
                    virconv_launcher=args.virconv_launcher,
                    virconv_nproc_per_node=args.virconv_nproc_per_node,
                    virconv_eval_tag=it.dataset_id.replace("/", "__") + "__" + run_id,
                    virconv_create_infos=args.virconv_create_infos,
                    virconv_max_frames=(args.virconv_max_frames if args.virconv_max_frames > 0 else None),
                    kitti_gt_root=det_gt_root,
                    kitti_native_eval_bin=os.path.abspath(args.kitti_native_eval_bin),
                    gt_label_dir=os.path.abspath(det_gt_label_dir),
                )

        if args.run_did_m3d:
            dense_src = args.did_m3d_dense_depth_src_dir
            if not dense_src:
                dense_src = os.path.join(os.path.abspath(args.did_m3d_root), "data", "KITTI3D", "training", "depth_dense")
            record["did_m3d_stage"] = stage_did_m3d_dataset(
                dataset_image_dir=it.image_dir,
                stage_dir=os.path.join(ds_out_dir, "_did_m3d_stage"),
                did_m3d_root=args.did_m3d_root,
                kitti_gt_root=det_gt_root,
                dense_depth_src_dir=dense_src,
                depth_cache_root=args.did_m3d_depth_cache_root,
                did_m3d_max_frames=(args.did_m3d_max_frames if args.did_m3d_max_frames > 0 else None),
            )
            record["did_m3d"] = eval_did_m3d(did_m3d_root=args.did_m3d_root, did_m3d_config=args.did_m3d_config, did_m3d_gpus=args.did_m3d_gpus)

        with open(os.path.join(ds_out_dir, "metrics.json"), "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        summary_rows.append(_flatten_summary_row(record))

    _write_summary_csv(out_root, summary_rows)

    print(out_root)


if __name__ == "__main__":
    main()
