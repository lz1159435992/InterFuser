# Merge Map

Use this file to track how each selected source file is integrated.

## Legend

- `KEEP`: copied with minimal path adaptation.
- `ADAPT`: copied with behavior-preserving edits.
- `REPLACE`: replaced by a better/cleaner equivalent.
- `DROP`: intentionally excluded.

## Mapping Table

| Source Host | Source Path | Target Path | RQ | Decision | Rationale | Owner | Date |
|---|---|---|---|---|---|---|---|
| host-a | <remote_a_root>/udacity/tools/run_combo_eval.py | experiments/udacity/upstream_hosts/host114/tools/run_combo_eval.py | RQ2 | KEEP | host-a variant retained for provenance comparison with host-b variant | Codex | 2026-03-31 |
| host-a | <remote_a_root>/udacity/docker/offline-eval/{offline_eval.py,batch_eval.py,Dockerfile} | experiments/udacity/upstream_hosts/host114/docker_offline_eval/ | RQ2 | KEEP | Docker evaluator stack captured as host-specific baseline | Codex | 2026-03-31 |
| host-b | <remote_b_root>/tools/py/{run_kitti_eval.py,run_kitti_eval_gpu.py,gen_kitti_combo_dataset.py,...} | experiments/kitti/upstream_hosts/host172/tools_py/ | RQ1 | KEEP | Primary KITTI orchestration and metric scripts for paper experiments | Codex | 2026-03-31 |
| host-b | <remote_b_root>/kitti_test/did_m3d/tools/eval.py | experiments/kitti/upstream_hosts/host172/did_m3d_tools/eval.py | RQ1 | KEEP | Detector-side evaluation entry retained for traceability | Codex | 2026-03-31 |
| host-b | <remote_b_root>/udacity/tools/{run_combo_eval.py,gen_combo_dataset.py,run_full_offline_experiments.sh,run_full_offline_generate_only.sh} | experiments/udacity/upstream_hosts/host172/tools/ | RQ2 | KEEP | Main Udacity orchestration scripts used for matrix runs | Codex | 2026-03-31 |
| host-b | <remote_b_root>/udacity/docker/offline-eval/{offline_eval.py,batch_eval.py,Dockerfile} | experiments/udacity/upstream_hosts/host172/docker_offline_eval/ | RQ2 | KEEP | Main offline evaluator implementation | Codex | 2026-03-31 |
| host-c | <remote_c_root>/carla_native_enhancement/* | experiments/carla/upstream_hosts/host210/carla_native_enhancement/ | RQ3 | KEEP | Core native CARLA configuration and launcher scripts | Codex | 2026-03-31 |
| host-c | <remote_c_root>/results/native/*.json | experiments/carla/upstream_hosts/host210/results_native/ | RQ3 | KEEP | Route-level result artifacts aligned with paper tables | Codex | 2026-03-31 |
| host-c | <remote_c_root>/data/eval_native/*/evaluation_metadata.json | experiments/carla/upstream_hosts/host210/eval_metadata_samples/ | RQ3 | KEEP | Metadata schema examples for run provenance fields | Codex | 2026-03-31 |

## Conflict Notes

Document function-level conflicts and which version is retained.

1. TODO
