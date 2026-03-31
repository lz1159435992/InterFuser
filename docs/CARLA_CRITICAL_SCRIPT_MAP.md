# CARLA Critical Script Map

This note captures the minimum code/resources required for the CARLA experiments in the paper, starting from the two primary launchers:

- `third_party/interfuser_project/carla_native_enhancement/run_evaluation_native.sh`
- `third_party/lmdrive/leaderboard/scripts/run_evaluation_lmdrive_native_sweep_parallel.sh`

## InterFuser Native Chain

Primary launcher flow:

1. `carla_native_enhancement/run_evaluation_native.sh`
2. `carla_native_enhancement/interfuser_agent_native.py`
3. `carla_native_enhancement/native_config_parser.py`
4. `leaderboard/leaderboard/leaderboard_evaluator.py`

Required resources for route/scenario selection:

- `leaderboard/data/evaluation_routes/routes_town05_long.xml` (town05 mode)
- `leaderboard/data/42routes/42routes.xml` (42routes mode)
- `leaderboard/data/42routes/42scenarios.json` (42routes mode)

## LMDrive Native Chain

Primary launcher flow:

1. `leaderboard/scripts/run_evaluation_lmdrive_native_sweep_parallel.sh`
2. `leaderboard/scripts/run_evaluation_lmdrive_native.sh`
3. `leaderboard/team_code/lmdriver_agent_native.py`
4. `leaderboard/team_code/lmdrive_native_config_parser.py`
5. `leaderboard/leaderboard/leaderboard_evaluator.py`

Required resources:

- `langauto/benchmark_long.xml`
- `langauto/benchmark_short.xml`
- `langauto/benchmark_tiny.xml`
- `leaderboard/data/official/all_towns_traffic_scenarios_public.json`
- `sensor_data_processor_module/data_processor.py` and `sensor_data_processor_module/data_processor_config.py` (imported by native agent)

## Current Status (2026-03-31)

Present:

- InterFuser native scripts and evaluator code.
- LMDrive native scripts and evaluator code.
- LMDrive official scenarios JSON: `leaderboard/data/official/all_towns_traffic_scenarios_public.json`.
- `sensor_data_processor_module` exists under `third_party/interfuser_project`.

Previously missing files are now added from source mirrors:

- `third_party/interfuser_project/leaderboard/data/evaluation_routes/routes_town05_long.xml`
- `third_party/interfuser_project/leaderboard/data/42routes/42routes.xml`
- `third_party/interfuser_project/leaderboard/data/42routes/42scenarios.json`
- `third_party/lmdrive/langauto/benchmark_long.xml`
- `third_party/lmdrive/langauto/benchmark_short.xml`
- `third_party/lmdrive/langauto/benchmark_tiny.xml`
- `third_party/lmdrive/sensor_data_processor_module/data_processor.py`
- `third_party/lmdrive/sensor_data_processor_module/data_processor_config.py`

## Portability and Anonymity Updates Applied

- Removed hardcoded legacy conda home path from InterFuser native launcher.
- Removed hardcoded legacy project root default from LMDrive processor launcher.
- Added sibling-project probing in LMDrive native launcher so it can load `sensor_data_processor_module` from:
  - `third_party/lmdrive/sensor_data_processor_module` (if present), or
  - `third_party/interfuser_project/sensor_data_processor_module`.
- Added fail-fast existence checks in LMDrive launchers for route/scenario files.

## Next Fill-In Action

Copy the missing route/scenario resources from your source mirrors into the target paths listed above, then run:

```bash
bash third_party/lmdrive/leaderboard/scripts/run_evaluation_lmdrive_native.sh langauto_tiny none
bash third_party/interfuser_project/carla_native_enhancement/run_evaluation_native.sh town05 none
```
