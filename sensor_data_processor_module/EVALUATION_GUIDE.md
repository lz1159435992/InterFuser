# 数据处理器评估指南

本指南介绍如何使用带数据处理器的 InterFuser agent 进行评估。

## 📋 目录

- [快速开始](#快速开始)
- [脚本说明](#脚本说明)
- [评估流程](#评估流程)
- [配置选项](#配置选项)
- [结果分析](#结果分析)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 最简单的方式（3 步）

```bash
# 1. 启动 CARLA 服务器（在终端 1）
cd /home/nju/InterFuser/evaluation_scripts
./start_carla_server.sh

# 2. 运行评估（在终端 2）
cd /home/nju/InterFuser/sensor_data_processor_module
./run_evaluation_with_processor.sh town05 moderate

# 3. 查看结果
python3 analyze_results.py results/with_processor/*.json
```

### 完整示例

```bash
# Town05 + 中度噪声（默认配置）
./run_evaluation_with_processor.sh town05 moderate

# 42 Routes + 轻度噪声
./run_evaluation_with_processor.sh 42routes mild

# 自定义路线 + 重度噪声，使用 GPU 1
GPU_ID=1 ./run_evaluation_with_processor.sh custom severe
```

---

## 📦 脚本说明

### 1. `run_evaluation_with_processor.sh`

**主评估脚本** - 自动部署、评估、保存结果

**功能：**
- ✅ 自动备份原始 agent 文件
- ✅ 部署数据处理器模块
- ✅ 配置数据处理参数
- ✅ 运行评估
- ✅ 保存结果到独立目录
- ✅ 评估后可选恢复原始文件

**用法：**
```bash
./run_evaluation_with_processor.sh [评估类型] [配置类型]

参数：
  评估类型: town05 | 42routes | custom
  配置类型: mild | moderate | severe | failure | custom

环境变量：
  GPU_ID        - GPU 编号（默认：0）
  RESUME        - 是否恢复中断的评估（默认：True）
  CUSTOM_ROUTES - 自定义路线文件（评估类型为 custom 时）
  CUSTOM_SCENARIOS - 自定义场景文件（评估类型为 custom 时）
```

**示例：**
```bash
# Town05 评估 + 中度噪声
./run_evaluation_with_processor.sh town05 moderate

# 42 Routes + 轻度噪声，使用 GPU 1
GPU_ID=1 ./run_evaluation_with_processor.sh 42routes mild

# 自定义路线 + 重度噪声
CUSTOM_ROUTES=leaderboard/data/my_routes.xml \
CUSTOM_SCENARIOS=leaderboard/data/my_scenarios.json \
./run_evaluation_with_processor.sh custom severe
```

### 2. `restore_original_agent.sh`

**恢复脚本** - 恢复原始 agent 文件

**功能：**
- 从备份恢复 `interfuser_agent.py`
- 删除或恢复数据处理器文件
- 清理 Python 缓存

**用法：**
```bash
# 手动指定备份目录
./restore_original_agent.sh /path/to/backup/dir

# 自动选择最近的备份
./restore_original_agent.sh
```

### 3. `analyze_results.py`

**结果分析脚本** - 分析和对比评估结果

**功能：**
- 📊 单个结果详细分析
- 📈 多结果对比分析
- 📉 性能变化统计
- 🎯 违规详情

**用法：**
```bash
# 分析单个结果
python3 analyze_results.py results/with_processor/town05_moderate_20250107_120000.json

# 详细分析（包含每条路线）
python3 analyze_results.py -d results/with_processor/town05_moderate_20250107_120000.json

# 对比多个结果
python3 analyze_results.py -c results/with_processor/town05_*.json

# 对比不同配置
python3 analyze_results.py -c \
    results/with_processor/town05_mild_*.json \
    results/with_processor/town05_moderate_*.json \
    results/with_processor/town05_severe_*.json
```

---

## 🔄 评估流程

### 完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 启动 CARLA 服务器                                          │
│    cd evaluation_scripts && ./start_carla_server.sh         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 运行评估脚本                                               │
│    ./run_evaluation_with_processor.sh town05 moderate      │
│                                                             │
│    ├─ 步骤 1: 备份原始文件                                   │
│    │   └─ 保存到 .backup_YYYYMMDD_HHMMSS/                  │
│    │                                                        │
│    ├─ 步骤 2: 部署数据处理器                                 │
│    │   ├─ 复制 data_processor.py                           │
│    │   ├─ 复制 data_processor_config.py                    │
│    │   └─ 部署 interfuser_agent_complete.py                │
│    │                                                        │
│    ├─ 步骤 3: 设置环境变量                                   │
│    │   ├─ CARLA 路径                                       │
│    │   ├─ Python 路径                                      │
│    │   └─ 评估参数                                         │
│    │                                                        │
│    ├─ 步骤 4: 检查 CARLA 服务器                              │
│    │   └─ 验证端口 2000 连接                                │
│    │                                                        │
│    └─ 步骤 5: 运行评估                                       │
│        └─ 调用 leaderboard_evaluator.py                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 保存结果                                                  │
│    ├─ JSON 结果: results/with_processor/...                │
│    ├─ 评估数据: data/eval_with_processor/...               │
│    └─ 元数据: evaluation_metadata.json                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 恢复或保留                                                │
│    ├─ [Y] 恢复原始 agent（运行 restore_original_agent.sh）  │
│    └─ [N] 保留数据处理器版本                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. 分析结果                                                  │
│    python3 analyze_results.py results/with_processor/*.json │
└─────────────────────────────────────────────────────────────┘
```

### 详细步骤

#### 步骤 1: 启动 CARLA 服务器

```bash
# 在终端 1 中
cd /home/nju/InterFuser/evaluation_scripts
./start_carla_server.sh

# 等待出现 "Waiting for the client..." 提示
```

#### 步骤 2: 运行评估

```bash
# 在终端 2 中
cd /home/nju/InterFuser/sensor_data_processor_module
chmod +x *.sh  # 首次使用时添加执行权限

# 运行评估
./run_evaluation_with_processor.sh town05 moderate
```

#### 步骤 3: 监控进度

评估过程中会显示：
- 当前路线进度
- 性能指标
- 违规记录
- 实时可视化（如果启用了 pygame）

#### 步骤 4: 查看结果

```bash
# 使用分析脚本
python3 analyze_results.py results/with_processor/town05_moderate_*.json

# 或使用通用查看器
bash /home/nju/InterFuser/evaluation_scripts/view_results.sh \
    results/with_processor/town05_moderate_20250107_120000.json
```

---

## ⚙️ 配置选项

### 评估类型

| 类型 | 说明 | 路线数 | 场景复杂度 |
|------|------|--------|-----------|
| `town05` | Town05 Long Benchmark | ~50 | 中等 |
| `42routes` | CARLA 42 Routes Benchmark | 42 | 高 |
| `custom` | 自定义路线 | 自定义 | 自定义 |

### 数据处理配置类型

| 配置 | 噪声级别 | RGB 噪声 | LiDAR 噪声 | GPS 漂移 | 推荐用途 |
|------|---------|---------|-----------|---------|---------|
| `mild` | 轻度 | σ=5 | σ=0.05m | σ=0.05° | 🟢 日常测试 |
| `moderate` | 中度 | σ=10 | σ=0.1m | σ=0.1° | 🟡 鲁棒性测试 |
| `severe` | 重度 | σ=20 | σ=0.2m | σ=0.2° | 🔴 压力测试 |
| `failure` | 故障模拟 | 20% dropout | 10% dropout | 2% 跳变 | ⚫ 极端条件 |
| `custom` | 自定义 | 自定义 | 自定义 | 自定义 | 🔧 研究用途 |

### 自定义配置

如需自定义配置，编辑 `data_processor_config.py`：

```python
# 在 data_processor_config.py 中
DATA_PROCESSOR_CONFIG = {
    "enabled": True,
    "rgb_effects": {
        "add_gaussian_noise": {
            "enabled": True,
            "std": 15,  # 自定义噪声强度
        },
        # ... 其他效果
    },
    # ... 其他传感器
}

# 设置为活动配置
ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG
```

然后运行：
```bash
./run_evaluation_with_processor.sh town05 custom
```

---

## 📊 结果分析

### 结果文件结构

```
/home/nju/InterFuser/
├── results/
│   └── with_processor/
│       ├── town05_moderate_20250107_120000.json      # 评估结果
│       ├── town05_mild_20250107_130000.json
│       └── town05_severe_20250107_140000.json
│
└── data/
    └── eval_with_processor/
        ├── town05_moderate_20250107_120000/
        │   ├── evaluation_metadata.json               # 评估元数据
        │   └── meta/                                   # 可视化图像
        │       ├── 0000.jpg
        │       ├── 0001.jpg
        │       └── ...
        └── ...
```

### 分析示例

#### 1. 单个结果分析

```bash
python3 analyze_results.py results/with_processor/town05_moderate_20250107_120000.json
```

输出：
```
======================================================================
📊 评估结果分析: town05_moderate_20250107_120000.json
======================================================================

🔧 评估配置:
  • 时间戳: 20250107_120000
  • 评估类型: town05
  • 数据处理配置: moderate
  • GPU ID: 0

📈 总体统计:
  • 总路线数: 50
  • 完成路线数: 45
  • 失败路线数: 5
  • 完成率: 90.00%

🎯 性能指标:
  • 平均驾驶分数: 78.45
  • 平均路线完成度: 82.30
  • 平均违规惩罚: 0.65

⚠️  违规统计:
  • 总违规次数: 23
  • 违规详情:
    - collisions_pedestrian: 8 次
    - collisions_vehicle: 6 次
    - red_light: 5 次
    - stop_infraction: 4 次
```

#### 2. 对比分析

```bash
python3 analyze_results.py -c \
    results/with_processor/town05_mild_*.json \
    results/with_processor/town05_moderate_*.json \
    results/with_processor/town05_severe_*.json
```

输出：
```
======================================================================
📊 评估结果对比
======================================================================

配置类型         完成率      驾驶分数      完成度        违规次数   
----------------------------------------------------------------------
mild            94.0%       85.23        88.45        12        
moderate        90.0%       78.45        82.30        23        
severe          82.0%       65.12        70.88        45        

🔍 性能对比分析:

  基准配置: mild

  moderate vs mild:
    驾驶分数变化: -6.78
    完成度变化: -6.15
    违规次数变化: +11

  severe vs mild:
    驾驶分数变化: -20.11
    完成度变化: -17.57
    违规次数变化: +33
```

### 理解结果指标

| 指标 | 说明 | 范围 | 目标 |
|------|------|------|------|
| **完成率** | 成功完成路线的百分比 | 0-100% | > 90% |
| **驾驶分数** | 综合驾驶质量评分 | 0-100 | > 80 |
| **完成度** | 路线完成程度 | 0-100 | > 85 |
| **违规惩罚** | 违规行为的惩罚分数 | 0-1 | < 0.1 |

---

## 🔧 常见问题

### Q1: 如何并行运行多个评估？

**A:** 使用不同的 GPU 和端口：

```bash
# 终端 1: GPU 0, 端口 2000
GPU_ID=0 PORT=2000 TM_PORT=2500 ./run_evaluation_with_processor.sh town05 mild

# 终端 2: GPU 1, 端口 3000
GPU_ID=1 PORT=3000 TM_PORT=3500 ./run_evaluation_with_processor.sh town05 moderate

# 注意：需要启动多个 CARLA 服务器
```

### Q2: 评估中断了，如何恢复？

**A:** 脚本默认启用恢复模式（`RESUME=True`），直接重新运行即可：

```bash
./run_evaluation_with_processor.sh town05 moderate
# 会自动从上次中断的地方继续
```

### Q3: 如何禁用数据处理器？

**A:** 有两种方法：

方法 1: 使用原始 agent
```bash
# 恢复原始 agent
./restore_original_agent.sh

# 使用原始评估脚本
cd /home/nju/InterFuser/evaluation_scripts
./run_evaluation.sh town05
```

方法 2: 在配置中禁用
```python
# 编辑 data_processor_config.py
DATA_PROCESSOR_CONFIG = {
    "enabled": False,  # 禁用处理器
    # ...
}
```

### Q4: 如何查看处理后的图像？

**A:** 启用图像保存：

```python
# 编辑 data_processor_config.py
ACTIVE_CONFIG = {
    "save_processed_images": True,  # 启用图像保存
    "save_path": "processed_sensor_data",
    # ...
}
```

然后查看：
```bash
ls data/eval_with_processor/*/processed_sensor_data/
```

### Q5: 评估速度太慢怎么办？

**A:** 优化建议：

1. **关闭图像保存**
   ```python
   "save_processed_images": False,
   ```

2. **使用轻度配置**
   ```bash
   ./run_evaluation_with_processor.sh town05 mild
   ```

3. **关闭可视化**
   ```bash
   # 编辑 interfuser_config.py
   # 将 pygame 显示相关代码注释掉
   ```

4. **使用更快的 GPU**
   ```bash
   GPU_ID=0 ./run_evaluation_with_processor.sh town05 moderate
   ```

### Q6: 如何备份所有评估结果？

**A:** 
```bash
# 创建备份
tar -czf evaluation_results_backup_$(date +%Y%m%d).tar.gz \
    results/with_processor/ \
    data/eval_with_processor/

# 恢复备份
tar -xzf evaluation_results_backup_20250107.tar.gz
```

### Q7: 评估结果在哪里？

**A:** 三个位置：

1. **JSON 结果**: `results/with_processor/`
2. **评估数据**: `data/eval_with_processor/`
3. **备份文件**: `.backup_YYYYMMDD_HHMMSS/`

### Q8: 如何自定义评估路线？

**A:**
```bash
# 1. 创建自定义路线和场景文件
vim my_routes.xml
vim my_scenarios.json

# 2. 运行评估
CUSTOM_ROUTES=my_routes.xml \
CUSTOM_SCENARIOS=my_scenarios.json \
./run_evaluation_with_processor.sh custom moderate
```

---

## 📚 更多资源

- **数据处理器详细文档**: `DATA_PROCESSOR_USAGE_GUIDE.md`
- **性能分析**: `PERFORMANCE_ANALYSIS.md`
- **项目技术分析**: `INTERFUSER_PROJECT_ANALYSIS.md`
- **版本对比**: `COMPLETE_vs_EXAMPLE.md`
- **快速入门**: `00_README_FIRST.md`

---

## 🤝 支持

如有问题，请检查：
1. CARLA 服务器是否正常运行
2. conda 环境是否正确激活
3. 文件路径是否正确
4. GPU 内存是否充足

---

**祝评估顺利！** 🚗💨

