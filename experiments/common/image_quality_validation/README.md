# Image Quality Validation (Appendix)

This folder contains scripts used for image-quality validation experiments reported in the appendix.

## Source Mapping

- Upstream mirror source: `InterFuser/tools/py`
- 2026-focused script snapshot:
  - `tools_py_2026/`

## Included 2026 Scripts

- `gen_kitti_combo_dataset.py`
- `gen_kitti_x2_baseline.py`
- `niqe_brisque_main.py`
- `run_kitti_eval.py`
- `run_kitti_eval_gpu.py`
- `ssim_lpips.py`
- `udacity_sort.py`

## Notes

- Scripts are preserved from source mirrors for traceability.
- Some scripts write outputs into sibling `output/` folders; use controlled paths when running in shared environments.
