# Meta 目录文件缺失问题 - 分析与解决方�?
## 问题现象

�?`data/eval_native/` 目录下，虽然 `meta` 目录被创建了，但是里面没有图像文件（或只有很少的文件）�?
## 问题原因

**评估过程提前失败或中�?*，没有运行足够长的时间来生成帧数据�?
### 具体分析

检查日志后发现以下问题�?
#### 1. CARLA 服务器超�?```
RuntimeError: time-out of 10000ms while waiting for the simulator
```
- 评估无法启动
- meta 目录创建但保持为�?
#### 2. CARLA 服务器崩�?```
ERROR: Invalid session: no stream available with id 1
Exiting abnormally (error code: 130)
```
- 这是 CARLA 的已知问�?- 通常与传感器流同步问题有�?
#### 3. 评估过早终止
- 只生成了 1 帧图�?- 可能由于场景加载错误

## Meta 文件位置

实际的目录结构：
```
data/eval_native/
└── town05_high_fps_20260204_180529/          # 评估根目�?    ├── evaluation_metadata.json               # 评估元数�?    ├── leaderboard_evaluator.log              # 评估日志
    ├── carla_server_28362.log                 # CARLA 日志
    └── routes_town05_long_02_04_18_07_19/    # 路线子目�?        └── meta/                              # �?Meta 文件在这里！
            ├── 0000.jpg                       # �?0 �?            ├── 0001.jpg                       # �?1 �?            └── ...
```

**重要**：meta 目录�?`routes_xxx/` 子目录下，不是直接在评估根目录下�?
## 解决方案

### 方案 1：应用同步模式修复（推荐）✅

已经修改�?`interfuser_agent_native.py`，添加了同步模式支持�?
```python
# �?run_step() 中自动应用同步模�?settings.synchronous_mode = True
settings.fixed_delta_seconds = 1.0 / frame_rate
```

**优点**�?- 防止传感器流不匹�?- 减少超时错误
- 提高稳定�?
### 方案 2：增加超时时�?
```bash
export EVAL_TIMEOUT=1200        # 增加�?20 分钟
export CARLA_TICK_TIMEOUT=1200
```

### 方案 3：使用快速测�?
先用短路线测试配置是否正常：

```bash
# 测试基线配置（无增强�?bash carla_native_enhancement/test_quick.sh none

# 测试高帧�?bash carla_native_enhancement/test_quick.sh high_fps

# 测试组合
bash carla_native_enhancement/test_quick.sh "high_fps,no_noise"
```

## 验证步骤

### 1. 检查文件数�?
```bash
# 找到最新的评估目录
LATEST_EVAL=$(ls -td data/eval_native/town05_* | head -1)

# 统计 meta 文件数量
find "${LATEST_EVAL}" -name "*.jpg" | wc -l

# 正常情况应该有数百到数千个文�?```

### 2. 查看评估日志

```bash
cat "${LATEST_EVAL}/leaderboard_evaluator.log"
```

**正常日志应该包含**�?- �?"Running the route" 消息
- �?路线进度信息
- �?没有 "time-out" 错误
- �?没有 "ERROR" �?"Exception"

### 3. 查看 CARLA 日志

```bash
cat "${LATEST_EVAL}"/carla_server_*.log
```

**正常日志应该包含**�?- �?正常启动消息
- �?没有 "Invalid session" 错误
- �?没有 "Exiting abnormally"

## 运行诊断

如果问题仍然存在，运行诊断脚本：

```bash
bash carla_native_enhancement/collect_diagnostics.sh
```

诊断脚本会检查：
- 系统信息（OS、GPU、Python�?- CARLA 版本和状�?- 最近的评估结果
- 端口占用情况
- Python 依赖�?
## 常见问题

### Q1: 为什么有些评估有文件，有些没有？

**A**: 取决于评估是否成功运行：

| 情况 | 文件�?| 原因 |
|------|--------|------|
| CARLA 早期崩溃 | 0 �?| 服务器启动失�?|
| 评估运行一小段时间 | 1-10 �?| 中途崩溃或超时 |
| 评估正常完成 | 数百到数千个 | 正常运行 |

### Q2: 应该有多少个 meta 文件�?
**A**: 估算公式�?```
文件�?= 路线�?× 平均时长(�? × 帧率 / skip_frames

示例�?2 routes）：
  = 42 × 45�?× 20Hz / 2
  = 18,900 个文�?```

