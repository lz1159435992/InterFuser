# RQ3 CARLA

This folder hosts RQ3 entry adapters and table-extraction scripts.

Layout:

- `pipeline/run_interfuser_native.sh`
  - Wrapper to `third_party/interfuser_project/carla_native_enhancement/run_evaluation_native.sh`.
- `pipeline/run_lmdrive_native.sh`
  - Wrapper to `third_party/lmdrive/leaderboard/scripts/run_evaluation_lmdrive_native.sh`.
- `pipeline/run_lmdrive_native_sweep_parallel.sh`
  - Wrapper to `third_party/lmdrive/leaderboard/scripts/run_evaluation_lmdrive_native_sweep_parallel.sh`.
- `rq3_scripts_original/`
  - Original RQ3 extraction scripts for paper tables.
  - Recommended command:
    `python experiments/carla/rq3_scripts_original/extract_rq3_tables.py --section native --out-dir results/raw/rq3`

Notes:

- InterFuser and LMDrive complete codebases are intentionally placed under `third_party/`.
- `experiments/carla` keeps unified wrappers so RQ3 can be launched from one stable entry.
- If `experiments/carla/carla_native_enhancement/` exists, treat it as a non-authoritative mirror copy; the canonical runnable path is `third_party/interfuser_project/carla_native_enhancement/`.
- Integrated RQ3 raw result layout:
  - `results/raw/rq3/interfuser/` (baseline + with_processor)
  - `results/raw/rq3/native_json/` (InterFuser native variants)
  - `results/raw/rq3/lmdrive/native_sweep/fullcover_native_20260320/` (LMDrive native sweep)
