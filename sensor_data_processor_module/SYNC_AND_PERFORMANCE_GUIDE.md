# Agent 与模拟器同步指南

## 📋 问题背景

在 CARLA 评估中，如果数据处理（特别是图像处理）时间过长，可能导致：
- ⏱️ 评估效率降低（模拟时间 ≠ 真实时间）
- ⚠️ 触发 watchdog timeout
- 🐌 帧率下降，影响评估质量

本文档提供完整的同步和性能优化方案。

---

## 🔍 当前同步机制

### CARLA Leaderboard 已使用同步模式

查看 `leaderboard/leaderboard/leaderboard_evaluator.py:209-211`：

```python
settings = self.world.get_settings()
settings.fixed_delta_seconds = 1.0 / self.frame_rate  # 固定时间步长
settings.synchronous_mode = True                       # 同步模式
self.world.apply_settings(settings)
```

**关键参数：**
- `frame_rate = 20.0 Hz`（每帧 50ms）
- `synchronous_mode = True`（模拟器等待 agent）
- `timeout = 10.0 秒`（agent 最大响应时间）

### 同步模式工作原理

```
┌─────────────────────────────────────────────────────────┐
│                    同步模式流程                           │
└─────────────────────────────────────────────────────────┘

1. CARLA 等待 ──→ world.tick()
                      ↓
2. 采集传感器数据 ──→ input_data
                      ↓
3. Agent 处理 ────→ run_step(input_data)
   ├─ tick()         ← 数据处理在这里！
   ├─ 模型推理
   └─ 控制生成
                      ↓
4. 应用控制 ──────→ vehicle.apply_control()
                      ↓
5. 模拟一帧 ──────→ world.tick() ──→ 回到步骤 1

⏱️ 每帧理论时间: 50ms (20 Hz)
⏱️ Agent 必须在 timeout 内完成
```

**好消息：** 模拟器会等待 agent 完成，不会"跑掉"

**坏消息：** 如果处理时间过长：
- 模拟时间 ≠ 真实时间（例如：模拟 1 秒 = 真实 2 秒）
- 评估效率降低（评估 50 条路线可能需要数天）
- 可能触发 timeout（默认 10 秒）

---

## 🎯 性能目标

### 理想性能指标

| 指标 | 目标 | 可接受 | 问题 |
|------|------|--------|------|
| **每帧处理时间** | < 50ms | < 100ms | > 200ms |
| **帧率** | 20 FPS | > 10 FPS | < 5 FPS |
| **模拟/真实时间比** | 1:1 | 1:2 | 1:4+ |
| **Timeout 触发** | 0 次 | < 5 次 | 频繁 |

### 数据处理器性能影响

根据 `PERFORMANCE_ANALYSIS.md`：

| 配置 | 额外开销 | 总处理时间 | 帧率影响 |
|------|---------|-----------|---------|
| **无处理** | 0ms | ~52ms | 19.2 FPS ✅ |
| **mild** | +3-5ms | ~55-57ms | 17.5 FPS ✅ |
| **moderate** | +5-10ms | ~57-62ms | 16.1 FPS ⚠️ |
| **severe** | +15-28ms | ~67-80ms | 12.5 FPS ⛔ |

---

## ✅ 解决方案

### 方案 1：优化数据处理性能（推荐）⭐⭐⭐

#### 1.1 关闭调试功能

**编辑 `data_processor_config.py`：**

```python
# ❌ 不要这样（会严重影响性能）
CONFIG_MODERATE_NOISE = {
    "save_processed_images": True,   # 保存图像，每帧 +50-100ms
    "save_path": "processed_sensor_data",
    "log_level": "DEBUG",            # 详细日志，每帧 +5-10ms
    # ...
}

# ✅ 应该这样
CONFIG_MODERATE_NOISE = {
    "save_processed_images": False,  # 关闭保存，节省 50-100ms
    "save_path": "",
    "log_level": "WARNING",          # 只记录警告，节省 5-10ms
    # ...
}
```

**性能提升：** ~60-110ms/帧

#### 1.2 使用轻度配置

```python
# 使用轻度噪声配置
ACTIVE_CONFIG = CONFIG_MILD_NOISE  # +3-5ms，可接受
```

#### 1.3 优化图像处理

```python
# data_processor.py 中的优化

# ❌ 慢速方法
def process_rgb(self, rgb_data, sensor_id="rgb"):
    img_pil = Image.fromarray(rgb_data)  # NumPy → PIL
    # ... 各种 PIL 操作 ...
    return np.array(img_pil)              # PIL → NumPy

# ✅ 快速方法（使用 OpenCV）
def process_rgb_fast(self, rgb_data, sensor_id="rgb"):
    # 直接使用 NumPy/OpenCV 操作
    if self.rgb_effects_config["add_gaussian_noise"]["enabled"]:
        noise = np.random.normal(0, std, rgb_data.shape).astype(np.int16)
        rgb_data = np.clip(rgb_data.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return rgb_data
```

### 方案 2：调整模拟器帧率

