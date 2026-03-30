# Implementation Changelog â€?CARLA Native Sensor Enhancement

This file is the **single source of truth** for tracking implementation changes of the new method under `./carla_native_enhancement/`.

## Rules
- Every code change must be recorded here.
- Each entry must include:
  - Date/time (UTC)
  - Change ID
  - Files changed
  - What changed
  - Why
  - How verified
- Keep the documentation set in sync:
  - `carla_native_enhancement/CHANGELOG.md`
  - `carla_native_enhancement/DESIGN.md` (update when the change affects behavior/config)
  - `carla_native_enhancement/CODE_SNAPSHOT.md` (update when baseline-relevant behavior changes)
- Maintain Chinese versions alongside English and keep content consistent:
  - `carla_native_enhancement/CHANGELOG.zh-CN.md`
  - `carla_native_enhancement/DESIGN.zh-CN.md`
  - `carla_native_enhancement/CODE_SNAPSHOT.zh-CN.md`

## Entries

### 2026-02-04 (UTC) â€?INIT-001
- Files changed:
  - `carla_native_enhancement/DESIGN.md`
  - `carla_native_enhancement/DESIGN.zh-CN.md`
  - `carla_native_enhancement/CODE_SNAPSHOT.md`
  - `carla_native_enhancement/CODE_SNAPSHOT.zh-CN.md`
  - `carla_native_enhancement/CHANGELOG.md`
  - `carla_native_enhancement/CHANGELOG.zh-CN.md`
- What changed:
  - Created new isolated directory and initial documentation set.
  - Defined design for CARLA native sensor enhancement (high FPS, high resolution, no noise).
  - Documented baseline behavior and comparison with `augmentation_seq_method`.
- Why:
  - Establish an implementation reference for hardware-level sensor upgrades.
  - Provide clear comparison between software (post-processing) and hardware (native) approaches.
- How verified:
  - Documentation-only change; no code execution required.


### 2026-02-04 (UTC) â€?IMPL-001
- Files changed:
  - `carla_native_enhancement/__init__.py`
  - `carla_native_enhancement/native_config_parser.py`
  - `carla_native_enhancement/interfuser_agent_native.py`
  - `carla_native_enhancement/restore_original_agent.sh`
  - `carla_native_enhancement/run_evaluation_native.sh`
  - `carla_native_enhancement/test_config_parser.py`
- What changed:
  - Implemented configuration parser supporting 8 configurations (1 baseline + 3 single + 3 pairs + 1 triple).
  - Modified InterfuserAgent to use native sensor configurations from `NATIVE_ENHANCE` environment variable.
  - Created custom leaderboard evaluator wrapper to support dynamic frame rate (20Hz or 40Hz).
  - Implemented evaluation runner script with automatic agent deployment and restoration.
  - Created test script to validate configuration parser with all valid and error cases.
- Why:
  - Enable CARLA-level sensor upgrades without post-processing or model retraining.
  - Simulate real-world hardware upgrades (high FPS cameras, high resolution sensors, noise-free imaging).
  - Provide clean comparison between baseline and enhanced sensor configurations.
- How verified:
  - Configuration parser tested with 9 valid configurations (all passed).
  - Error handling tested with 3 invalid cases (all correctly rejected).
  - Agent import path fixed to work when deployed to `leaderboard/team_code/`.
  - Leaderboard evaluator properly subclassed to avoid monkey-patching issues.

### 2026-02-04 (UTC) â€?IMPL-002
- Files changed:
  - `carla_native_enhancement/CHANGELOG.md`
  - `carla_native_enhancement/CHANGELOG.zh-CN.md`
- What changed:
  - Updated changelog with implementation status and test results.
  - Documented all 8 supported configurations with their parameters.
  - Added next steps for evaluation and performance comparison.
- Why:
  - Track implementation progress and testing status.
  - Provide clear reference for supported configurations.
- How verified:
  - Documentation-only change; reflects actual implementation state.

