# Meta 目录文件缺失问题 - 分析与解决方案

## 问题描述

在 `data/eval_native/` 目录下，虽然 `meta` 目录被创建了，但是里面没有图像文件生成（或只有很少的文件）。

## 根本原因

**评估过程在早期就失败或中断了**，没有运行足够长的时间来生成帧数据。

### 具体原因分析

通过检查日志文件发现：

1. **CARLA 服务器超时**（第一批评估）：
   ```
   RuntimeError: time-out of 10000ms while waiting for the simulator
   ```
   - 评估根本没有开始运行
   - meta 目录被创建但保持为空

2. **CARLA 服务器崩溃**（第一批评估）：
   ```
   ERROR: Invalid session: no stream available with id 1
   FUnixPlatformMisc::RequestExitWithStatus
   Exiting abnormally (error code: 130)
   ```
   - 这是一个已知的 CARLA 传感器流问题
   - 通常与异步模式下的传感器同步问题有关

3. **评估过早终止**（第二批评估）：
   - 只生成了 1 帧图像（`0000.jpg`）
   - 可能由于场景加载错误或其他问题导致

## 目录结构说明

Meta 文件的实际位置：
```
data/eval_native/
└── town05_high_fps_20260204_180529/          # 评估根目录
    ├── evaluation_metadata.json
    ├── leaderboard_evaluator.log
    ├── carla_server_28362.log
    └── routes_town05_long_02_04_18_07_19/    # 路线子目录
        └── meta/                              # ← Meta 文件在这里！
            └── 0000.jpg                       # 帧图像
            └── 0001.jpg
            └── ...
```

**注意**：meta 目录不是直接在评估根目录下，而是在 `routes_xxx/` 子目录下。

## 解决方案

### 1. 应用同步模式修复（已实施）

修改了 `interfuser_agent_native.py`，在 `run_step()` 方法中添加：

```python
# 应用世界设置（同步模式 + 固定时间步长）
if not self.world_settings_applied:
    client = carla.Client('localhost', int(os.environ.get('PORT', '2000')))
    client.set_timeout(30.0)
    world = client.get_world()
    
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 1.0 / self.native_config.frame_rate
    world.apply_settings(settings)
    
    self.world_settings_applied = True
```

**为什么这样做**：
- 同步模式确保传感器数据按顺序到达
- 固定时间步长防止传感器流不匹配
- 减少 "no stream available" 错误

### 2. 增加超时时间

在运行评估前设置：

```bash
export EVAL_TIMEOUT=1200        # 从 600 增加到 1200 秒
export CARLA_TICK_TIMEOUT=1200
```

### 3. 使用快速测试脚本

验证配置是否工作：

```bash
# 测试基线配置
bash carla_native_enhancement/test_quick.sh none

# 测试 high_fps
bash carla_native_enhancement/test_quick.sh high_fps

# 测试组合
bash carla_native_enhancement/test_quick.sh "high_fps,no_noise"
```

### 4. 运行诊断

如果问题仍然存在：

```bash
bash carla_native_enhancement/collect_diagnostics.sh
```

## 验证修复

### 检查评估是否成功

```bash
# 找到最新的评估目录
LATEST_EVAL=$(ls -td data/eval_native/town05_* | head -1)

# 检查 meta 文件数量
find "${LATEST_EVAL}" -name "*.jpg" | wc -l

# 应该看到多个文件（取决于评估长度）
# 例如：42 routes × 平均 50 帧 = ~2100 个文件
```

### 检查日志

```bash
# 查看评估日志
cat "${LATEST_EVAL}/leaderboard_evaluator.log"

# 应该看到：
# - "Running the route" 消息
# - 没有 "time-out" 或 "ERROR" 消息
# - 正常的评估进度输出
```

### 检查 CARLA 日志

```bash
# 查看 CARLA 服务器日志
cat "${LATEST_EVAL}"/carla_server_*.log

# 应该看到：
# - 正常的启动消息
# - 没有 "Invalid session" 错误
# - 没有 "Exiting abnormally" 消息
```

## 常见问题

### Q1: 为什么有些评估有文件，有些没有？

**A**: 这取决于评估是否成功运行：
- 如果 CARLA 在早期崩溃 → 0 个文件
- 如果评估运行了一小段时间 → 少量文件（1-10 个）
- 如果评估正常完成 → 大量文件（数百到数千个）

### Q2: Meta 文件应该有多少个？

**A**: 取决于：
- 路线数量（例如 42 routes）
- 每条路线的长度（例如平均 30-60 秒）
- 帧率（20Hz 或 40Hz）
- skip_frames 设置（默认每 2 帧保存一次）

**估算**：
```
文件数 ≈ 路线数 × 平均时长(秒) × 帧率 / skip_frames
      ≈ 42 × 45 × 20 / 2
      ≈ 18,900 个文件
```

### Q3: 如何减少 GPU 内存使用？

**A**: 
1. 不使用 `high_res`（保持 800×600）
2. 先测试单个增强，不要组合
3. 减少并发评估数量
4. 关闭其他 GPU 应用

### Q4: 可以在评估过程中查看进度吗？

**A**: 可以，使用：
```bash
# 实时查看日志
tail -f data/eval_native/YOUR_EVAL_DIR/leaderboard_evaluator.log

# 实时统计文件数
watch -n 5 'find data/eval_native/YOUR_EVAL_DIR -name "*.jpg" | wc -l'
```

## 下一步

1. **运行快速测试**：
   ```bash
   bash carla_native_enhancement/test_quick.sh none
   ```

2. **如果测试成功**，运行完整评估：
   ```bash
   bash carla_native_enhancement/run_evaluation_native.sh town05 high_fps
   ```

3. **如果测试失败**，查看故障排查指南：
   ```bash
   cat carla_native_enhancement/TROUBLESHOOTING.md
   ```

## 相关文件

- `TROUBLESHOOTING.md` - 详细的故障排查指南
- `collect_diagnostics.sh` - 诊断信息收集脚本
- `test_quick.sh` - 快速测试脚本
- `interfuser_agent_native.py` - 已修复的 agent（包含同步模式）

## 更新日志

- **2026-02-04**: 识别问题根本原因（CARLA 超时/崩溃）
- **2026-02-04**: 实施同步模式修复
- **2026-02-04**: 创建诊断和测试工具
