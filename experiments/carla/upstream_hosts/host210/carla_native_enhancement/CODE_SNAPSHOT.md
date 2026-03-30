# Code Snapshot (Baseline Behavior) â€?captured 2026-02-04

This document describes the **current baseline behavior** in `./` before implementing the CARLA native sensor enhancement method.

## 1. Baseline entry points

### 1.1 Primary workflow
- Directory: `leaderboard/team_code/`
- Agent: `leaderboard/team_code/interfuser_agent.py`
- Evaluator: `leaderboard/leaderboard/leaderboard_evaluator.py`

### 1.2 Baseline sensor configuration

The baseline InterfuserAgent defines sensors in the `sensors()` method:

```python
def sensors(self):
    return [
        {
            "type": "sensor.camera.rgb",
            "x": 1.3, "y": 0.0, "z": 2.3,
            "roll": 0.0, "pitch": 0.0, "yaw": 0.0,
            "width": 800,
            "height": 600,
            "fov": 100,
            "id": "rgb",
        },
        # ... similar for rgb_left, rgb_right
        {
            "type": "sensor.other.imu",
            "sensor_tick": 0.05,  # 20Hz
            "id": "imu",
        },
        {
            "type": "sensor.other.gnss",
            "sensor_tick": 0.01,  # 100Hz
            "id": "gps",
        },
        # ... lidar, speedometer
    ]
```

**Key baseline parameters:**
- Camera resolution: 800x600
- Camera sensor_tick: not specified (defaults to world tick rate)
- World tick rate: 20Hz (fixed_delta_seconds = 0.05)
- No explicit noise/post-processing configuration (uses CARLA defaults)

## 2. World simulation configuration

File: `leaderboard/leaderboard/leaderboard_evaluator.py`

```python
def _load_and_wait_for_world(self, args, town, ego_vehicles=None):
    self.world = self.client.load_world(town)
    settings = self.world.get_settings()
    settings.fixed_delta_seconds = 1.0 / self.frame_rate  # Default: 20Hz
    settings.synchronous_mode = True
    self.world.apply_settings(settings)
```

**Baseline world settings:**
- `frame_rate`: 20 (from evaluator initialization)
- `fixed_delta_seconds`: 0.05 (1/20)
- `synchronous_mode`: True

## 3. Agent behavior (baseline)

### 3.1 run_step frequency

The agent's `run_step(input_data, timestamp)` is called once per world tick:
- Frequency: 20 times per second
- Time between calls: 0.05 seconds

### 3.2 Internal step counter

```python
def run_step(self, input_data, timestamp):
    if not self.initialized:
        self._init()
    
    self.step += 1  # Increments once per world tick
    
    if self.step % self.skip_frames != 0 and self.step > 4:
        return self.prev_control  # Skip processing
    
    # ... normal processing
```

**Key behavior:**
- `self.step` increments once per world tick (20 times per second).
- `skip_frames` logic: agent may skip processing on some frames.
- Default `skip_frames`: typically 0 or 1 (processes every frame or every other frame).

### 3.3 Image preprocessing

```python
# Front camera: resize to 224x224
self.rgb_front_transform = create_carla_rgb_transform(224)

# Side cameras: resize to 128x128
self.rgb_left_transform = create_carla_rgb_transform(128)
self.rgb_right_transform = create_carla_rgb_transform(128)
```

Images are resized from 800x600 to these dimensions before feeding to the model.

## 4. Sensor data flow

```
CARLA World (20Hz tick)
    â†?Sensors capture data (20Hz for cameras, varies for others)
    â†?CallBack â†?SensorInterface.update_sensor()
    â†?Data stored in Queue (_new_data_buffers)
    â†?SensorInterface.get_data() waits for all sensors
    â†?Agent.run_step(input_data, timestamp)
    â†?Agent returns VehicleControl
    â†?Control applied to vehicle
```

### 4.1 SensorInterface.get_data() behavior

