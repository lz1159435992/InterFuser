# 快速参考卡片 🚀

## 最常用的命令

### 1. 基本评估流程

```bash
# 终端 1: 启动 CARLA
cd /home/nju/InterFuser/evaluation_scripts
./start_carla_server.sh

# 终端 2: 运行评估
cd /home/nju/InterFuser/sensor_data_processor_module
./run_evaluation_with_processor.sh town05 moderate

# 查看结果
python3 analyze_results.py results/with_processor/*.json
```

---

## 2. 评估命令速查

### Town05 评估

```bash
# 轻度噪声
./run_evaluation_with_processor.sh town05 mild

# 中度噪声（推荐）
./run_evaluation_with_processor.sh town05 moderate

# 重度噪声
./run_evaluation_with_processor.sh town05 severe

# 传感器故障模拟
./run_evaluation_with_processor.sh town05 failure
```

### 42 Routes 评估

```bash
# 轻度噪声
./run_evaluation_with_processor.sh 42routes mild

# 中度噪声
./run_evaluation_with_processor.sh 42routes moderate
```

### 指定 GPU

```bash
# 使用 GPU 0
GPU_ID=0 ./run_evaluation_with_processor.sh town05 moderate

# 使用 GPU 1
GPU_ID=1 ./run_evaluation_with_processor.sh town05 moderate
```

---

## 3. 结果分析命令

### 查看单个结果

```bash
# 基本信息
python3 analyze_results.py results/with_processor/town05_moderate_*.json

# 详细信息（包含每条路线）
python3 analyze_results.py -d results/with_processor/town05_moderate_*.json
```

### 对比多个结果

```bash
# 对比不同配置
python3 analyze_results.py -c \
    results/with_processor/town05_mild_*.json \
    results/with_processor/town05_moderate_*.json \
    results/with_processor/town05_severe_*.json

# 对比所有 town05 结果
python3 analyze_results.py -c results/with_processor/town05_*.json
```

### 使用通用查看器

```bash
bash /home/nju/InterFuser/evaluation_scripts/view_results.sh \
    results/with_processor/town05_moderate_20250107_120000.json
```

---

## 4. 文件管理命令

### 查看结果文件

```bash
# 列出所有评估结果
ls -lh results/with_processor/

# 查看最新结果
ls -lt results/with_processor/ | head -5

# 查看评估数据
ls -lh data/eval_with_processor/
```

### 恢复原始 agent

```bash
# 自动选择最近备份
./restore_original_agent.sh

# 指定备份目录
./restore_original_agent.sh .backup_20250107_120000
```

### 清理旧结果

```bash
# 删除 7 天前的结果
find results/with_processor/ -name "*.json" -mtime +7 -delete
find data/eval_with_processor/ -type d -mtime +7 -exec rm -rf {} +

# 压缩旧结果
tar -czf old_results_$(date +%Y%m%d).tar.gz \
    results/with_processor/ \
    data/eval_with_processor/
```

---

## 5. 配置修改

### 编辑数据处理器配置

```bash
# 编辑配置文件
vim data_processor_config.py

# 或
nano data_processor_config.py
```

### 常用配置模板

```python
# 轻度噪声（推荐用于日常测试）
ACTIVE_CONFIG = CONFIG_MILD_NOISE

# 中度噪声（推荐用于鲁棒性测试）
ACTIVE_CONFIG = CONFIG_MODERATE_NOISE

# 重度噪声（用于压力测试）
ACTIVE_CONFIG = CONFIG_SEVERE_NOISE

# 传感器故障模拟
ACTIVE_CONFIG = CONFIG_SENSOR_FAILURE

# 自定义配置
ACTIVE_CONFIG = DATA_PROCESSOR_CONFIG
```

---

## 6. 测试和调试

### 测试数据处理器

```bash
# 运行测试脚本
./test_data_processor.sh

# 直接测试
cd /home/nju/InterFuser
conda activate interfuser
python3 -c "from leaderboard.team_code.data_processor import SensorDataProcessor; print('OK')"
```

### 检查环境

```bash
# 检查 conda 环境
conda env list

# 检查 Python 包
conda activate interfuser
pip list | grep -E "torch|carla|opencv|numpy"

# 检查 CARLA 服务器
timeout 2 bash -c "echo > /dev/tcp/localhost/2000" && echo "CARLA OK" || echo "CARLA NOT RUNNING"
```

