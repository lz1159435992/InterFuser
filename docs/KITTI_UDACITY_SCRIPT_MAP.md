# KITTI/Udacity Script Integration Map

This file maps source mirror directories to publication-oriented paths in this repository.

## Source Mirror (Local)

- Mirror root: `../IntuitionTester_sources`
- Auto-detected subdirectory should contain:
  - `tools/py`
  - `udacity`
  - `process_mothod` (legacy upstream name)
  - `kitti_test`

## Mapping

| Source | Target | Purpose |
|---|---|---|
| `tools/py` | `experiments/kitti/pipeline/tools_py` | Mixed helper scripts snapshot (KITTI + some legacy CH2 utilities) |
| `tools/py` (files modified in 2026) | `experiments/common/image_quality_validation/tools_py_2026` | Appendix image-quality validation scripts |
| `udacity` | `experiments/udacity/pipeline/udacity` | Udacity offline evaluation scripts + docker configs |
| `kitti_test` | `experiments/kitti/support_files` | KITTI support files for evaluation pipelines |
| `process_mothod` (legacy source name) | `third_party/process_methods` | Enhancement method integrations (SR/FI/DN) |

## Exclusion Policy During Sync

- Exclude large outputs/logs/checkpoints:
  - `out_eval/`, `results/`, `logs/`, `train_log/`
  - `*.pth`, `*.pt`, `*.ckpt`, `*.onnx`, `*.npy`, `*.npz`, archives

## Sync Command

```bash
INTUITION_TESTER_SOURCES=/abs/path/to/IntuitionTester_sources \
bash scripts/ingest/sync_kitti_udacity_from_local.sh
```
