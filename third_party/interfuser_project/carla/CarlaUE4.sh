#!/bin/sh
UE4_TRUE_SCRIPT_NAME=$(echo "$0" | xargs readlink -f)
UE4_PROJECT_ROOT=$(dirname "$UE4_TRUE_SCRIPT_NAME")
UE4_BIN="$UE4_PROJECT_ROOT/CarlaUE4/Binaries/Linux/CarlaUE4-Linux-Shipping"
chmod +x "$UE4_BIN"
exec "$UE4_BIN" CarlaUE4 "$@"
