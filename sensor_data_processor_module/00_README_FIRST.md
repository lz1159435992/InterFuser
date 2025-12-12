# 📦 传感器数据处理器模块

欢迎使用 InterFuser 传感器数据处理器模块！

---

## 📁 文件夹内容

### 📄 文档文件（按阅读顺序）

1. **`CONTROL_QUICK_REFERENCE.md`** 🎛️ NEW! 快速控制指南
   - **3 种方法控制数据处理开关**
   - **预设配置切换**
   - **常用场景配置示例**
   - **快速操作步骤**

2. **`HOW_TO_EXTEND.md`** 🔧 NEW! 扩展开发指南
   - **如何添加新的处理方法**
   - **完整的开发示例**
   - **最佳实践和调试技巧**

3. **`README_DATA_PROCESSOR.md`** ⭐ 从这里开始
   - 项目总结和快速导航
   - 验收清单
   - 学习路径指引

4. **`DATA_PROCESSOR_USAGE_GUIDE.md`** 
   - 详细的使用指南
   - 快速开始步骤
   - 配置说明
   - 集成教程
   - 常见问题解答

5. **`INTERFUSER_PROJECT_ANALYSIS.md`**
   - 完整的项目架构分析
   - 数据流详解
   - 4 种拦截方案对比
   - 技术深入解析

6. **`PERFORMANCE_ANALYSIS.md`** (性能分析) ⭐
   - 详细的性能影响分析
   - 基准测试数据
   - 优化建议
   - 实时性分析

### 💻 代码文件

1. **`data_processor.py`** (16 KB)
   - 核心实现：SensorDataProcessor 类
   - 支持 RGB、LiDAR、GPS、速度、罗盘处理
   - 包含统计、日志、对比图像功能

2. **`data_processor_config.py`** (7.5 KB)
   - 配置文件
   - 5 个预设配置（轻度/中度/严重噪声、传感器故障、默认）
   - 详细的参数说明

3. **`interfuser_agent_with_processor_example.py`** (8.5 KB) ⭐ 示例
   - 集成示例代码片段
   - 详细注释和说明
   - 关键修改点标注

4. **`interfuser_agent_complete.py`** (NEW! 完整版本) ⭐⭐⭐
   - 完整的可用代码
   - 已集成数据处理器
   - 包含性能监控
   - 可直接替换使用

### 🔧 工具脚本

1. **`test_data_processor.sh`**
   - 一键测试脚本
   - 验证所有功能

2. **`run_evaluation_with_processor.sh`** ⭐ NEW!
   - 完整的评估脚本
   - 自动部署、评估、保存结果
   - 支持多种配置

3. **`restore_original_agent.sh`**
   - 恢复原始文件
   - 清理部署的文件

4. **`analyze_results.py`** ⭐ NEW!
   - 评估结果分析
   - 支持对比分析
   - 生成统计报告

5. **`quick_test.sh`** 🧪 NEW!
   - 快速测试脚本
   - 仅 3 条路线
   - 5-15 分钟完成

### 📚 参考文档

1. **`EVALUATION_GUIDE.md`** ⭐ NEW!
   - 完整的评估指南
   - 详细的使用说明
   - 常见问题解答

2. **`QUICK_REFERENCE.md`** ⭐ NEW!
   - 快速参考卡片
   - 常用命令速查
   - 一键命令

3. **`COMPLETE_vs_EXAMPLE.md`**
   - 版本对比说明
   - 选择指南

4. **`SYNC_AND_PERFORMANCE_GUIDE.md`** ⭐ NEW!
   - Agent 与模拟器同步指南
   - 性能优化方案
   - 同步机制详解
   - 故障诊断

5. **`QUICK_TEST_GUIDE.md`** 🧪 NEW!
   - 快速测试指南（3 条路线）
   - 5-15 分钟验证功能
   - 测试模式说明
   - 故障排查

---

## 🚀 快速开始

### 🎛️ 控制数据处理（最常用）

**关闭所有数据处理（推荐测试基线）：**
```bash
# 编辑配置文件
vim data_processor_config.py

# 修改第 34 行
ENABLE_ALL_PROCESSING = False  # ← 改为 False

# 或使用无处理配置（文件末尾）
ACTIVE_CONFIG = CONFIG_NO_PROCESSING
```

**切换到轻度噪声：**
```bash
# 修改文件末尾
ACTIVE_CONFIG = CONFIG_MILD_NOISE
```

**详细控制说明**：查看 `CONTROL_QUICK_REFERENCE.md` 📖

---

### 选项 A：快速功能测试（1 分钟）
```bash
cd /home/nju/InterFuser/sensor_data_processor_module
./test_data_processor.sh
```

### 选项 B：快速 Agent 测试（5-15 分钟）🧪 推荐新手
```bash
# 终端 1: 启动 CARLA 服务器
cd /home/nju/InterFuser/evaluation_scripts
./start_carla_server.sh

# 终端 2: 运行快速测试（只测试 3 条路线）
cd /home/nju/InterFuser/sensor_data_processor_module
./quick_test.sh fast
```

