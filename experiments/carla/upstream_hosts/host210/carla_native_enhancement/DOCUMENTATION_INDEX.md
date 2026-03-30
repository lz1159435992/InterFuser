# CARLA Native Enhancement - Documentation Index

## Quick Access

### 🚀 Getting Started
- [README.md](README.md) - Main documentation and quick start guide
- [USAGE.txt](USAGE.txt) - Basic usage instructions

### 🔧 Troubleshooting (Meta Files Issue)
- **Quick Fix**: [QUICK_FIX_GUIDE.zh-CN.md](QUICK_FIX_GUIDE.zh-CN.md) ⭐ Start here!
- **Detailed Analysis**: 
  - English: [META_FILES_ISSUE_SUMMARY.md](META_FILES_ISSUE_SUMMARY.md)
  - 中文: [META_FILES_ISSUE_SUMMARY.zh-CN.md](META_FILES_ISSUE_SUMMARY.zh-CN.md)
- **Full Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### 📖 Design & Implementation
- English:
  - [DESIGN.md](DESIGN.md) - Architecture and design decisions
  - [CODE_SNAPSHOT.md](CODE_SNAPSHOT.md) - Code structure overview
  - [CHANGELOG.md](CHANGELOG.md) - Version history
- 中文:
  - [DESIGN.zh-CN.md](DESIGN.zh-CN.md) - 架构和设计决策
  - [CODE_SNAPSHOT.zh-CN.md](CODE_SNAPSHOT.zh-CN.md) - 代码结构概览
  - [CHANGELOG.zh-CN.md](CHANGELOG.zh-CN.md) - 版本历史

### 🧹 Cleanup & Maintenance
- [CLEANUP_GUIDE.txt](CLEANUP_GUIDE.txt) - How to clean up evaluation results

## Scripts

### Evaluation Scripts
- `run_evaluation_native.sh` - Main evaluation script
- `run_single_config.sh` - Run single configuration
- `run_remaining_7_configs.sh` - Run all 7 configs in parallel
- `run_remaining_7_configs_safe.sh` - Safe parallel execution (recommended)

### Testing & Diagnostics
- `test_quick.sh` - Quick test with short routes ⭐
- `collect_diagnostics.sh` - Collect diagnostic information
- `test_config_parser.py` - Test configuration parser

### Cleanup Scripts
- `cleanup_native_configs.sh` - Clean up all evaluation results
- `cleanup_specific_configs.sh` - Clean up specific configurations
- `test_cleanup.sh` - Test cleanup functionality

### Utility Scripts
- `restore_original_agent.sh` - Restore original agent
- `fix_permissions.sh` - Fix file permissions
- `example_usage.sh` - Usage examples

## Core Files

### Python Modules
- `interfuser_agent_native.py` - Main agent with native enhancements
- `native_config_parser.py` - Configuration parser

### Configuration
- `__init__.py` - Package initialization

## Problem-Specific Guides

### Meta Files Not Generated

**Symptom**: `data/eval_native/*/routes_*/meta/` directories are empty or have very few files.

**Quick Solution**:
```bash
# 1. Run quick test
bash carla_native_enhancement/test_quick.sh none

# 2. If failed, run diagnostics
bash carla_native_enhancement/collect_diagnostics.sh

# 3. Read the guide
cat carla_native_enhancement/QUICK_FIX_GUIDE.zh-CN.md
```

**Related Documents**:
1. [QUICK_FIX_GUIDE.zh-CN.md](QUICK_FIX_GUIDE.zh-CN.md) - Quick fix steps
2. [META_FILES_ISSUE_SUMMARY.zh-CN.md](META_FILES_ISSUE_SUMMARY.zh-CN.md) - Detailed analysis
3. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Full troubleshooting guide

### CARLA Server Issues

**Symptoms**:
- "time-out of 10000ms while waiting for the simulator"
- "Invalid session: no stream available"
- "Exiting abnormally"

**Solution**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → "CARLA Server Issues" section

### GPU Memory Issues

**Symptom**: Out of memory errors or CUDA errors

**Solution**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → "GPU Memory Optimization" section

### Port Conflicts

**Symptom**: "Address already in use"