### Q3: 如何实时查看进度�?
**A**: 使用以下命令�?
```bash
# 实时查看日志
tail -f data/eval_native/YOUR_EVAL_DIR/leaderboard_evaluator.log

# 实时统计文件�?watch -n 5 'find data/eval_native/YOUR_EVAL_DIR -name "*.jpg" | wc -l'

# 查看最新生成的图像
ls -lt data/eval_native/YOUR_EVAL_DIR/routes_*/meta/*.jpg | head -5
```

### Q4: GPU 内存不足怎么办？

**A**: 降低配置�?
1. **不使用高分辨�?*�?   ```bash
   # 避免 high_res，保�?800×600
   bash run_evaluation_native.sh town05 high_fps
   ```

2. **单独测试每个增强**�?   ```bash
   # 不要组合多个增强
   bash run_evaluation_native.sh town05 high_fps      # �?   bash run_evaluation_native.sh town05 no_noise      # �?   # 避免：high_fps,high_res,no_noise                 # �?   ```

3. **关闭其他 GPU 应用**�?   ```bash
   # 检�?GPU 使用情况
   nvidia-smi
   ```

### Q5: 可以手动启动 CARLA 吗？

**A**: 可以，分两步�?
```bash
# 终端 1：手动启�?CARLA
cd ./carla
DISPLAY=:99 ./CarlaUE4.sh -opengl -RenderOffScreen -world-port=2000

# 等待 1-2 分钟，直到看�?"Listening on port 2000"

# 终端 2：运行评估（不自动启�?CARLA�?cd .
export AUTO_START_CARLA=0
export PORT=2000
bash carla_native_enhancement/run_evaluation_native.sh town05 high_fps
```

## 推荐流程

### 第一步：快速测�?
```bash
cd .

# 测试基线配置
bash carla_native_enhancement/test_quick.sh none
```

### 第二步：检查结�?
```bash
# 查看最新评�?LATEST=$(ls -td data/eval_native/custom_* | head -1)

# 统计文件
find "${LATEST}" -name "*.jpg" | wc -l

# 如果有文件生成，说明配置正常 �?```

### 第三步：运行完整评估

```bash
# 基线配置
bash carla_native_enhancement/run_evaluation_native.sh town05 none

# 高帧率配�?bash carla_native_enhancement/run_evaluation_native.sh town05 high_fps

# 无噪声配�?bash carla_native_enhancement/run_evaluation_native.sh town05 no_noise
```

### 第四步：批量运行

```bash
# 运行所有配�?bash carla_native_enhancement/run_remaining_7_configs_safe.sh
```

## 故障排查

如果测试失败，按以下顺序检查：

1. **运行诊断**�?   ```bash
   bash carla_native_enhancement/collect_diagnostics.sh
   ```

2. **查看详细故障排查指南**�?   ```bash
   cat carla_native_enhancement/TROUBLESHOOTING.md
   ```

3. **检查系统要�?*�?   - GPU: 至少 6GB VRAM（推�?8GB+�?   - Python: 3.7
   - CARLA: 0.9.10
   - CUDA: 10.x �?11.x

4. **检查端�?*�?   ```bash
   # 确保端口未被占用
   netstat -tuln | grep 2000
   ```

5. **检�?CARLA 进程**�?   ```bash
   # 清理旧进�?   pkill -9 CarlaUE4
   ```

## 相关文件

| 文件 | 说明 |
|------|------|
| `META_FILES_ISSUE_SUMMARY.md` | 本文档（英文版） |
| `TROUBLESHOOTING.md` | 详细故障排查指南 |
| `collect_diagnostics.sh` | 诊断信息收集脚本 |
| `test_quick.sh` | 快速测试脚�?|
| `interfuser_agent_native.py` | 已修复的 agent |

## 更新记录

- **2026-02-04 18:30**: 识别问题根本原因
- **2026-02-04 18:45**: 实施同步模式修复
- **2026-02-04 19:00**: 创建诊断和测试工�?- **2026-02-04 19:15**: 完成文档

## 总结

**问题**：meta 目录下没有文件生�?
**原因**：CARLA 服务器超时或崩溃，评估提前终�?
**解决**�?1. �?应用同步模式修复（已实施�?2. �?增加超时时间
3. �?使用快速测试验�?4. �?运行诊断工具

**下一�?*：运�?`test_quick.sh` 验证修复是否有效

