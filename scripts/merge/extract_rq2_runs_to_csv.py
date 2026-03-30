#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
from typing import Dict, List


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def is_primary_summary(path: Path) -> bool:
    name = path.name
    if not name.startswith("summary_") or not name.endswith(".csv"):
        return False
    if "__main.csv" in name or "__komanda.csv" in name:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect RQ2 merged summary_*.csv files into one normalized CSV.")
    parser.add_argument("--input-root", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    args = parser.parse_args()

    input_root = args.input_root.resolve()
    rows: List[Dict[str, str]] = []
    for summary in sorted(p for p in input_root.rglob("summary_*.csv") if is_primary_summary(p)):
        rel = summary.relative_to(input_root).as_posix()
        pipeline = summary.parent.name
        for r in load_csv(summary):
            out = dict(r)
            out["summary_path"] = rel
            out["pipeline"] = pipeline
            rows.append(out)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        with args.output_csv.open("w", encoding="utf-8", newline="") as f:
            f.write("summary_path,pipeline\n")
        print(f"Wrote empty CSV: {args.output_csv}")
        return

    keys: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)

    with args.output_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