#### 2.1 降低帧率（牺牲精度换速度）

**编辑 `leaderboard/leaderboard/leaderboard_evaluator.py`：**

```python
class LeaderboardEvaluator(object):
    # 从 20 Hz 降低到 10 Hz
    frame_rate = 10.0  # 原来是 20.0
```

**或者在评估脚本中设置环境变量：**

```bash
# 暂不支持，需要修改代码
```

**效果：**
- 每帧时间：50ms → 100ms
- 允许更多处理时间
- 但可能影响控制精度

#### 2.2 调整 skip_frames

**在 `interfuser_config.py` 中：**

```python
class GlobalConfig:
    skip_frames = 1  # 原来可能是 1，可以改为 2
```

**效果：**
- Agent 每 2 帧才处理一次
- 处理压力降低 50%
- 但反应速度下降

### 方案 3：增加 Timeout（治标不治本）

**编辑 `leaderboard/leaderboard/leaderboard_evaluator.py`：**

```python
class LeaderboardEvaluator(object):
    client_timeout = 20.0  # 从 10.0 增加到 20.0
```

**仅用于：**
- 临时解决 timeout 问题
- 不改善性能，只避免崩溃

### 方案 4：使用性能监控定位瓶颈⭐⭐

**在 `interfuser_agent_complete.py` 中启用监控：**

```python
class InterfuserAgent(autonomous_agent.AutonomousAgent):
    def setup(self, path_to_conf_file):
        # ...
        self.enable_performance_monitoring = True  # 启用监控
```

**运行评估后查看报告：**

```bash
./run_evaluation_with_processor.sh town05 moderate

# 评估结束时会输出：
# ⏱️  Data Processing Performance Report
# ======================================================================
#   RGB         : avg=  5.23ms, max= 12.45ms, min=  2.10ms
#   LIDAR       : avg=  3.12ms, max=  8.30ms, min=  1.50ms
#   GPS         : avg=  0.15ms, max=  0.50ms, min=  0.05ms
#   TOTAL       : avg=  8.50ms, max= 21.25ms, min=  3.65ms
# ======================================================================
```

**根据报告优化：**
- 如果 RGB 时间过长 → 简化 RGB 处理
- 如果 LIDAR 时间过长 → 减少点云处理
- 如果 TOTAL > 50ms → 考虑降低帧率

### 方案 5：异步处理（高级）⭐

**使用多线程预处理：**

```python
from concurrent.futures import ThreadPoolExecutor

class InterfuserAgent(autonomous_agent.AutonomousAgent):
    def setup(self, path_to_conf_file):
        # ...
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.processing_future = None
    
    def tick(self, input_data):
        # 启动异步处理
        if self.processing_future is None:
            self.processing_future = self.executor.submit(
                self._process_data_async, input_data
            )
        
        # 获取结果（如果还没完成，会等待）
        result = self.processing_future.result(timeout=1.0)
        
        # 启动下一帧的处理
        self.processing_future = self.executor.submit(
            self._process_data_async, input_data
        )
        
        return result
```

⚠️ **注意：** 异步处理复杂，可能引入延迟，谨慎使用。

---

## 📊 性能优化清单

### 立即可做（推荐）✅

- [ ] **关闭图像保存** (`save_processed_images = False`)
- [ ] **降低日志级别** (`log_level = "WARNING"`)
- [ ] **使用轻度配置** (`ACTIVE_CONFIG = CONFIG_MILD_NOISE`)
- [ ] **启用性能监控** (`enable_performance_monitoring = True`)

**预期效果：** 节省 60-110ms/帧，帧率从 12 FPS → 18 FPS

### 可以尝试

- [ ] 增加 `skip_frames` (1 → 2)
- [ ] 降低帧率 (20 Hz → 15 Hz)
- [ ] 增加 timeout (10s → 20s)

### 高级优化

- [ ] 使用 OpenCV 替代 PIL
- [ ] 优化算法（减少不必要的拷贝）
- [ ] GPU 加速数据处理
- [ ] 异步处理

---

## 🔧 实践示例

### 示例 1：优化配置用于快速评估

**创建 `data_processor_config.py` 的快速模式：**

```python
CONFIG_FAST_MILD = {
    "enabled": True,
    "save_processed_images": False,  # 关键！
    "save_path": "",
    "log_level": "ERROR",            # 关键！
    "rgb_effects": {
        "add_gaussian_noise": {"enabled": True, "mean": 0, "std": 5},
        # 只启用最重要的效果
    },
    "lidar_effects": {
        "add_noise": {"enabled": True, "mean": 0, "std": 0.05},
    },
    "gps_effects": {},     # 禁用 GPS 处理
    "other_effects": {},   # 禁用其他处理
}

ACTIVE_CONFIG = CONFIG_FAST_MILD
```

**运行评估：**

```bash
./run_evaluation_with_processor.sh town05 custom
```

### 示例 2：性能分析工作流

