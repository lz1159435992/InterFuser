# Third-party Dependencies

Record external repositories and models used by the artifact:

| Name | URL | Commit/Version | License | Used In |
|---|---|---|---|---|
| InterFuser-related upstream scripts | Local mirrored sources (host114/172/210) | mixed | upstream-defined | `experiments/*/upstream_hosts` |
| CARLA Leaderboard result JSON schema | CARLA Leaderboard | mixed | upstream-defined | `experiments/carla/upstream_hosts/host210/results_native` |
| SRGAN / SwinIR / RIFE wrappers | upstream implementations | mixed | upstream-defined | `experiments/kitti/upstream_hosts`, `experiments/udacity/upstream_hosts` |

Notes:

- Files under `experiments/*/upstream_hosts` preserve upstream content for traceability.
- Verify and keep original licenses when redistributing upstream-derived code.
- Place enhancement dependencies under `third_party/process_mothod/` for the data
  preparation script:
  `bash scripts/data/prepare_augmented_inputs.sh`.
