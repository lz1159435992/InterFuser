# Udacity Pipeline Scripts

This folder stores upstream-derived Udacity CH2 pipeline scripts.

## Layout

- `udacity/`: synchronized from `InterFuser/udacity`
  - includes offline eval scripts and docker-related configs
  - excludes large output folders during sync (e.g., `out_eval/`)

## Main Use Cases

- offline steering-model evaluation
- dockerized evaluation workflow
- generation/evaluation orchestration for RQ2

## Sync

Use:

```bash
bash scripts/ingest/sync_kitti_udacity_from_local.sh
```