```bash
# 1. 启用性能监控
# 编辑 interfuser_agent_complete.py:
#   self.enable_performance_monitoring = True

# 2. 运行短评估
ROUTES=leaderboard/data/evaluation_routes/routes_town01_short.xml \
./run_evaluation_with_processor.sh custom moderate

# 3. 查看性能报告
# 评估结束时会输出详细的性能数据

# 4. 根据报告调整配置

# 5. 重新评估验证
```

### 示例 3：对比不同配置的性能

```bash
# 测试无处理
./run_evaluation_with_processor.sh town05 custom  # ACTIVE_CONFIG enabled=False

# 测试轻度处理
./run_evaluation_with_processor.sh town05 mild

# 测试中度处理
./run_evaluation_with_processor.sh town05 moderate

# 对比结果（包含性能数据）
python3 analyze_results.py -c results/with_processor/*.json
```

---

## 📈 性能监控和诊断

### 监控指标

1. **每帧处理时间**
   ```python
   # 在 tick() 方法开始和结束添加计时
   start = time.time()
   # ... 处理 ...
   elapsed = (time.time() - start) * 1000  # ms
   ```

2. **帧率**
   ```bash
   # CARLA 窗口会显示实时 FPS
   # 或查看日志中的时间戳
   ```

3. **Timeout 次数**
   ```bash
   # 查看评估日志中的 timeout 警告
   grep -i "timeout" evaluation.log
   ```

### 诊断问题

**问题：帧率低于 10 FPS**

```bash
# 检查：
1. 关闭了图像保存吗？
2. 日志级别是否为 WARNING 或更高？
3. 是否使用了 severe 配置？
4. GPU 内存是否充足？

# 解决：
- 切换到 mild 配置
- 关闭所有调试功能
- 增加 skip_frames
```

**问题：频繁 Timeout**

```bash
# 检查：
1. 单帧处理时间是否超过 5 秒？
2. 是否有内存泄漏？
3. 模型推理是否正常？

# 解决：
- 增加 timeout 时间（临时）
- 优化数据处理
- 检查系统资源
```

---

## 🎯 最佳实践总结

### 日常评估（推荐配置）

```python
# data_processor_config.py
ACTIVE_CONFIG = {
    "enabled": True,
    "save_processed_images": False,      # ← 必须关闭
    "log_level": "WARNING",              # ← 必须设置
    "rgb_effects": {
        "add_gaussian_noise": {"enabled": True, "std": 5},  # 轻度
    },
    "lidar_effects": {
        "add_noise": {"enabled": True, "std": 0.05},
    },
    # 其他效果根据需要启用
}
```

**性能：** ~18 FPS，可接受

### 研究用途（详细分析）

```python
# 开启所有调试功能
ACTIVE_CONFIG = {
    "enabled": True,
    "save_processed_images": True,       # 保存对比图像
    "log_level": "DEBUG",                # 详细日志
    "rgb_effects": { ... },              # 完整配置
}

# 使用短路线
ROUTES=leaderboard/data/evaluation_routes/routes_town01_short.xml
```

**性能：** ~8 FPS，仅用于少量路线的详细分析

### 离线分析（最大噪声）

```python
ACTIVE_CONFIG = CONFIG_SEVERE_NOISE

# 降低帧率
# 修改 leaderboard_evaluator.py: frame_rate = 10.0
```

**性能：** ~5 FPS，用于压力测试

---

## 📚 相关文档

- `PERFORMANCE_ANALYSIS.md` - 详细的性能分析数据
- `EVALUATION_GUIDE.md` - 评估流程和配置
- `DATA_PROCESSOR_USAGE_GUIDE.md` - 数据处理器使用指南

---

## 🔍 FAQ

### Q1: 为什么我的评估这么慢？

**A:** 检查以下几点：
1. `save_processed_images` 是否设置为 `False`
2. `log_level` 是否设置为 `WARNING` 或更高
3. 是否使用了 `severe` 或 `failure` 配置
4. 是否启用了性能监控（仅用于调试）

### Q2: 如何知道我的配置是否太重？

**A:** 
```python
# 启用性能监控
self.enable_performance_monitoring = True

# 运行评估，查看报告
# 如果 TOTAL > 50ms，说明配置太重
```

### Q3: 同步模式会影响评估结果吗？

**A:** 不会。同步模式确保：
- 每帧时间固定（50ms 模拟时间）
- Agent 有充足时间处理
- 结果具有可重复性

只是真实时间会变长。

### Q4: 能否使用异步模式加速？

**A:** 不推荐。CARLA Leaderboard 设计为同步模式：
- 确保确定性
- 便于调试
- 结果可重复

异步模式会引入不确定性。

### Q5: 我的 GPU 很强，为什么还是慢？

**A:** 数据处理器主要使用 CPU：
- 图像处理（PIL/OpenCV）在 CPU
- LiDAR 处理在 CPU
- 模型推理在 GPU（不受影响）

优化 CPU 代码更重要。

---

**总结：保持 agent 和模拟器同步的关键是优化数据处理性能，而不是修改同步机制！** ✅

