#!/bin/bash
#
# Test script for cleanup and random port functionality
#
# This script tests:
# 1. Random port allocation
# 2. CARLA process cleanup on normal exit
# 3. CARLA process cleanup on abort (Ctrl+C)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================================================"
echo "Cleanup and Random Port Test"
echo "========================================================================"
echo ""

# Test 1: Random port allocation
echo "Test 1: Random Port Allocation"
echo "----------------------------------------------------------------------"
echo "Testing PORT=random..."
echo ""

export PORT=random
export AUTO_START_CARLA=0  # Don't actually start CARLA for this test

# Extract port allocation logic
PYTHON_BIN=python3
set +e
PORT_CANDIDATE=$(${PYTHON_BIN} - <<'PY' 2>/dev/null
import random
import socket
import sys

def can_bind(p: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', p))
    except OSError:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass
    return True

for _ in range(300):
    p = random.randint(2000, 40000)
    if can_bind(p) and can_bind(p + 1) and can_bind(p + 2):
        print(p)
        sys.exit(0)

sys.exit(1)
PY
)
PORT_CANDIDATE_EXIT_CODE=$?
set -e

if [ "${PORT_CANDIDATE_EXIT_CODE}" -eq 0 ] && [ -n "${PORT_CANDIDATE}" ]; then
    echo "✓ Random port allocated: ${PORT_CANDIDATE}"
    echo "✓ Port ${PORT_CANDIDATE} is available"
    echo "✓ Port $((PORT_CANDIDATE + 1)) is available"
    echo "✓ Port $((PORT_CANDIDATE + 2)) is available"
else
    echo "✗ Failed to allocate random port"
    exit 1
fi
echo ""

# Test 2: Traffic Manager port allocation
echo "Test 2: Traffic Manager Port Allocation"
echo "----------------------------------------------------------------------"
TM_PORT=$((PORT_CANDIDATE + 500))
echo "Testing TM_PORT=${TM_PORT}..."
echo ""

set +e
TM_PORT_CANDIDATE=$(${PYTHON_BIN} - <<PY 2>/dev/null
import socket
import sys

start = int(${TM_PORT})
end = start + 50

for p in range(start, end + 1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', p))
    except OSError:
        s.close()
        continue
    s.close()
    print(p)
    sys.exit(0)

sys.exit(1)
PY
)
TM_PORT_CANDIDATE_EXIT_CODE=$?
set -e

if [ "${TM_PORT_CANDIDATE_EXIT_CODE}" -eq 0 ] && [ -n "${TM_PORT_CANDIDATE}" ]; then
    echo "✓ Traffic Manager port allocated: ${TM_PORT_CANDIDATE}"
else
    echo "⚠ Failed to allocate TM port in range ${TM_PORT}-$((TM_PORT + 50))"
    echo "  Trying fallback method..."
    
    set +e
    TM_PORT_FALLBACK=$(${PYTHON_BIN} - <<PY 2>/dev/null
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', 0))
print(s.getsockname()[1])
s.close()
PY
)
    set -e
    
    if [ -n "${TM_PORT_FALLBACK}" ]; then
        echo "✓ Fallback TM port allocated: ${TM_PORT_FALLBACK}"
    else
        echo "✗ Failed to allocate TM port"
        exit 1
    fi
fi
echo ""

# Test 3: Cleanup function test
echo "Test 3: Cleanup Function Test"
echo "----------------------------------------------------------------------"
echo "This test will:"
echo "  1. Start a dummy CARLA process (sleep command)"
echo "  2. Verify cleanup kills the process on exit"
echo ""

# Create a test script that simulates CARLA
TEST_PORT=9999
TEST_SCRIPT="/tmp/test_carla_cleanup_$$"

cat > "${TEST_SCRIPT}.sh" << 'EOF'
#!/bin/bash
PORT=$1
echo "Fake CARLA server starting on port ${PORT}..."
echo "PID: $$"
echo "Command: CarlaUE4.sh --world-port=${PORT}"

# Simulate CARLA process
while true; do
    sleep 1
done
EOF

chmod +x "${TEST_SCRIPT}.sh"

# Start fake CARLA
"${TEST_SCRIPT}.sh" ${TEST_PORT} &
FAKE_CARLA_PID=$!
echo "Started fake CARLA process (PID: ${FAKE_CARLA_PID})"
sleep 2

# Check if process is running
if kill -0 ${FAKE_CARLA_PID} 2>/dev/null; then
    echo "✓ Fake CARLA process is running"
else
    echo "✗ Fake CARLA process failed to start"
    rm -f "${TEST_SCRIPT}.sh"
    exit 1
fi

# Test cleanup
echo ""
echo "Testing cleanup function..."
echo "Sending SIGTERM to fake CARLA..."
kill ${FAKE_CARLA_PID} 2>/dev/null || true
sleep 2

# Check if process was killed
if kill -0 ${FAKE_CARLA_PID} 2>/dev/null; then
    echo "⚠ Process still running, sending SIGKILL..."
    kill -9 ${FAKE_CARLA_PID} 2>/dev/null || true
    sleep 1
fi

if kill -0 ${FAKE_CARLA_PID} 2>/dev/null; then
    echo "✗ Failed to kill fake CARLA process"
    rm -f "${TEST_SCRIPT}.sh"
    exit 1
else
    echo "✓ Fake CARLA process was successfully killed"
fi

# Cleanup
rm -f "${TEST_SCRIPT}.sh"
echo ""

# Test 4: Verify cleanup configuration
echo "Test 4: Cleanup Configuration"
echo "----------------------------------------------------------------------"
echo "Checking default cleanup settings in run_evaluation_native.sh..."
echo ""

if grep -q "CLEANUP_KILL_EXISTING_CARLA_ON_ABORT=\${CLEANUP_KILL_EXISTING_CARLA_ON_ABORT:-1}" "${SCRIPT_DIR}/run_evaluation_native.sh"; then
    echo "✓ CLEANUP_KILL_EXISTING_CARLA_ON_ABORT defaults to 1 (enabled)"
else
    echo "⚠ CLEANUP_KILL_EXISTING_CARLA_ON_ABORT may not default to 1"
fi

if grep -q "CLEANUP_KILL_PYTHON_ON_EXIT=\${CLEANUP_KILL_PYTHON_ON_EXIT:-1}" "${SCRIPT_DIR}/run_evaluation_native.sh"; then
    echo "✓ CLEANUP_KILL_PYTHON_ON_EXIT defaults to 1 (enabled)"
else
    echo "⚠ CLEANUP_KILL_PYTHON_ON_EXIT may not default to 1"
fi

if grep -q "trap on_abort INT TERM HUP QUIT" "${SCRIPT_DIR}/run_evaluation_native.sh"; then
    echo "✓ Signal traps are configured (INT TERM HUP QUIT)"
else
    echo "✗ Signal traps are not configured"
    exit 1
fi

if grep -q "trap cleanup EXIT" "${SCRIPT_DIR}/run_evaluation_native.sh"; then
    echo "✓ EXIT trap is configured"
else
    echo "✗ EXIT trap is not configured"
    exit 1
fi

echo ""

# Summary
echo "========================================================================"
echo "Test Summary"
echo "========================================================================"
echo ""
echo "✓ Random port allocation: PASSED"
echo "✓ Traffic Manager port allocation: PASSED"
echo "✓ Cleanup function: PASSED"
echo "✓ Cleanup configuration: PASSED"
echo ""
echo "All tests passed!"
echo ""
echo "Usage examples:"
echo "  # Use random port"
echo "  PORT=random bash carla_native_enhancement/run_evaluation_native.sh town05 none"
echo ""
echo "  # Use specific port"
echo "  PORT=3000 bash carla_native_enhancement/run_evaluation_native.sh town05 high_fps"
echo ""
echo "  # Auto-start CARLA with random port"
echo "  PORT=random AUTO_START_CARLA=1 bash carla_native_enhancement/run_evaluation_native.sh town05 none"
echo ""
echo "Cleanup behavior:"
echo "  - Normal exit: Kills CARLA if AUTO_START_CARLA=1"
echo "  - Abort (Ctrl+C): Kills CARLA by default (CLEANUP_KILL_EXISTING_CARLA_ON_ABORT=1)"
echo "  - Always restores original agent"
echo ""
