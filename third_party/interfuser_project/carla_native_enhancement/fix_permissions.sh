#!/bin/bash
#
# Fix permissions for carla_native_enhancement directory
# Run as root: sudo bash carla_native_enhancement/fix_permissions.sh
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Fixing permissions for carla_native_enhancement"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    echo "Usage: sudo bash $0"
    exit 1
fi

echo "Changing ownership to carlauser..."
chown -R carlauser:carlauser "${SCRIPT_DIR}"

echo "Adding write permission..."
chmod -R u+w "${SCRIPT_DIR}"

echo ""
echo "✓ Permissions fixed!"
echo ""
echo "Verification:"
ls -ld "${SCRIPT_DIR}"
echo ""
echo "Sample files:"
ls -l "${SCRIPT_DIR}"/*.sh | head -3
echo ""
