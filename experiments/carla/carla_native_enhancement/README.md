# CARLA Native Enhancement Module

Simulate CARLA-level sensor upgrades (high FPS, high resolution, no noise) without post-processing.

## Quick Start

```bash
# Activate conda environment
conda activate interfuser

# Run all 7 configs in parallel (recommended)
cd /path/to/project
bash carla_native_enhancement/run_remaining_7_configs_safe.sh

# Or run all configs in parallel (same as above, kept for compatibility)
bash carla_native_enhancement/run_remaining_7_configs.sh

# Or run single config
bash carla_native_enhancement/run_single_config.sh 1 high_fps
```

## Configurations

8 configurations total (baseline + 3 single + 3 pairs + 1 triple):

| Config | FPS | Resolution | Noise | Description |
|--------|-----|------------|-------|-------------|
| `none` | 20Hz | 800x600 | Yes | Baseline |
| `high_fps` | 40Hz | 800x600 | Yes | High frame rate |
| `high_res` | 20Hz | 1600x1200 | Yes | High resolution |
| `no_noise` | 20Hz | 800x600 | No | No sensor noise |
| `high_fps,high_res` | 40Hz | 1600x1200 | Yes | FPS + Resolution |
| `high_fps,no_noise` | 40Hz | 800x600 | No | FPS + No noise |
| `high_res,no_noise` | 20Hz | 1600x1200 | No | Resolution + No noise |
| `high_fps,high_res,no_noise` | 40Hz | 1600x1200 | No | All enhancements |
| `gauss8` | 20Hz | 800x600 | Yes | Gaussian noise (sigma=8), standalone |
| `gauss16` | 20Hz | 800x600 | Yes | Gaussian noise (sigma=16), standalone |

## GPU Memory

Based on actual usage analysis, all 7 configs can run in parallel safely:
- GPU 1: ~14GB (44% usage) - 2 low-res configs
- GPU 2: ~20GB (64% usage) - 2 high-res configs
- GPU 3: ~22GB (68% usage) - 3 mixed configs

All GPUs have >23GB free memory, providing safe margins.

## Environment Variables

- `NATIVE_ENHANCE`: Comma-separated enhancements (e.g., `high_fps,high_res`)
- `GPU_ID`: GPU to use (default: 0)
- `PORT`: CARLA port (use `random` for auto-allocation)
- `SAVE_META`: Save meta screenshots to `SAVE_PATH/.../meta/` (default: 0)
- `DISABLE_META`: Force disable meta screenshot saving (default: 0)

## Troubleshooting

### Meta Files Not Generated

If you find that `data/eval_native/*/routes_*/meta/` directories are empty or have very few files:

**Quick Fix**:
```bash
# Run quick test to verify configuration
bash carla_native_enhancement/test_quick.sh none

# Run diagnostics
bash carla_native_enhancement/collect_diagnostics.sh
```

**Common Causes**:
1. CARLA server timeout or crash
2. Evaluation terminated early
3. GPU memory insufficient

**Detailed Guide**:
- English: [META_FILES_ISSUE_SUMMARY.md](META_FILES_ISSUE_SUMMARY.md)
- 中文: [META_FILES_ISSUE_SUMMARY.zh-CN.md](META_FILES_ISSUE_SUMMARY.zh-CN.md)
- Full troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Other Issues

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for:
- Port conflicts
- Python environment issues
- Permission problems
- GPU memory optimization
- `AUTO_START_CARLA`: Auto-start CARLA server (default: 0)
- `CLEANUP_KILL_EXISTING_CARLA_ON_ABORT`: Kill CARLA on abort (default: 1)

## Files

- `interfuser_agent_native.py` - Modified agent with native sensor support
- `native_config_parser.py` - Parse NATIVE_ENHANCE environment variable
- `run_evaluation_native.sh` - Core evaluation script
- `run_remaining_7_configs_safe.sh` - Run all 7 configs in parallel (recommended)
- `run_remaining_7_configs.sh` - Run all 7 configs in parallel (same as above)
- `run_single_config.sh` - Single config runner
- `test_config_parser.py` - Test configuration parser
- `test_cleanup.sh` - Test cleanup functionality

## Documentation

- `README.md` - This file
- `DESIGN.md` / `DESIGN.zh-CN.md` - Design documentation
- `CHANGELOG.md` / `CHANGELOG.zh-CN.md` - Change log
- `CODE_SNAPSHOT.md` / `CODE_SNAPSHOT.zh-CN.md` - Code snapshot

## Example Usage

```bash
# Activate conda environment first
conda activate interfuser

# Example 1: Run all 7 configs in parallel (recommended)
bash carla_native_enhancement/run_remaining_7_configs_safe.sh

# Example 2: Single config on GPU 1
GPU_ID=1 PORT=random AUTO_START_CARLA=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 high_fps

# Example 3: Manual NATIVE_ENHANCE
export NATIVE_ENHANCE=high_fps,high_res,no_noise
GPU_ID=2 PORT=3000 AUTO_START_CARLA=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 high_fps,high_res,no_noise
```

## Monitoring

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# View logs
tail -f data/eval_native/town05_*/leaderboard_evaluator.log

# View results
ls -lh results/native/
cat results/native/town05_*.json
```

## Emergency Stop

```bash
# Stop evaluation scripts
pkill -f "run_evaluation_native.sh"

# Stop CARLA servers
pkill -9 CarlaUE4

# Verify
ps aux | grep CarlaUE4
nvidia-smi
```
