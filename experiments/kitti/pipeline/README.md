# KITTI Pipeline Scripts

This folder stores upstream-derived KITTI generation/evaluation scripts and support files.

## Layout

- `tools_py/`: scripts synchronized from `InterFuser/tools/py`
- `support_files/`: synchronized from `InterFuser/kitti_test`

## Main Use Cases

- generate enhanced KITTI variants (SR/DN/FI/compositions)
- run image-quality metrics (PSNR/SSIM/LPIPS/NIQE/BRISQUE)
- run detector consistency evaluation wrappers

## Sync

Use:

```bash
bash scripts/ingest/sync_kitti_udacity_from_local.sh
```
