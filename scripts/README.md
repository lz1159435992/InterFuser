# Scripts

- `ingest/`: synchronize local mirrored sources into this repository.
- `data/`: prepare KITTI/CH2 enhanced combo inputs under `data/`.
- `run/`: unified experiment entry points.
- `merge/`: aggregate raw outputs into stable tables/figures inputs.
- `plot/`: plotting and table formatting helpers.

Code sync helpers:

- `ingest/sync_open_source_from_local.sh`: sync full InterFuser and LMDrive open-source trees from local mirror into `third_party/`.
- `ingest/sync_kitti_udacity_from_local.sh`: sync KITTI/Udacity scripts from local mirrors into publication-friendly paths (`experiments/kitti/pipeline`, `experiments/udacity/pipeline`, `experiments/common/image_quality_validation`, `third_party/process_methods`).

Notable merge helpers:

- `merge/extract_rq1_runs_to_csv.py`
- `merge/extract_rq2_runs_to_csv.py`
- `merge/extract_rq3_native_json_to_csv.py`

## Environment Quick Start

```bash
# Create project environments (run at repository root)
conda env create -f environment/intuitiontester-rq1-quality.yml
conda env create -f environment/intuitiontester-rq1-3d-eval.yml
conda env create -f environment/intuitiontester-rq2-orchestrator.yml
conda env create -f environment/intuitiontester-rq3-interfuser.yml
conda env create -f environment/intuitiontester-rq3-lmdrive.yml
```

```bash
# RQ1: split interpreters
CONDA_BASE=$(conda info --base)
bash scripts/run/run_rq1_kitti.sh --profile paper-kitti-main -- \
  --kitti-root ./data/kitti \
  --virconv-root ./data/virconv \
  --did-m3d-root ./data/did_m3d \
  --quality-python "${CONDA_BASE}/envs/intuitiontester-rq1-quality/bin/python" \
  --virconv-python "${CONDA_BASE}/envs/intuitiontester-rq1-3d-eval/bin/python"
```

```bash
# RQ2: host orchestration scripts (core eval still in Docker)
conda activate intuitiontester-rq2-orchestrator
bash scripts/run/run_rq2_udacity.sh --profile paper-ch2-main -- --ch2-root ./data/ch2 --weights-root ./data/community-models
```

```bash
# RQ3: native CARLA chains
conda activate intuitiontester-rq3-interfuser
bash scripts/run/run_rq3_carla.sh --profile paper-carla-native

conda activate intuitiontester-rq3-lmdrive
bash scripts/run/run_rq3_carla.sh --profile paper-carla-lmdrive-native -- langauto_tiny none
```

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
bash scripts/run/run_image_quality_validation.sh niqe_brisque --img-dir /path/to/images
```

```bash
# Integrated profiles
bash scripts/run/run_rq1_kitti.sh --profile paper-kitti-main -- --kitti-root ./data/kitti --virconv-root ./data/virconv --did-m3d-root ./data/did_m3d --sources combo,objects
bash scripts/run/run_rq2_udacity.sh --profile paper-ch2-main -- --ch2-root ./data/ch2 --weights-root ./data/community-models --pipelines all --segments 1,2,3,4,5,6 --resume
bash scripts/run/run_rq3_carla.sh --profile paper-carla-summary

# RQ3 paper-table extraction from integrated raw results
python experiments/carla/rq3_scripts_original/extract_rq3_tables.py --section native --out-dir results/raw/rq3
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

```bash
# Build a release-ready code bundle for Zenodo (code/config/results-processed only)
bash scripts/release/build_zenodo_bundle.sh
```
