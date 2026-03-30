import argparse
import csv
import math
import os
import re
from datetime import datetime

import offline_eval


def _ensure_parent_dir(file_path):
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _parse_csv_rows(csv_path, *, start_index=0, stride=1):
    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        _ = next(reader, None)
        for idx, row in enumerate(reader):
            if idx < start_index:
                continue
            if stride > 1 and ((idx - start_index) % stride != 0):
                continue
            if len(row) < 2:
                continue
            frame_id = row[0].strip()
            try:
                steering = float(row[1])
            except ValueError:
                continue
            yield frame_id, steering


def eval_interp_only_full_context(
    predictor,
    images_dir,
    orig_csv,
    add_csv,
    *,
    start_index=0,
    stride=1,
    max_frames=None,
    save_pred_csv=None,
):
    orig_ids = set()
    for frame_id, _ in _parse_csv_rows(orig_csv, start_index=0, stride=1):
        orig_ids.add(frame_id)

    mse = 0.0
    used = 0
    total = 0
    missing_images = 0
    inserted_idx = 0

    pred_writer = None
    pred_f = None
    try:
        if save_pred_csv is not None:
            _ensure_parent_dir(save_pred_csv)
            pred_f = open(save_pred_csv, "w", newline="")
            pred_writer = csv.writer(pred_f)
            pred_writer.writerow(["frame_id", "gt", "pred", "error"]) 

        for frame_id, gt in _parse_csv_rows(add_csv, start_index=0, stride=1):
            is_inserted = frame_id not in orig_ids
            selected = False
            if is_inserted:
                if inserted_idx >= start_index and (stride <= 1 or ((inserted_idx - start_index) % stride == 0)):
                    selected = True
                inserted_idx += 1

            img_path = os.path.join(images_dir, f"{frame_id}.jpg")
            if not os.path.exists(img_path):
                if selected:
                    total += 1
                    missing_images += 1
                continue

            img = offline_eval._read_image_rgb_uint8(img_path)
            pred = float(predictor.predict(img))

            if not selected:
                continue

            total += 1
            err = gt - pred
            mse += float(err * err)
            used += 1

            if pred_writer is not None:
                pred_writer.writerow([frame_id, gt, pred, err])

            if max_frames is not None and used >= max_frames:
                break

        if used == 0:
            return {
                "rmse": None,
                "mse": None,
                "used": used,
                "total": total,
                "missing_images": missing_images,
            }

        return {
            "rmse": math.sqrt(mse / used),
            "mse": mse / used,
            "used": used,
            "total": total,
            "missing_images": missing_images,
        }
    finally:
        if pred_f is not None:
            pred_f.close()


def _parse_interp_only_rows(orig_csv_path, add_csv_path, *, start_index=0, stride=1):
    orig_ids = set()
    for frame_id, _ in _parse_csv_rows(orig_csv_path, start_index=0, stride=1):
        orig_ids.add(frame_id)

    tmp = []
    for frame_id, steering in _parse_csv_rows(add_csv_path, start_index=0, stride=1):
        if frame_id not in orig_ids:
            tmp.append((frame_id, steering))

    for idx, (frame_id, steering) in enumerate(tmp):
        if idx < start_index:
            continue
        if stride > 1 and ((idx - start_index) % stride != 0):
            continue
        yield frame_id, steering


def eval_one(
    predictor,
    images_dir,
    steering_csv,
    *,
    rows_iter=None,
    start_index=0,
    stride=1,
    max_frames=None,
    save_pred_csv=None,
):
    mse = 0.0
    used = 0
    total = 0
    missing_images = 0

    pred_writer = None
    pred_f = None
    try:
        if save_pred_csv is not None:
            _ensure_parent_dir(save_pred_csv)
            pred_f = open(save_pred_csv, "w", newline="")
            pred_writer = csv.writer(pred_f)
            pred_writer.writerow(["frame_id", "gt", "pred", "error"]) 

        if rows_iter is None:
            rows_iter = _parse_csv_rows(steering_csv, start_index=start_index, stride=stride)

        for frame_id, gt in rows_iter:
            total += 1
            img_path = os.path.join(images_dir, f"{frame_id}.jpg")
            if not os.path.exists(img_path):
                missing_images += 1
                continue

            img = offline_eval._read_image_rgb_uint8(img_path)
            pred = float(predictor.predict(img))
            err = gt - pred
            mse += float(err * err)
            used += 1

            if pred_writer is not None:
                pred_writer.writerow([frame_id, gt, pred, err])

            if max_frames is not None and used >= max_frames:
                break

        if used == 0:
            return {
                "rmse": None,
                "mse": None,
                "used": used,
                "total": total,
                "missing_images": missing_images,
            }

        return {
            "rmse": math.sqrt(mse / used),
            "mse": mse / used,
            "used": used,
            "total": total,
            "missing_images": missing_images,
        }
    finally:
        if pred_f is not None:
            pred_f.close()


