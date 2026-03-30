# Data Access and Storage Policy

This artifact repository does not commit large datasets or model checkpoints.

## What Is Included

- scripts
- evaluation wrappers
- selected result artifacts (CSV/JSON summaries)
- metadata and mapping docs

## What Is Excluded

- full raw datasets (KITTI, Udacity CH2, CARLA recordings)
- large model weights
- heavyweight intermediate caches

## Known Remote Dataset Locations

See:

- `../IntuitionTester_sources/DATASET_LOCATIONS.md` (outside this repo root)

## Recommended Setup

1. Put datasets/checkpoints in external storage.
2. Prefer repo-relative paths via command-line flags (`--kitti-root`, `--ch2-root`, etc.), e.g., `./data/kitti`, `./data/ch2`.
3. Avoid hardcoding machine-local paths in committed scripts.

## Reproducibility Note

For each run, capture:

- dataset path (or identifier)
- model/checkpoint path and checksum
- script command line
- git commit hash
- hardware/runtime metadata
