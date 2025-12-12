# 🎨 InterFuser 图像处理方法模块集合

本目录包含用于 InterFuser 数据处理的各种图像处理方法模块。

---

## 📂 模块列表

### 1. SwinIR - 图像修复与超分辨率 ⭐

**路径**: `SwinIR/`  
**状态**: ✅ 已集成  
**来源**: [GitHub - SwinIR](https://github.com/JingyunLiang/SwinIR)

**功能**:
- ✨ 图像超分辨率（2x, 4x, 8x）
- ✨ 图像去噪（噪声等级 15, 25, 50）
- ✨ JPEG 压缩伪影去除

**快速开始**:
```bash
cd SwinIR
cat README_INTEGRATION.txt  # 查看集成总结
```

**文档**:
- `SwinIR/README_INTEGRATION.txt` - 集成总结和检查清单
- `SwinIR/SWINIR_INTEGRATION_GUIDE.md` - 详细集成指南
- `SwinIR/swinir_wrapper.py` - Python 包装器
- `SwinIR/example_usage.py` - 使用示例

---

### 2. 其他模块（待添加）

未来可以在此添加更多图像处理模块，例如：
- 其他超分辨率模型
- 图像增强模型
- 风格迁移模型
- 等等...

---

## 🚀 快速导航

### 查看 SwinIR 模块

```bash
# 进入 SwinIR 目录
cd /home/nju/InterFuser/process_mothod/SwinIR

# 查看集成总结
cat README_INTEGRATION.txt

# 查看详细指南
cat SWINIR_INTEGRATION_GUIDE.md

# 测试包装器
python3 swinir_wrapper.py

# 运行示例
python3 example_usage.py
```

---

## 📖 集成到 InterFuser

所有处理模块都可以通过两种方式集成到 InterFuser：

### 方法 1: 集成到数据处理器（推荐）

在 `/home/nju/InterFuser/sensor_data_processor_module/data_processor_config.py` 中配置：

```python
import sys
sys.path.insert(0, '/home/nju/InterFuser/process_mothod/SwinIR')
from swinir_wrapper import SwinIRProcessor

DATA_PROCESSOR_CONFIG = {
    'enabled': True,
    'rgb': {
        # 其他效果...
        
        'swinir': {
            'enabled': True,
            'task': 'sr',  # 'sr', 'denoise', 'jpeg'
            'model_path': '/home/nju/InterFuser/process_mothod/SwinIR/model_zoo/swinir/xxx.pth',
            'upscale': 2,
            'device': 'cuda',
        },
    },
}
```

### 方法 2: 在 Agent 中直接使用

在 `interfuser_agent.py` 中：

```python
import sys
sys.path.insert(0, '/home/nju/InterFuser/process_mothod/SwinIR')
from swinir_wrapper import SwinIRProcessor

class InterfuserAgent(autonomous_agent.AutonomousAgent):
    def setup(self, path_to_conf_file):
        # 初始化处理器
        self.swinir = SwinIRProcessor(
            model_path='...',
            task='sr',
            upscale=2
        )
    
    def tick(self, input_data):
        # 处理图像
        rgb = self.swinir.process(rgb)
        # ...
```

---

## 🗂️ 目录结构

```
process_mothod/
├── README.md                          # 📖 本文件（总索引）
│
└── SwinIR/                            # 🖼️ SwinIR 模块
    ├── README.md                      # SwinIR 原始文档
    ├── README_INTEGRATION.txt         # 集成总结
    ├── SWINIR_INTEGRATION_GUIDE.md    # 详细集成指南
    ├── swinir_wrapper.py              # Python 包装器
    ├── example_usage.py               # 使用示例
    │
    ├── models/                        # 模型定义
    │   └── network_swinir.py
    ├── model_zoo/                     # 预训练模型（需下载）
    ├── utils/                         # 工具函数
    ├── testsets/                      # 测试数据集
    └── ...                            # 其他 SwinIR 文件
```

---

## 📝 添加新模块指南

### 推荐的模块组织结构

```
process_mothod/
├── README.md                  # 总索引
├── ModuleName1/               # 模块 1
│   ├── README.md             # 模块说明
│   ├── wrapper.py            # Python 包装器
│   ├── example_usage.py      # 使用示例
│   └── ...                   # 模块源代码
│
└── ModuleName2/               # 模块 2
    ├── README.md
    ├── wrapper.py
    └── ...
```

### 添加新模块的步骤

1. **创建模块文件夹**
   ```bash
   mkdir -p /home/nju/InterFuser/process_mothod/NewModule
   ```

2. **复制或克隆模块代码**
   ```bash
   cp -r /path/to/source /home/nju/InterFuser/process_mothod/NewModule/
   ```

3. **创建 Python 包装器**
   - 参考 `SwinIR/swinir_wrapper.py` 的结构
   - 提供简单的接口: `process(image)` 方法

4. **编写集成文档**
   - `README.md`: 模块说明
   - 集成指南: 如何集成到 InterFuser

5. **创建使用示例**
   - `example_usage.py`: 展示基本用法

6. **更新本 README**
   - 在"模块列表"中添加新模块

---

## 🎯 使用场景

### SwinIR 使用场景

| 场景 | 配置 | 说明 |
|-----|------|------|
| 模拟低分辨率传感器 | SR 模型 | 降采样后再上采样 |
| 模拟噪声环境 | Denoise 模型 | 添加噪声后去噪 |
| 模拟 JPEG 压缩 | JPEG 修复模型 | 压缩后修复 |
| 图像质量增强 | SR 模型 | 提升输入质量 |

---

## 💡 最佳实践

### 1. 模块隔离
- 每个模块独立文件夹
- 提供统一的包装器接口
- 清晰的文档说明

### 2. 路径管理
```python
import sys
sys.path.insert(0, '/home/nju/InterFuser/process_mothod/ModuleName')
from module_wrapper import ModuleProcessor
```

### 3. 性能考虑
- 使用 GPU 加速（如果可用）
- 注意内存占用
- 考虑实时性要求

### 4. 文档完整性
- README: 模块概述
- 集成指南: 详细步骤
- 示例代码: 可运行的例子

---

## 🔗 相关资源

- **InterFuser 项目**: `/home/nju/InterFuser/`
- **数据处理器**: `/home/nju/InterFuser/sensor_data_processor_module/`
- **SwinIR GitHub**: https://github.com/JingyunLiang/SwinIR

---

## 📞 支持

如有问题：
1. 查看各模块的详细文档
2. 运行示例代码测试
3. 检查路径和依赖配置

---

**最后更新**: 2025-11-04  
**维护者**: InterFuser Project
