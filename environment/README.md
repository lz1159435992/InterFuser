# Python Environment Guide

This repository provides ready-to-create conda environments with project-oriented names.

## Environment Files

- `intuitiontester-rq1-quality.yml`
  - RQ1 quality metrics (NIQE/BRISQUE/PSNR/SSIM/LPIPS) and appendix image-quality scripts.
- `intuitiontester-rq1-3d-eval.yml`
  - RQ1 VirConv + DID-M3D execution chain.
- `intuitiontester-rq2-orchestrator.yml`
  - RQ2 host-side orchestration scripts for Udacity CH2 pipeline.
- `intuitiontester-rq3-interfuser.yml`
  - RQ3 InterFuser native CARLA chain.
- `intuitiontester-rq3-lmdrive.yml`
  - RQ3 LMDrive native CARLA chain.

Lock files for strict reproducibility:

- `intuitiontester-rq3-interfuser-lock.yml`
- `intuitiontester-rq3-lmdrive-lock.yml`
- `intuitiontester-rq3-interfuser-lock-requirements.txt`
- `intuitiontester-rq3-lmdrive-lock-requirements.txt`

## Create All Environments

Run from repository root:

```bash
conda env create -f environment/intuitiontester-rq1-quality.yml
conda env create -f environment/intuitiontester-rq1-3d-eval.yml
conda env create -f environment/intuitiontester-rq2-orchestrator.yml
conda env create -f environment/intuitiontester-rq3-interfuser.yml
conda env create -f environment/intuitiontester-rq3-lmdrive.yml
```

## Interpreter Mapping in Scripts

RQ1 supports split interpreters:

- `--quality-python` -> `intuitiontester-rq1-quality`
- `--virconv-python` -> `intuitiontester-rq1-3d-eval`

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

RQ3 examples:

```bash
conda activate intuitiontester-rq3-interfuser
bash scripts/run/run_rq3_carla.sh --profile paper-carla-native -- town05 none

conda activate intuitiontester-rq3-lmdrive
bash scripts/run/run_rq3_carla.sh --profile paper-carla-lmdrive-native -- langauto_tiny none
```

## Notes

- RQ2 evaluation is docker-based (`experiments/udacity/pipeline/udacity/docker/offline-eval`), while `intuitiontester-rq2-orchestrator` is used for host-side orchestration and preprocessing helpers.
- For KITTI native evaluation, compile once before full RQ1 rerun:

```bash
make -C experiments/kitti/support_files/kitti_native_evaluation
```