### 选项 C：完整评估（2-4 小时） ⭐ 推荐熟悉后使用
```bash
# 终端 1: 启动 CARLA 服务器
cd /home/nju/InterFuser/evaluation_scripts
./start_carla_server.sh

# 终端 2: 运行评估
cd /home/nju/InterFuser/sensor_data_processor_module
./run_evaluation_with_processor.sh town05 moderate

# 查看结果
python3 analyze_results.py results/with_processor/*.json
```

### 选项 D：手动集成（2-3 步）

#### 步骤 1：测试
```bash
cd /home/nju/InterFuser/sensor_data_processor_module
./test_data_processor.sh
```

#### 步骤 2：阅读文档
```bash
# 先看总结
cat README_DATA_PROCESSOR.md

# 再看使用指南
cat DATA_PROCESSOR_USAGE_GUIDE.md
```

#### 步骤 3：使用模块

#### 方式 A：复制到 team_code 目录
```bash
cd /home/nju/InterFuser/sensor_data_processor_module

# 复制核心文件到 team_code
cp data_processor.py ../leaderboard/team_code/
cp data_processor_config.py ../leaderboard/team_code/

# 查看集成示例
cat interfuser_agent_with_processor_example.py
```

#### 方式 B：使用符号链接
```bash
cd /home/nju/InterFuser/leaderboard/team_code

# 创建符号链接
ln -s ../../sensor_data_processor_module/data_processor.py .
ln -s ../../sensor_data_processor_module/data_processor_config.py .
```

然后按照 `DATA_PROCESSOR_USAGE_GUIDE.md` 中的说明修改 `interfuser_agent.py`。

---

## 📖 文档导航

### 我想...

| 需求 | 查看文档 | 章节 |
|------|---------|------|
| 快速了解项目 | `README_DATA_PROCESSOR.md` | 全文 |
| **快速测试** 🧪 | `QUICK_TEST_GUIDE.md` | 全文 |
| **运行评估** ⭐ | `EVALUATION_GUIDE.md` | "快速开始" |
| **查看命令** ⭐ | `QUICK_REFERENCE.md` | 全文 |
| 开始使用 | `DATA_PROCESSOR_USAGE_GUIDE.md` | "快速开始" |
| 配置参数 | `DATA_PROCESSOR_USAGE_GUIDE.md` | "配置说明" |
| 集成到 Agent | `DATA_PROCESSOR_USAGE_GUIDE.md` | "集成到 InterfuserAgent" |
| 分析结果 | `EVALUATION_GUIDE.md` | "结果分析" |
| 了解性能影响 | `PERFORMANCE_ANALYSIS.md` | 全文 |
| 理解项目架构 | `INTERFUSER_PROJECT_ANALYSIS.md` | "数据流架构" |
| 了解数据流 | `INTERFUSER_PROJECT_ANALYSIS.md` | "完整数据流程图" |
| 方案对比 | `INTERFUSER_PROJECT_ANALYSIS.md` | "数据拦截和编辑方案" |
| 查看代码示例 | `interfuser_agent_with_processor_example.py` | 全文 |
| 使用完整代码 | `interfuser_agent_complete.py` | 全文 |
| **优化性能** ⭐ | `SYNC_AND_PERFORMANCE_GUIDE.md` | 全文 |
| **Agent 同步问题** ⭐ | `SYNC_AND_PERFORMANCE_GUIDE.md` | "同步机制" |
| 解决问题 | `DATA_PROCESSOR_USAGE_GUIDE.md` | "常见问题" |

---

## 🎯 主要功能

### 支持的传感器处理

- ✅ **RGB 相机**: 噪声、亮度、模糊、对比度、饱和度、像素丢失、色彩偏移
- ✅ **LiDAR**: 位置噪声、点云丢失、距离限制、强度噪声
- ✅ **GPS**: 位置漂移、随机跳变
- ✅ **速度传感器**: 测量误差、系统偏差
- ✅ **罗盘**: 方向误差、磁偏角

### 预设配置

1. `CONFIG_MILD_NOISE` - 轻度噪声（良好条件）
2. `CONFIG_MODERATE_NOISE` - 中度噪声（一般条件）
3. `CONFIG_SEVERE_NOISE` - 严重噪声（恶劣条件）
4. `CONFIG_SENSOR_FAILURE` - 传感器故障模拟
5. `DATA_PROCESSOR_CONFIG` - 默认配置（可自定义）

### 高级功能

- 📸 对比图像保存
- 📊 统计信息记录
- 📝 数据日志
- ⚙️ 热配置切换

---

## 📂 文件结构