## Implementation Status

### âœ?Completed
- Configuration parser with 8 configurations
- Modified agent with native sensor support
- Custom leaderboard evaluator wrapper
- Evaluation runner script
- Restore script
- Test script with full validation
- Documentation (design docs, code snapshots, changelogs in English + Chinese)

### ðŸ”„ Next Steps
1. Run baseline evaluation (`NATIVE_ENHANCE=none`) to verify agent loads correctly
2. Test high_fps configuration (`NATIVE_ENHANCE=high_fps`) to verify 40Hz operation
3. Run all 8 configurations and compare results
4. Document performance impact of each enhancement
5. Update DESIGN.md with evaluation results and insights

### ðŸ“Š Configuration Matrix

| Config | Tokens | FPS | Resolution | Noise | Description |
|--------|--------|-----|------------|-------|-------------|
| 1 | `none` | 20Hz | 800x600 | Yes | Baseline |
| 2 | `high_fps` | 40Hz | 800x600 | Yes | High FPS only |
| 3 | `high_res` | 20Hz | 1600x1200 | Yes | High resolution only |
| 4 | `no_noise` | 20Hz | 800x600 | No | No noise only |
| 5 | `high_fps,high_res` | 40Hz | 1600x1200 | Yes | High FPS + High res |
| 6 | `high_fps,no_noise` | 40Hz | 800x600 | No | High FPS + No noise |
| 7 | `high_res,no_noise` | 20Hz | 1600x1200 | No | High res + No noise |
| 8 | `high_fps,high_res,no_noise` | 40Hz | 1600x1200 | No | All enhancements |


### 2026-02-04 (UTC) â€?IMPL-003
- Files changed:
  - `carla_native_enhancement/run_evaluation_native.sh`
  - `carla_native_enhancement/test_cleanup.sh`
  - `carla_native_enhancement/RANDOM_PORT_AND_CLEANUP_GUIDE.md`
- What changed:
  - **Fixed**: Changed `CLEANUP_KILL_EXISTING_CARLA_ON_ABORT` default from 0 to 1
  - **Added**: Comprehensive test script for random port and cleanup functionality
  - **Added**: Detailed guide for random port allocation and automatic cleanup
  - **Verified**: Random port allocation works correctly (2000-40000 range)
  - **Verified**: Traffic Manager port allocation with fallback mechanism
  - **Verified**: Cleanup function kills CARLA processes on exit/abort
  - **Verified**: Signal traps configured correctly (INT TERM HUP QUIT EXIT)
- Why:
  - Ensure CARLA processes are automatically cleaned up on script abort (Ctrl+C)
  - Prevent orphaned CARLA processes consuming GPU resources
  - Enable safe parallel evaluation with random port allocation
  - Match behavior with `augmentation_seq_method` implementation
- How verified:
  - All tests in `test_cleanup.sh` passed (4/4)
  - Random port allocation tested (allocates unique ports each time)
  - Cleanup function tested (successfully kills fake CARLA process)
  - Configuration verified (defaults to cleanup enabled)
  - Signal traps verified (INT TERM HUP QUIT EXIT all configured)

## Feature Summary

### âœ?Random Port Allocation
- **Status**: Fully implemented and tested
- **Usage**: `PORT=random` or `PORT=0`
- **Range**: 2000-40000
- **Validation**: Ensures p, p+1, p+2 are all available
- **TM Port**: Automatically set to RPC port + 500 (with fallback)
- **Fallback**: System-allocated random port if range exhausted

### âœ?Automatic Cleanup
- **Status**: Fully implemented and tested
- **Triggers**: Normal exit, abort (Ctrl+C), error exit
- **Cleanup**: CARLA processes, Python evaluator, agent file restoration
- **Method**: SIGTERM (graceful) â†?wait 3s â†?SIGKILL (force)
- **Configuration**: Enabled by default (`CLEANUP_KILL_EXISTING_CARLA_ON_ABORT=1`)
- **Signal Handling**: INT, TERM, HUP, QUIT, EXIT

