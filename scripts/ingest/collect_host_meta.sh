#!/usr/bin/env bash
set -euo pipefail

# Collect reproducibility metadata on each remote host.
# Usage:
#   bash collect_host_meta.sh <host-tag> <project-dir> <output-dir>
# Example:
#   bash collect_host_meta.sh host_a_udacity ./upstream_a/udacity ./meta_out

HOST_TAG="${1:?missing host-tag}"
PROJECT_DIR="${2:?missing project-dir}"
OUTPUT_DIR="${3:?missing output-dir}"

mkdir -p "${OUTPUT_DIR}/${HOST_TAG}"
OUT="${OUTPUT_DIR}/${HOST_TAG}"

{
  echo "host_tag=${HOST_TAG}"
  echo "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "hostname=$(hostname)"
  echo "project_dir=${PROJECT_DIR}"
} > "${OUT}/meta.env"

if [ -d "${PROJECT_DIR}/.git" ]; then
  git -C "${PROJECT_DIR}" rev-parse --abbrev-ref HEAD > "${OUT}/git_branch.txt" || true
  git -C "${PROJECT_DIR}" rev-parse HEAD > "${OUT}/git_commit.txt" || true
  git -C "${PROJECT_DIR}" status --short > "${OUT}/git_status_short.txt" || true
fi

python -m pip freeze > "${OUT}/pip_freeze.txt" || true
nvidia-smi > "${OUT}/nvidia_smi.txt" || true
uname -a > "${OUT}/uname.txt" || true

echo "Metadata exported to ${OUT}"
