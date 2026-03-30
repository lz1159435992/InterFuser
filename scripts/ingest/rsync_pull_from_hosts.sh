#!/usr/bin/env bash
set -euo pipefail

# Pull raw snapshots from remote hosts into IntuitionTester_sources.
# Run this script from a Linux shell (local Linux or WSL).

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BASE_DIR="${1:-${REPO_ROOT}/../IntuitionTester_sources}"

# Configure remote endpoints via env vars to avoid hard-coded identities in repo.
HOST_A_ALIAS="${HOST_A_ALIAS:-host_a_udacity}"
HOST_A_SSH="${HOST_A_SSH:-user@host-a.example}"
HOST_A_PORT="${HOST_A_PORT:-22}"
HOST_A_REMOTE_DIR="${HOST_A_REMOTE_DIR:-/path/to/upstream_a/udacity/}"

HOST_B_ALIAS="${HOST_B_ALIAS:-host_b_interfuser}"
HOST_B_SSH="${HOST_B_SSH:-user@host-b.example}"
HOST_B_PORT="${HOST_B_PORT:-22}"
HOST_B_REMOTE_DIR="${HOST_B_REMOTE_DIR:-/path/to/upstream_b/interfuser/}"

HOST_C_ALIAS="${HOST_C_ALIAS:-host_c_carla}"
HOST_C_SSH="${HOST_C_SSH:-user@host-c.example}"
HOST_C_PORT="${HOST_C_PORT:-22}"
HOST_C_REMOTE_DIR="${HOST_C_REMOTE_DIR:-/path/to/upstream_c/interfuser/}"

mkdir -p "${BASE_DIR}/${HOST_A_ALIAS}"
mkdir -p "${BASE_DIR}/${HOST_B_ALIAS}"
mkdir -p "${BASE_DIR}/${HOST_C_ALIAS}"

echo "[1/3] Pulling ${HOST_A_ALIAS} ..."
rsync -avz -e "ssh -p ${HOST_A_PORT}" \
  "${HOST_A_SSH}:${HOST_A_REMOTE_DIR}" \
  "${BASE_DIR}/${HOST_A_ALIAS}/"

echo "[2/3] Pulling ${HOST_B_ALIAS} ..."
rsync -avz -e "ssh -p ${HOST_B_PORT}" \
  "${HOST_B_SSH}:${HOST_B_REMOTE_DIR}" \
  "${BASE_DIR}/${HOST_B_ALIAS}/"

echo "[3/3] Pulling ${HOST_C_ALIAS} ..."
rsync -avz -e "ssh -p ${HOST_C_PORT}" \
  "${HOST_C_SSH}:${HOST_C_REMOTE_DIR}" \
  "${BASE_DIR}/${HOST_C_ALIAS}/"

echo "Done. Raw mirrors are under: ${BASE_DIR}"