File: `leaderboard/leaderboard/envs/sensor_interface.py`

```python
def get_data(self):
    try: 
        data_dict = {}
        while len(data_dict.keys()) < len(self._sensors_objects.keys()):
            # Wait for all sensors (blocks until data available)
            sensor_data = self._new_data_buffers.get(True, self._queue_timeout)
            data_dict[sensor_data[0]] = ((sensor_data[1], sensor_data[2]))
    except Empty:
        raise SensorReceivedNoData("A sensor took too long to send their data")
    
    return data_dict
```

**Key behavior:**
- Blocks until all sensors have provided data for the current tick.
- Uses FIFO queue (first data in, first data out).
- Timeout: 10 seconds (configurable via `SENSOR_QUEUE_TIMEOUT`).

## 5. CARLA camera post-processing (defaults)

When no explicit attributes are set, CARLA cameras use these defaults:

```python
# From CARLA documentation
"bloom_intensity": 0.675,
"lens_flare_intensity": 0.1,
"motion_blur_intensity": 0.45,
"motion_blur_max_distortion": 0.35,
"chromatic_aberration_intensity": 0.0,
"lens_circle_falloff": 5.0,
"lens_circle_multiplier": 0.0,
```

These post-processing effects simulate realistic camera artifacts.

## 6. Baseline stability rule

This snapshot corresponds to the state where the baseline InterfuserAgent produces valid results on standard Leaderboard routes. The new method must not change this baseline behavior when `NATIVE_ENHANCE=none`.

## 7. New method runner (isolated)

The new CARLA native enhancement method is implemented under `carla_native_enhancement/` and is intended to be executed via an isolated runner:
- `carla_native_enhancement/run_evaluation_native.sh`

Key differences vs baseline runner:
- Instead of using the default agent, the runner deploys `carla_native_enhancement/interfuser_agent_native.py`.
- Sensor configurations are modified based on `NATIVE_ENHANCE` environment variable.
- World tick rate may be changed (20Hz â†?40Hz for `high_fps`).
- When `AUTO_START_CARLA=1`, the runner will start CARLA automatically with appropriate settings.

## 8. Critical implementation notes

### 8.1 High FPS implementation

When `high_fps` is enabled:
1. World `fixed_delta_seconds` must be changed to 0.025 (40Hz).
2. Camera `sensor_tick` should be set to 0.025 (or omitted to use world tick).
3. Agent `run_step()` will be called 40 times per second automatically.
4. No changes needed to agent logic (it adapts automatically).

### 8.2 High resolution implementation

When `high_res` is enabled:
1. Camera `width` and `height` are changed to 1600x1200.
2. Agent preprocessing still resizes to 224x224 (or 128x128).
3. Model input dimensions remain unchanged.
4. Benefit: downsampling from higher resolution preserves more details.

### 8.3 No noise implementation

When `no_noise` is enabled:
1. Set camera attributes to disable post-processing:
   - `bloom_intensity`: 0.0
   - `lens_flare_intensity`: 0.0
   - `motion_blur_intensity`: 0.0
   - `motion_blur_max_distortion`: 0.0
2. Optionally disable lens distortion:
   - `lens_circle_falloff`: 0.0
   - `lens_k`: 0.0
   - `lens_kcube`: 0.0

## 9. Comparison with augmentation_seq_method

| Aspect | Baseline | augmentation_seq_method | carla_native_enhancement |
|--------|----------|------------------------|-------------------------|
| **World tick** | 20Hz | 20Hz | 20Hz or 40Hz |
| **Camera config** | 800x600, defaults | 800x600, defaults | Configurable |
| **Processing** | None | Post-processing (SwinIR/SRGAN/RIFE) | None (native quality) |
| **Agent frequency** | 20Hz | 20Hz (with FI: 2 updates per tick) | 20Hz or 40Hz |
| **Model input** | 224x224 | 224x224 | 224x224 |


