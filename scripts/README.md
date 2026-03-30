# Scripts

- `ingest/`: pull raw sources and collect host metadata.
- `data/`: prepare KITTI/CH2 enhanced combo inputs under `data/`.
- `run/`: unified experiment entry points.
- `merge/`: aggregate raw outputs into stable tables/figures inputs.
- `plot/`: plotting and table formatting helpers.

Notable merge helpers:

- `merge/extract_rq1_runs_to_csv.py`
- `merge/extract_rq2_runs_to_csv.py`
- `merge/extract_rq3_native_json_to_csv.py`

## Run Examples

```bash
bash scripts/data/prepare_augmented_inputs.sh --task all
bash scripts/data/prepare_augmented_inputs.sh --task ch2 --segments 1,2,3,4,5,6
```

```bash
bash scripts/run/run_unified.sh rq1
bash scripts/run/run_unified.sh rq2
bash scripts/run/run_unified.sh rq3
bash scripts/run/run_unified.sh all
```

```bash
bash scripts/run/run_rq1_kitti.sh
bash scripts/run/run_rq2_udacity.sh
bash scripts/run/run_rq3_carla.sh
```

```bash
# Integrated profiles
bash scripts/run/run_rq1_kitti.sh --profile paper-kitti-main -- --kitti-root ./data/kitti --virconv-root ./data/virconv --did-m3d-root ./data/did_m3d --sources combo,objects
bash scripts/run/run_rq2_udacity.sh --profile paper-ch2-main -- --ch2-root ./data/ch2 --weights-root ./data/community-models --pipelines all --segments 1,2,3,4,5,6 --resume
bash scripts/run/run_rq3_carla.sh --profile paper-carla-summary
```

```bash
# End-to-end wrapper with explicit profiles
bash scripts/run/reproduce_main_results.sh \
  --rq1-profile paper-kitti-main \
  --rq2-profile paper-ch2-main \
  --rq3-profile paper-carla-native

# End-to-end with data preparation first
bash scripts/run/reproduce_main_results.sh --prepare-data
```
