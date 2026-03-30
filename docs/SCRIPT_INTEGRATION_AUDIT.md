# Script Integration Audit

This document records the script-level analysis from selected mirrors and the initial integration placement in `IntuitionTester`.

## Source Mirrors Used

- `IntuitionTester_sources/host_a_udacity_selected`
- `IntuitionTester_sources/host_b_interfuser_selected`
- `IntuitionTester_sources/host_c_carla_selected`

Publication policy:

- Upstream-integrated scripts are kept public in `experiments/*/upstream_hosts` for full traceability.

## RQ1 (KITTI) Integration

Integrated to:

- `experiments/kitti/upstream_hosts/host172/tools_py/`
- `experiments/kitti/upstream_hosts/host172/did_m3d_tools/`

Key scripts read and their role:

1. `run_kitti_eval.py`
- Purpose: main KITTI quality/eval orchestrator for selected datasets.
- Inputs: `--kitti-root`, `--sources`, optional explicit dataset paths.
- Outputs: per-dataset evaluation outputs under a configurable output root.
- Notes: includes pipeline list for DN/SR/FI permutations and GT selection logic for PSNR.

2. `run_kitti_eval_gpu.py`
- Purpose: GPU-accelerated quality metric evaluation.
- Inputs: similar dataset selectors; uses GPU metrics (LPIPS/NIQE/BRISQUE) and CPU PSNR/SSIM.
- Outputs: summary CSV/JSON-like records.
- Notes: requires `torch`, `lpips`, `pyiqa`, `piq`.

3. `gen_kitti_combo_dataset.py`
- Purpose: generate combo datasets for DN/SR/FI permutation pipelines.
- Inputs: left/right source objects, process-method roots, model paths for SRGAN/SwinIR/RIFE.
- Outputs: generated images under `<output-root>/<pipeline>/training/image_2`.
- Notes: central pre-processing generator for RQ1 combos.

4. `gen_kitti_x2_baseline.py`, `ssim_lpips.py`, `niqe_brisque.py`, `niqe_brisque_main.py`
- Purpose: baseline generation and quality metric helpers.

5. `did_m3d/tools/eval.py`
- Purpose: detector-side evaluation hook for DID-M3D branch.

## RQ2 (Udacity) Integration

Integrated to:

- `experiments/udacity/upstream_hosts/host172/tools/`
- `experiments/udacity/upstream_hosts/host172/docker_offline_eval/`
- `experiments/udacity/upstream_hosts/host114/tools/`
- `experiments/udacity/upstream_hosts/host114/docker_offline_eval/`

Key scripts read and their role:

1. `run_combo_eval.py` (host172 and host114 variants)
- Purpose: orchestrates full pipeline matrix (`GN8`, `GN16`, single ops, pair/triple compositions).
- Inputs: segments, stride/start-index/max-frames, docker image, paths for CH2 input and weights.
- Outputs: per-pipeline summary CSVs, optional prediction CSVs.
- Notes: dispatches two model groups (`rambo,chauffeur,autumn` and `komanda`) and merges summaries.

2. `run_full_offline_experiments.sh`
- Purpose: one-shot full matrix execution wrapper.
- Behavior: invokes `run_combo_eval.py --pipelines all --segments 1..6 --resume`.

3. `run_full_offline_generate_only.sh` (host172)
- Purpose: generate-only variant (`--skip-eval`) for precomputing transformed inputs.

4. `offline_eval.py` + `batch_eval.py` (docker/offline-eval)
- Purpose: model inference + RMSE evaluation on CH2 frame streams.
- Outputs: mode-level summary CSV and optional per-frame prediction CSV.
- Notes: compatibility layer includes legacy Keras Merge support for older models.

## RQ3 (CARLA) Integration

Integrated to:

- `experiments/carla/upstream_hosts/host210/carla_native_enhancement/`
- `experiments/carla/upstream_hosts/host210/results_native/`
- `experiments/carla/upstream_hosts/host210/eval_metadata_samples/`

Key scripts read and their role:

1. `carla_native_enhancement/run_evaluation_native.sh`
- Purpose: primary CARLA native-enhancement runner.
- Inputs: eval type (`town05`/`42routes`), native config tokens, GPU/env settings.
- Behavior: swaps agent implementation, configures ports/CARLA env, launches leaderboard evaluator.
- Outputs: checkpoints under `results/native/*.json` and metadata under `data/eval_native/...`.

2. `carla_native_enhancement/native_config_parser.py`
- Purpose: canonical parser for native config tokens.
- Supported tokens: `none`, `high_fps`, `high_res`, `no_noise`, `gauss8`, `gauss16`.
- Derived parameters: frame-rate, fixed-delta, sensor tick, camera resolution, post-process/noise settings.

3. `carla_native_enhancement/interfuser_agent_native.py`
- Purpose: native-enhancement-aware Interfuser agent.
- Behavior: reads parsed config and adjusts sensor definitions + world interaction.

4. `carla_native_enhancement/run_single_config.sh`, `run_remaining_7_configs.sh`
- Purpose: convenience wrappers for single/batch configuration experiments.

5. `results_native/*.json` + `eval_metadata_samples/*.json`
- Purpose: representative route-level outputs and metadata for reproducibility mapping.

## Immediate Next Unification Steps

1. Create thin adapters in:
- `experiments/kitti/adapter_rq1.py`
- `experiments/udacity/adapter_rq2.py`
- `experiments/carla/adapter_rq3.py`

2. Normalize outputs to:
- `results/raw/rq1/<run_id>/`
- `results/raw/rq2/<run_id>/`
- `results/raw/rq3/<run_id>/`

3. Wire adapters into:
- `scripts/run/run_rq1_kitti.sh`
- `scripts/run/run_rq2_udacity.sh`
- `scripts/run/run_rq3_carla.sh`