```
sensor_data_processor_module/
├── 📖 文档
│   ├── 00_README_FIRST.md                          ← 本文件（开始看这里）
│   ├── README_DATA_PROCESSOR.md                    ← 项目总结
│   ├── DATA_PROCESSOR_USAGE_GUIDE.md               ← 详细使用指南
│   ├── INTERFUSER_PROJECT_ANALYSIS.md              ← 项目深入分析
│   ├── PERFORMANCE_ANALYSIS.md                     ← 性能分析 ⭐
│   ├── COMPLETE_vs_EXAMPLE.md                      ← 版本对比
│   ├── EVALUATION_GUIDE.md                         ← 评估指南 ⭐ NEW!
│   ├── QUICK_REFERENCE.md                          ← 快速参考 ⭐ NEW!
│   ├── SYNC_AND_PERFORMANCE_GUIDE.md               ← 同步与性能 ⭐ NEW!
│   └── QUICK_TEST_GUIDE.md                         ← 快速测试 🧪 NEW!
│
├── 💻 核心代码
│   ├── data_processor.py                           ← 数据处理器实现
│   ├── data_processor_config.py                    ← 配置文件
│   ├── data_processor_config_fast.py               ← 快速配置 ⚡ NEW!
│   ├── interfuser_agent_with_processor_example.py  ← 集成示例
│   └── interfuser_agent_complete.py                ← 完整版本 ⭐
│
└── 🔧 工具脚本
    ├── test_data_processor.sh                      ← 功能测试
    ├── quick_test.sh                               ← 快速测试 🧪 NEW!
    ├── run_evaluation_with_processor.sh            ← 完整评估 ⭐ NEW!
    ├── restore_original_agent.sh                   ← 恢复脚本 NEW!
    └── analyze_results.py                          ← 结果分析 ⭐ NEW!
```

**总文件数**: 21 个
- 📖 文档: 10 个
- 💻 代码: 5 个  
- 🔧 脚本: 5 个
- 📄 数据: 1 个 (test_routes_short.xml)

---

## ✅ 测试状态

- ✅ 基础功能测试通过
- ✅ RGB 处理测试通过
- ✅ LiDAR 处理测试通过
- ✅ GPS 处理测试通过
- ✅ 速度/罗盘处理测试通过
- ✅ 配置加载测试通过

---

## 💡 使用示例

### 1. 测试处理器

```bash
cd /home/nju/InterFuser/sensor_data_processor_module
./test_data_processor.sh
```

### 2. 修改配置

编辑 `data_processor_config.py`，修改最后一行：
```python
# 选择预设配置
ACTIVE_CONFIG = CONFIG_MODERATE_NOISE  # 中度噪声

# 或自定义配置
ACTIVE_CONFIG = {
    'enabled': True,
    'rgb': {
        'add_gaussian_noise': {'enabled': True, 'mean': 0, 'std': 15},
    },
    'lidar': {
        'dropout': {'enabled': True, 'rate': 0.1},
    },
}
```

### 3. 集成到项目

参考 `interfuser_agent_with_processor_example.py`：

```python
# 1. 导入
from team_code.data_processor import SensorDataProcessor
from team_code.data_processor_config import ACTIVE_CONFIG

# 2. 初始化
self.data_processor = SensorDataProcessor(ACTIVE_CONFIG)

# 3. 使用
processed_rgb = self.data_processor.process_rgb(rgb_image)
processed_lidar = self.data_processor.process_lidar(lidar_points)
```

---

## 🔗 相关资源

### 在项目中的位置
- 原始 InterfuserAgent: `/home/nju/InterFuser/leaderboard/team_code/interfuser_agent.py`
- 评估脚本: `/home/nju/InterFuser/evaluation_scripts/`
- 项目 README: `/home/nju/InterFuser/README.md`

### 外部链接
- CARLA 官方文档: https://carla.readthedocs.io/
- InterFuser 论文: 参见项目 README

---

## 📞 技术支持

遇到问题？

1. 查看 `DATA_PROCESSOR_USAGE_GUIDE.md` → "常见问题"
2. 查看 `INTERFUSER_PROJECT_ANALYSIS.md` 了解技术细节
3. 运行 `test_data_processor.sh` 诊断问题

---

## 🎓 学习路径

### 新手（30 分钟）
1. ✅ 阅读本文件
2. ✅ 运行 `test_data_processor.sh`
3. ✅ 浏览 `README_DATA_PROCESSOR.md`

### 使用者（1 小时）
1. ✅ 阅读 `DATA_PROCESSOR_USAGE_GUIDE.md` 的前 3 节
2. ✅ 修改配置文件
3. ✅ 集成到 Agent
4. ✅ 运行评估

### 开发者（2-3 小时）
1. ✅ 完整阅读 `INTERFUSER_PROJECT_ANALYSIS.md`
2. ✅ 学习数据流和架构
3. ✅ 理解 4 种拦截方案
4. ✅ 查看源代码实现
5. ✅ 扩展新功能

---

## 🎉 开始使用

现在就开始吧！

```bash
# 1. 测试
cd /home/nju/InterFuser/sensor_data_processor_module
./test_data_processor.sh

# 2. 阅读总结
cat README_DATA_PROCESSOR.md

# 3. 开始集成
cat DATA_PROCESSOR_USAGE_GUIDE.md
```

**祝您使用愉快！** 🚀

