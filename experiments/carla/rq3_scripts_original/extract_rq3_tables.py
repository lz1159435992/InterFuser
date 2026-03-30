from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


SAFETY_KEYS = (
    "collisions_layout",
    "collisions_pedestrian",
    "collisions_vehicle",
    "outside_route_lanes",
    "red_light",
    "route_timeout",
    "vehicle_blocked",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _find_latest(directory: Path, pattern: str) -> Optional[Path]:
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def _find_latest_by_mtime(directory: Path, pattern: str) -> Optional[Path]:
    files = list(directory.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def _as_number(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    return None


def _count_or_value(x: Any) -> float:
    if x is None:
        return 0.0
    if isinstance(x, list):
        return float(len(x))
    if isinstance(x, (int, float)):
        return float(x)
    return 0.0


@dataclass(frozen=True)
class GlobalMetrics:
    driving_score: Optional[float]
    route_completion: Optional[float]
    route_dev: float
    collisions: float
    offroad: float
    red_lights: float
    timeout: float
    blocked: float


@dataclass(frozen=True)
class RouteMetrics:
    ds: Optional[float]
    rc: Optional[float]
    duration_game: Optional[float]
    route_dev: float
    collisions: float
    offroad: float
    red_lights: float
    timeout: float
    blocked: float


@dataclass(frozen=True)
class ViolationSummary:
    n_routes: int
    viol_path: int
    viol_time: int
    viol_safety: int
    viol_any: int
    mean_delta_ds: float
    mean_delta_rc: float
    mean_delta_coll: float
    mean_delta_to: float
    mean_delta_blk: float

    @property
    def viol_path_ratio(self) -> float:
        return self.viol_path / self.n_routes if self.n_routes > 0 else float("nan")

    @property
    def viol_time_ratio(self) -> float:
        return self.viol_time / self.n_routes if self.n_routes > 0 else float("nan")

    @property
    def viol_safety_ratio(self) -> float:
        return self.viol_safety / self.n_routes if self.n_routes > 0 else float("nan")

    @property
    def viol_any_ratio(self) -> float:
        return self.viol_any / self.n_routes if self.n_routes > 0 else float("nan")


def _get_checkpoint(result: Mapping[str, Any]) -> Mapping[str, Any]:
    ckpt = result.get("_checkpoint")
    if not isinstance(ckpt, dict):
        raise ValueError("Missing _checkpoint")
    return ckpt


def _get_global_metrics(result: Mapping[str, Any]) -> GlobalMetrics:
    ckpt = _get_checkpoint(result)
    gr = ckpt.get("global_record")
    if not isinstance(gr, dict):
        raise ValueError("Missing _checkpoint.global_record")

    scores = gr.get("scores") or {}
    infra = gr.get("infractions") or {}

    ds = _as_number(scores.get("score_composed"))
    rc = _as_number(scores.get("score_route"))

    collisions = (
        _count_or_value(infra.get("collisions_pedestrian"))
        + _count_or_value(infra.get("collisions_vehicle"))
        + _count_or_value(infra.get("collisions_layout"))
    )

    return GlobalMetrics(
        driving_score=ds,
        route_completion=rc,
        route_dev=_count_or_value(infra.get("route_dev")),
        collisions=collisions,
        offroad=_count_or_value(infra.get("outside_route_lanes")),
        red_lights=_count_or_value(infra.get("red_light")),
        timeout=_count_or_value(infra.get("route_timeout")),
        blocked=_count_or_value(infra.get("vehicle_blocked")),
    )


def _get_route_table(result: Mapping[str, Any]) -> Dict[str, RouteMetrics]:
    ckpt = _get_checkpoint(result)
    records = ckpt.get("records")
    if not isinstance(records, list):
        raise ValueError("Missing _checkpoint.records")

    out: Dict[str, RouteMetrics] = {}
    for r in records:
        if not isinstance(r, dict):
            continue
        rid = r.get("route_id")
        if not isinstance(rid, str) or not rid:
            continue

        scores = r.get("scores") or {}
        infra = r.get("infractions") or {}
        meta = r.get("meta") or {}

        ds = _as_number(scores.get("score_composed"))
        rc = _as_number(scores.get("score_route"))

        duration_game: Optional[float] = None
        if isinstance(meta, dict):
            duration_game = _as_number(meta.get("duration_game"))

        collisions = (
            _count_or_value(infra.get("collisions_pedestrian"))
            + _count_or_value(infra.get("collisions_vehicle"))
            + _count_or_value(infra.get("collisions_layout"))
        )

        out[rid] = RouteMetrics(
            ds=ds,
            rc=rc,
            duration_game=duration_game,
            route_dev=_count_or_value(infra.get("outside_route_lanes")),
            collisions=collisions,
            offroad=_count_or_value(infra.get("outside_route_lanes")),
            red_lights=_count_or_value(infra.get("red_light")),
            timeout=_count_or_value(infra.get("route_timeout")),
            blocked=_count_or_value(infra.get("vehicle_blocked")),
        )

    return out


def _summarize_violations(
    baseline: Dict[str, RouteMetrics],
    enhanced: Dict[str, RouteMetrics],
    *,
    path_tol: float = 0.0,
    rc_tol: float = 0.0,
    time_tol: float = 0.0,
    safety_tol: Optional[Mapping[str, float]] = None,
) -> ViolationSummary:
    if safety_tol is None:
        safety_tol = {}

    route_ids = sorted(set(baseline.keys()) & set(enhanced.keys()))

    n = 0
    viol_path = 0
    viol_time = 0
    viol_safety = 0
    viol_any = 0

    sum_delta_ds = 0.0
    sum_delta_rc = 0.0
    sum_delta_coll = 0.0
    sum_delta_to = 0.0
    sum_delta_blk = 0.0

    for rid in route_ids:
        b = baseline[rid]
        e = enhanced[rid]

        if (
            b.ds is None
            or e.ds is None
            or b.rc is None
            or e.rc is None
            or b.duration_game is None
            or e.duration_game is None
        ):
            continue

        n += 1
        sum_delta_ds += (e.ds - b.ds)
        sum_delta_rc += (e.rc - b.rc)
        sum_delta_coll += (e.collisions - b.collisions)
        sum_delta_to += (e.timeout - b.timeout)
        sum_delta_blk += (e.blocked - b.blocked)

        worse_path = e.route_dev > (b.route_dev + path_tol)
        worse_time = (e.rc < (b.rc - rc_tol)) or (e.duration_game > (b.duration_game + time_tol))

        def _worse_safety_metric(key: str, e_val: float, b_val: float) -> bool:
            tol = float(safety_tol.get(key, 0.0))
            return e_val > (b_val + tol)

        worse_safety = (
            _worse_safety_metric("collisions", e.collisions, b.collisions)
            or _worse_safety_metric("red_lights", e.red_lights, b.red_lights)
            or _worse_safety_metric("timeout", e.timeout, b.timeout)
            or _worse_safety_metric("blocked", e.blocked, b.blocked)
        )

        if worse_path:
            viol_path += 1
        if worse_time:
            viol_time += 1
        if worse_safety:
            viol_safety += 1
        if worse_path or worse_time or worse_safety:
            viol_any += 1

    if n == 0:
        return ViolationSummary(
            n_routes=0,
            viol_path=0,
            viol_time=0,
            viol_safety=0,
            viol_any=0,
            mean_delta_ds=float("nan"),
            mean_delta_rc=float("nan"),
            mean_delta_coll=float("nan"),
            mean_delta_to=float("nan"),
            mean_delta_blk=float("nan"),
        )

    return ViolationSummary(
        n_routes=n,
        viol_path=viol_path,
        viol_time=viol_time,
        viol_safety=viol_safety,
        viol_any=viol_any,
        mean_delta_ds=sum_delta_ds / n,
        mean_delta_rc=sum_delta_rc / n,
        mean_delta_coll=sum_delta_coll / n,
        mean_delta_to=sum_delta_to / n,
        mean_delta_blk=sum_delta_blk / n,
    )


def _fmt_or_na(x: Optional[float]) -> str:
    return "N/A" if x is None else f"{x:.3f}"


def _fmt_ratio(x: float) -> str:
    if x != x:  # NaN
        return "N/A"
    return f"{x:.3f}"


def _fmt_delta(x: float) -> str:
    if x != x:  # NaN
        return "N/A"
    return f"{x:.3f}"


def _fmt_pct(x: float) -> str:
    if x != x:  # NaN
        return "N/A"
    return f"{100.0 * x:.1f}\\%"


def _print_simulator_table_rows(rows: List[Tuple[str, str, str, Optional[Path]]]) -> None:
    for ads, suite, variant, path in rows:
        if path is None or not path.exists():
            print(f"{ads} & {suite} & {variant} & N/A & N/A & N/A & N/A & N/A & N/A & N/A & N/A \\")
            continue
        gm = _get_global_metrics(_load_json(path))
        print(
            " & ".join(
                [
                    ads,
                    suite,
                    variant,
                    _fmt_or_na(gm.driving_score),
                    _fmt_or_na(gm.route_completion),
                    f"{gm.route_dev:.3f}",
                    f"{gm.collisions:.3f}",
                    f"{gm.offroad:.3f}",
                    f"{gm.red_lights:.3f}",
                    f"{gm.timeout:.3f}",
                    f"{gm.blocked:.3f}",
                ]
            )
            + " \\",
        )


def _print_violation_rows(
    ads: str,
    rows: List[Tuple[str, str, Optional[Path], Optional[Path]]],
    *,
    path_tol: float = 0.0,
    rc_tol: float = 0.0,
    time_tol: float = 0.0,
    safety_tol: float = 0.0,
) -> None:
    total_n = 0
    total_viol_path = 0
    total_viol_time = 0
    total_viol_safety = 0
    total_viol_any = 0
    total_delta_ds = 0.0
    total_delta_rc = 0.0
    total_delta_coll = 0.0
    total_delta_to = 0.0
    total_delta_blk = 0.0

    suite_summaries: List[Tuple[str, str, ViolationSummary]] = []

    for suite, variant, base_path, enh_path in rows:
        if base_path is None or enh_path is None or not base_path.exists() or not enh_path.exists():
            continue

        base = _get_route_table(_load_json(base_path))
        enh = _get_route_table(_load_json(enh_path))
        per_metric_tol = {
            "collisions": safety_tol,
            "offroad": safety_tol,
            "red_lights": safety_tol,
            "timeout": safety_tol,
            "blocked": safety_tol,
        }
        summary = _summarize_violations(
            base,
            enh,
            path_tol=path_tol,
            rc_tol=rc_tol,
            time_tol=time_tol,
            safety_tol=per_metric_tol,
        )

        if summary.n_routes == 0:
            continue

        suite_summaries.append((suite, variant, summary))

        total_n += summary.n_routes
        total_viol_path += summary.viol_path
        total_viol_time += summary.viol_time
        total_viol_safety += summary.viol_safety
        total_viol_any += summary.viol_any
        total_delta_ds += summary.mean_delta_ds * summary.n_routes
        total_delta_rc += summary.mean_delta_rc * summary.n_routes
        total_delta_coll += summary.mean_delta_coll * summary.n_routes
        total_delta_to += summary.mean_delta_to * summary.n_routes
        total_delta_blk += summary.mean_delta_blk * summary.n_routes

        print(
            " & ".join(
                [
                    ads,
                    suite,
                    variant,
                    str(summary.n_routes),
                    _fmt_ratio(summary.viol_path_ratio),
                    _fmt_ratio(summary.viol_time_ratio),
                    _fmt_ratio(summary.viol_safety_ratio),
                    _fmt_ratio(summary.viol_any_ratio),
                    _fmt_delta(summary.mean_delta_ds),
                    _fmt_delta(summary.mean_delta_rc),
                    _fmt_delta(summary.mean_delta_coll),
                    _fmt_delta(summary.mean_delta_to),
                    _fmt_delta(summary.mean_delta_blk),
                ]
            )
            + " \\",
        )

    if total_n == 0:
        return

    overall = ViolationSummary(
        n_routes=total_n,
        viol_path=total_viol_path,
        viol_time=total_viol_time,
        viol_safety=total_viol_safety,
        viol_any=total_viol_any,
        mean_delta_ds=total_delta_ds / total_n,
        mean_delta_rc=total_delta_rc / total_n,
        mean_delta_coll=total_delta_coll / total_n,
        mean_delta_to=total_delta_to / total_n,
        mean_delta_blk=total_delta_blk / total_n,
    )

    variant_set = {variant for _, variant, _ in suite_summaries}
    if len(variant_set) != 1:
        return

    (only_variant,) = tuple(variant_set)
    print(
        " & ".join(
            [
                ads,
                "Overall",
                only_variant,
                str(overall.n_routes),
                _fmt_ratio(overall.viol_path_ratio),
                _fmt_ratio(overall.viol_time_ratio),
                _fmt_ratio(overall.viol_safety_ratio),
                _fmt_ratio(overall.viol_any_ratio),
                _fmt_delta(overall.mean_delta_ds),
                _fmt_delta(overall.mean_delta_rc),
                _fmt_delta(overall.mean_delta_coll),
                _fmt_delta(overall.mean_delta_to),
                _fmt_delta(overall.mean_delta_blk),
            ]
        )
        + " \\",
    )


def _parse_native_variant(path: Path) -> Optional[Tuple[str, str]]:
    name = path.stem
    if name.startswith("town05_"):
        suite = "Town05"
        rest = name[len("town05_") :]
    elif name.startswith("42routes_"):
        suite = "42 Routes"
        rest = name[len("42routes_") :]
    else:
        return None

    tokens = rest.split("_")
    if not tokens:
        return None

    variant_tokens: List[str] = []
    for t in tokens:
        if t.isdigit() or (len(t) == 8 and t.isdigit()):
            break
        if len(t) == 6 and t.isdigit():
            break
        if len(t) == 15 and t.isdigit():
            break
        if t == "20260204" or t == "20260304" or t == "20260307" or t == "20260210" or t == "20260214" or t == "20260219" or t == "20260228":
            break
        if t in {"gauss8", "gauss16", "none", "high", "fps", "res", "no", "noise"}:
            variant_tokens.append(t)
        else:
            variant_tokens.append(t)

    variant = "_".join(variant_tokens)
    variant = variant.replace("high_fps", "high_fps").replace("high_res", "high_res").replace("no_noise", "no_noise")
    variant = variant.replace("high_fps_high_res", "high_fps+high_res")
    variant = variant.replace("high_fps_no_noise", "high_fps+no_noise")
    variant = variant.replace("high_res_no_noise", "high_res+no_noise")
    variant = variant.replace("high_fps_high_res_no_noise", "high_fps+high_res+no_noise")
    if variant == "":
        return None
    return suite, variant


def _collect_interfuser_native_rows(native_dir: Path) -> List[Tuple[str, str, Path]]:
    def _record_count(path: Path) -> int:
        try:
            data = _load_json(path)
        except Exception:
            return 0
        ckpt = data.get("_checkpoint")
        if not isinstance(ckpt, dict):
            return 0
        recs = ckpt.get("records")
        return len(recs) if isinstance(recs, list) else 0

    # Prefer the newest file that contains non-empty route records.
    latest: Dict[Tuple[str, str], Tuple[int, float, Path]] = {}
    for p in native_dir.glob("*.json"):
        parsed = _parse_native_variant(p)
        if parsed is None:
            continue
        suite, variant = parsed
        nrec = _record_count(p)
        if nrec <= 0:
            continue
        key = (suite, variant)
        ts = p.stat().st_mtime
        prev = latest.get(key)
        if prev is None or ts > prev[1]:
            latest[key] = (nrec, ts, p)

    ordered_variants = [
        "none",
        "high_fps",
        "high_res",
        "no_noise",
        "high_fps+high_res",
        "high_fps+no_noise",
        "high_res+no_noise",
        "high_fps+high_res+no_noise",
        "gauss8",
        "gauss16",
    ]
    ordered_suites = ["Town05", "42 Routes"]
    rows: List[Tuple[str, str, Path]] = []
    for suite in ordered_suites:
        for variant in ordered_variants:
            entry = latest.get((suite, variant))
            if entry is not None:
                rows.append((suite, variant, entry[2]))
    return rows


def _print_interfuser_native_suite_summary(
    *,
    base_town05: Path,
    base_42: Path,
    native_dir: Path,
    path_tol: float,
    rc_tol: float,
    time_tol: float,
    safety_tol: float,
) -> None:
    base_map = {"Town05": base_town05, "42 Routes": base_42}
    base_tables = {suite: _get_route_table(_load_json(p)) for suite, p in base_map.items()}
    base_sizes = {suite: len(tbl) for suite, tbl in base_tables.items()}
    rows = _collect_interfuser_native_rows(native_dir)
    per_metric_tol = {
        "collisions": safety_tol,
        "offroad": safety_tol,
        "red_lights": safety_tol,
        "timeout": safety_tol,
        "blocked": safety_tol,
    }

    print("# Interfuser native suite summary rows (tab:rq3_suite_summary)")
    print("# Columns: Enhancement & Viol.(Path) & Viol.(Time) & Viol.(Safe) & Viol.(Sys) \\")
    variants_in_order = [
        "none",
        "high_fps",
        "high_res",
        "no_noise",
        "high_fps+high_res",
        "high_fps+no_noise",
        "high_res+no_noise",
        "high_fps+high_res+no_noise",
        "gauss8",
        "gauss16",
    ]

    for variant in variants_in_order:
        if variant == "none":
            # Under baseline pairing choice A, 'none' is defined as the original baseline JSONs.
            # Therefore, comparing baseline vs baseline yields 0 violations by construction.
            print(" & ".join(["none", "0.0\\%", "0.0\\%", "0.0\\%", "0.0\\%"]) + " \\")
            continue
        # pool Town05 + 42 Routes together like the paper's "Overall" for a single ADS
        summaries: List[ViolationSummary] = []
        weights: List[int] = []
        for suite, v, path in rows:
            if v != variant:
                continue
            base = base_tables.get(suite)
            if base is None:
                continue
            enh = _get_route_table(_load_json(path))
            summary = _summarize_violations(
                base,
                enh,
                path_tol=path_tol,
                rc_tol=rc_tol,
                time_tol=time_tol,
                safety_tol=per_metric_tol,
            )
            # Require full suite coverage to keep ratios comparable to the baseline suite.
            if summary.n_routes == 0 or summary.n_routes != base_sizes.get(suite, summary.n_routes):
                continue
            summaries.append(summary)
            weights.append(summary.n_routes)

        if not summaries:
            continue
        # Under choice A, we require both suites to be present with full coverage.
        if len(summaries) != 2:
            continue
        total_n = sum(weights)
        viol_path = sum(s.viol_path for s in summaries)
        viol_time = sum(s.viol_time for s in summaries)
        viol_safe = sum(s.viol_safety for s in summaries)
        viol_any = sum(s.viol_any for s in summaries)
        pooled = ViolationSummary(
            n_routes=total_n,
            viol_path=viol_path,
            viol_time=viol_time,
            viol_safety=viol_safe,
            viol_any=viol_any,
            mean_delta_ds=float("nan"),
            mean_delta_rc=float("nan"),
            mean_delta_coll=float("nan"),
            mean_delta_to=float("nan"),
            mean_delta_blk=float("nan"),
        )

        print(
            " & ".join(
                [
                    variant,
                    _fmt_pct(pooled.viol_path_ratio),
                    _fmt_pct(pooled.viol_time_ratio),
                    _fmt_pct(pooled.viol_safety_ratio),
                    _fmt_pct(pooled.viol_any_ratio),
                ]
            )
            + " \\",
        )


def _print_interfuser_native_supporting_stats(
    *,
    base_town05: Path,
    base_42: Path,
    native_dir: Path,
    path_tol: float,
    rc_tol: float,
    time_tol: float,
    safety_tol: float,
) -> None:
    base_map = {"Town05": base_town05, "42 Routes": base_42}
    base_tables = {suite: _get_route_table(_load_json(p)) for suite, p in base_map.items()}
    base_sizes = {suite: len(tbl) for suite, tbl in base_tables.items()}
    rows = _collect_interfuser_native_rows(native_dir)
    per_metric_tol = {
        "collisions": safety_tol,
        "offroad": safety_tol,
        "red_lights": safety_tol,
        "timeout": safety_tol,
        "blocked": safety_tol,
    }

    variants_in_order = [
        "none",
        "high_fps",
        "high_res",
        "no_noise",
        "high_fps+high_res",
        "high_fps+no_noise",
        "high_res+no_noise",
        "high_fps+high_res+no_noise",
        "gauss8",
        "gauss16",
    ]

    print("# Interfuser native supporting stats rows (tab:rq3_simulator)")
    print("# Columns: Enhancement & MeanΔDS & MeanΔRC & MeanΔColl & MeanΔTO & MeanΔBlk \\")
    for variant in variants_in_order:
        if variant == "none":
            # Baseline vs baseline.
            print(" & ".join(["none", "0.00", "0.00", "0.00", "0.00", "0.00"]) + " \\")
            continue
        summaries: List[ViolationSummary] = []
        weights: List[int] = []
        for suite, v, path in rows:
            if v != variant:
                continue
            base = base_tables.get(suite)
            if base is None:
                continue
            enh = _get_route_table(_load_json(path))
            summary = _summarize_violations(
                base,
                enh,
                path_tol=path_tol,
                rc_tol=rc_tol,
                time_tol=time_tol,
                safety_tol=per_metric_tol,
            )
            # Require full suite coverage to keep means comparable to the baseline suite.
            if summary.n_routes == 0 or summary.n_routes != base_sizes.get(suite, summary.n_routes):
                continue
            summaries.append(summary)
            weights.append(summary.n_routes)

        if not summaries:
            continue
        # Under choice A, we require both suites to be present with full coverage.
        if len(summaries) != 2:
            continue
        total_n = sum(weights)
        mean_delta_ds = sum(s.mean_delta_ds * s.n_routes for s in summaries) / total_n
        mean_delta_rc = sum(s.mean_delta_rc * s.n_routes for s in summaries) / total_n
        mean_delta_coll = sum(s.mean_delta_coll * s.n_routes for s in summaries) / total_n
        mean_delta_to = sum(s.mean_delta_to * s.n_routes for s in summaries) / total_n
        mean_delta_blk = sum(s.mean_delta_blk * s.n_routes for s in summaries) / total_n

        print(
            " & ".join(
                [
                    variant,
                    f"{mean_delta_ds:.2f}",
                    f"{mean_delta_rc:.2f}",
                    f"{mean_delta_coll:.2f}",
                    f"{mean_delta_to:.2f}",
                    f"{mean_delta_blk:.2f}",
                ]
            )
            + " \\",
        )


def _print_lmdrive_native_supporting_stats(
    *,
    native_dir: Path,
    path_tol: float,
    rc_tol: float,
    time_tol: float,
    safety_tol: float,
) -> None:
    # LMDrive native results are stored as separate suite splits (long/short/tiny).
    # We pool by route count (weights) to match the paper's Overall aggregation.
    base_paths = {
        "long": native_dir / "langauto_long_none.json",
        "short": native_dir / "langauto_short_none.json",
        "tiny": native_dir / "langauto_tiny_none.json",
    }
    base_tables: Dict[str, Dict[str, RouteMetrics]] = {}
    base_sizes: Dict[str, int] = {}
    for suite, p in base_paths.items():
        if not p.exists():
            continue
        tbl = _get_route_table(_load_json(p))
        base_tables[suite] = tbl
        base_sizes[suite] = len(tbl)

    per_metric_tol = {
        "collisions": safety_tol,
        "offroad": safety_tol,
        "red_lights": safety_tol,
        "timeout": safety_tol,
        "blocked": safety_tol,
    }

    def _pooled_variant_summary(variant: str) -> Optional[ViolationSummary]:
        summaries: List[ViolationSummary] = []
        base_weights: List[int] = []
        for suite in ("long", "short", "tiny"):
            base = base_tables.get(suite)
            if base is None:
                return None
            enh_path = native_dir / f"langauto_{suite}_{variant}.json"
            if not enh_path.exists():
                return None
            enh = _get_route_table(_load_json(enh_path))
            summary = _summarize_violations(
                base,
                enh,
                path_tol=path_tol,
                rc_tol=rc_tol,
                time_tol=time_tol,
                safety_tol=per_metric_tol,
            )
            # Require full suite coverage.
            if summary.n_routes == 0 or summary.n_routes != base_sizes.get(suite, summary.n_routes):
                return None
            summaries.append(summary)
            base_weights.append(summary.n_routes)

        total_n = sum(base_weights)
        pooled = ViolationSummary(
            n_routes=total_n,
            viol_path=sum(s.viol_path for s in summaries),
            viol_time=sum(s.viol_time for s in summaries),
            viol_safety=sum(s.viol_safety for s in summaries),
            viol_any=sum(s.viol_any for s in summaries),
            mean_delta_ds=sum(s.mean_delta_ds * s.n_routes for s in summaries) / total_n,
            mean_delta_rc=sum(s.mean_delta_rc * s.n_routes for s in summaries) / total_n,
            mean_delta_coll=sum(s.mean_delta_coll * s.n_routes for s in summaries) / total_n,
            mean_delta_to=sum(s.mean_delta_to * s.n_routes for s in summaries) / total_n,
            mean_delta_blk=sum(s.mean_delta_blk * s.n_routes for s in summaries) / total_n,
        )
        return pooled

    def _print_row(row_name: str, pooled: ViolationSummary) -> None:
        print(
            " & ".join(
                [
                    row_name,
                    f"{pooled.mean_delta_ds:.2f}",
                    f"{pooled.mean_delta_rc:.2f}",
                    f"{pooled.mean_delta_coll:.2f}",
                    f"{pooled.mean_delta_to:.2f}",
                    f"{pooled.mean_delta_blk:.2f}",
                ]
            )
            + " \\",
        )

    # Map to the row names used in appendix.tex.
    # Note: in native_sweep, joint settings are stored with expanded variant names rather than comp2/comp3.
    single_variants_in_order: List[Tuple[str, str]] = [
        ("FR", "high_fps"),
        ("RS", "high_res"),
        ("VP", "no_noise"),
        (r"\\mbox{Gaussian Noise ($\\sigma$=8)}", "gauss8"),
        (r"\\mbox{Gaussian Noise ($\\sigma$=16)}", "gauss16"),
    ]

    print("# LMDrive native supporting stats rows (tab:rq3_simulator)")
    print("# Columns: Enhancement & MeanΔDS & MeanΔRC & MeanΔColl & MeanΔTO & MeanΔBlk \\")

    pooled_k3 = _pooled_variant_summary("high_fps_high_res_no_noise")
    if pooled_k3 is not None:
        _print_row("Composite ($K=3$)", pooled_k3)

    pooled_k2_parts: List[ViolationSummary] = []
    for v in ("high_fps_high_res", "high_fps_no_noise", "high_res_no_noise"):
        s = _pooled_variant_summary(v)
        if s is not None:
            pooled_k2_parts.append(s)
    if len(pooled_k2_parts) == 3:
        mean_ds = sum(s.mean_delta_ds for s in pooled_k2_parts) / 3.0
        mean_rc = sum(s.mean_delta_rc for s in pooled_k2_parts) / 3.0
        mean_coll = sum(s.mean_delta_coll for s in pooled_k2_parts) / 3.0
        mean_to = sum(s.mean_delta_to for s in pooled_k2_parts) / 3.0
        mean_blk = sum(s.mean_delta_blk for s in pooled_k2_parts) / 3.0
        pooled_k2 = ViolationSummary(
            n_routes=pooled_k2_parts[0].n_routes,
            viol_path=0,
            viol_time=0,
            viol_safety=0,
            viol_any=0,
            mean_delta_ds=mean_ds,
            mean_delta_rc=mean_rc,
            mean_delta_coll=mean_coll,
            mean_delta_to=mean_to,
            mean_delta_blk=mean_blk,
        )
        _print_row("Composite ($K=2$)", pooled_k2)

    for row_name, variant in single_variants_in_order:
        pooled = _pooled_variant_summary(variant)
        if pooled is None:
            continue
        _print_row(row_name, pooled)


def _print_lmdrive_native_suite_summary(
    *,
    native_dir: Path,
    path_tol: float,
    rc_tol: float,
    time_tol: float,
    safety_tol: float,
) -> None:
    base_paths = {
        "long": native_dir / "langauto_long_none.json",
        "short": native_dir / "langauto_short_none.json",
        "tiny": native_dir / "langauto_tiny_none.json",
    }
    base_tables: Dict[str, Dict[str, RouteMetrics]] = {}
    base_sizes: Dict[str, int] = {}
    for suite, p in base_paths.items():
        if not p.exists():
            continue
        tbl = _get_route_table(_load_json(p))
        base_tables[suite] = tbl
        base_sizes[suite] = len(tbl)

    per_metric_tol = {
        "collisions": safety_tol,
        "offroad": safety_tol,
        "red_lights": safety_tol,
        "timeout": safety_tol,
        "blocked": safety_tol,
    }

    def _pooled_variant_summary(variant: str) -> Optional[ViolationSummary]:
        summaries: List[ViolationSummary] = []
        weights: List[int] = []
        for suite in ("long", "short", "tiny"):
            base = base_tables.get(suite)
            if base is None:
                return None
            enh_path = native_dir / f"langauto_{suite}_{variant}.json"
            if not enh_path.exists():
                return None
            enh = _get_route_table(_load_json(enh_path))
            summary = _summarize_violations(
                base,
                enh,
                path_tol=path_tol,
                rc_tol=rc_tol,
                time_tol=time_tol,
                safety_tol=per_metric_tol,
            )
            if summary.n_routes == 0 or summary.n_routes != base_sizes.get(suite, summary.n_routes):
                return None
            summaries.append(summary)
            weights.append(summary.n_routes)

        total_n = sum(weights)
        pooled = ViolationSummary(
            n_routes=total_n,
            viol_path=sum(s.viol_path for s in summaries),
            viol_time=sum(s.viol_time for s in summaries),
            viol_safety=sum(s.viol_safety for s in summaries),
            viol_any=sum(s.viol_any for s in summaries),
            mean_delta_ds=float("nan"),
            mean_delta_rc=float("nan"),
            mean_delta_coll=float("nan"),
            mean_delta_to=float("nan"),
            mean_delta_blk=float("nan"),
        )
        return pooled

    def _print_row(row_name: str, pooled: ViolationSummary) -> None:
        print(
            " & ".join(
                [
                    row_name,
                    _fmt_pct(pooled.viol_path_ratio),
                    _fmt_pct(pooled.viol_time_ratio),
                    _fmt_pct(pooled.viol_safety_ratio),
                    _fmt_pct(pooled.viol_any_ratio),
                ]
            )
            + " \\",
        )

    print("# LMDrive native suite summary rows (tab:rq3_suite_summary)")
    print("# Columns: Enhancement & Viol.(Path) & Viol.(Time) & Viol.(Safe) & Viol.(Sys) \\")

    pooled_k3 = _pooled_variant_summary("high_fps_high_res_no_noise")
    if pooled_k3 is not None:
        _print_row("Composite ($K=3$)", pooled_k3)

    pooled_k2_parts: List[ViolationSummary] = []
    for v in ("high_fps_high_res", "high_fps_no_noise", "high_res_no_noise"):
        s = _pooled_variant_summary(v)
        if s is not None:
            pooled_k2_parts.append(s)
    if len(pooled_k2_parts) == 3:
        # Composite ratios are defined as mean over settings.
        # Each setting ratio is computed on the same 64-route pool.
        def _mean_ratio(getter):
            return sum(getter(s) for s in pooled_k2_parts) / 3.0

        viol_path = _mean_ratio(lambda s: s.viol_path_ratio)
        viol_time = _mean_ratio(lambda s: s.viol_time_ratio)
        viol_safe = _mean_ratio(lambda s: s.viol_safety_ratio)
        viol_any = _mean_ratio(lambda s: s.viol_any_ratio)
        # Wrap into a ViolationSummary-like object for printing.
        pooled_k2 = ViolationSummary(
            n_routes=pooled_k2_parts[0].n_routes,
            viol_path=int(round(viol_path * pooled_k2_parts[0].n_routes)),
            viol_time=int(round(viol_time * pooled_k2_parts[0].n_routes)),
            viol_safety=int(round(viol_safe * pooled_k2_parts[0].n_routes)),
            viol_any=int(round(viol_any * pooled_k2_parts[0].n_routes)),
            mean_delta_ds=float("nan"),
            mean_delta_rc=float("nan"),
            mean_delta_coll=float("nan"),
            mean_delta_to=float("nan"),
            mean_delta_blk=float("nan"),
        )
        _print_row("Composite ($K=2$)", pooled_k2)

    for row_name, variant in [
        ("FR", "high_fps"),
        ("RS", "high_res"),
        ("VP", "no_noise"),
        ("gauss8", "gauss8"),
        ("gauss16", "gauss16"),
    ]:
        pooled = _pooled_variant_summary(variant)
        if pooled is None:
            continue
        if row_name == "gauss8":
            _print_row(r"\\mbox{Gaussian Noise ($\\sigma$=8)}", pooled)
        elif row_name == "gauss16":
            _print_row(r"\\mbox{Gaussian Noise ($\\sigma$=16)}", pooled)
        else:
            _print_row(row_name, pooled)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract RQ3 CARLA Leaderboard metrics and System MR violation ratios from JSON results.",
    )
    parser.add_argument(
        "--path-tol",
        type=float,
        default=0.0,
        help="Route deviation tolerance for route-level Path degradation (default: 0.0).",
    )
    parser.add_argument(
        "--rc-tol",
        type=float,
        default=0.0,
        help="Route completion tolerance for Time degradation (default: 0.0).",
    )
    parser.add_argument(
        "--time-tol",
        type=float,
        default=0.0,
        help="Duration tolerance in seconds for travel time increase (default: 0.0).",
    )
    parser.add_argument(
        "--safety-tol",
        type=float,
        default=0.0,
        help="Uniform tolerance added to each per-route infraction count (default: 0.0).",
    )
    parser.add_argument(
        "--section",
        choices=("simulator", "violations", "native", "all"),
        default="all",
        help="Which section to print (default: all).",
    )

    args = parser.parse_args(argv)

    root = _repo_root()
    out_dir = root / "output"

    interfuser_dir = out_dir / "interfuser"
    interfuser_proc = interfuser_dir / "with_processor"
    interfuser_native = interfuser_dir / "native"

    lmdrive_proc = out_dir / "lmdrive" / "with_processor"
    lmdrive_native = out_dir / "lmdrive" / "native_sweep" / "fullcover_native_20260320"

    interfuser_town05_orig = interfuser_dir / "interfuser_town05_result.json"
    interfuser_42_orig = interfuser_dir / "interfuser_42routes_result.json"

    interfuser_town05_sr = _find_latest(interfuser_proc, "town05_srgan_2x_*.json")
    interfuser_42_sr = _find_latest(interfuser_proc, "42routes_srgan_2x_*.json")

    lmdrive_long_orig = _find_latest(lmdrive_proc, "langauto_long_*no_process*.json")
    lmdrive_long_sr = _find_latest(lmdrive_proc, "langauto_long_*srgan_2x_*.json")
    lmdrive_long_dn = _find_latest(lmdrive_proc, "langauto_long_*denoise15_*.json")

    lmdrive_short_orig = _find_latest(lmdrive_proc, "langauto_short_*no_process*.json")
    lmdrive_short_sr = _find_latest(lmdrive_proc, "langauto_short_*srgan_2x_*.json")
    lmdrive_short_dn = _find_latest(lmdrive_proc, "langauto_short_*denoise15_*.json")

    lmdrive_tiny_orig = _find_latest(lmdrive_proc, "langauto_tiny_*no_process*.json")
    lmdrive_tiny_sr = _find_latest(lmdrive_proc, "langauto_tiny_*srgan_2x_*.json")
    lmdrive_tiny_dn = _find_latest(lmdrive_proc, "langauto_tiny_*denoise15_*.json")

    simulator_rows = [
        ("Interfuser", "Town05", "Original", interfuser_town05_orig),
        ("Interfuser", "Town05", "SR", interfuser_town05_sr),
        ("Interfuser", "Town05", "DN", None),
        ("Interfuser", "42 Routes", "Original", interfuser_42_orig),
        ("Interfuser", "42 Routes", "SR", interfuser_42_sr),
        ("Interfuser", "42 Routes", "DN", None),
        ("LMDrive", "long", "Original", lmdrive_long_orig),
        ("LMDrive", "long", "SR", lmdrive_long_sr),
        ("LMDrive", "long", "DN", lmdrive_long_dn),
        ("LMDrive", "short", "Original", lmdrive_short_orig),
        ("LMDrive", "short", "SR", lmdrive_short_sr),
        ("LMDrive", "short", "DN", lmdrive_short_dn),
        ("LMDrive", "tiny", "Original", lmdrive_tiny_orig),
        ("LMDrive", "tiny", "SR", lmdrive_tiny_sr),
        ("LMDrive", "tiny", "DN", lmdrive_tiny_dn),
    ]

    if args.section in ("simulator", "all"):
        print("# RQ3 simulator table rows (tab:rq3_simulator)")
        _print_simulator_table_rows(simulator_rows)
        print()

    if args.section in ("violations", "all"):
        print("# RQ3 route-level MR violation rows (tab:rq3_mr_violations)")

        print("## Interfuser (SR)")
        _print_violation_rows(
            "Interfuser",
            [
                ("Town05", "SR", interfuser_town05_orig, interfuser_town05_sr),
                ("42 Routes", "SR", interfuser_42_orig, interfuser_42_sr),
            ],
            path_tol=args.path_tol,
            rc_tol=args.rc_tol,
            time_tol=args.time_tol,
            safety_tol=args.safety_tol,
        )
        print()

        print("## LMDrive (SR)")
        _print_violation_rows(
            "LMDrive",
            [
                ("long", "SR", lmdrive_long_orig, lmdrive_long_sr),
                ("short", "SR", lmdrive_short_orig, lmdrive_short_sr),
                ("tiny", "SR", lmdrive_tiny_orig, lmdrive_tiny_sr),
            ],
            path_tol=args.path_tol,
            rc_tol=args.rc_tol,
            time_tol=args.time_tol,
            safety_tol=args.safety_tol,
        )
        print()

        print("## LMDrive (DN)")
        _print_violation_rows(
            "LMDrive",
            [
                ("long", "DN", lmdrive_long_orig, lmdrive_long_dn),
                ("short", "DN", lmdrive_short_orig, lmdrive_short_dn),
                ("tiny", "DN", lmdrive_tiny_orig, lmdrive_tiny_dn),
            ],
            path_tol=args.path_tol,
            rc_tol=args.rc_tol,
            time_tol=args.time_tol,
            safety_tol=args.safety_tol,
        )
        print()

    if args.section in ("native", "all"):
        # Native upgrades for Interfuser only (from output/interfuser/native)
        if not interfuser_native.exists():
            print("# Interfuser native directory not found:", interfuser_native)
            return 0

        _print_interfuser_native_suite_summary(
            base_town05=interfuser_town05_orig,
            base_42=interfuser_42_orig,
            native_dir=interfuser_native,
            path_tol=args.path_tol,
            rc_tol=args.rc_tol,
            time_tol=args.time_tol,
            safety_tol=args.safety_tol,
        )
        print()
        _print_interfuser_native_supporting_stats(
            base_town05=interfuser_town05_orig,
            base_42=interfuser_42_orig,
            native_dir=interfuser_native,
            path_tol=args.path_tol,
            rc_tol=args.rc_tol,
            time_tol=args.time_tol,
            safety_tol=args.safety_tol,
        )
        print()

        if not lmdrive_native.exists():
            print("# LMDrive native directory not found:", lmdrive_native)
            return 0

        _print_lmdrive_native_supporting_stats(
            native_dir=lmdrive_native,
            path_tol=args.path_tol,
            rc_tol=args.rc_tol,
            time_tol=args.time_tol,
            safety_tol=args.safety_tol,
        )
        print()

        _print_lmdrive_native_suite_summary(
            native_dir=lmdrive_native,
            path_tol=args.path_tol,
            rc_tol=args.rc_tol,
            time_tol=args.time_tol,
            safety_tol=args.safety_tol,
        )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
