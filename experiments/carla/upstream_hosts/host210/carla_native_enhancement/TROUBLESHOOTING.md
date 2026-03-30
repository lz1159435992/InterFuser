# CARLA Native Enhancement - 故障排查指南

## 问题：meta 目录下没有文件生�?
### 症状
- `data/eval_native/` 下的评估目录中，`routes_xxx/meta/` 目录存在但为�?- 或者只有很少的图像文件�?-2 张）

### 根本原因
评估过程在早期就失败或中断了，没有运行足够长的时间来生成帧数据�?
### 常见原因

#### 1. CARLA 服务器超�?崩溃

**症状**�?```
RuntimeError: time-out of 10000ms while waiting for the simulator
```

**检查方�?*�?```bash
# 查看 CARLA 服务器日�?cat data/eval_native/YOUR_EVAL_DIR/carla_server_*.log

# 查看评估日志
cat data/eval_native/YOUR_EVAL_DIR/leaderboard_evaluator.log
```

**常见错误**�?- `ERROR: Invalid session: no stream available with id 1`
- `FUnixPlatformMisc::RequestExitWithStatus`
- `Exiting abnormally (error code: 130)`

**解决方案**�?
1. **增加超时时间**�?   ```bash
   export EVAL_TIMEOUT=1200  # �?600 增加�?1200 �?   export CARLA_TICK_TIMEOUT=1200
   ```

2. **使用同步模式**（推荐）�?   �?`interfuser_agent_native.py` �?`setup()` 方法中添加：
   ```python
   # �?setup() 方法末尾添加
   self.world_settings_applied = False
   ```
   
   �?`run_step()` 方法开始处添加�?   ```python
   if not self.world_settings_applied:
       world = self._world
       settings = world.get_settings()
       settings.synchronous_mode = True
       settings.fixed_delta_seconds = 1.0 / self.native_config.frame_rate
       world.apply_settings(settings)
       self.world_settings_applied = True
   ```

3. **降低传感器负�?*�?   - 先测�?`NATIVE_ENHANCE=none`（基线配置）
   - 确认基线工作后，再逐步添加增强

4. **检�?GPU 内存**�?   ```bash
   nvidia-smi
   ```
   如果 GPU 内存不足，尝试：
   - 降低分辨率（不使�?`high_res`�?   - 减少并发评估数量

#### 2. 端口冲突

**症状**�?```
Address already in use
```

**解决方案**�?```bash
# 使用随机端口
export PORT=random

# 或手动指定未使用的端�?export PORT=3000
```

#### 3. Python 环境问题

**症状**�?```
ImportError: cannot import name 'xxx'
ModuleNotFoundError: No module named 'xxx'
```

**解决方案**�?```bash
# 确认 conda 环境已激�?conda activate interfuser

# 检�?Python 版本（必须是 3.7�?python --version

# 重新安装依赖
pip install -r requirements.txt
```

#### 4. 权限问题

**症状**�?```
Permission denied
```

**解决方案**�?```bash
# 修复权限
chmod +x carla_native_enhancement/*.sh
chmod +x carla/CarlaUE4.sh

# 确保不是�?root 运行
# CARLA 拒绝�?root 权限运行
```

### 调试步骤

#### 步骤 1：测试基线配�?
```bash
cd .

# 使用最简单的配置
export NATIVE_ENHANCE=none
export AUTO_START_CARLA=1
export EVAL_TIMEOUT=1200

bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

#### 步骤 2：检查日�?
```bash
# 找到最新的评估目录
LATEST_EVAL=$(ls -td data/eval_native/town05_* | head -1)

# 查看评估日志
cat "${LATEST_EVAL}/leaderboard_evaluator.log"

# 查看 CARLA 日志
cat "${LATEST_EVAL}"/carla_server_*.log

# 检查是否有图像生成
find "${LATEST_EVAL}" -name "*.jpg" -o -name "*.png"
```

#### 步骤 3：手动启�?CARLA

如果自动启动失败，尝试手动启动：

```bash
# 终端 1：启�?CARLA
cd ./carla
DISPLAY=:99 ./CarlaUE4.sh -opengl -RenderOffScreen -world-port=2000

# 等待 CARLA 完全启动（约 1-2 分钟�?
# 终端 2：运行评�?cd .
export AUTO_START_CARLA=0
export PORT=2000
bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

#### 步骤 4：逐步添加增强

基线工作后，逐步测试增强�?
```bash
# 1. 只测�?high_fps
bash carla_native_enhancement/run_evaluation_native.sh town05 high_fps

# 2. 测试 no_noise
bash carla_native_enhancement/run_evaluation_native.sh town05 no_noise

# 3. 测试 high_res
bash carla_native_enhancement/run_evaluation_native.sh town05 high_res

# 4. 测试组合
bash carla_native_enhancement/run_evaluation_native.sh town05 "high_fps,no_noise"
```

### 预防措施

1. **使用较短的测试路�?*�?   ```bash
   # 使用短路线进行快速测�?   export CUSTOM_ROUTES=leaderboard/data/evaluation_routes/routes_town05_short.xml
   bash carla_native_enhancement/run_evaluation_native.sh custom none
   ```

2. **启用详细日志**�?   ```bash
   export DEBUG_CHALLENGE=1
   ```

3. **监控资源使用**�?   ```bash
   # 在另一个终端监�?   watch -n 1 nvidia-smi
   watch -n 1 'ps aux | grep -E "carla|python" | grep -v grep'
   ```

### 已知限制

1. **高分辨率 + 高帧�?*�?   - 组合 `high_res,high_fps` 需要大�?GPU 内存
   - 建议至少 8GB VRAM

2. **多个传感�?*�?   - InterfuserAgent 使用 4 个摄像头（前、左、右、中心）
   - 每个摄像头都会应用增强设�?   - 总负�?= 单个传感器负�?× 4

3. **同步模式性能**�?   - 40Hz 模式下，每帧必须�?25ms 内完�?   - 如果处理时间超过 25ms，会导致超时

### 获取帮助

如果问题仍然存在�?
1. 收集诊断信息�?   ```bash
   bash carla_native_enhancement/collect_diagnostics.sh
   ```

2. 检查以下文件：
   - `data/eval_native/YOUR_EVAL_DIR/leaderboard_evaluator.log`
   - `data/eval_native/YOUR_EVAL_DIR/carla_server_*.log`
   - `data/eval_native/YOUR_EVAL_DIR/evaluation_metadata.json`

3. 提供系统信息�?   - GPU 型号�?VRAM
   - CUDA 版本
   - Python 版本
   - CARLA 版本

