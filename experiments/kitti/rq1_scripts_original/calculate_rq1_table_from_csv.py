import argparse
import csv
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


_MODELS = ("VirConv-L", "VirConv-S", "VirConv-T", "DID-M3D")


@dataclass(frozen=True)
class RowSpec:
    key: str
    label: str


def _read_csv_rows(path: Path, encoding: str) -> List[List[str]]:
    with path.open("r", encoding=encoding, newline="") as f:
        return list(csv.reader(f))


def _column_index(model: str, metric: str, difficulty: str) -> int:
    models = list(_MODELS)
    metrics = ["2D", "bev", "3D", "aos"]
    diffs = ["easy", "normal", "hard"]

    base_col = 2
    mi = models.index(model)
    metri_i = metrics.index(metric)
    di = diffs.index(difficulty)
    return base_col + mi * 12 + metri_i * 3 + di


def _build_row_index(rows: List[List[str]]) -> Dict[str, List[str]]:
    name_map = {
        "原始数据": "orig",
        "双倍大小": "double",
        "去噪声": "DN",
        "插帧后一帧": "FI",
        "超分辨率": "SR",
        "8噪声": "GN8",
        "16噪声": "GN16",
        "去噪声-超分辨率": "DN_SR",
        "插帧-超分辨率": "FI_SR",
        "超分辨率-插帧": "SR_FI",
        "去噪声-插帧": "DN_FI",
        "插帧-去噪声": "FI_DN",
        "超分辨率-去噪声": "SR_DN",
    }

    out: Dict[str, List[str]] = {}
    for r in rows[3:]:
        if not r:
            continue
        key = name_map.get(r[0])
        if key:
            out[key] = r
    return out


def _read_eval_tex_row_cells(eval_tex: Path) -> Dict[str, List[str]]:
    text = eval_tex.read_text(encoding="utf-8")
    lines = text.splitlines()

    labels = [
        "Composite ($K=2$)",
        "DN",
        "FI",
        "SR",
        "Gaussian Noise ($\\sigma$=8)",
        "Gaussian Noise ($\\sigma$=16)",
    ]

    out: Dict[str, List[str]] = {}
    for label in labels:
        row_line = None
        for ln in lines:
            s = ln.lstrip()
            if s.startswith(label + " ") or s.startswith(label + "&"):
                row_line = ln.strip()
                break

        if row_line is None:
            raise ValueError(f"Cannot find LaTeX row for label: {label}")

        row_line = re.sub(r"\\\\\s*$", "", row_line)
        cols = [c.strip() for c in row_line.split("&")]
        out[label] = cols

    return out


def _ap_3d_normal(row_by_key: Mapping[str, List[str]], key: str, model: str) -> float:
    idx = _column_index(model, metric="3D", difficulty="normal")
    return float(row_by_key[key][idx])


def _parse_latex_float(s: str) -> float:
    cleaned = s
    cleaned = cleaned.replace("{", " ").replace("}", " ")
    cleaned = cleaned.replace("\\libertineSB", " ")
    cleaned = cleaned.strip()
    return float(cleaned)


def _read_eval_tex_deltas(eval_tex: Path) -> Dict[str, Dict[str, float]]:
    text = eval_tex.read_text(encoding="utf-8")
    out: Dict[str, Dict[str, float]] = {}

    labels = [
        "Composite ($K=2$)",
        "DN",
        "FI",
        "SR",
        "Gaussian Noise ($\\sigma$=8)",
        "Gaussian Noise ($\\sigma$=16)",
    ]

    lines = text.splitlines()
    for label in labels:
        row_line = None
        for ln in lines:
            if ln.lstrip().startswith(label + " ") or ln.lstrip().startswith(label + "&"):
                row_line = ln.strip()
                break

        if row_line is None:
            raise ValueError(f"Cannot find LaTeX row for label: {label}")

        # Strip trailing LaTeX row terminator.
        row_line = re.sub(r"\\\\\s*$", "", row_line)
        cols = [c.strip() for c in row_line.split("&")]
        if len(cols) < 1 + 2 * len(_MODELS):
            raise ValueError(f"Unexpected LaTeX row format for label: {label}")

        deltas: Dict[str, float] = {}
        for i, model in enumerate(_MODELS):
            deltas[model] = _parse_latex_float(cols[1 + i * 2])
        out[label] = deltas

    return out


