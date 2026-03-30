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
    kitti/                   # RQ1 scripts and adapters
    udacity/                 # RQ2 scripts and adapters
    carla/                   # RQ3 scripts and adapters
  configs/
    kitti/
    udacity/
    carla/
  scripts/
    ingest/                  # Pull/record from remote hosts
    data/                    # Dataset enhancement/combo preparation
    run/                     # Unified reproduction entry points
    merge/                   # Cross-host result merging
    plot/                    # Figure/table generation helpers
  results/
    raw/                     # Immutable per-run outputs
    processed/               # Aggregated csv/json
    tables/                  # Paper table artifacts
    figures/                 # Paper figure artifacts
  provenance/                # Commit/env/hardware metadata per run
  docs/
    INTEGRATION_PLAN.md
    MERGE_MAP.md
    EXPERIMENT_MATRIX.md
  environment/
    environment.yml
    requirements.txt
```

## Open-Source Essentials

- Citation metadata: `CITATION.cff`.
- Contribution guide: `CONTRIBUTING.md`.
- Data policy: `docs/DATA_ACCESS.md`.

## Source Mirrors (Read-only)

Raw remote snapshots are kept outside this repo under:

`../IntuitionTester_sources`

Do not directly edit mirrored files. Integrate by copying/selecting into this repository and recording decisions in `docs/MERGE_MAP.md`.

## Integration Workflow

1. Pull all three remote sources into `IntuitionTester_sources`.
2. Export provenance metadata from each host (`git rev`, env, hardware).
3. Map files to RQ1/RQ2/RQ3 folders in this repo.
4. Standardize configs and run entries under `configs/` and `scripts/run/`.
5. Merge raw outputs into unified metrics under `results/processed/`.
6. Regenerate paper tables/figures under `results/tables/` and `results/figures/`.
7. Fill `docs/EXPERIMENT_MATRIX.md` to map each table/figure back to scripts and data.

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
```

Profile aliases (for backward compatibility):

- `paper-kitti-main` = `upstream-host172-cpu`
- `paper-kitti-gpu` = `upstream-host172-gpu`
- `paper-ch2-main` = `upstream-host172`
- `paper-ch2-variant` = `upstream-host114`
- `paper-carla-native` = `upstream-host210-native`
- `paper-carla-summary` = `upstream-host210-summary`

Required data paths for rerun profiles:

- RQ1 integrated profile: pass `--kitti-root`, and for default full-run also pass `--virconv-root` and `--did-m3d-root`.
- RQ2 integrated profile: pass both `--ch2-root` and `--weights-root`, and prepare `input_combo` via `scripts/data/prepare_augmented_inputs.sh`.
- If omitted, wrappers look for local placeholders under `data/` and fail fast with guidance.

## Platform Notes

- `scripts/run/*.sh` are Bash scripts; run them in Linux/WSL/Git-Bash environments.
- On Windows PowerShell, you can call Python entry scripts directly under `scripts/merge/` and `experiments/*`.

## Notes

- Large datasets and checkpoints should not be committed. Provide download and checksum instructions in subfolder README files.
- Keep `results/raw` append-only once experiments are completed.
- Every run should write a `meta.json` with commit hash, config hash, seed, host, and timestamp.
- Upstream scripts under `experiments/*/upstream_hosts` are included intentionally for full public release and provenance.
- A richer release-ready sample artifact set is provided under `results/processed/reference_bundle/`.