def discover_segments(input_root, *, segments_filter=None):
    segs = []
    pat = re.compile(r"^HMB_(\d+)$")
    for name in sorted(os.listdir(input_root)):
        m = pat.match(name)
        if not m:
            continue
        seg_id = int(m.group(1))
        if segments_filter is not None and seg_id not in segments_filter:
            continue
        segs.append(seg_id)
    return segs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-root",
        default="/data/ch2/input",
        help="CH2 input directory that contains HMB_n, HMB_n_old and CSVs",
    )
    parser.add_argument(
        "--weights-root",
        default="/repo/self-driving-car/steering-models/community-models",
        help="community-models directory containing model weights",
    )
    parser.add_argument("--models", default="rambo,chauffeur,komanda,autumn")
    parser.add_argument("--segments", default="auto", help="auto or comma-separated list like 1,2,3")

    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--max-frames", type=int, default=None)

    parser.add_argument(
        "--out-dir",
        type=str,
        default="/out",
        help="Output directory inside container (recommend mounting host dir to /out)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run identifier used in output filenames. Defaults to timestamp.",
    )

    parser.add_argument(
        "--save-preds-dir",
        type=str,
        default=None,
        help="If set, write per-frame predictions CSVs under this directory",
    )
    parser.add_argument(
        "--no-save-preds",
        action="store_true",
        help="Disable writing per-frame prediction CSVs (default is enabled).",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default=None,
        help="If set, write summary CSV to this path",
    )

    parser.add_argument(
        "--interp-only-context",
        choices=["only", "full", "both"],
        default="both",
        help="For inserted-only evaluation: 'only' streams inserted frames only; 'full' streams full add.csv sequence but evaluates errors on inserted frames only; 'both' computes both variants.",
    )

    parser.add_argument(
        "--modes",
        default="auto",
        help="Evaluation modes to run. 'auto' (default) runs orig+interp and inserted-only variants per --interp-only-context. Or pass comma-separated subset of: orig,interp,interp_only,interp_only_full",
    )

    args = parser.parse_args()

    if args.run_id is None:
        args.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.output_csv is None:
        args.output_csv = os.path.join(args.out_dir, f"summary_{args.run_id}.csv")

    if args.save_preds_dir is None and not args.no_save_preds:
        args.save_preds_dir = os.path.join(args.out_dir, f"preds_{args.run_id}")

    models = [m.strip() for m in args.models.split(",") if m.strip()]

    if args.segments == "auto":
        segs = discover_segments(args.input_root)
    else:
        segs = [int(x) for x in args.segments.split(",") if x.strip()]

    predictors = {}
    if "rambo" in models:
        base = os.path.join(args.weights_root, "rambo", "weights")
        predictors["rambo"] = offline_eval.RamboPredictor(
            os.path.join(base, "final_model.hdf5"),
            os.path.join(base, "X_train_mean.npy"),
        )
    if "chauffeur" in models:
        base = os.path.join(args.weights_root, "chauffeur", "weights")
        predictors["chauffeur"] = offline_eval.ChauffeurPredictor(
            os.path.join(base, "cnn.json"),
            os.path.join(base, "cnn.weights"),
            os.path.join(base, "lstm.json"),
            os.path.join(base, "lstm.weights"),
        )
    if "komanda" in models:
        base = os.path.join(args.weights_root, "komanda", "weights")
        predictors["komanda"] = offline_eval.KomandaPredictor(
            os.path.join(base, "komanda.test-subgraph.meta"),
            base,
        )

    if "autumn" in models:
        base = os.path.join(args.weights_root, "autumn")
        weights_dir = os.path.join(base, "weights")
        if os.path.isdir(weights_dir):
            base = weights_dir

        meta_path = os.path.join(base, "autumn-cnn-model-tf.meta")
        ckpt_path = os.path.join(base, "autumn-cnn-weights.ckpt")
        predictors["autumn"] = offline_eval.AutumnPredictor(meta_path, ckpt_path)

    selected = None
    if args.modes is not None and str(args.modes).strip().lower() != "auto":
        selected = {m.strip() for m in str(args.modes).split(",") if m.strip()}

    modes = []
    if selected is None or "orig" in selected:
        modes.append(("orig", "{seg}_old", "{seg}_steering.csv"))
    if selected is None or "interp" in selected:
        modes.append(("interp", "{seg}", "{seg}_steering_add.csv"))
    if selected is None:
        if args.interp_only_context in ("only", "both"):
            modes.append(("interp_only", "{seg}", "{seg}_steering_add2.csv"))
        if args.interp_only_context in ("full", "both"):
            modes.append(("interp_only_full", "{seg}", "{seg}_steering_add.csv"))
    else:
        if "interp_only" in selected:
            modes.append(("interp_only", "{seg}", "{seg}_steering_add2.csv"))
        if "interp_only_full" in selected:
            modes.append(("interp_only_full", "{seg}", "{seg}_steering_add.csv"))

    rows = []
    global_stats = {}

    for seg in segs:
        seg_name = f"HMB_{seg}"
        for mode_name, img_tpl, csv_tpl in modes:
            images_dir = os.path.join(args.input_root, img_tpl.format(seg=seg_name))
            steering_csv = os.path.join(args.input_root, csv_tpl.format(seg=seg_name))

            if not os.path.exists(images_dir):
                continue

            rows_iter = None
            orig_csv = os.path.join(args.input_root, f"{seg_name}_steering.csv")
            add_csv = os.path.join(args.input_root, f"{seg_name}_steering_add.csv")

            if mode_name == "interp_only":
                if not os.path.exists(steering_csv):
                    if os.path.exists(orig_csv) and os.path.exists(add_csv):
                        rows_iter = _parse_interp_only_rows(
                            orig_csv,
                            add_csv,
                            start_index=args.start_index,
                            stride=args.stride,
                        )
                        steering_csv = "(generated: add - orig)"
                    else:
                        continue
            elif mode_name == "interp_only_full":
                if not (os.path.exists(orig_csv) and os.path.exists(add_csv)):
                    continue
            elif not os.path.exists(steering_csv):
                continue

            for model_name in models:
                predictor = predictors.get(model_name)
                if predictor is None:
                    continue

                if hasattr(predictor, "reset"):
                    predictor.reset()

                save_pred_csv = None
                if args.save_preds_dir is not None:
                    save_pred_csv = os.path.join(
                        args.save_preds_dir,
                        f"{model_name}__{seg_name}__{mode_name}.csv",
                    )

                if mode_name == "interp_only_full":
                    stats = eval_interp_only_full_context(
                        predictor,
                        images_dir,
                        orig_csv,
                        add_csv,
                        start_index=args.start_index,
                        stride=args.stride,
                        max_frames=args.max_frames,
                        save_pred_csv=save_pred_csv,
                    )
                else:
                    stats = eval_one(
                        predictor,
                        images_dir,
                        steering_csv,
                        rows_iter=rows_iter,
                        start_index=args.start_index,
                        stride=args.stride,
                        max_frames=args.max_frames,
                        save_pred_csv=save_pred_csv,
                    )

                if mode_name == "interp_only":
                    row_ctx = "only"
                elif mode_name == "interp_only_full":
                    row_ctx = "full"
                else:
                    row_ctx = "na"

                rows.append(
                    {
                        "run_id": args.run_id,
                        "interp_only_context": row_ctx,
                        "stride": args.stride,
                        "start_index": args.start_index,
                        "max_frames": args.max_frames,
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "model": model_name,
                        "segment": seg_name,
                        "mode": mode_name,
                        "images_dir": images_dir,
                        "steering_csv": steering_csv,
                        **stats,
                    }
                )

                key = (model_name, mode_name)
                gs = global_stats.setdefault(key, {"sse": 0.0, "n": 0})
                if stats["rmse"] is not None:
                    gs["sse"] += (stats["mse"] * stats["used"]) if stats["mse"] is not None else 0.0
                    gs["n"] += stats["used"]

    for (model_name, mode_name), gs in sorted(global_stats.items()):
        if gs["n"] == 0:
            continue
        rmse = math.sqrt(gs["sse"] / gs["n"])
        if mode_name == "interp_only":
            row_ctx = "only"
        elif mode_name == "interp_only_full":
            row_ctx = "full"
        else:
            row_ctx = "na"

        rows.append(
            {
                "run_id": args.run_id,
                "interp_only_context": row_ctx,
                "stride": args.stride,
                "start_index": args.start_index,
                "max_frames": args.max_frames,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "model": model_name,
                "segment": "ALL",
                "mode": mode_name,
                "images_dir": "",
                "steering_csv": "",
                "rmse": rmse,
                "mse": gs["sse"] / gs["n"],
                "used": gs["n"],
                "total": "",
                "missing_images": "",
            }
        )

    _ensure_parent_dir(args.output_csv)
    with open(args.output_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_id",
                "timestamp",
                "interp_only_context",
                "stride",
                "start_index",
                "max_frames",
                "model",
                "segment",
                "mode",
                "images_dir",
                "steering_csv",
                "rmse",
                "mse",
                "used",
                "total",
                "missing_images",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"summary_csv={args.output_csv}")

    for r in rows:
        if r["segment"] == "ALL":
            print(f"[ALL] model={r['model']} mode={r['mode']} rmse={r['rmse']} n={r['used']}")


if __name__ == "__main__":
    main()