def _baseline_key_for_delta(transform_key: str) -> str:
    # Per user instruction:
    # - Use 3D-normal
    # - SR baseline is Double Size
    # - For SR-like pipelines (any pipeline that includes SR and thus changes resolution),
    #   also use the Double Size baseline
    sr_like = {"SR", "DN_SR", "FI_SR", "SR_FI", "SR_DN", "DN_SR", "SR_DN"}
    return "double" if transform_key in sr_like else "orig"


def _baseline_key_for_viol_est(transform_key: str) -> str:
    # Keep the estimation baseline consistent with the ΔAP baseline used in the table.
    return _baseline_key_for_delta(transform_key)


def _delta_ap(row_by_key: Mapping[str, List[str]], transform_key: str, model: str) -> float:
    base_key = _baseline_key_for_delta(transform_key)
    return _ap_3d_normal(row_by_key, transform_key, model) - _ap_3d_normal(row_by_key, base_key, model)


def _estimated_viol_ratio_pct(row_by_key: Mapping[str, List[str]], transform_key: str, model: str) -> float:
    # Heuristic proxy (since MR violation logs are unavailable):
    # interpret relative AP degradation as an estimate of violation prevalence.
    base_key = _baseline_key_for_viol_est(transform_key)
    ap_base = _ap_3d_normal(row_by_key, base_key, model)
    ap_new = _ap_3d_normal(row_by_key, transform_key, model)

    if ap_base <= 0:
        return 0.0

    if ap_new >= ap_base:
        return 0.0

    ratio = (ap_base - ap_new) / ap_base
    return max(0.0, min(1.0, ratio)) * 100.0


def _estimated_viol_ratio_from_delta_pct(ap_orig: float, delta_ap: float) -> float:
    if ap_orig <= 0:
        return 0.0
    if delta_ap >= 0:
        return 0.0
    ratio = (-delta_ap) / ap_orig
    return max(0.0, min(1.0, ratio)) * 100.0


def _mean(values: Iterable[float]) -> float:
    vals = list(values)
    return statistics.mean(vals) if vals else float("nan")


def _format_delta(x: float) -> str:
    if abs(x) < 0.005:
        x = 0.0
    return f"{x:.2f}"


def _format_pct_1(x: float) -> str:
    return f"{x:.1f}"


def _round_1(x: float) -> float:
    return float(f"{x:.1f}")


def _latex_row(label: str, deltas: Mapping[str, float], viols: Mapping[str, float]) -> str:
    mean_viol = _mean(viols[m] for m in _MODELS)
    parts = [label]
    for m in _MODELS:
        parts.append(_format_delta(deltas[m]))
        parts.append(_format_pct_1(viols[m]))
    parts.append(_format_pct_1(mean_viol))
    return " & ".join(parts) + " \\\\"


