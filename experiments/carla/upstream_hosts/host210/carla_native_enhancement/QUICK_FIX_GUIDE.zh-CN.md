# Meta 文件缺失问题 - 快速修复指�?
## 问题

`./data/eval_native` 目录下的 meta 目录没有文件生成�?
## 快速诊�?
```bash
cd .

# 1. 检查最新评�?LATEST=$(ls -td data/eval_native/town05_* | head -1)
echo "最新评�? ${LATEST}"

# 2. 统计文件�?find "${LATEST}" -name "*.jpg" | wc -l

# 3. 查看错误
grep -i "error\|exception\|timeout" "${LATEST}/leaderboard_evaluator.log"
```

## 快速修�?
### 方法 1：运行快速测试（推荐�?
```bash
# 测试基线配置
bash carla_native_enhancement/test_quick.sh none
```

**如果成功**：会看到 "�?Meta 文件已成功生成！"

**如果失败**：继续方�?2

### 方法 2：手动启�?CARLA

```bash
# 终端 1：启�?CARLA
cd ./carla
DISPLAY=:99 ./CarlaUE4.sh -opengl -RenderOffScreen -world-port=2000

# 等待 1-2 分钟，看�?"Listening on port 2000"

# 终端 2：运行评�?cd .
export AUTO_START_CARLA=0
export PORT=2000
export EVAL_TIMEOUT=1200
bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

### 方法 3：增加超时时�?
```bash
export EVAL_TIMEOUT=1800        # 30 分钟
export CARLA_TICK_TIMEOUT=1800
bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

## 验证修复

```bash
# 等待评估运行 5-10 分钟后检�?LATEST=$(ls -td data/eval_native/town05_* | head -1)

# 应该看到文件数量持续增加
watch -n 5 "find ${LATEST} -name '*.jpg' | wc -l"

# Ctrl+C 退�?watch
```

## 常见错误及解�?
### 错误 1: "time-out of 10000ms"

**原因**：CARLA 服务器响应慢或崩�?
**解决**�?```bash
# 增加超时
export CARLA_TICK_TIMEOUT=1800

# 或手动启�?CARLA（见方法 2�?```

### 错误 2: "Invalid session: no stream available"

**原因**：传感器流同步问�?
**解决**：已在代码中修复（同步模式），重新运行即�?
### 错误 3: "Address already in use"

**原因**：端口被占用

**解决**�?```bash
# 使用随机端口
export PORT=random
bash carla_native_enhancement/run_evaluation_native.sh town05 none

# 或清理旧进程
pkill -9 CarlaUE4
```

### 错误 4: GPU 内存不足

**原因**：配置要求超�?GPU 容量

**解决**�?```bash
# 不使用高分辨�?bash carla_native_enhancement/run_evaluation_native.sh town05 high_fps

# 检�?GPU 使用
nvidia-smi
```

## 完整诊断

如果上述方法都不行：

```bash
# 运行完整诊断
bash carla_native_enhancement/collect_diagnostics.sh

# 查看详细故障排查指南
cat carla_native_enhancement/TROUBLESHOOTING.md

# 查看完整问题分析
cat carla_native_enhancement/META_FILES_ISSUE_SUMMARY.zh-CN.md
```

## 预期结果

### 正常情况

```bash
# 文件数量示例�?2 routes�?0Hz�?5�?route�?$ find data/eval_native/town05_none_20260204_190000 -name "*.jpg" | wc -l
18900

# 目录结构
data/eval_native/town05_none_20260204_190000/
├── evaluation_metadata.json
├── leaderboard_evaluator.log
├── carla_server_2000.log
└── routes_town05_long_02_04_19_00_15/
    └── meta/
        ├── 0000.jpg
        ├── 0001.jpg
        ├── 0002.jpg
        └── ... (数千个文�?
```

### 异常情况

```bash
# 文件数量�?0 或很�?$ find data/eval_native/town05_none_20260204_180000 -name "*.jpg" | wc -l
0

# 或只�?1-2 个文�?$ find data/eval_native/town05_none_20260204_180000 -name "*.jpg" | wc -l
1
```

## 需要帮助？

1. **查看日志**�?   ```bash
   LATEST=$(ls -td data/eval_native/town05_* | head -1)
   cat "${LATEST}/leaderboard_evaluator.log"
   cat "${LATEST}"/carla_server_*.log
   ```

2. **运行诊断**�?   ```bash
   bash carla_native_enhancement/collect_diagnostics.sh > diagnostics.txt
   ```

3. **检查文�?*�?   - 快速修复：本文�?   - 详细分析：`META_FILES_ISSUE_SUMMARY.zh-CN.md`
   - 完整故障排查：`TROUBLESHOOTING.md`

## 总结

**问题**：meta 目录没有文件

**原因**：CARLA 超时/崩溃，评估提前终�?
**修复**�?1. �?运行 `test_quick.sh` 快速测�?2. �?手动启动 CARLA（如果自动启动失败）
3. �?增加超时时间
4. �?检�?GPU 内存

**验证**：文件数量应该持续增加，最终达到数千个

**下一�?*：运�?`test_quick.sh none` 开始测�?
