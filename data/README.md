# Data Layout

Place datasets and model assets under this folder before running rerun profiles.

## Required for RQ1 (KITTI)

- Raw KITTI root: `data/kitti/`
- Expected minimum structure:

```text
data/kitti/
  object_0/training/image_2/
  object_2/training/image_2/
  object_3/training/image_2/
```

- Generated combo outputs (by script): `data/kitti/combo/<pipeline>/training/image_2/`

## Required for RQ2 (Udacity CH2)

- Raw CH2 root: `data/ch2/`
- Expected minimum structure:

```text
data/ch2/
  input/
    HMB_1_old/
    HMB_1_steering.csv
    ...
```

- Generated combo outputs (by script): `data/ch2/input_combo/<pipeline>/...`

## Optional runtime dependencies

- Community control-model weights: `data/community-models/`
- VirConv root (for RQ1 full run): `data/virconv/`
- DID-M3D root (for RQ1 full run): `data/did_m3d/`
- Enhancement methods root: `third_party/process_mothod/`

## Prepare augmented inputs

```bash
bash scripts/data/prepare_augmented_inputs.sh --task all
```
