# Integration Plan

## Goal

Integrate three remote repositories into one paper-ready open-source project with reproducible mapping to:

- RQ1: KITTI detection consistency.
- RQ2: Udacity CH2 control consistency.
- RQ3: CARLA closed-loop system consistency.

## Inputs

- `host-a` (Udacity-related source)
- `host-b` (KITTI/Udacity source)
- `host-c` (CARLA-related source)

## Phase A: Mirror (No edits)

1. Pull each remote source to `../IntuitionTester_sources`.
2. Export metadata from each host:
- git branch and commit
- dependency lock (`pip freeze` or conda env)
- GPU and driver info
- key run commands used for paper results
3. Keep mirrors read-only.

## Phase B: Semantic Merge by Paper RQs

1. Place selected scripts into:
- `experiments/kitti`
- `experiments/udacity`
- `experiments/carla`
2. Normalize command-line arguments and config format under `configs/`.
3. Move common reusable logic to shared modules (if needed).
4. Record all source-to-target decisions in `docs/MERGE_MAP.md`.

## Phase C: Reproducibility Layer

1. Add unified run entries:
- `scripts/run/reproduce_main_results.sh`
- `scripts/run/run_rq1_kitti.sh`
- `scripts/run/run_rq2_udacity.sh`
- `scripts/run/run_rq3_carla.sh`
2. Ensure each run writes:
- `results/raw/<rq>/<run_id>/metrics.*`
- `results/raw/<rq>/<run_id>/meta.json`
3. Aggregate with `scripts/merge/merge_results.py`.
4. Export final paper-ready tables/figures to `results/tables` and `results/figures`.

## Definition of Done

- Each main table in `eval.tex` has a script/data path mapping in `docs/EXPERIMENT_MATRIX.md`.
- One command (or short command list) can reproduce key numbers from clean environment instructions.
- No hidden manual spreadsheet steps for final metrics.
