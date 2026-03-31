# Offline Evaluation Runbook (CH2, JPG + CSV)

This document describes how to run **offline RMSE evaluation** for Udacity CH2 steering models inside a **single Docker image**.

## What you get

- Evaluate **4 models**:
  - `rambo`
  - `chauffeur`
  - `komanda`
  - `autumn`
- On **3 dataset variants** + **2 inserted-only contexts**:
  - `orig`: original frames
  - `interp`: interpolated frames (original + inserted)
  - `interp_only`: inserted-only frames (sequence contains inserted frames only)
  - `interp_only_full`: inserted-only evaluation but model state is driven by the full interpolated sequence
- Outputs are persisted under a host-mounted `/out` directory:
  - Summary CSV per run
  - Per-frame prediction CSVs per model/segment/mode

## CH2 input naming rules (this repo)

All paths below are under:

- `udacity/self-driving-car/datasets/CH2/input/`

For each segment `HMB_n`:

- **Original frames**: `HMB_n_old/`
- **Interpolated frames**: `HMB_n/`

Labels:

- **Original labels**: `HMB_n_steering.csv`
- **Interpolated labels**: `HMB_n_steering_add.csv`
- **Inserted-only labels**: `HMB_n_steering_add2.csv`
  - If `*_add2.csv` is missing, the evaluator will derive inserted-only rows as `(add.csv frame_ids) - (orig.csv frame_ids)` in add.csv order.

## Weights location

Weights are stored under:

- `udacity/self-driving-car/steering-models/community-models/<model>/...`

This setup supports:

- `rambo/weights/{final_model.hdf5,X_train_mean.npy}`
- `chauffeur/weights/{cnn.json,cnn.weights,lstm.json,lstm.weights}`
- `komanda/weights/{komanda.test-subgraph.meta,checkpoint,*.index,*.data-*}`
- `autumn/` (repo already contains):
  - `autumn-cnn-model-tf.meta`
  - `autumn-cnn-weights.ckpt`
  - (LSTM artifacts exist but the original evaluation path used the CNN output `y`)

A manifest of downloaded weights is in:

- `udacity/OFFLINE_EVAL_MODELS.md`

## Docker image

Docker context:

- `udacity/docker/offline-eval/`

Image includes:

- Python 3.7
- TensorFlow 1.15.5
- Keras 2.2.4

Build (run from `udacity/docker/offline-eval/`):

```bash
sudo docker build -t udacity-offline-eval:tf1 .
```

## Full experiment: one-line command

This runs all segments (auto-detected), all 4 models, all modes including both inserted-only contexts, with **stride=1**.
Results are persisted to the mounted output directory (recommended repo-relative path):

- `<repo>/results/raw/rq2/offline_eval`

```bash
sudo docker run --rm \
  -v "$(pwd)/self-driving-car/datasets/CH2:/data/ch2" \
  -v "$(pwd)/self-driving-car/steering-models/community-models:/models/community-models" \
  -v "$(pwd)/../../../results/raw/rq2/offline_eval:/out" \
  udacity-offline-eval:tf1 \
  /app/batch_eval.py \
  --input-root /data/ch2/input \
  --weights-root /models/community-models \
  --models rambo,chauffeur,komanda,autumn \
  --segments auto \
  --interp-only-context both \
  --stride 1
```

### Notes

- Per-frame predictions are enabled by default. To reduce disk usage, add `--no-save-preds`.
- For sanity checks, you can add `--segments 1 --max-frames 200`.

## Output locations and file naming

All outputs are under the host directory:

- `udacity/out_eval/`

### Summary file

One summary CSV is produced per run:

- `udacity/out_eval/summary_<run_id>.csv`

It contains per-segment results and `segment=ALL` aggregated rows.

### Per-frame predictions

Per-frame files are written to:

- `udacity/out_eval/preds_<run_id>/`

Filename format:

- `<model>__<segment>__<mode>.csv`

Examples:

- `chauffeur__HMB_1__orig.csv`
- `chauffeur__HMB_1__interp.csv`
- `chauffeur__HMB_1__interp_only.csv`
- `chauffeur__HMB_1__interp_only_full.csv`

Columns:

- `frame_id, gt, pred, error` where `error = gt - pred`.

## Important implementation notes / compatibility fixes

Because these are legacy community models, several compatibility shims are implemented to make them runnable under TF1.15/Keras2:

- `LegacyMerge`: supports old Keras `Merge` layer deserialization.
- Legacy regularizer conversion: converts old `WeightRegularizer` JSON configs into Keras2 `L1L2` format for `chauffeur`.
- `imageio` compatibility: falls back to `import imageio` when `imageio.v2` is unavailable.

## Common pitfalls

- **Running `docker build` from the wrong directory**: you must build from `udacity/docker/offline-eval/`.
- **Docker permission error**: use `sudo docker ...` or add user to `docker` group.
- **Stride too large for temporal models**: for final comparison use `--stride 1` (especially important for rambo/autumn/komanda).
