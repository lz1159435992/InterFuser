# 🚀 InterFuser 评估快速入门

## 📍 评估脚本位置

所有评估相关的脚本和文档已整理到：

```
📁 evaluation_scripts/
├── 📜 README.md                    # 脚本说明文档
├── 📜 EVALUATION_GUIDE.md          # 详细评估指南
├── 🔧 start_carla_server.sh        # CARLA 服务器启动脚本
├── 🔧 run_evaluation.sh            # 评估执行脚本
└── 🔧 view_results.sh              # 结果查看脚本
```

---

## ⚡ 快速开始（2 步）

### 步骤 1：启动 CARLA 服务器

**终端 1**：
```bash
cd evaluation_scripts
./start_carla_server.sh
```

### 步骤 2：运行评估

**终端 2**（等服务器启动完成）：
```bash
cd evaluation_scripts
./run_evaluation.sh town05
```

---

## 📚 更多信息

- **脚本使用说明**: `evaluation_scripts/README.md`
- **详细评估指南**: `evaluation_scripts/EVALUATION_GUIDE.md`
- **项目完整文档**: `README.md`

---

## 🔗 快速链接

```bash
# 进入脚本目录
cd evaluation_scripts/

# 查看脚本说明
cat README.md

# 查看详细指南
cat EVALUATION_GUIDE.md
```

---

**🎯 提示**：首次使用建议先阅读 `evaluation_scripts/README.md`