---

## 7. 常见问题快速解决

### CARLA 服务器未运行

```bash
# 启动服务器
cd /home/nju/InterFuser/evaluation_scripts
./start_carla_server.sh
```

### 模块导入错误

```bash
# 重新激活环境
conda deactivate
conda activate interfuser

# 检查 PYTHONPATH
echo $PYTHONPATH
```

### 评估中断恢复

```bash
# 直接重新运行（自动恢复）
./run_evaluation_with_processor.sh town05 moderate
```

### GPU 内存不足

```bash
# 使用其他 GPU
GPU_ID=1 ./run_evaluation_with_processor.sh town05 moderate

# 或关闭其他进程
nvidia-smi
kill -9 [PID]
```

---

## 8. 文件路径速查

```
/home/nju/InterFuser/
├── sensor_data_processor_module/          # 数据处理器模块
│   ├── run_evaluation_with_processor.sh   # 主评估脚本 ⭐
│   ├── analyze_results.py                 # 结果分析 ⭐
│   ├── restore_original_agent.sh          # 恢复脚本
│   ├── data_processor.py                  # 数据处理器实现
│   ├── data_processor_config.py           # 配置文件
│   ├── interfuser_agent_complete.py       # 完整版 agent
│   └── EVALUATION_GUIDE.md                # 详细指南
│
├── results/
│   └── with_processor/                    # 评估结果（JSON）
│
├── data/
│   └── eval_with_processor/               # 评估数据（图像等）
│
├── leaderboard/team_code/                 # Agent 代码
│   ├── interfuser_agent.py                # 当前使用的 agent
│   ├── data_processor.py                  # 部署的处理器
│   └── data_processor_config.py           # 部署的配置
│
└── evaluation_scripts/                    # 通用评估脚本
    ├── start_carla_server.sh              # CARLA 启动
    └── view_results.sh                    # 结果查看器
```

---

## 9. 性能参考

### 典型评估时间

| 评估类型 | 路线数 | 预计时间 | 配置推荐 |
|---------|--------|---------|---------|
| town05 | ~50 | 2-4 小时 | mild/moderate |
| 42routes | 42 | 1.5-3 小时 | mild |

### 性能开销

| 配置 | 处理开销 | FPS 影响 | 推荐场景 |
|------|---------|---------|---------|
| mild | +3-5ms | ~10% | ✅ 日常测试 |
| moderate | +5-10ms | ~15% | ⚠️ 鲁棒性测试 |
| severe | +15-28ms | ~50% | ⛔ 离线分析 |

---

## 10. 批量评估脚本

### 评估所有配置

```bash
#!/bin/bash
# 批量评估所有配置

configs=("mild" "moderate" "severe")

for config in "${configs[@]}"; do
    echo "开始评估: $config"
    ./run_evaluation_with_processor.sh town05 $config
    sleep 10
done

echo "全部完成！对比结果..."
python3 analyze_results.py -c results/with_processor/town05_*.json
```

### 多 GPU 并行评估

```bash
#!/bin/bash
# 并行评估（需要多个 CARLA 服务器）

# GPU 0: mild
GPU_ID=0 PORT=2000 TM_PORT=2500 \
    ./run_evaluation_with_processor.sh town05 mild &

# GPU 1: moderate
GPU_ID=1 PORT=3000 TM_PORT=3500 \
    ./run_evaluation_with_processor.sh town05 moderate &

# 等待完成
wait

echo "并行评估完成！"
```

---

## 📌 备忘

### 记住这些关键点

1. **总是先启动 CARLA 服务器**
2. **评估脚本会自动备份和恢复文件**
3. **结果保存在 `results/with_processor/` 目录**
4. **使用 `-c` 参数对比多个结果**
5. **`mild` 配置适合日常测试**
6. **评估可以中断后恢复**

### 一键命令

```bash
# 最常用的完整流程（复制粘贴即可）
cd /home/nju/InterFuser/sensor_data_processor_module && \
./run_evaluation_with_processor.sh town05 moderate && \
python3 analyze_results.py results/with_processor/town05_moderate_*.json
```

---

**快速参考完毕！需要详细信息请查看 `EVALUATION_GUIDE.md`** 📖

