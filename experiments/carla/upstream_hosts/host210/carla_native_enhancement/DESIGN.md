# Design Doc: CARLA Native Sensor Enhancement for InterFuser/Leaderboard

## 1. Background

The current repository contains two stable evaluation paths:
- `sensor_data_processor_module/`: applies post-processing (SwinIR/SRGAN) to sensor data
- `augmentation_seq_method/`: applies ordered sequences of post-processing operations

This new method explores a different approach: **upgrading sensors at the CARLA simulation level** rather than post-processing the output. This simulates real-world hardware upgrades where better cameras/sensors are installed on the vehicle.

## 2. Goals

- **G1 (Hardware Simulation)**: Simulate real-world sensor upgrades (higher frame rate, higher resolution, lower noise) by modifying CARLA sensor configurations.
- **G2 (No Model Retraining)**: Evaluate model performance under sensor upgrades without retraining, simulating "plug-and-play" hardware upgrades.
- **G3 (Agent Adaptation)**: Adapt agent processing frequency to match sensor upgrades (e.g., 40Hz agent for 40Hz camera).
- **G4 (Isolation)**: Do not break existing baseline scripts/agents.
- **G5 (Comparability)**: Enable direct comparison with post-processing methods (`augmentation_seq_method`).

## 3. Non-Goals

- Retraining or fine-tuning the model for new sensor configurations.
- Implementing post-processing operations (use `augmentation_seq_method` for that).
- Changing the model architecture or input dimensions beyond what's necessary for resolution changes.

## 4. Terminology

- **High FPS (high_fps)**: Increase camera frame rate from 20Hz to 40Hz, and run the simulation at 40Hz.
- **High Resolution (high_res)**: Increase camera resolution from 800x600 to 1600x1200.
- **No Noise (no_noise)**: Disable CARLA post-processing effects (motion blur, lens flare, bloom, etc.) to simulate cleaner sensors.
- **Gaussian Noise (gauss8/gauss16)**: Inject standalone Gaussian noise (sigma=8 or 16) into RGB images in the agent. This setting cannot be combined with other tokens.
- **Native Enhancement**: Sensor improvements applied at the CARLA simulation level, not through post-processing.

## 5. High-Level Architecture

New method lives under:
- `./carla_native_enhancement/`

Key components:
- **Config Parser**: parses `NATIVE_ENHANCE` into sensor configuration parameters.
- **Sensor Config Builder**: constructs CARLA sensor specifications based on parsed config.
- **Agent Integration**: modified agent that adapts to different sensor configurations.
- **Sensor Interface Patch**: modified `SensorInterface` to handle high-frequency data correctly.

## 6. Configuration Interface

### 6.1 Core variables

- `NATIVE_ENHANCE` (string): comma-separated enhancement tokens.
  - Allowed tokens: `none`, `high_fps`, `high_res`, `no_noise`, `gauss8`, `gauss16`.
  - Examples:
    - `none` (baseline: 20Hz, 800x600, default noise)
    - `high_fps` (40Hz, 800x600, default noise)
    - `high_res` (20Hz, 1600x1200, default noise)
    - `no_noise` (20Hz, 800x600, no post-processing)
    - `high_fps,high_res` (40Hz, 1600x1200, default noise)
    - `high_fps,high_res,no_noise` (40Hz, 1600x1200, no post-processing)
    - `gauss8` (20Hz, 800x600, inject gaussian noise sigma=8; standalone)
    - `gauss16` (20Hz, 800x600, inject gaussian noise sigma=16; standalone)

**Constraint**:
- `gauss8` and `gauss16` are standalone tokens and cannot be combined with any other token.

### 6.2 Sensor configuration mapping

| Token | Frame Rate | Resolution | Motion Blur | Lens Flare | Bloom |
|-------|-----------|-----------|-------------|-----------|-------|
| `none` | 20Hz (0.05s) | 800x600 | 0.45 | 0.1 | 0.675 |
| `high_fps` | 40Hz (0.025s) | 800x600 | 0.45 | 0.1 | 0.675 |
| `high_res` | 20Hz (0.05s) | 1600x1200 | 0.45 | 0.1 | 0.675 |
| `no_noise` | 20Hz (0.05s) | 800x600 | 0.0 | 0.0 | 0.0 |

### 6.3 World simulation frequency

**Critical Decision**: When `high_fps` is enabled, the world simulation frequency must also be increased to 40Hz.

```python
# Baseline (20Hz)
settings.fixed_delta_seconds = 0.05  # 20Hz world tick

# High FPS (40Hz)
settings.fixed_delta_seconds = 0.025  # 40Hz world tick
```

**Rationale**:
- Ensures sensor data and world state are synchronized.
- Agent receives fresh data at every tick (no queue backlog).
- Simulates real-world scenario where control loop frequency matches sensor frequency.

### 6.4 Agent processing frequency

The agent's `run_step()` is called once per world tick:
- Baseline: 20 times per second (every 0.05s)
- High FPS: 40 times per second (every 0.025s)

**No code changes needed in agent logic** - the agent automatically adapts to the world tick rate.

### 6.5 Image preprocessing

For `high_res` (1600x1200):
- Images are still resized to 224x224 (or 128x128 for side cameras) before feeding to the model.
- The model input dimensions remain unchanged.
- Benefit: Downsampling from higher resolution preserves more details (anti-aliasing effect).

### 6.6 Output/metadata

Each run should record:
- `native_enhance` original string.
- Parsed configuration (fps, resolution, noise settings).
- World tick rate (`fixed_delta_seconds`).
- Actual frame rate achieved.
- Per-tick inference time (to verify 40Hz is achievable).

### 6.7 Evaluation runner robustness options

