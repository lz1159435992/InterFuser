#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _safe_float(x: Any) -> Optional[float]:
    if isinstance(x, (int, float)):
        return float(x)
    return None


def _count_metric(x: Any) -> float:
    if x is None:
        return 0.0
    if isinstance(x, list):
        return float(len(x))
    if isinstance(x, (int, float)):
        return float(x)
    return 0.0


def _parse_variant(stem: str) -> Tuple[str, str]:
    # Example:
    # - town05_high_fps_20260204_182243
    # - 42routes_gauss16_20260214_120217
    # - town05_gauss8
    if stem.startswith("town05_"):
        suite = "town05"
        rest = stem[len("town05_") :]
    elif stem.startswith("42routes_"):
        suite = "42routes"
        rest = stem[len("42routes_") :]
    else:
        suite = "unknown"
        rest = stem

    # Remove trailing timestamp token if present.
    parts = rest.split("_")
    if len(parts) >= 3 and parts[-2].isdigit() and parts[-1].isdigit():
        variant = "_".join(parts[:-2])
    else:
        variant = rest
    return suite, variant


def _extract_row(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    ckpt = data.get("_checkpoint", {})
    global_record = ckpt.get("global_record", {})
    scores = global_record.get("scores", {})
    infra = global_record.get("infractions", {})

    suite, variant = _parse_variant(path.stem)
    collisions = (
        _count_metric(infra.get("collisions_pedestrian"))
        + _count_metric(infra.get("collisions_vehicle"))
        + _count_metric(infra.get("collisions_layout"))
    )

    return {
        "file": path.name,
        "suite": suite,
        "variant": variant,
        "score_composed": _safe_float(scores.get("score_composed")),
        "score_route": _safe_float(scores.get("score_route")),
        "score_penalty": _safe_float(scores.get("score_penalty")),
        "n_collisions": collisions,
        "n_outside_route_lanes": _count_metric(infra.get("outside_route_lanes")),
        "n_red_light": _count_metric(infra.get("red_light")),
        "n_route_timeout": _count_metric(infra.get("route_timeout")),
        "n_vehicle_blocked": _count_metric(infra.get("vehicle_blocked")),
        "n_records": len(ckpt.get("records", [])) if isinstance(ckpt.get("records"), list) else 0,
    }


def _rows_to_csv(rows: Iterable[Dict[str, Any]], output_csv: Path) -> None:
    rows = list(rows)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    keys = [
        "file",
        "suite",
        "variant",
        "score_composed",
        "score_route",
        "score_penalty",
        "n_collisions",
        "n_outside_route_lanes",
        "n_red_light",
        "n_route_timeout",
        "n_vehicle_blocked",
        "n_records",
    ]
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract CARLA native result JSON files into a normalized CSV summary.",
    )
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"Input dir not found: {input_dir}")

    json_files = sorted(p for p in input_dir.glob("*.json") if p.is_file())
    rows = [_extract_row(p) for p in json_files]
    _rows_to_csv(rows, args.output_csv.resolve())
    print(f"Wrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
