import argparse
import csv
import os
import subprocess
import sys
from datetime import datetime


ALL_PIPELINES = [
    "GN8",
    "GN16",
    "A",
    "B",
    "C",
    "A->B",
    "B->A",
    "A->C",
    "C->A",
    "B->C",
    "C->B",
    "A->B->C",
    "A->C->B",
    "B->A->C",
    "B->C->A",
    "C->A->B",
    "C->B->A",
]


SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
DEFAULT_CH2_ROOT = os.path.join(PROJECT_ROOT, "data", "ch2")
DEFAULT_WEIGHTS_ROOT = os.path.join(PROJECT_ROOT, "data", "community-models")
DEFAULT_OUT_ROOT = os.path.join(PROJECT_ROOT, "results", "raw", "rq2", "ch2_main")


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def _read_rows(path):
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def _write_rows(path, rows, fieldnames):
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _run(cmd, *, allow_fail=False):
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        if allow_fail:
            return False
        raise


def _has_valid_summary_csv(path):
    if not os.path.exists(path):
        return False
    try:
        if os.path.getsize(path) <= 0:
            return False
    except OSError:
        return False

    try:
        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return False
            required = {"model", "segment", "mode", "rmse", "used"}
            if not required.issubset(set(reader.fieldnames)):
                return False
            for _ in reader:
                return True
            return False
    except Exception:
        return False


def _default_resume_run_id(pipeline, args):
    seg = str(args.segments).replace(",", "-")
    maxf = "all" if args.max_frames is None else str(args.max_frames)
    return f"{pipeline}_seg{seg}_stride{args.stride}_start{args.start_index}_max{maxf}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipelines", default="all")
    parser.add_argument("--segments", default="1,2,3,4,5,6")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--max-frames", type=int, default=None)

    parser.add_argument("--skip-gen", action="store_true")
    parser.add_argument("--skip-eval", action="store_true")

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip docker eval if expected output CSVs already exist and look valid.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Optional run identifier. If multiple pipelines are evaluated, pipeline name is prefixed.",
    )

    parser.add_argument(
        "--ch2-root",
        default=DEFAULT_CH2_ROOT,
    )
    parser.add_argument(
        "--weights-root",
        default=DEFAULT_WEIGHTS_ROOT,
    )
    parser.add_argument(
        "--out-root",
        default=DEFAULT_OUT_ROOT,
    )

    parser.add_argument("--docker-image", default="udacity-offline-eval:tf1")
    parser.add_argument("--docker-sudo", action="store_true")
    parser.add_argument("--save-preds", action="store_true")

    args = parser.parse_args()

    if args.pipelines == "all":
        pipelines = list(ALL_PIPELINES)
    else:
        pipelines = [p.strip() for p in args.pipelines.split(",") if p.strip()]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    gen_script = os.path.join(os.path.dirname(__file__), "gen_combo_dataset.py")

    for pipeline in pipelines:
        if not args.skip_gen:
            gen_cmd = [
                sys.executable,
                gen_script,
                "--pipeline",
                pipeline,
                "--segments",
                args.segments,
                "--input-root",
                os.path.join(os.path.abspath(args.ch2_root), "input"),
                "--output-root",
                os.path.join(os.path.abspath(args.ch2_root), "input_combo"),
            ]
            _run(gen_cmd)

        if args.skip_eval:
            continue

        pipeline_out_dir = os.path.join(os.path.abspath(args.out_root), pipeline)
        _ensure_dir(pipeline_out_dir)

        if args.run_id is not None:
            if len(pipelines) == 1:
                base_run_id = args.run_id
            else:
                base_run_id = f"{pipeline}_{args.run_id}"
        elif args.resume:
            base_run_id = _default_resume_run_id(pipeline, args)
        else:
            base_run_id = f"{pipeline}_{ts}"

        input_root_in_container = f"/data/ch2/input_combo/{pipeline}"

        has_rife = "C" in [t.strip() for t in pipeline.split("->") if t.strip()]

        def docker_cmd(models, group, output_csv, preds_dir):
            cmd = []
            if args.docker_sudo:
                cmd.append("sudo")
            cmd.extend(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{os.path.abspath(args.ch2_root)}:/data/ch2",
                    "-v",
                    f"{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docker', 'offline-eval'))}:/app",
                    "-v",
                    f"{os.path.abspath(args.weights_root)}:/models/community-models",
                    "-v",
                    f"{os.path.abspath(pipeline_out_dir)}:/out",
                    args.docker_image,
                    "/app/batch_eval.py",
                    "--input-root",
                    input_root_in_container,
                    "--weights-root",
                    "/models/community-models",
                    "--models",
                    models,
                    "--segments",
                    args.segments,
                    "--interp-only-context",
                    "both",
                    "--stride",
                    str(args.stride),
                    "--start-index",
                    str(args.start_index),
                    "--run-id",
                    base_run_id,
                    "--output-csv",
                    f"/out/{output_csv}",
                ]
            )

            if not has_rife:
                cmd.extend(["--modes", "orig"])

            if args.max_frames is not None:
                cmd.extend(["--max-frames", str(args.max_frames)])
            if args.save_preds:
                cmd.extend(["--save-preds-dir", f"/out/{preds_dir}"])
            else:
                cmd.append("--no-save-preds")
            return cmd

        main_csv = f"summary_{base_run_id}__main.csv"
        main_preds = f"preds_{base_run_id}__main"
        main_csv_host = os.path.join(pipeline_out_dir, main_csv)
        if args.resume and _has_valid_summary_csv(main_csv_host):
            main_ok = True
        else:
            main_ok = _run(
                docker_cmd(
                    "rambo,chauffeur,autumn",
                    "main",
                    main_csv,
                    main_preds,
                )
            )

        kom_csv = f"summary_{base_run_id}__komanda.csv"
        kom_preds = f"preds_{base_run_id}__komanda"
        kom_csv_host = os.path.join(pipeline_out_dir, kom_csv)
        if args.resume and _has_valid_summary_csv(kom_csv_host):
            kom_ok = True
        else:
            kom_ok = _run(
                docker_cmd(
                    "komanda",
                    "komanda",
                    kom_csv,
                    kom_preds,
                ),
                allow_fail=True,
            )

        merged = []
        fieldnames = None

        if main_ok and os.path.exists(os.path.join(pipeline_out_dir, main_csv)):
            rows, fns = _read_rows(os.path.join(pipeline_out_dir, main_csv))
            merged.extend(rows)
            fieldnames = fns

        if kom_ok and os.path.exists(os.path.join(pipeline_out_dir, kom_csv)):
            rows, fns = _read_rows(os.path.join(pipeline_out_dir, kom_csv))
            merged.extend(rows)
            if fieldnames is None:
                fieldnames = fns

        if fieldnames is not None:
            merged_csv = os.path.join(pipeline_out_dir, f"summary_{base_run_id}.csv")
            _write_rows(merged_csv, merged, fieldnames)


if __name__ == "__main__":
    main()
