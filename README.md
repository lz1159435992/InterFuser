# IntuitionTester

This repository is the open-source artifact companion for the paper:

`IntuitionTester: Evaluating the Intuitive Consistency of Autonomous Driving Systems`

It is organized around the three research questions in the paper:

- RQ1 (Perception consistency): KITTI-based detection consistency.
- RQ2 (End-to-end control consistency): Udacity CH2-based control consistency.
- RQ3 (System consistency): CARLA closed-loop route-level consistency.

## Repository Layout

```text
IntuitionTester/
  experiments/
    common/
      image_quality_validation/  # Appendix image-quality validation scripts
    kitti/                   # RQ1 scripts and adapters
    udacity/                 # RQ2 scripts and adapters
    carla/                   # RQ3 scripts and adapters
    .../pipeline/*                  # Self-contained runnable experiment code
  configs/
    kitti/
    udacity/
    carla/
  scripts/
    ingest/                  # Sync from local mirrors
    data/                    # Dataset enhancement/combo preparation
    run/                     # Unified reproduction entry points
    merge/                   # Cross-run result merging
    plot/                    # Figure/table generation helpers
  results/
    raw/                     # Immutable per-run outputs
    processed/               # Aggregated csv/json
    tables/                  # Paper table artifacts
    figures/                 # Paper figure artifacts
  provenance/                # Commit/env/hardware metadata per run
  docs/
    INTEGRATION_PLAN.md
    EXPERIMENT_MATRIX.md
  environment/
    intuitiontester-rq1-quality.yml
    intuitiontester-rq1-3d-eval.yml
    intuitiontester-rq3-interfuser.yml
    intuitiontester-rq3-lmdrive.yml
  third_party/
    interfuser_project/     # Full InterFuser code mirror (code-only)
    lmdrive/                # Full LMDrive code mirror (code-only)
```

## Open-Source Essentials

- Citation metadata: `CITATION.cff`.
- Contribution guide: `CONTRIBUTING.md`.
- Data policy: `docs/DATA_ACCESS.md`.

## Source Mirrors (Read-only)

Raw source snapshots are kept outside this repo under:

`../IntuitionTester_sources`

Do not directly edit mirrored files. Integrate by copying/selecting into this repository and documenting decisions in `docs/INTEGRATION_PLAN.md`.

## Full Code Sync

To sync complete InterFuser/LMDrive code from local mirrors:

```bash
bash scripts/ingest/sync_open_source_from_local.sh
```

Default local source root:

- `../IntuitionTester_sources/carla_source_mirror/`

Synced folders:

- `third_party/interfuser_project/`
- `third_party/lmdrive/`
- `experiments/carla/pipeline/` (thin wrappers for unified RQ3 entry)

Override mirror root if needed:

```bash
INTUITION_TESTER_SOURCES=/abs/path/to/IntuitionTester_sources \
bash scripts/ingest/sync_open_source_from_local.sh
```

To sync KITTI/Udacity generation/evaluation scripts and appendix image-quality scripts:

```bash
INTUITION_TESTER_SOURCES=/abs/path/to/IntuitionTester_sources \
bash scripts/ingest/sync_kitti_udacity_from_local.sh
```

## Reproduction Environments

Project environments (out-of-box):

- `environment/intuitiontester-rq1-quality.yml`
- `environment/intuitiontester-rq1-3d-eval.yml`
- `environment/intuitiontester-rq2-orchestrator.yml`
- `environment/intuitiontester-rq3-interfuser.yml`
- `environment/intuitiontester-rq3-lmdrive.yml`

Lock files (for strict reproducibility):

- `environment/intuitiontester-rq3-interfuser-lock.yml`
- `environment/intuitiontester-rq3-lmdrive-lock.yml`
- `environment/intuitiontester-rq3-interfuser-lock-requirements.txt`
- `environment/intuitiontester-rq3-lmdrive-lock-requirements.txt`

Full setup guide:

- `environment/README.md`

Create envs:

```bash
conda env create -f environment/intuitiontester-rq1-quality.yml
conda env create -f environment/intuitiontester-rq1-3d-eval.yml
conda env create -f environment/intuitiontester-rq2-orchestrator.yml
conda env create -f environment/intuitiontester-rq3-interfuser.yml
conda env create -f environment/intuitiontester-rq3-lmdrive.yml
```

For RQ1 (KITTI), use separate Python envs:

- `intuitiontester-rq1-quality` for NIQE/BRISQUE/PSNR/SSIM/LPIPS quality metrics (`--quality-python`)
- `intuitiontester-rq1-3d-eval` for VirConv + DID-M3D (`--virconv-python` and script runtime python)

For RQ2 (Udacity CH2), use `intuitiontester-rq2-orchestrator` for local orchestration scripts, while the core evaluation still runs in Docker.

Example:

```bash
CONDA_BASE=$(conda info --base)
bash scripts/run/run_rq1_kitti.sh --profile paper-kitti-main -- \
  --kitti-root ./data/kitti \
  --virconv-root ./data/virconv \
  --did-m3d-root ./experiments/kitti/support_files/did_m3d \
  --quality-python "${CONDA_BASE}/envs/intuitiontester-rq1-quality/bin/python" \
  --virconv-python "${CONDA_BASE}/envs/intuitiontester-rq1-3d-eval/bin/python"
```

## Integration Workflow

1. Pull all source mirrors into `IntuitionTester_sources`.
2. Export provenance metadata from each run environment (`git rev`, env, hardware).
3. Map files to RQ1/RQ2/RQ3 folders in this repo.
4. Standardize configs and run entries under `configs/` and `scripts/run/`.
5. Merge raw outputs into unified metrics under `results/processed/`.
6. Regenerate paper tables/figures under `results/tables/` and `results/figures/`.
7. Fill `docs/EXPERIMENT_MATRIX.md` to map each table/figure back to scripts and data.

