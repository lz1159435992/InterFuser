# 实现变更日志 �?CARLA 原生传感器增�?
本文件是 `./carla_native_enhancement/` 下新方法实现变更跟踪�?*唯一真实来源**�?
## 规则
- 每次代码更改都必须在此记录�?- 每个条目必须包括�?  - 日期/时间（UTC�?  - 变更 ID
  - 更改的文�?  - 更改了什�?  - 为什�?  - 如何验证
- 保持文档集同步：
  - `carla_native_enhancement/CHANGELOG.zh-CN.md`
  - `carla_native_enhancement/DESIGN.zh-CN.md`（当更改影响行为/配置时更新）
  - `carla_native_enhancement/CODE_SNAPSHOT.zh-CN.md`（当 baseline 相关行为更改时更新）
- 维护中英文版本并保持内容一致：
  - `carla_native_enhancement/CHANGELOG.md`
  - `carla_native_enhancement/DESIGN.md`
  - `carla_native_enhancement/CODE_SNAPSHOT.md`

## 条目

### 2026-02-04 (UTC) �?INIT-001
- 更改的文件：
  - `carla_native_enhancement/DESIGN.md`
  - `carla_native_enhancement/DESIGN.zh-CN.md`
  - `carla_native_enhancement/CODE_SNAPSHOT.md`
  - `carla_native_enhancement/CODE_SNAPSHOT.zh-CN.md`
  - `carla_native_enhancement/CHANGELOG.md`
  - `carla_native_enhancement/CHANGELOG.zh-CN.md`
- 更改了什么：
  - 创建了新的隔离目录和初始文档集�?  - 定义�?CARLA 原生传感器增强的设计（高帧率、高分辨率、无噪声）�?  - 记录�?baseline 行为以及�?`augmentation_seq_method` 的对比�?- 为什么：
  - 为硬件级传感器升级建立实现参考�?  - 提供软件（后处理）和硬件（原生）方法之间的清晰对比�?- 如何验证�?  - 仅文档更改；无需代码执行�?

### 2026-02-04 (UTC) �?IMPL-001
- 更改的文件：
  - `carla_native_enhancement/__init__.py`
  - `carla_native_enhancement/native_config_parser.py`
  - `carla_native_enhancement/interfuser_agent_native.py`
  - `carla_native_enhancement/restore_original_agent.sh`
  - `carla_native_enhancement/run_evaluation_native.sh`
  - `carla_native_enhancement/test_config_parser.py`
- 更改了什么：
  - 实现了支�?8 种配置的配置解析器（1 �?baseline + 3 个单�?+ 3 个双�?+ 1 个三项）�?  - 修改�?InterfuserAgent 以使用来�?`NATIVE_ENHANCE` 环境变量的原生传感器配置�?  - 创建了自定义 leaderboard 评估器包装器以支持动态帧率（20Hz �?40Hz）�?  - 实现了带有自�?agent 部署和恢复的评估运行脚本�?  - 创建了测试脚本以验证配置解析器的所有有效和错误情况�?- 为什么：
  - 启用 CARLA 级别的传感器升级，无需后处理或模型重新训练�?  - 模拟真实世界的硬件升级（高帧率相机、高分辨率传感器、无噪声成像）�?  - 提供 baseline 和增强传感器配置之间的清晰对比�?- 如何验证�?  - 配置解析器使�?9 种有效配置进行测试（全部通过）�?  - 错误处理使用 3 种无效情况进行测试（全部正确拒绝）�?  - 修复�?agent 导入路径以在部署�?`leaderboard/team_code/` 时正常工作�?  - 正确地子类化�?leaderboard 评估器以避免 monkey-patching 问题�?
### 2026-02-04 (UTC) �?IMPL-002
- 更改的文件：
  - `carla_native_enhancement/CHANGELOG.md`
  - `carla_native_enhancement/CHANGELOG.zh-CN.md`
- 更改了什么：
  - 更新了变更日志，包含实现状态和测试结果�?  - 记录了所�?8 种支持的配置及其参数�?  - 添加了评估和性能比较的后续步骤�?- 为什么：
  - 跟踪实现进度和测试状态�?  - 为支持的配置提供清晰的参考�?- 如何验证�?  - 仅文档更改；反映实际实现状态�?