Inherits all robustness options from `augmentation_seq_method`:
- `PORT`, `TM_PORT`: Port configuration with auto-selection.
- `AUTO_START_CARLA`: Automatic CARLA server startup.
- `KILL_EXISTING_CARLA`: Clean up existing CARLA processes.
- `SENSOR_QUEUE_TIMEOUT`: Timeout for sensor data (may need adjustment for 40Hz).
- `CARLA_STARTUP_WAIT_SEC`, `CARLA_READY_TIMEOUT`: Startup timing.
- `CLEANUP_KILL_PYTHON_ON_EXIT`: Process cleanup on exit.

## 7. Technical Challenges and Solutions

### 7.1 Challenge: Sensor data queue backlog at 40Hz

**Problem**: If camera runs at 40Hz but agent processes at 20Hz, sensor data accumulates in queue.

**Solution**: 
- Run world at 40Hz when `high_fps` is enabled.
- Agent automatically processes at 40Hz (called once per world tick).
- No queue backlog occurs.

### 7.2 Challenge: Model inference speed at 40Hz

**Problem**: Agent must complete inference within 25ms (1/40s) to maintain real-time performance.

**Analysis**:
```
40Hz budget: 25ms per frame
Typical InterfuserAgent inference: 15-20ms on RTX 3090
Margin: 5-10ms (sufficient)
```

**Mitigation**:
- Monitor per-tick inference time.
- If inference exceeds 25ms, log warning but continue (simulation will slow down).
- Record actual achieved frame rate in metadata.

### 7.3 Challenge: High resolution computational cost

**Problem**: Rendering 1600x1200 images is more expensive than 800x600.

**Impact**:
- CARLA rendering: +30-50% GPU time.
- Agent preprocessing (resize): +10-20% CPU time.
- Total: Still within real-time budget for modern GPUs.

**Mitigation**:
- Monitor CARLA FPS to ensure it maintains target rate.
- If CARLA cannot maintain 40Hz with high_res, consider reducing other visual settings.

## 8. Experiment Matrix

### 8.1 Baselines
- `none` (20Hz, 800x600, default noise)

### 8.2 Single enhancements
- `high_fps` (40Hz, 800x600, default noise)
- `high_res` (20Hz, 1600x1200, default noise)
- `no_noise` (20Hz, 800x600, no post-processing)
- `gauss8` (20Hz, 800x600, gaussian noise sigma=8)
- `gauss16` (20Hz, 800x600, gaussian noise sigma=16)

### 8.3 Pairwise combinations
- `high_fps,high_res` (40Hz, 1600x1200, default noise)
- `high_fps,no_noise` (40Hz, 800x600, no post-processing)
- `high_res,no_noise` (20Hz, 1600x1200, no post-processing)

### 8.4 Triple combination
- `high_fps,high_res,no_noise` (40Hz, 1600x1200, no post-processing)

**Total: 8 configurations**

## 9. Metrics and Reporting

Primary (Leaderboard):
- Route completion, driving score, infractions.

Secondary (performance):
- Actual achieved frame rate (world ticks per second).
- Per-tick inference time (mean/std/p95).
- CARLA rendering FPS.
- Wall-clock time per route.

Comparison:
- Compare with `augmentation_seq_method` results to evaluate hardware vs. software approaches.

## 10. Validation Plan

- **V1**: `NATIVE_ENHANCE=none` matches original baseline behavior.
- **V2**: `high_fps` achieves 40Hz without timeouts or crashes.
- **V3**: `high_res` images are correctly resized and processed.
- **V4**: `no_noise` produces visibly cleaner images.
- **V5**: All 8 configurations run end-to-end without errors.
- **V6**: Metadata and logs are generated for every run.

## 11. Comparison with augmentation_seq_method

| Aspect | augmentation_seq_method | carla_native_enhancement |
|--------|------------------------|-------------------------|
| **Approach** | Post-processing (SwinIR/SRGAN/RIFE) | Native sensor upgrade |
| **Frame rate** | Interpolation (20Hz â†?40Hz equivalent) | True 40Hz simulation |
| **Resolution** | Upscaling (800x600 â†?1600x1200) | Native high-res rendering |
| **Noise** | Denoising (SwinIR) | Disable noise at source |
| **Computation** | Agent-side processing | CARLA-side rendering |
| **Real-world analog** | Software upgrade | Hardware upgrade |

## 12. Risks and Mitigations

- **RISK: 40Hz inference too slow**
  - Mitigation: Monitor inference time; simulation will slow down gracefully if needed.
  
- **RISK: CARLA cannot maintain 40Hz**
  - Mitigation: Reduce visual quality settings; monitor actual FPS.
  
- **RISK: High resolution causes memory issues**
  - Mitigation: Monitor GPU memory; reduce batch size if needed.
  
- **RISK: Model performs worse on clean images**
  - Mitigation: This is a valid experimental finding; document and analyze.

## 13. Expected Outcomes

### 13.1 Performance predictions

| Configuration | Expected Driving Score Change | Rationale |
|--------------|-------------------------------|-----------|
| `high_fps` | +5% to +15% | Faster reaction time, smoother control |
| `high_res` | +3% to +10% | Better distant object detection |
| `no_noise` | +10% to +20% | Clearer images, better feature extraction |
| `high_fps,high_res,no_noise` | +15% to +35% | Combined benefits |

### 13.2 Comparison with post-processing

We expect:
- Native `high_fps` (40Hz) > Interpolated FI (20Hz â†?40Hz)
- Native `high_res` (1600x1200) â‰?Upscaled SR (800x600 â†?1600x1200)
- Native `no_noise` â‰?Denoised DN (noisy â†?clean)

This will validate whether hardware or software upgrades are more effective.


