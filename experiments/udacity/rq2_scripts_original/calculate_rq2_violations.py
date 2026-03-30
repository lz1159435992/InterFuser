import argparse
import pathlib
import sys


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


def _auc_average(points):
    pts = sorted(points, key=lambda x: x[0])
    if len(pts) < 2:
        return None
    x0 = pts[0][0]
    x1 = pts[-1][0]
    if x1 == x0:
        return None
    area = 0.0
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        area += 0.5 * (ya + yb) * (xb - xa)
    return area / (x1 - x0)


def _point_at(points, x_target, tol=1e-9):
    for x, y in points:
        if abs(x - x_target) <= tol:
            return y
    return None


def _resolve_module():
    root = _repo_root()
    sys.path.insert(0, str(root))
    import compute_e2e_control_metrics as m

    return m


def _run(args) -> None:
    m = _resolve_module()

    preds_dir = m._resolve_preds_dir(args.preds_dir)
    run_id = preds_dir.name
    if run_id.startswith("preds_"):
        run_id = run_id[len("preds_") :]

    out_dir = pathlib.Path(args.out_dir) if args.out_dir else (_repo_root() / "output" / "RQ2_scripts")
    out_dir.mkdir(parents=True, exist_ok=True)

    kappa_values = []
    k = float(args.kappa_start)
    while k <= float(args.kappa_end) + 1e-9:
        kappa_values.append(round(k, 10))
        k += float(args.kappa_step)

    index = {}
    for path in sorted(pathlib.Path(preds_dir).glob("*.csv")):
        parsed = m._try_parse_preds_filename(path)
        if parsed is None:
            continue
        model, segment, mode = parsed
        index.setdefault(model, {}).setdefault(segment, {})[mode] = path

    if not index:
        raise SystemExit(f"No preds CSVs found under: {preds_dir}")

    rows = []
    summary_rows = []

    pooled_all = {}
    pooled_by_model = {}

    for model in sorted(index.keys()):
        for segment in sorted(index[model].keys()):
            mode_data = {}
            for mode, path in sorted(index[model][segment].items()):
                mode_data[mode] = m._read_preds_csv(path)

            if "orig" not in mode_data or "interp" not in mode_data:
                continue

            orig_ids_sorted = sorted(mode_data["orig"]["pred_by_id"].keys())
            interp_ids_sorted = sorted(mode_data["interp"]["pred_by_id"].keys())
            orig_set = set(orig_ids_sorted)
            inserted_ids_sorted = [fid for fid in interp_ids_sorted if fid not in orig_set]
            triple_ids = m._build_triple_ids(orig_ids_sorted, inserted_ids_sorted)

            curve_specs = [("Mixed-stream", "orig", "interp")]
            if "interp_only" in mode_data:
                curve_specs.append(("Inserted-only", "orig", "interp_only"))
            curve_specs.append(("Upsampled", "interp", "interp"))

            for curve_name, end_mode, mid_mode in curve_specs:
                curve, sat_counts, n_triples = m._monotonicity_curve(
                    triple_ids,
                    mode_data[end_mode]["pred_by_id"],
                    mode_data[mid_mode]["pred_by_id"],
                    alpha=float(args.alpha),
                    kappa_values=kappa_values,
                    eps_smooth=float(args.epsilon_smooth),
                    eps_bound=float(args.epsilon_bound),
                )

                if n_triples == 0:
                    continue

                pts = [(kv, cr) for kv, cr in zip(kappa_values, curve) if cr is not None]
                auc = _auc_average(pts)
                m0 = _point_at(pts, 0.0)
                m1 = _point_at(pts, 1.0)
                m2 = _point_at(pts, 2.0)

                for kappa, sat, rate in zip(kappa_values, sat_counts, curve):
                    if rate is None:
                        continue
                    rows.append(
                        {
                            "run_id": run_id,
                            "model": model,
                            "segment": segment,
                            "curve": curve_name,
                            "alpha": float(args.alpha),
                            "epsilon_smooth": float(args.epsilon_smooth),
                            "epsilon_bound": float(args.epsilon_bound),
                            "kappa": kappa,
                            "n_triples": n_triples,
                            "satisfied": sat,
                            "violation_ratio": 1.0 - float(rate),
                        }
                    )

                agg_all = pooled_all.setdefault(
                    curve_name,
                    {
                        "satisfied": [0 for _ in kappa_values],
                        "n_triples": 0,
                    },
                )
                for i, sat in enumerate(sat_counts):
                    agg_all["satisfied"][i] += sat
                agg_all["n_triples"] += n_triples

                agg_model = pooled_by_model.setdefault(
                    (model, curve_name),
                    {
                        "satisfied": [0 for _ in kappa_values],
                        "n_triples": 0,
                    },
                )
                for i, sat in enumerate(sat_counts):
                    agg_model["satisfied"][i] += sat
                agg_model["n_triples"] += n_triples

    def _emit_agg(*, model_name: str, curve_name: str, agg) -> None:
        n_triples = int(agg["n_triples"])
        if n_triples <= 0:
            return
        curve = [s / n_triples for s in agg["satisfied"]]
        pts = [(kv, cr) for kv, cr in zip(kappa_values, curve)]
        auc = _auc_average(pts)
        m0 = _point_at(pts, 0.0)
        m1 = _point_at(pts, 1.0)
        m2 = _point_at(pts, 2.0)

        for kappa, sat, rate in zip(kappa_values, agg["satisfied"], curve):
            rows.append(
                {
                    "run_id": run_id,
                    "model": model_name,
                    "segment": "ALL",
                    "curve": curve_name,
                    "alpha": float(args.alpha),
                    "epsilon_smooth": float(args.epsilon_smooth),
                    "epsilon_bound": float(args.epsilon_bound),
                    "kappa": kappa,
                    "n_triples": n_triples,
                    "satisfied": sat,
                    "violation_ratio": 1.0 - float(rate),
                }
            )

        summary_rows.append(
            {
                "run_id": run_id,
                "model": model_name,
                "segment": "ALL",
                "curve": curve_name,
                "alpha": float(args.alpha),
                "epsilon_smooth": float(args.epsilon_smooth),
                "epsilon_bound": float(args.epsilon_bound),
                "auc": auc,
                "m0": m0,
                "m1": m1,
                "m2": m2,
                "viol_m0": None if m0 is None else 1.0 - float(m0),
                "viol_m1": None if m1 is None else 1.0 - float(m1),
                "viol_m2": None if m2 is None else 1.0 - float(m2),
                "n_triples": n_triples,
            }
        )

    for (model, curve_name), agg in sorted(pooled_by_model.items()):
        _emit_agg(model_name=model, curve_name=curve_name, agg=agg)

    for curve_name, agg in sorted(pooled_all.items()):
        _emit_agg(model_name="ALL", curve_name=curve_name, agg=agg)

    out_csv = out_dir / f"rq2_violation_curve_{run_id}.csv"
    out_summary_csv = out_dir / f"rq2_violation_summary_{run_id}.csv"

    import csv

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_id",
                "model",
                "segment",
                "curve",
                "alpha",
                "epsilon_smooth",
                "epsilon_bound",
                "kappa",
                "n_triples",
                "satisfied",
                "violation_ratio",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    with out_summary_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_id",
                "model",
                "segment",
                "curve",
                "alpha",
                "epsilon_smooth",
                "epsilon_bound",
                "auc",
                "m0",
                "m1",
                "m2",
                "viol_m0",
                "viol_m1",
                "viol_m2",
                "n_triples",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[OK] wrote: {out_csv}")
    print(f"[OK] wrote: {out_summary_csv}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compute explicit Control MR violation ratios for RQ2 based on the tuple-level predicate in Sec 3.3.2. "
            "This script summarizes violations as 1 - satisfaction." 
        )
    )
    parser.add_argument("--preds-dir", type=str, default=str(_repo_root() / "output" / "out_eval"))
    parser.add_argument("--out-dir", type=str, default="")
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--kappa-start", type=float, default=0.0)
    parser.add_argument("--kappa-end", type=float, default=2.0)
    parser.add_argument("--kappa-step", type=float, default=0.1)
    parser.add_argument("--epsilon-smooth", dest="epsilon_smooth", type=float, default=0.01)
    parser.add_argument("--epsilon-bound", dest="epsilon_bound", type=float, default=0.02)
    args = parser.parse_args()

    _run(args)


if __name__ == "__main__":
    main()
