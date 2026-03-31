# Third-party Dependencies

Record external repositories and models used by the artifact:

| Name | URL | Commit/Version | License | Used In |
|---|---|---|---|---|
| InterFuser full project mirror | Local mirror (`IntuitionTester_sources`) | mixed | upstream-defined | `third_party/interfuser_project` |
| LMDrive full project mirror | Local mirror (`IntuitionTester_sources`) | mixed | upstream-defined | `third_party/lmdrive` |
| InterFuser evaluation scripts | Local mirrored sources | mixed | upstream-defined | `third_party/interfuser_project/carla_native_enhancement` |
| CARLA Leaderboard result JSON schema | CARLA Leaderboard | mixed | upstream-defined | `results/raw/rq3/native_json` |
| SRGAN / SwinIR / RIFE wrappers | upstream implementations | mixed | upstream-defined | `third_party/process_methods`, `experiments/kitti/pipeline`, `experiments/udacity/pipeline` |

Notes:

- Full project mirrors are synchronized via `scripts/ingest/sync_open_source_from_local.sh`.
- Verify and keep original licenses when redistributing upstream-derived code.
- Place enhancement dependencies under `third_party/process_mothod/` for the data
  preparation script:
  `bash scripts/data/prepare_augmented_inputs.sh`.