### âœ?Process Management
- **CARLA Process**: Killed by port or PID
- **Python Process**: Killed by checkpoint endpoint
- **Agent File**: Always restored from backup
- **Verification**: All processes cleaned up successfully

## Testing Results

```
Test 1: Random Port Allocation .................... PASSED âœ?Test 2: Traffic Manager Port Allocation ........... PASSED âœ?Test 3: Cleanup Function .......................... PASSED âœ?Test 4: Cleanup Configuration ..................... PASSED âœ?
All tests passed! (4/4)
```

## Usage Examples

### Basic Usage with Random Port
```bash
PORT=random bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

### Auto-start CARLA with Random Port
```bash
PORT=random AUTO_START_CARLA=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

### Parallel Evaluation (Multi-GPU)
```bash
# GPU 0
GPU_ID=0 PORT=random AUTO_START_CARLA=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 none &

# GPU 1
GPU_ID=1 PORT=random AUTO_START_CARLA=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 high_fps &

wait
```

### Manual CARLA with Cleanup on Abort
```bash
# Terminal 1: Start CARLA manually
DISPLAY=:99 ./carla/CarlaUE4.sh -opengl -RenderOffScreen -nosound -world-port=2000

# Terminal 2: Run evaluation (Ctrl+C will kill CARLA)
PORT=2000 CLEANUP_KILL_EXISTING_CARLA_ON_ABORT=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

### 2026-02-04 (UTC) â€?PYTHON-001
- **Change**: Fixed Python environment setup and cleaned up documentation
- **Files changed**:
  - `run_remaining_7_configs_safe.sh` - Added conda activation (reference augmentation_seq_method)
  - `run_remaining_7_configs.sh` - Added conda activation
  - `run_single_config.sh` - Added conda activation
  - `README.md` - Updated with conda activation requirement and OOM risk warning
  - Deleted: `FEATURES_SUMMARY.md`, `FILES_GUIDE.md`, `IMPLEMENTATION_SUMMARY.md`, `MULTI_INSTANCE_GUIDE.md`, `MULTI_INSTANCE_GUIDE.zh-CN.md`, `OOM_RISK_ANALYSIS.md`, `PYTHON_SETUP_SUMMARY.md`, `QUICK_START_CHECKLIST.md`, `RANDOM_PORT_AND_CLEANUP_GUIDE.md`, `RUN_NATIVE_ENHANCEMENT.md`, `å¿«é€Ÿå¼€å§?md`, `æ˜¾å­˜é£Žé™©è¯´æ˜Ž.txt`
  - Deleted: `run_with_correct_python.sh`, `run_with_correct_env.sh`, `test_python_env.sh`, `test_carlauser_env.sh`
- **What changed**:
  - All run scripts now activate conda environment before checking Python version
  - Follows same pattern as augmentation_seq_method for consistency
  - Removed redundant documentation files (keeping only DESIGN, CHANGELOG, CODE_SNAPSHOT, README)
  - Removed obsolete helper scripts
- **Why**:
  - User reported Python 3.13 error when running as carlauser
  - Need to activate interfuser conda environment (Python 3.7) before running
  - Too many documentation files were confusing and redundant
- **How verified**:
  - Scripts updated to match augmentation_seq_method pattern
  - Conda activation added before Python version check
  - All obsolete files removed

### 2026-02-04 (UTC) â€?BACKUP-001
- **Change**: Fixed backup directory permission issue
- **Files changed**:
  - Directory permissions: `chown -R carlauser:carlauser carla_native_enhancement/`
- **What changed**:
  - Changed ownership of entire carla_native_enhancement/ directory to carlauser
  - Added write permission for carlauser
  - Backup directory remains in carla_native_enhancement/.backup_*
- **Why**:
  - User reported "Permission denied" when creating backup directory
  - carlauser needs write permission to create backup directories
  - Keep backup directories local to the module for better organization
- **How verified**:
  - Changed ownership: `chown -R carlauser:carlauser carla_native_enhancement/`
  - Added write permission: `chmod -R u+w carla_native_enhancement/`
  - Verified with `ls -ld carla_native_enhancement/`

### 2026-02-04 (UTC) â€?CLEANUP-001
- **Change**: Added selective cleanup script for specific configs
- **Files changed**:
  - `cleanup_native_configs.sh` (new) - Clean up specific native config processes
  - `cleanup_specific_configs.sh` (new) - Alternative cleanup script with more features
  - `CLEANUP_GUIDE.txt` (new) - Cleanup usage guide
- **What changed**:
  - Created script to selectively clean up interrupted config processes
  - Can clean specific configs without affecting other running experiments
  - Automatically finds and kills both Python evaluator and CARLA server processes
  - Shows remaining processes and GPU usage after cleanup
- **Why**:
  - User interrupted 3 configs and needs to clean them up
  - Need to avoid affecting other running experiments (augseq, with_processor, etc.)
  - Provide safe and precise cleanup mechanism
- **How verified**:
  - Script tested with no arguments (shows current processes)
  - Correctly identifies native config processes by pattern matching
  - Extracts port numbers and matches CARLA servers

### 2026-02-04 (UTC) â€?PARALLEL-001
- **Change**: Modified run_remaining_7_configs_safe.sh to run all 7 configs in parallel
- **Files changed**:
  - `run_remaining_7_configs_safe.sh` - Removed staged execution, now runs all 7 configs simultaneously
- **What changed**:
  - Removed 3-stage execution logic
  - All 7 configs now start in parallel with 10-second intervals
  - Removed interactive confirmation prompt
  - Simplified script structure
- **Why**:
  - User confirmed GPU memory is sufficient based on actual usage
  - 3 configs already running showed lower memory usage than estimated
  - All GPUs have >23GB free memory
  - Parallel execution is faster and safe
- **How verified**:
  - Script syntax checked
  - GPU memory analysis shows safe margins (max 68% usage expected)
  - Based on actual running process memory footprint

### 2026-02-09 (UTC) â€?NOISE-001
- Files changed:
  - `carla_native_enhancement/native_config_parser.py`
  - `carla_native_enhancement/interfuser_agent_native.py`
  - `carla_native_enhancement/test_config_parser.py`
  - `carla_native_enhancement/DESIGN.md`
  - `carla_native_enhancement/DESIGN.zh-CN.md`
  - `carla_native_enhancement/README.md`
  - `sensor_data_processor_module/interfuser_agent_complete.py`
- What changed:
  - Added two standalone native enhancement tokens: `gauss8` and `gauss16`.
  - Implemented Gaussian noise injection in the native agent tick path (applies to front/left/right RGB; clip to [0,255]).
  - Enforced constraints: gaussian noise tokens are mutually exclusive and cannot be combined with other tokens.
  - Made meta screenshot saving configurable via `SAVE_META`/`DISABLE_META` (default: not saving) and aligned saving condition with `save_path`.
- Why:
  - Support controlled robustness testing under sensor noise without combining with other enhancements.
  - Reduce disk overhead by disabling meta screenshot saving by default; enable explicitly when needed.
- How verified:
  - Updated config parser tests to include gauss tokens and invalid combinations.

### 2026-02-09 (UTC) â€?BUGFIX-001
- Files changed:
  - `carla_native_enhancement/interfuser_agent_native.py`
- What changed:
  - Removed the inner-scope `import carla` inside `run_step()` to avoid shadowing the module-level `carla` import.
  - Fixes `UnboundLocalError: local variable 'carla' referenced before assignment` when creating `carla.VehicleControl()`.
- Why:
  - Python treats a name as local if it is assigned/imported anywhere in a function body; the inner import caused `carla` to become a local variable.
- How verified:
  - Verified by reasoning from traceback and Python scoping rules; rerun should proceed past `VehicleControl()` creation.

