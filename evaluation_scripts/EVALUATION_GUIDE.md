# InterFuser 评估指南

本指南帮助您快速使用预训练模型进行评估。

## 📁 脚本说明

我们提供了三个便捷脚本：

1. **`start_carla_server.sh`** - 启动 CARLA 仿真服务器
2. **`run_evaluation.sh`** - 运行模型评估
3. **`view_results.sh`** - 查看评估结果

## 🚀 快速开始

### 第一步：启动 CARLA 服务器

在**终端 1** 中运行：

```bash
cd /home/nju/InterFuser
./start_carla_server.sh
```

或指定 GPU（0-7）：
```bash
./start_carla_server.sh 1  # 使用 GPU 1
```

**等待服务器完全启动**（约 1-2 分钟），看到 `Waiting for the client...` 表示成功。

---

### 第二步：运行评估

在**终端 2** 中运行：

#### 选项 A：Town05 Long 基准测试（推荐新手）
```bash
cd /home/nju/InterFuser
./run_evaluation.sh town05
```

#### 选项 B：CARLA 42 Routes 基准测试
```bash
./run_evaluation.sh 42routes
```

#### 选项 C：自定义评估
```bash
CUSTOM_ROUTES=leaderboard/data/training_routes/routes_town01_short.xml \
CUSTOM_SCENARIOS=leaderboard/data/scenarios/town01_all_scenarios.json \
CUSTOM_RESULT=results/my_custom_result.json \
./run_evaluation.sh custom
```

#### 使用不同 GPU
```bash
GPU_ID=1 ./run_evaluation.sh town05  # 使用 GPU 1
```

---

### 第三步：查看结果

评估完成后：

```bash
./view_results.sh
```

查看特定结果文件：
```bash
./view_results.sh results/interfuser_42routes_result.json
```

---

## 📊 评估指标说明

评估会生成以下关键指标：

- **Score (总分)**: 综合评分（0-100）
- **Route Completion (路线完成度)**: 完成路线的百分比
- **Infraction Penalty (违规惩罚)**: 违规行为的惩罚分数

常见违规类型：
- `collisions_pedestrian` - 与行人碰撞
- `collisions_vehicle` - 与车辆碰撞
- `collisions_layout` - 与静态物体碰撞
- `red_light` - 闯红灯
- `route_dev` - 路线偏离
- `stop_infraction` - 停车违规

---

## 🔧 高级选项

### 恢复中断的评估

如果评估中断，可以从断点继续：

```bash
RESUME=True ./run_evaluation.sh town05
```

### 禁用恢复（从头开始）

```bash
RESUME=False ./run_evaluation.sh town05
```

### 多次重复评估

修改 `run_evaluation.sh` 中的 `REPETITIONS` 变量：
```bash
export REPETITIONS=3  # 每条路线重复 3 次
```

### 调试模式

```bash
# 在 run_evaluation.sh 中设置
export DEBUG_CHALLENGE=1
```

---

## 📂 文件位置

```
/home/nju/InterFuser/
├── start_carla_server.sh          # CARLA 服务器启动脚本
├── run_evaluation.sh              # 评估脚本
├── view_results.sh                # 结果查看脚本
├── results/                       # 评估结果目录
│   ├── interfuser_town05_result.json
│   └── interfuser_42routes_result.json
├── data/eval/                     # 评估数据目录
└── leaderboard/team_code/
    └── interfuser.pth.tar         # 预训练模型
```

---

## ⚠️ 常见问题

### 1. 无法连接 CARLA 服务器

**症状**: 提示 `无法连接到 CARLA 服务器`

**解决方案**:
- 确保 CARLA 服务器已启动并完全加载
- 检查端口 2000 是否被占用: `lsof -i :2000`
- 等待更长时间（服务器首次启动可能需要 2-3 分钟）

### 2. GPU 内存不足

**症状**: CUDA out of memory

**解决方案**:
- 使用内存更大的 GPU
- 关闭其他占用 GPU 的程序
- 减少场景复杂度

### 3. 评估速度慢

**症状**: 评估运行缓慢

**解决方案**:
- 使用更快的 GPU
- 使用较短的路线进行测试
- 检查系统负载

### 4. 模型文件损坏

**症状**: 加载模型时出错

**解决方案**:
```bash
cd /home/nju/InterFuser/leaderboard/team_code
# 检查文件大小（应约 607 MB）
ls -lh interfuser.pth.tar
# 如需重新下载，请参考 README.md
```

---

## 💡 性能优化建议

1. **首次评估**: 使用短路线测试（如 `routes_town01_short.xml`）
2. **批量评估**: 可以写脚本循环调用不同的评估配置
3. **结果分析**: 使用 `view_results.sh` 快速查看关键指标
4. **日志记录**: 将输出重定向到文件以便后续分析
   ```bash
   ./run_evaluation.sh town05 2>&1 | tee evaluation.log
   ```

---

## 📞 获取帮助

如果遇到问题：

1. 检查 CARLA 和 conda 环境是否正确配置
2. 查看终端输出的错误信息
3. 参考主 README.md 文件
4. 访问项目 GitHub Issues

---

## 🎯 评估示例工作流

完整的评估流程示例：

```bash
# 终端 1: 启动 CARLA
cd /home/nju/InterFuser
./start_carla_server.sh

# 终端 2: 等待服务器启动后运行评估
cd /home/nju/InterFuser
./run_evaluation.sh town05

# 评估完成后查看结果
./view_results.sh

# 如需继续评估其他场景
./run_evaluation.sh 42routes
```

---

**祝评估顺利！🚗💨**

