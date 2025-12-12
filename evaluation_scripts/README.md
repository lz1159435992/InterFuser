# InterFuser 评估脚本集

本文件夹包含用于 InterFuser 模型评估的便捷脚本。

## 📁 文件说明

| 文件名 | 说明 | 大小 |
|--------|------|------|
| `start_carla_server.sh` | CARLA 服务器启动脚本 | 589 字节 |
| `run_evaluation.sh` | 模型评估主脚本 | 4.3 KB |
| `view_results.sh` | 结果查看脚本 | 3.6 KB |
| `EVALUATION_GUIDE.md` | 详细评估指南 | 4.8 KB |

## 🚀 快速开始

### 1️⃣ 启动 CARLA 服务器

**终端 1**：
```bash
cd /home/nju/InterFuser/evaluation_scripts
./start_carla_server.sh
```

💡 **提示**：等待服务器完全启动（约 1-2 分钟）

---

### 2️⃣ 运行评估

**终端 2**：

#### Town05 评估（推荐新手）
```bash
cd /home/nju/InterFuser/evaluation_scripts
./run_evaluation.sh town05
```

#### CARLA 42 Routes 评估
```bash
cd /home/nju/InterFuser/evaluation_scripts
./run_evaluation.sh 42routes
```

---

### 3️⃣ 查看结果

```bash
cd /home/nju/InterFuser/evaluation_scripts
./view_results.sh
```

或查看特定结果：
```bash
./view_results.sh ../results/interfuser_town05_result.json
```

---

## 📖 详细文档

请查看 **`EVALUATION_GUIDE.md`** 获取：
- 完整使用说明
- 高级配置选项
- 常见问题解决方案
- 性能优化建议

```bash
cat EVALUATION_GUIDE.md
# 或使用编辑器
vim EVALUATION_GUIDE.md
```

---

## 🔧 常用命令

### 指定 GPU
```bash
# 启动服务器时指定 GPU
./start_carla_server.sh 1  # 使用 GPU 1

# 运行评估时指定 GPU
GPU_ID=1 ./run_evaluation.sh town05
```

### 从断点继续评估
```bash
RESUME=True ./run_evaluation.sh town05
```

### 查看脚本帮助
```bash
./run_evaluation.sh  # 显示使用说明
```

---

## 📊 结果文件位置

评估结果保存在：
```
/home/nju/InterFuser/
├── results/                    # 评估结果（JSON 格式）
│   ├── interfuser_town05_result.json
│   └── interfuser_42routes_result.json
└── data/eval/                  # 评估数据
```

---

## ⚙️ 环境要求

- **CARLA 版本**: 0.9.10.1
- **Python**: 3.7
- **Conda 环境**: interfuser
- **GPU**: CUDA 兼容 GPU（推荐）

---

## 💡 使用技巧

1. **首次使用**：先用 Town05 测试，这是标准基准
2. **保存日志**：
   ```bash
   ./run_evaluation.sh town05 2>&1 | tee evaluation.log
   ```
3. **批量评估**：可以创建循环脚本调用不同配置
4. **监控进度**：评估过程会实时显示进度信息

---

## 🐛 故障排除

### 无法连接 CARLA 服务器
- 确保 CARLA 已启动并完全加载
- 检查端口 2000 是否被占用：`lsof -i :2000`

### GPU 内存不足
- 使用更大内存的 GPU
- 关闭其他 GPU 程序

### 脚本权限错误
```bash
chmod +x *.sh
```

---

## 📞 获取帮助

- 查看主项目 README: `../README.md`
- 查看详细指南: `EVALUATION_GUIDE.md`
- 项目主页: https://github.com/opendilab/InterFuser

---

**祝您评估顺利！🚗💨**

最后更新：2025-10-07