**Solution**:
```bash
export PORT=random
bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

## Workflow Guides

### First-Time Setup

1. Read [README.md](README.md)
2. Run quick test: `bash test_quick.sh none`
3. If successful, run full evaluation
4. If failed, check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Running Evaluations

1. **Single config**: `bash run_single_config.sh 1 high_fps`
2. **All configs**: `bash run_remaining_7_configs_safe.sh`
3. **Custom config**: Set `NATIVE_ENHANCE` and run `run_evaluation_native.sh`

### Debugging Issues

1. Run diagnostics: `bash collect_diagnostics.sh`
2. Check logs in `data/eval_native/*/`
3. Consult [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. Check specific issue guides (see "Problem-Specific Guides" above)

### Cleaning Up

1. Review [CLEANUP_GUIDE.txt](CLEANUP_GUIDE.txt)
2. Test cleanup: `bash test_cleanup.sh`
3. Clean all: `bash cleanup_native_configs.sh`
4. Clean specific: `bash cleanup_specific_configs.sh <config_name>`

## Document Categories

### User Documentation
- README.md
- USAGE.txt
- QUICK_FIX_GUIDE.zh-CN.md
- TROUBLESHOOTING.md

### Technical Documentation
- DESIGN.md / DESIGN.zh-CN.md
- CODE_SNAPSHOT.md / CODE_SNAPSHOT.zh-CN.md
- META_FILES_ISSUE_SUMMARY.md / META_FILES_ISSUE_SUMMARY.zh-CN.md

### Maintenance Documentation
- CLEANUP_GUIDE.txt
- CHANGELOG.md / CHANGELOG.zh-CN.md

## Quick Reference

### Common Commands

```bash
# Quick test
bash carla_native_enhancement/test_quick.sh none

# Run diagnostics
bash carla_native_enhancement/collect_diagnostics.sh

# Run single config
bash carla_native_enhancement/run_single_config.sh 1 high_fps

# Run all configs
bash carla_native_enhancement/run_remaining_7_configs_safe.sh

# Clean up
bash carla_native_enhancement/cleanup_native_configs.sh

# Check results
find data/eval_native -name "*.jpg" | wc -l
```

### Environment Variables

```bash
# Configuration
export NATIVE_ENHANCE="high_fps,no_noise"

# GPU selection
export GPU_ID=0

# Port configuration
export PORT=random  # or specific port like 2000

# Timeout settings
export EVAL_TIMEOUT=1200
export CARLA_TICK_TIMEOUT=1200

# CARLA startup
export AUTO_START_CARLA=1  # or 0 for manual start
```

### File Locations

```
carla_native_enhancement/
├── Documentation (this index)
├── Scripts (*.sh)
├── Python modules (*.py)
└── Backups (.backup_*/)

data/eval_native/
└── <eval_name>_<timestamp>/
    ├── evaluation_metadata.json
    ├── leaderboard_evaluator.log
    ├── carla_server_*.log
    └── routes_*/
        └── meta/
            └── *.jpg  ← Frame images

results/native/
└── <eval_name>_<timestamp>.json  ← Evaluation results
```

## Getting Help

### Step 1: Identify the Problem

- Meta files not generated? → [QUICK_FIX_GUIDE.zh-CN.md](QUICK_FIX_GUIDE.zh-CN.md)
- CARLA crashes? → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- GPU memory issues? → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Other issues? → Run diagnostics first

### Step 2: Run Diagnostics

```bash
bash carla_native_enhancement/collect_diagnostics.sh > diagnostics.txt
cat diagnostics.txt
```

### Step 3: Check Logs

```bash
LATEST=$(ls -td data/eval_native/town05_* | head -1)
cat "${LATEST}/leaderboard_evaluator.log"
cat "${LATEST}"/carla_server_*.log
```

### Step 4: Consult Documentation

1. Check this index for relevant documents
2. Read the specific guide for your issue
3. Follow the troubleshooting steps

## Version Information

- **Module Version**: 1.0.0
- **Last Updated**: 2026-02-04
- **CARLA Version**: 0.9.10
- **Python Version**: 3.7

## Contributing

When adding new documentation:
1. Add entry to this index
2. Update README.md if necessary
3. Update CHANGELOG.md
4. Keep both English and Chinese versions in sync

## License

See [LICENSE](../LICENSE) in project root.
