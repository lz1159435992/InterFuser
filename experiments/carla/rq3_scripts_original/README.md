# RQ3 Original Extraction Scripts

This folder contains the original RQ3 table-extraction scripts used for paper reporting.

## Main Script

- `extract_rq3_tables.py`
  - Prints LaTeX-ready rows for:
    - simulator summary rows
    - route-level MR violation rows
    - native-enhancement suite summaries

## Recommended Data Layout

Use integrated paths under this repository:

- InterFuser baseline + with-processor:
  - `results/raw/rq3/interfuser/interfuser_town05_result.json`
  - `results/raw/rq3/interfuser/interfuser_42routes_result.json`
  - `results/raw/rq3/interfuser/with_processor/*.json`
- InterFuser native variants:
  - `results/raw/rq3/native_json/*.json`
- LMDrive native sweep:
  - `results/raw/rq3/lmdrive/native_sweep/fullcover_native_20260320/*.json`

## Usage

From repository root:

```bash
python experiments/carla/rq3_scripts_original/extract_rq3_tables.py --section all --out-dir results/raw/rq3
```

Useful variants:

```bash
python experiments/carla/rq3_scripts_original/extract_rq3_tables.py --section simulator --out-dir results/raw/rq3
python experiments/carla/rq3_scripts_original/extract_rq3_tables.py --section violations --out-dir results/raw/rq3
python experiments/carla/rq3_scripts_original/extract_rq3_tables.py --section native --out-dir results/raw/rq3
```

Optional path overrides:

- `--interfuser-native-dir`
- `--lmdrive-native-dir`

