from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@dataclass(frozen=True)
class ClassifyResult:
    category: str
    reason: str


def _classify_result(path: Path) -> ClassifyResult:
    try:
        data = _load_json(path)
    except Exception as e:
        return ClassifyResult("parse_error", f"json_load_failed: {e}")

    ckpt = data.get("_checkpoint")
    if not isinstance(ckpt, dict):
        return ClassifyResult("missing_checkpoint", "missing _checkpoint")

    gr = ckpt.get("global_record")
    if not isinstance(gr, dict):
        return ClassifyResult("missing_global_record", "missing _checkpoint.global_record")

    progress = ckpt.get("progress")
    if not (isinstance(progress, list) and len(progress) == 2):
        return ClassifyResult("missing_progress", "missing or invalid _checkpoint.progress")

    done, total = progress[0], progress[1]
    if not isinstance(done, int) or not isinstance(total, int) or total <= 0:
        return ClassifyResult("invalid_progress", "invalid progress counters")

    records = ckpt.get("records")
    if not isinstance(records, list):
        return ClassifyResult("missing_records", "missing _checkpoint.records")

    scores = gr.get("scores")
    if not isinstance(scores, dict):
        return ClassifyResult("missing_global_scores", "missing _checkpoint.global_record.scores")

    ds = scores.get("score_composed")
    rc = scores.get("score_route")
    if ds is None or rc is None:
        return ClassifyResult("missing_global_scores", "global scores missing score_composed or score_route")

    try:
        ds_f = float(ds)
        rc_f = float(rc)
    except Exception:
        return ClassifyResult("invalid_global_scores", "global scores not numeric")

    if done < total:
        return ClassifyResult("partial_run", f"progress {done}/{total}")

    if len(records) == 0:
        return ClassifyResult("empty_shell", "records is empty")

    if ds_f == 0.0 and rc_f == 0.0:
        return ClassifyResult("all_zero_scores", "global score_composed and score_route are both 0")

    return ClassifyResult("complete", "ok")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Non-destructively move incomplete/corrupted Interfuser JSON results to a _trash_incomplete folder. "
            "This keeps only complete results in place for RQ3 aggregation."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(_repo_root() / "output" / "interfuser" / "with_processor"),
        help="Directory containing Interfuser with_processor JSON results.",
    )
    parser.add_argument(
        "--trash-root",
        type=str,
        default="",
        help=(
            "Trash root directory. Default: <input-dir>/_trash_incomplete/<timestamp>. "
            "If provided, files will be moved under this directory."
        ),
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        default="",
        help="Optional timestamp for the trash folder (format: YYYYmmdd_HHMMSS).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print planned moves; do not move files.",
    )

    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input dir does not exist: {input_dir}")

    ts = args.timestamp.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.trash_root.strip():
        trash_dir = Path(args.trash_root).resolve()
    else:
        trash_dir = input_dir / "_trash_incomplete" / ts

    moved = 0
    kept = 0

    files = sorted(input_dir.glob("*.json"))
    if not files:
        print(f"No JSON files found in {input_dir}")
        return 0

    for fp in files:
        res = _classify_result(fp)
        if res.category == "complete":
            kept += 1
            print(f"KEPT complete {fp.name}")
            continue

        _ensure_dir(trash_dir)
        dst = trash_dir / fp.name
        moved += 1
        print(f"MOVED {res.category} {fp.name} -> {dst}")
        if not args.dry_run:
            shutil.move(str(fp), str(dst))

    print(f"Moved {moved} files to {trash_dir}")
    print(f"Kept {kept} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