## Data and Release Strategy

- Use GitHub for code/config/docs and lightweight processed artifacts.
- Use Zenodo for large reproducibility bundles.
- Keep external raw datasets out of the repository unless redistribution is explicitly allowed.
- See:
  - `docs/DATA_MANIFEST.md`
  - `docs/ZENODO_RELEASE_PLAN.md`
  - `docs/KITTI_UDACITY_SCRIPT_MAP.md`

## Quick Start (Planned)

```bash
bash scripts/run/reproduce_main_results.sh
```

Prepare local KITTI/CH2 augmented inputs after downloading raw datasets:

```bash
bash scripts/data/prepare_augmented_inputs.sh --task all
```

Data layout is documented in:

`data/README.md`

Default run mode is rerun-oriented:

```bash
bash scripts/run/reproduce_main_results.sh \
  --rq1-profile paper-kitti-main \
  --rq2-profile paper-ch2-main \
  --rq3-profile paper-carla-native
```

One-command mode (prepare + run):

```bash
bash scripts/run/reproduce_main_results.sh --prepare-data
```

## Run Entry Examples

Unified dispatcher:

```bash
# run default RQ1 entry (calculate_rq1_table_from_csv.py)
bash scripts/run/run_unified.sh rq1

# run default RQ2 entry (calculate_rq2_violations.py)
bash scripts/run/run_unified.sh rq2

# run default RQ3 entry (extract_rq3_tables.py)
bash scripts/run/run_unified.sh rq3

# run all defaults in sequence
bash scripts/run/run_unified.sh all

# run RQ3 integrated native-result summary profile
bash scripts/run/run_unified.sh rq3 --rq3-profile paper-carla-summary
```

Direct per-RQ wrappers:

```bash
# use default script
bash scripts/run/run_rq1_kitti.sh
bash scripts/run/run_rq2_udacity.sh
bash scripts/run/run_rq3_carla.sh
```

Pass extra arguments to the selected profile:

```bash
# RQ1 original script args
bash scripts/run/run_rq1_kitti.sh -- --csv /path/to/data.csv

# RQ2 original script args
bash scripts/run/run_rq2_udacity.sh -- --preds-dir /path/to/preds_run

# RQ3 original extractor args
bash scripts/run/run_rq3_carla.sh -- --section native --path-tol 0 --rc-tol 5 --time-tol 5 --safety-tol 0.1
```

Use profile-based integrated entries:

```bash
# RQ1 integrated evaluator (default full-run)
bash scripts/run/run_rq1_kitti.sh --profile paper-kitti-main -- --kitti-root ./data/kitti --virconv-root ./data/virconv --did-m3d-root ./data/did_m3d --sources combo,objects

# RQ2 integrated evaluator (requires CH2 + docker env, defaults to --skip-gen)
bash scripts/run/run_rq2_udacity.sh --profile paper-ch2-main -- --ch2-root ./data/ch2 --weights-root ./data/community-models --pipelines all --segments 1,2,3,4,5,6 --resume

# RQ3 summarize integrated JSON artifacts
bash scripts/run/run_rq3_carla.sh --profile paper-carla-summary

# RQ3 LMDrive native single run
bash scripts/run/run_rq3_carla.sh --profile paper-carla-lmdrive-native -- langauto_tiny none

# RQ3 LMDrive native sweep (parallel)
bash scripts/run/run_rq3_carla.sh --profile paper-carla-lmdrive-sweep

# RQ3 paper-table extraction (original extractor, aligned to current layout)
python experiments/carla/rq3_scripts_original/extract_rq3_tables.py --section native --out-dir results/raw/rq3
```

Profile aliases (public entry names):

- `paper-kitti-main`
- `paper-kitti-gpu`
- `paper-ch2-main`
- `paper-ch2-variant`
- `paper-carla-native`
- `paper-carla-lmdrive-native`
- `paper-carla-lmdrive-sweep`
- `paper-carla-summary`

Required data paths for rerun profiles:

- RQ1 integrated profile: pass `--kitti-root`, and for default full-run also pass `--virconv-root` and `--did-m3d-root`.
- RQ2 integrated profile: pass both `--ch2-root` and `--weights-root`, and prepare `input_combo` via `scripts/data/prepare_augmented_inputs.sh`.
- If omitted, wrappers look for local placeholders under `data/` and fail fast with guidance.

RQ3 integrated result layout:

- InterFuser baseline + with-processor:
  - `results/raw/rq3/interfuser/interfuser_town05_result.json`
  - `results/raw/rq3/interfuser/interfuser_42routes_result.json`
  - `results/raw/rq3/interfuser/with_processor/*.json`
- InterFuser native (for `paper-carla-summary`):
  - `results/raw/rq3/native_json/*.json`
- LMDrive native sweep:
  - `results/raw/rq3/lmdrive/native_sweep/fullcover_native_20260320/*.json`

## Platform Notes

- `scripts/run/*.sh` are Bash scripts; run them in Linux/WSL/Git-Bash environments.
- On Windows PowerShell, you can call Python entry scripts directly under `scripts/merge/` and `experiments/*`.

## Notes

- Large datasets and checkpoints should not be committed. Provide download and checksum instructions in subfolder README files.
- Keep `results/raw` append-only once experiments are completed.
- Every run should write a `meta.json` with commit hash, config hash, seed, runtime environment, and timestamp.
- This repository is self-contained for code execution; no extra code mirror is required.
- A richer release-ready sample artifact set is provided under `results/processed/reference_bundle/`.