## 实现状�?
### �?已完�?- 支持 8 种配置的配置解析�?- 具有原生传感器支持的修改�?agent
- 自定�?leaderboard 评估器包装器
- 评估运行脚本
- 恢复脚本
- 带有完整验证的测试脚�?- 文档（设计文档、代码快照、中英文变更日志�?
### 🔄 后续步骤
1. 运行 baseline 评估（`NATIVE_ENHANCE=none`）以验证 agent 正确加载
2. 测试 high_fps 配置（`NATIVE_ENHANCE=high_fps`）以验证 40Hz 操作
3. 运行所�?8 种配置并比较结果
4. 记录每种增强的性能影响
5. 使用评估结果和见解更�?DESIGN.zh-CN.md

### 📊 配置矩阵

| 配置 | 令牌 | 帧率 | 分辨�?| 噪声 | 描述 |
|------|------|------|--------|------|------|
| 1 | `none` | 20Hz | 800x600 | �?| Baseline |
| 2 | `high_fps` | 40Hz | 800x600 | �?| 仅高帧率 |
| 3 | `high_res` | 20Hz | 1600x1200 | �?| 仅高分辨�?|
| 4 | `no_noise` | 20Hz | 800x600 | �?| 仅无噪声 |
| 5 | `high_fps,high_res` | 40Hz | 1600x1200 | �?| 高帧�?+ 高分辨率 |
| 6 | `high_fps,no_noise` | 40Hz | 800x600 | �?| 高帧�?+ 无噪�?|
| 7 | `high_res,no_noise` | 20Hz | 1600x1200 | �?| 高分辨率 + 无噪�?|
| 8 | `high_fps,high_res,no_noise` | 40Hz | 1600x1200 | �?| 所有增�?|


### 2026-02-04 (UTC) �?IMPL-003
- 更改的文件：
  - `carla_native_enhancement/run_evaluation_native.sh`
  - `carla_native_enhancement/test_cleanup.sh`
  - `carla_native_enhancement/RANDOM_PORT_AND_CLEANUP_GUIDE.md`
- 更改了什么：
  - **修复**：将 `CLEANUP_KILL_EXISTING_CARLA_ON_ABORT` 默认值从 0 改为 1
  - **新增**：随机端口和清理功能的综合测试脚�?  - **新增**：随机端口分配和自动清理的详细指�?  - **验证**：随机端口分配正常工作（2000-40000 范围�?  - **验证**：Traffic Manager 端口分配及回退机制
  - **验证**：清理函数在退�?中止时关�?CARLA 进程
  - **验证**：信号捕获正确配置（INT TERM HUP QUIT EXIT�?- 为什么：
  - 确保脚本中止时（Ctrl+C）自动清�?CARLA 进程
  - 防止孤儿 CARLA 进程占用 GPU 资源
  - 通过随机端口分配实现安全的并行评�?  - �?`augmentation_seq_method` 实现保持一�?- 如何验证�?  - `test_cleanup.sh` 中的所有测试通过�?/4�?  - 随机端口分配测试（每次分配唯一端口�?  - 清理函数测试（成功关闭模�?CARLA 进程�?  - 配置验证（默认启用清理）
  - 信号捕获验证（INT TERM HUP QUIT EXIT 全部配置�?
## 功能总结

### �?随机端口分配
- **状�?*：完全实现并测试
- **使用**：`PORT=random` �?`PORT=0`
- **范围**�?000-40000
- **验证**：确�?p, p+1, p+2 都可�?- **TM 端口**：自动设置为 RPC 端口 + 500（带回退�?- **回退**：如果范围耗尽，使用系统分配的随机端口

### �?自动清理
- **状�?*：完全实现并测试
- **触发**：正常退出、中止（Ctrl+C）、错误退�?- **清理**：CARLA 进程、Python 评估器、agent 文件恢复
- **方法**：SIGTERM（优雅）�?等待 3 �?�?SIGKILL（强制）
- **配置**：默认启用（`CLEANUP_KILL_EXISTING_CARLA_ON_ABORT=1`�?- **信号处理**：INT、TERM、HUP、QUIT、EXIT

