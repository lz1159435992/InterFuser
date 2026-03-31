# RQ1 KITTI

This folder contains runnable scripts/adapters for detection consistency experiments (RQ1).

Key components:

- `pipeline/tools_py/gen_kitti_combo_dataset.py`
  - Generate enhanced KITTI combo inputs (SR/DN/FI pipelines).
- `pipeline/tools_py/run_kitti_eval.py`
  - Integrated RQ1 evaluator (quality + VirConv + DID-M3D).
- `pipeline/tools_py/run_kitti_eval_gpu.py`
  - GPU-oriented RQ1 variant.
- `pipeline/tools_py/v100/tools/py/pkl_to_dir.py`
  - Required VirConv result conversion helper for native eval.
- `support_files/kitti_native_evaluation/`
  - KITTI native detection evaluator (compile before full rerun).
- `support_files/did_m3d/`
  - DID-M3D evaluation code/assets used by RQ1.
