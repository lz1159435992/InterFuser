# Remote Source Map

This map links remote hosts to local selected mirrors and integration targets.

## Hosts and Roles

1. `host-a`
- Remote root: `<remote_a_root>/udacity/`
- Role: Udacity offline-eval stack and backup orchestration scripts for RQ2.
- Selected mirror: `IntuitionTester_sources/host_a_udacity_selected/`

2. `host-b`
- Remote root: `<remote_b_root>/InterFuser/`
- Role: Main KITTI (RQ1) and Udacity (RQ2) scripts.
- Selected mirror: `IntuitionTester_sources/host_b_interfuser_selected/`

3. `host-c`
- Remote root: `<remote_c_root>/InterFuser/`
- Role: CARLA native-enhancement scripts and result JSONs for RQ3.
- Selected mirror: `IntuitionTester_sources/host_c_carla_selected/`

## Integrated Targets in This Repo

- RQ1: `experiments/kitti/upstream_hosts/host172/`
- RQ2: `experiments/udacity/upstream_hosts/host172/`, `experiments/udacity/upstream_hosts/host114/`
- RQ3: `experiments/carla/upstream_hosts/host210/`

## Selection Policy Used

Only script/result/config-document types were mirrored from remotes:

- code/scripts: `.py`, `.sh`, `.bash`
- configs/docs: `.yaml`, `.yml`, `.json`, `.jsonl`, `.md`, `.cfg`, `.ini`, `.toml`, `.tex`
- result tables: `.csv`, `.tsv`
- build files: `Dockerfile`, `Makefile`

Large raw datasets were intentionally not mirrored and are tracked separately.
