#!/bin/bash
#
# Example Usage — CARLA Native Sensor Enhancement
#
# This script demonstrates how to run evaluations with different
# native sensor configurations.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================================================"
echo "CARLA Native Sensor Enhancement — Example Usage"
echo "========================================================================"
echo ""

# Example 1: Baseline (20Hz, 800x600, default noise)
echo "Example 1: Baseline Configuration"
echo "  Command: bash run_evaluation_native.sh town05 none"
echo "  FPS: 20Hz"
echo "  Resolution: 800x600"
echo "  Noise: Default"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 none

# Example 2: High FPS only (40Hz, 800x600, default noise)
echo "Example 2: High FPS Configuration"
echo "  Command: bash run_evaluation_native.sh town05 high_fps"
echo "  FPS: 40Hz"
echo "  Resolution: 800x600"
echo "  Noise: Default"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 high_fps

# Example 3: High resolution only (20Hz, 1600x1200, default noise)
echo "Example 3: High Resolution Configuration"
echo "  Command: bash run_evaluation_native.sh town05 high_res"
echo "  FPS: 20Hz"
echo "  Resolution: 1600x1200"
echo "  Noise: Default"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 high_res

# Example 4: No noise only (20Hz, 800x600, no noise)
echo "Example 4: No Noise Configuration"
echo "  Command: bash run_evaluation_native.sh town05 no_noise"
echo "  FPS: 20Hz"
echo "  Resolution: 800x600"
echo "  Noise: None"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 no_noise

# Example 5: High FPS + High resolution (40Hz, 1600x1200, default noise)
echo "Example 5: High FPS + High Resolution Configuration"
echo "  Command: bash run_evaluation_native.sh town05 high_fps,high_res"
echo "  FPS: 40Hz"
echo "  Resolution: 1600x1200"
echo "  Noise: Default"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 high_fps,high_res

# Example 6: High FPS + No noise (40Hz, 800x600, no noise)
echo "Example 6: High FPS + No Noise Configuration"
echo "  Command: bash run_evaluation_native.sh town05 high_fps,no_noise"
echo "  FPS: 40Hz"
echo "  Resolution: 800x600"
echo "  Noise: None"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 high_fps,no_noise

# Example 7: High resolution + No noise (20Hz, 1600x1200, no noise)
echo "Example 7: High Resolution + No Noise Configuration"
echo "  Command: bash run_evaluation_native.sh town05 high_res,no_noise"
echo "  FPS: 20Hz"
echo "  Resolution: 1600x1200"
echo "  Noise: None"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 high_res,no_noise

# Example 8: All enhancements (40Hz, 1600x1200, no noise)
echo "Example 8: All Enhancements Configuration"
echo "  Command: bash run_evaluation_native.sh town05 high_fps,high_res,no_noise"
echo "  FPS: 40Hz"
echo "  Resolution: 1600x1200"
echo "  Noise: None"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 high_fps,high_res,no_noise

# Advanced examples
echo "========================================================================"
echo "Advanced Examples"
echo "========================================================================"
echo ""

# Example 9: Custom routes with 42routes
echo "Example 9: Custom Routes (42routes)"
echo "  Command: bash run_evaluation_native.sh 42routes high_fps"
echo "  Routes: leaderboard/data/42routes/42routes.xml"
echo "  Scenarios: leaderboard/data/42routes/42scenarios.json"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# bash "${SCRIPT_DIR}/run_evaluation_native.sh" 42routes high_fps

# Example 10: Auto-start CARLA server
echo "Example 10: Auto-start CARLA Server"
echo "  Command: AUTO_START_CARLA=1 bash run_evaluation_native.sh town05 high_fps"
echo "  Note: CARLA server will be started automatically"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# AUTO_START_CARLA=1 bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 high_fps

# Example 11: Custom GPU and port
echo "Example 11: Custom GPU and Port"
echo "  Command: GPU_ID=1 PORT=3000 bash run_evaluation_native.sh town05 high_res"
echo "  GPU: 1"
echo "  Port: 3000"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# GPU_ID=1 PORT=3000 bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 high_res

# Example 12: Batch evaluation of all configurations
echo "Example 12: Batch Evaluation (All Configurations)"
echo "  This will run all 8 configurations sequentially"
echo ""
read -p "Press Enter to continue or Ctrl+C to exit..."
echo ""

# Uncomment to run:
# for config in none high_fps high_res no_noise high_fps,high_res high_fps,no_noise high_res,no_noise high_fps,high_res,no_noise; do
#     echo "Running configuration: $config"
#     bash "${SCRIPT_DIR}/run_evaluation_native.sh" town05 "$config"
# done

echo "========================================================================"
echo "Examples Complete"
echo "========================================================================"
echo ""
echo "To actually run an example, uncomment the corresponding line in this script."
echo "Or run the commands directly in your terminal."
echo ""
echo "For more information, see:"
echo "  - README.md: Quick start guide"
echo "  - DESIGN.md: Design documentation"
echo "  - IMPLEMENTATION_SUMMARY.md: Implementation details"
echo ""