def _compute_composite(
    row_by_key: Mapping[str, List[str]],
    ordered_pairs: List[str],
) -> Tuple[Dict[str, float], Dict[str, float]]:
    deltas: Dict[str, float] = {}
    viols: Dict[str, float] = {}

    for m in _MODELS:
        ds = [_delta_ap(row_by_key, k, m) for k in ordered_pairs]
        vs = [_estimated_viol_ratio_pct(row_by_key, k, m) for k in ordered_pairs]
        deltas[m] = _mean(ds)
        viols[m] = _mean(vs)

    return deltas, viols


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default=str(_repo_root() / "数据.csv"),
        help="Path to 数据.csv (gb18030 encoding)",
    )
    parser.add_argument(
        "--eval_tex",
        default="",
        help="Optional path to eval.tex; if provided, keep ΔAP from eval.tex and only estimate Viol.(Det)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify eval.tex Viol.(Det) numbers and referenced percentages against the estimation rule",
    )
    parser.add_argument(
        "--out_tex",
        default=str(_repo_root() / "output" / "RQ1_scripts" / "rq1_table_rows_from_csv.tex"),
        help="Output .tex file with LaTeX rows",
    )
    parser.add_argument(
        "--encoding",
        default="gb18030",
        help="CSV encoding (default: gb18030)",
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)
    rows = _read_csv_rows(csv_path, encoding=args.encoding)
    row_by_key = _build_row_index(rows)

    eval_tex_path = Path(args.eval_tex) if args.eval_tex else None

    required = {
        "orig",
        "double",
        "DN",
        "FI",
        "SR",
        "GN8",
        "GN16",
        "DN_SR",
        "SR_DN",
        "DN_FI",
        "FI_DN",
        "SR_FI",
        "FI_SR",
    }
    missing = sorted(k for k in required if k not in row_by_key)
    if missing:
        raise SystemExit(f"Missing rows in CSV: {missing}")

    ordered_pairs = ["DN_SR", "SR_DN", "DN_FI", "FI_DN", "SR_FI", "FI_SR"]

    specs = [
        RowSpec("Composite", "Composite ($K=2$)"),
        RowSpec("DN", "DN"),
        RowSpec("FI", "FI"),
        RowSpec("SR", "SR"),
        RowSpec("GN8", "Gaussian Noise ($\\sigma$=8)"),
        RowSpec("GN16", "Gaussian Noise ($\\sigma$=16)"),
    ]

    out_lines: List[str] = []

    if eval_tex_path is not None:
        deltas_by_label = _read_eval_tex_deltas(eval_tex_path)
        ap_orig_by_model = {m: _ap_3d_normal(row_by_key, "orig", m) for m in _MODELS}

        for spec in specs:
            deltas = deltas_by_label[spec.label]
            viols = {
                m: _estimated_viol_ratio_from_delta_pct(ap_orig_by_model[m], deltas[m])
                for m in _MODELS
            }
            out_lines.append(_latex_row(spec.label, deltas=deltas, viols=viols))

        if args.verify:
            ok = True

            row_cells = _read_eval_tex_row_cells(eval_tex_path)
            for label, cols in row_cells.items():
                viol_calc_raw: Dict[str, float] = {}
                viol_tex: Dict[str, float] = {}

                for i, model in enumerate(_MODELS):
                    delta = _parse_latex_float(cols[1 + i * 2])
                    viol_tex[model] = _round_1(float(cols[2 + i * 2]))
                    viol_calc_raw[model] = _estimated_viol_ratio_from_delta_pct(
                        ap_orig_by_model[model], delta
                    )

                    if viol_tex[model] != _round_1(viol_calc_raw[model]):
                        ok = False
                        print(
                            "Mismatch",
                            label,
                            model,
                            "tex",
                            viol_tex[model],
                            "calc",
                            _round_1(viol_calc_raw[model]),
                        )

                mean_tex = _round_1(float(cols[-1]))
                mean_calc = _round_1(_mean(viol_calc_raw[m] for m in _MODELS))
                if mean_tex != mean_calc:
                    ok = False
                    print("Mismatch mean", label, "tex", mean_tex, "calc", mean_calc)

            # Verify referenced percentages in RQ1 Results text.
            text = eval_tex_path.read_text(encoding="utf-8")
            m = re.search(r"\\myparagraph\{Results\.\}(.+?)\\subsection\{RQ2", text, flags=re.S)
            if not m:
                ok = False
                print("Cannot locate RQ1 Results block")
            else:
                blk = m.group(1)
                comp = row_cells["Composite ($K=2$)"]
                comp_vl = _round_1(float(comp[2]))
                comp_vs = _round_1(float(comp[4]))
                comp_vt = _round_1(float(comp[6]))
                comp_vm = _round_1(float(comp[8]))
                comp_mean = _round_1(float(comp[-1]))
                comp_mean3 = _round_1((comp_vl + comp_vs + comp_vt) / 3.0)

                dn_mean = _round_1(float(row_cells["DN"][-1]))
                sr_mean = _round_1(float(row_cells["SR"][-1]))
                gn8_mean = _round_1(float(row_cells["Gaussian Noise ($\\sigma$=8)"][-1]))
                gn16_mean = _round_1(float(row_cells["Gaussian Noise ($\\sigma$=16)"][-1]))

                required = [
                    f"{comp_vl}\\%",
                    f"{comp_vs}\\%",
                    f"{comp_vt}\\%",
                    f"{comp_vm}\\%",
                    f"{comp_mean}\\%",
                    f"{comp_mean3}\\%",
                    f"{sr_mean}\\%",
                    f"{dn_mean}\\%",
                    f"{gn8_mean}\\%--{gn16_mean}\\%",
                ]

                for s in required:
                    if s not in blk:
                        ok = False
                        print("Missing in Results text:", s)

            print("ALL_OK" if ok else "HAS_MISMATCH")
    else:
        for spec in specs:
            if spec.key == "Composite":
                deltas, viols = _compute_composite(row_by_key, ordered_pairs)
            else:
                deltas = {m: _delta_ap(row_by_key, spec.key, m) for m in _MODELS}
                viols = {m: _estimated_viol_ratio_pct(row_by_key, spec.key, m) for m in _MODELS}

            out_lines.append(_latex_row(spec.label, deltas=deltas, viols=viols))

    out_path = Path(args.out_tex)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    print("\n".join(out_lines))


if __name__ == "__main__":
    main()
