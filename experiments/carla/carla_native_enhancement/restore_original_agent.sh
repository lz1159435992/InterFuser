#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT=${PROJECT_ROOT:-"$(cd "${SCRIPT_DIR}/.." && pwd)"}
TEAM_CODE_DIR="${PROJECT_ROOT}/leaderboard/team_code"
BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_dir>"
    exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: backup dir not found: $BACKUP_DIR"
    exit 1
fi

if [ -f "${BACKUP_DIR}/interfuser_agent.py.bak" ]; then
    cp "${BACKUP_DIR}/interfuser_agent.py.bak" "${TEAM_CODE_DIR}/interfuser_agent.py"
else
    rm -f "${TEAM_CODE_DIR}/interfuser_agent.py"
fi

rm -rf "${TEAM_CODE_DIR}/__pycache__"