### �?进程管理
- **CARLA 进程**：按端口�?PID 关闭
- **Python 进程**：按 checkpoint endpoint 关闭
- **Agent 文件**：始终从备份恢复
- **验证**：所有进程成功清�?
## 测试结果

```
测试 1：随机端口分�?............................ 通过 �?测试 2：Traffic Manager 端口分配 ................ 通过 �?测试 3：清理函�?................................ 通过 �?测试 4：清理配�?................................ 通过 �?
所有测试通过�?4/4)
```

## 使用示例

### 基本使用（随机端口）
```bash
PORT=random bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

### 自动启动 CARLA（随机端口）
```bash
PORT=random AUTO_START_CARLA=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

### 并行评估（多 GPU�?```bash
# GPU 0
GPU_ID=0 PORT=random AUTO_START_CARLA=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 none &

# GPU 1
GPU_ID=1 PORT=random AUTO_START_CARLA=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 high_fps &

wait
```

### 手动启动 CARLA，中止时自动清理
```bash
# 终端 1：手动启�?CARLA
DISPLAY=:99 ./carla/CarlaUE4.sh -opengl -RenderOffScreen -nosound -world-port=2000

# 终端 2：运行评估（Ctrl+C 会关�?CARLA�?PORT=2000 CLEANUP_KILL_EXISTING_CARLA_ON_ABORT=1 \
bash carla_native_enhancement/run_evaluation_native.sh town05 none
```

### 2026-02-04 (UTC) �?PYTHON-001
- **变更**: 修复 Python 环境设置并清理文�?- **修改文件**:
  - `run_remaining_7_configs_safe.sh` - 添加 conda 激活（参�?augmentation_seq_method�?  - `run_remaining_7_configs.sh` - 添加 conda 激�?  - `run_single_config.sh` - 添加 conda 激�?  - `README.md` - 更新 conda 激活要求和 OOM 风险警告
  - 删除: `FEATURES_SUMMARY.md`, `FILES_GUIDE.md`, `IMPLEMENTATION_SUMMARY.md`, `MULTI_INSTANCE_GUIDE.md`, `MULTI_INSTANCE_GUIDE.zh-CN.md`, `OOM_RISK_ANALYSIS.md`, `PYTHON_SETUP_SUMMARY.md`, `QUICK_START_CHECKLIST.md`, `RANDOM_PORT_AND_CLEANUP_GUIDE.md`, `RUN_NATIVE_ENHANCEMENT.md`, `快速开�?md`, `显存风险说明.txt`
  - 删除: `run_with_correct_python.sh`, `run_with_correct_env.sh`, `test_python_env.sh`, `test_carlauser_env.sh`
- **变更内容**:
  - 所有运行脚本现在在检�?Python 版本前激�?conda 环境
  - 遵循�?augmentation_seq_method 相同的模式以保持一致�?  - 删除冗余文档文件（仅保留 DESIGN、CHANGELOG、CODE_SNAPSHOT、README�?  - 删除过时的辅助脚�?- **原因**:
  - 用户报告�?carlauser 身份运行时出�?Python 3.13 错误
  - 需要在运行前激�?interfuser conda 环境（Python 3.7�?  - 太多文档文件令人困惑且冗�?- **验证方式**:
  - 脚本更新以匹�?augmentation_seq_method 模式
  - �?Python 版本检查前添加 conda 激�?  - 删除所有过时文�?
### 2026-02-04 (UTC) �?BACKUP-001
- **变更**: 修复备份目录权限问题
- **修改文件**:
  - 目录权限: `chown -R carlauser:carlauser carla_native_enhancement/`
- **变更内容**:
  - 将整�?carla_native_enhancement/ 目录的所有权改为 carlauser
  - �?carlauser 添加写权�?  - 备份目录保持�?carla_native_enhancement/.backup_*
- **原因**:
  - 用户报告创建备份目录�?Permission denied"
  - carlauser 需要写权限来创建备份目�?  - 保持备份目录在模块本地以便更好地组织
- **验证方式**:
  - 更改所有权: `chown -R carlauser:carlauser carla_native_enhancement/`
  - 添加写权�? `chmod -R u+w carla_native_enhancement/`
  - 使用 `ls -ld carla_native_enhancement/` 验证

### 2026-02-04 (UTC) �?CLEANUP-001
- **变更**: 添加选择性清理脚本用于特定配�?- **修改文件**:
  - `cleanup_native_configs.sh` (新增) - 清理特定 native 配置进程
  - `cleanup_specific_configs.sh` (新增) - 功能更多的备选清理脚�?  - `CLEANUP_GUIDE.txt` (新增) - 清理使用指南
- **变更内容**:
  - 创建脚本以选择性清理被中断的配置进�?  - 可以清理特定配置而不影响其他正在运行的实�?  - 自动查找并杀�?Python 评估器和 CARLA 服务器进�?  - 清理后显示剩余进程和 GPU 使用情况
- **原因**:
  - 用户中断�?个配置，需要清理它�?  - 需要避免影响其他正在运行的实验（augseq、with_processor 等）
  - 提供安全和精确的清理机制
- **验证方式**:
  - 使用无参数测试脚本（显示当前进程�?  - 通过模式匹配正确识别 native 配置进程
  - 提取端口号并匹配 CARLA 服务�?
### 2026-02-04 (UTC) �?PARALLEL-001
- **变更**: 修改 run_remaining_7_configs_safe.sh 为并行运行所�?个配�?- **修改文件**:
  - `run_remaining_7_configs_safe.sh` - 移除分阶段执行，现在同时运行所�?个配�?- **变更内容**:
  - 移除3阶段执行逻辑
  - 所�?个配置现在以10秒间隔并行启�?  - 移除交互式确认提�?  - 简化脚本结�?- **原因**:
  - 用户根据实际使用情况确认 GPU 显存充足
  - 已运行的3个配置显示显存使用低于估�?  - 所�?GPU 都有 >23GB 可用显存
  - 并行执行更快且安�?- **验证方式**:
  - 脚本语法检查通过
  - GPU 显存分析显示安全余量（预计最�?8%使用率）
  - 基于实际运行进程的显存占�?
### 2026-02-09 (UTC) �?NOISE-001
- 修改文件�?  - `carla_native_enhancement/native_config_parser.py`
  - `carla_native_enhancement/interfuser_agent_native.py`
  - `carla_native_enhancement/test_config_parser.py`
  - `carla_native_enhancement/DESIGN.md`
  - `carla_native_enhancement/DESIGN.zh-CN.md`
  - `carla_native_enhancement/README.md`
  - `sensor_data_processor_module/interfuser_agent_complete.py`
- 变更内容�?  - 新增两个独立的增�?token：`gauss8` �?`gauss16`�?  - 在原�?agent �?tick 路径实现高斯噪声注入（作用于�?�?�?RGB；并裁剪�?[0,255]）�?  - 添加约束：高斯噪�?token 互斥，且不允许与其他 token 组合�?  - �?meta 截图保存改为�?`SAVE_META`/`DISABLE_META` 控制（默认不保存），并将保存条件�?`save_path` 对齐�?- 原因�?  - 支持在不与其他增强组合的前提下，对传感器噪声进行可控鲁棒性测试�?  - 默认关闭 meta 截图保存以减少磁盘开销；需要时再显式开启�?- 验证方式�?  - 更新配置解析器测试，覆盖 gauss token 与非法组合�?
### 2026-02-09 (UTC) �?BUGFIX-001
- 修改文件�?  - `carla_native_enhancement/interfuser_agent_native.py`
- 变更内容�?  - 移除 `run_step()` 函数内部�?`import carla`，避免遮蔽模块级 `carla` 导入�?  - 修复在创�?`carla.VehicleControl()` 时触发的 `UnboundLocalError: local variable 'carla' referenced before assignment`�?- 原因�?  - Python 作用域规则：函数体内出现 import/赋值会将该名字视为局部变量；内部导入导致后续引用走向未赋值的局部变量�?- 验证方式�?  - 基于 traceback �?Python 作用域规则确认；重新运行应可越过 `VehicleControl()` 创建位置�?
