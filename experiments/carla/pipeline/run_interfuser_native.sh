#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
TARGET="${ROOT_DIR}/third_party/interfuser_project/carla_native_enhancement/run_evaluation_native.sh"

if [ ! -f "${TARGET}" ]; then
  echo "InterFuser native launcher not found: ${TARGET}" >&2
  exit 1
fi

exec bash "${TARGET}" "$@"
