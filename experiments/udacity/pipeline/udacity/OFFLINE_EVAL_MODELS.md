# Offline Evaluation: Model Weights Manifest

This repository includes an **offline evaluation** setup (JPG frames + `*_steering.csv` -> RMSE) for Udacity CH2 models.

- Offline evaluator: `udacity/docker/offline-eval/offline_eval.py`
- Docker image: `udacity-offline-eval:tf1` (Python 3.7 + TensorFlow 1.15.5 + Keras 2.2.4)
- Weight source: official Udacity S3 links referenced in `self-driving-car/steering-models/evaluation/README.md`

## Dataset (CH2)

Expected inputs:

- Images directory (timestamp-named JPGs), e.g. `.../datasets/CH2/input/HMB_1/1479424215935744028.jpg`
- Steering CSV, e.g. `.../datasets/CH2/input/HMB_1_steering.csv`

## Weights Location (local)

Weights are stored under:

- `self-driving-car/steering-models/community-models/<model>/weights/`

## Model: rambo

- Source URLs:
  - https://s3.amazonaws.com/udacity-sdc/steering-models/rambo/final_model.hdf5
  - https://s3.amazonaws.com/udacity-sdc/steering-models/rambo/X_train_mean.npy
- Local files:
  - `self-driving-car/steering-models/community-models/rambo/weights/final_model.hdf5` (28,597,436 bytes)
  - `self-driving-car/steering-models/community-models/rambo/weights/X_train_mean.npy` (786,528 bytes)

## Model: chauffeur

- Source URLs:
  - https://s3.amazonaws.com/udacity-sdc/steering-models/chauffeur/cnn.json
  - https://s3.amazonaws.com/udacity-sdc/steering-models/chauffeur/cnn.weights
  - https://s3.amazonaws.com/udacity-sdc/steering-models/chauffeur/lstm.json
  - https://s3.amazonaws.com/udacity-sdc/steering-models/chauffeur/lstm.weights
- Local files:
  - `self-driving-car/steering-models/community-models/chauffeur/weights/cnn.json` (13,644 bytes)
  - `self-driving-car/steering-models/community-models/chauffeur/weights/cnn.weights` (978,504 bytes)
  - `self-driving-car/steering-models/community-models/chauffeur/weights/lstm.json` (1,052 bytes)
  - `self-driving-car/steering-models/community-models/chauffeur/weights/lstm.weights` (77,818,668 bytes)

## Model: komanda

- Source URLs:
  - https://s3.amazonaws.com/udacity-sdc/steering-models/komanda/komanda.test-subgraph.meta
  - https://s3.amazonaws.com/udacity-sdc/steering-models/komanda/udacity-challenge2-model/
- Checkpoint name (as declared by `checkpoint` file):
  - `FINE_TUNE_2-checkpoint-sdc-ch2-epoch5` (epoch 5)
- Local files:
  - `self-driving-car/steering-models/community-models/komanda/weights/komanda.test-subgraph.meta` (147,876 bytes)
  - `self-driving-car/steering-models/community-models/komanda/weights/checkpoint` (131 bytes)
  - `self-driving-car/steering-models/community-models/komanda/weights/FINE_TUNE_2-checkpoint-sdc-ch2-epoch5.index` (3,890 bytes)
  - `self-driving-car/steering-models/community-models/komanda/weights/FINE_TUNE_2-checkpoint-sdc-ch2-epoch5.data-00000-of-00001` (2,321,275,964 bytes)

## Offline evaluator: Docker runtime versions

From `udacity/docker/offline-eval/requirements.txt`:

- `tensorflow==1.15.5`
- `Keras==2.2.4`
- `h5py==2.10.0`
- `protobuf==3.20.3`
- `numpy==1.18.5` (TF1.15 constraint)
- `opencv-python-headless==4.2.0.34`

## Example run (inside Docker)

Below shows the key arguments only; adjust HMB segment as needed.

### rambo

- `--rambo-model`: `.../rambo/weights/final_model.hdf5`
- `--rambo-mean`: `.../rambo/weights/X_train_mean.npy`

### chauffeur

- `--chauffeur-cnn-json`: `.../chauffeur/weights/cnn.json`
- `--chauffeur-cnn-weights`: `.../chauffeur/weights/cnn.weights`
- `--chauffeur-lstm-json`: `.../chauffeur/weights/lstm.json`
- `--chauffeur-lstm-weights`: `.../chauffeur/weights/lstm.weights`

### komanda

- `--komanda-metagraph`: `.../komanda/weights/komanda.test-subgraph.meta`
- `--komanda-checkpoint-dir`: `.../komanda/weights` (directory containing `checkpoint`, `*.index`, `*.data-*`)
