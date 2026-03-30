#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List


def collect_csv_files(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.csv") if p.is_file()]

def collect_json_files(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.json") if p.is_file()]


def summarize_csv(path: Path) -> Dict[str, str]:
    # Generic summary for tracking integration progress.
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        col_count = 0
        row_count = 0
        for i, row in enumerate(reader):
            if i == 0:
                col_count = len(row)
            else:
                row_count += 1
    return {
        "relative_path": str(path),
        "rows": str(row_count),
        "cols": str(col_count),
    }

def summarize_json(path: Path) -> Dict[str, str]:
    size = path.stat().st_size
    return {
        "relative_path": str(path),
        "size_bytes": str(size),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge and index raw experiment results.")
    parser.add_argument("--input-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()

    input_root = args.input_root.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    csv_files = collect_csv_files(input_root)
    summaries: List[Dict[str, str]] = []
    for f in csv_files:
        rel = f.relative_to(input_root)
        item = summarize_csv(f)
        item["relative_path"] = str(rel).replace("\\", "/")
        summaries.append(item)

    index_csv = output_root / "merged_csv_index.csv"
    with index_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["relative_path", "rows", "cols"])
        writer.writeheader()
        writer.writerows(summaries)

    index_json = output_root / "merged_csv_index.json"
    with index_json.open("w", encoding="utf-8") as f:
        json.dump({"count": len(summaries), "files": summaries}, f, indent=2)

    json_files = collect_json_files(input_root)
    json_summaries: List[Dict[str, str]] = []
    for f in json_files:
        rel = f.relative_to(input_root)
        item = summarize_json(f)
        item["relative_path"] = str(rel).replace("\\", "/")
        json_summaries.append(item)

    json_index_csv = output_root / "merged_json_index.csv"
    with json_index_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["relative_path", "size_bytes"])
        writer.writeheader()
        writer.writerows(json_summaries)

    json_index = output_root / "merged_json_index.json"
    with json_index.open("w", encoding="utf-8") as f:
        json.dump({"count": len(json_summaries), "files": json_summaries}, f, indent=2)

    print(f"Indexed {len(summaries)} csv files.")
    print(f"Wrote: {index_csv}")
    print(f"Wrote: {index_json}")
    print(f"Indexed {len(json_summaries)} json files.")
    print(f"Wrote: {json_index_csv}")
    print(f"Wrote: {json_index}")


if __name__ == "__main__":
    main()
