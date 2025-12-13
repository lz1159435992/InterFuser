# InterFuser + LMDrive（含 LAVIS / vision_encoder / processor）新机器完整环境配置指南

本指南用于在一台新机器上复现你当前已经跑通的 **InterFuser** 与 **LMDrive**（含 LAVIS、vision_encoder/timm、leaderboard/scenario_runner）环境与评测流程，并包含：

- 两套 Conda 环境（InterFuser / LMDrive）
- CARLA 0.9.10.1 安装与端口配置
- LAVIS 依赖兼容性修复（`peft`、`huggingface_hub`/`diffusers` 版本组合）
- `vision_encoder` 自带 `timm` 的使用方式（解决 Memfuser `Unknown model`）
- IDE/编辑器中 **两个项目的 Python 解释器选择**
- LMDrive baseline 与带 processor 的评测脚本使用方式
- 典型报错/卡住现象的原因与处理

> 约定：下面所有命令均在 Linux（Ubuntu/Debian 系）下执行；路径以你的当前目录结构为准：`/home/nju/InterFuser` 为 git 根目录。

如果你的新机器目录不是 `/home/nju/InterFuser`（例如你现在是 `root@ubuntu:/Hyf`），建议先定义几个路径变量，然后把本文中的路径按需替换：

```bash
export IF_ROOT=/abs/path/to/InterFuser
export CARLA_ROOT=$IF_ROOT/carla
export LMDRIVE_ROOT=$IF_ROOT/LMDrive
```

后续所有命令里的 `/home/nju/InterFuser` 都可以理解为 `$IF_ROOT`。

---

## 0. 目录结构（建议保持一致）

建议新机器上保持和当前相同的目录结构：

```text
/home/nju/InterFuser
├── carla/                        # CARLA 0.9.10.1
├── interfuser/                   # InterFuser python package
├── leaderboard/                  # InterFuser leaderboard
├── scenario_runner/              # InterFuser scenario_runner
├── evaluation_scripts/           # InterFuser 便捷评测脚本
├── LMDrive/                      # LMDrive 工程（含 LAVIS / vision_encoder 等）
└── sensor_data_processor_module/ # 图像处理模块（SwinIR/SRGAN）
```

> 重要：**InterFuser 和 LMDrive 共用同一份 CARLA 安装**。也就是说你只需要把 CARLA 安装在 `/home/nju/InterFuser/carla` 一次即可。
> LMDrive 的评测脚本默认把 CARLA 当作位于 LMDrive 目录的上一级：`/home/nju/InterFuser/LMDrive/../carla`。

---

## 0.1 （可选）把本机 Conda 环境直接迁移到新机器

 你可以把本机已经跑通的 `interfuser` / `lmdrive` 两个 Conda 环境“导出并搬运”到新机器，但通常有两种做法：

 - **方式 A（推荐，可复现）**：导出 `environment.yml`，在新机器 `conda env create` 重建。
 - **方式 B（最快，直接搬运）**：使用 `conda-pack` 把整个环境打包成 `tar.gz`，拷贝到新机器解压使用。

 > 注意：无论哪种方式，**GPU 驱动 / 系统级依赖 / CARLA 本体**都不在 Conda 环境里，仍然需要按本文的“系统级依赖”和“CARLA 安装”部分在新机器完成。

 ### 方式 A（推荐）：导出 yml 并在新机器重建

 仓库已提供（源机器导出好的）两个环境文件，直接在新机器使用即可：

 - `env_exports/interfuser_env.yml`
 - `env_exports/lmdrive_env.yml`

 在新机器创建：

 ```bash
 conda env create -f env_exports/interfuser_env.yml
 conda env create -f env_exports/lmdrive_env.yml
 ```

 验证：

 ```bash
 conda activate interfuser
 python -c "import sys; print(sys.version)"

 conda activate lmdrive
 python -c "import sys; print(sys.version)"
 ```

 如果你希望在新机器上“自己重新导出一份”或做长期维护，也可以按下面方式导出（建议每个环境导出一份“完整版本”和一份“最小历史版本”）：

 在当前机器导出（建议每个环境导出一份“完整版本”和一份“最小历史版本”）：

 ```bash
 # InterFuser env
 conda activate interfuser
 conda env export --no-builds > interfuser_env_full.yml
 conda env export --from-history > interfuser_env_min.yml

 # LMDrive env
 conda activate lmdrive
 conda env export --no-builds > lmdrive_env_full.yml
 conda env export --from-history > lmdrive_env_min.yml
 ```

 把 `*_env_full.yml`（或 `*_env_min.yml`）拷贝到新机器后，在新机器创建：

 ```bash
 conda env create -f interfuser_env_full.yml
 conda env create -f lmdrive_env_full.yml
 ```

 验证：

 ```bash
 /path/to/conda/envs/interfuser/bin/python -c "import sys; print(sys.version)"
 /path/to/conda/envs/lmdrive/bin/python -c "import sys; print(sys.version)"
 ```

 > 经验：
 > - `*_env_full.yml` 更接近“完整复刻”，但更依赖当时的包源可用性。
 > - `*_env_min.yml` 更干净，适合长期维护；但你需要按本文各章节再把 pip 依赖（LAVIS/vision_encoder/processor 等）补齐。

 ### 方式 B（最快）：conda-pack 打包整个环境并解压使用

 适用场景：你希望最快把“当前可运行的环境”搬到新机器，不想重新解析依赖。

 约束：

 - 两台机器需要同为 **Linux x86_64**，并且系统库（glibc 等）不要差太多。
 - `conda-pack` 只搬运 Python/Conda 包，不包含 NVIDIA 驱动、CARLA、系统依赖。

 在当前机器（源机器）打包：

 ```bash
 # 如果没有 conda-pack，需要先安装（推荐 conda-forge）
 # conda install -c conda-forge conda-pack

 conda pack -n interfuser -o interfuser.tar.gz
 conda pack -n lmdrive -o lmdrive.tar.gz
 ```

 > 说明：你当前机器的 Conda 版本较旧（`conda 4.5.12`），并且没有 `conda run`。
 > 如果安装 `conda-pack` 遇到问题，建议在源机器/新机器使用 Miniconda3/Anaconda3（Python3 的 base）来执行 `conda-pack` 或按“方式 A”重建。

 拷贝到新机器（任选一种方式，如 scp/rsync/U 盘），在新机器解压到一个固定目录，例如：

 ```bash
 mkdir -p /opt/conda_envs/interfuser
 tar -xzf interfuser.tar.gz -C /opt/conda_envs/interfuser
 /opt/conda_envs/interfuser/bin/conda-unpack

 mkdir -p /opt/conda_envs/lmdrive
 tar -xzf lmdrive.tar.gz -C /opt/conda_envs/lmdrive
 /opt/conda_envs/lmdrive/bin/conda-unpack
 ```

 使用时可以直接激活（不一定需要 `conda activate`）：

 ```bash
 source /opt/conda_envs/interfuser/bin/activate
 python -c "import sys; print(sys.executable); print(sys.version)"

 source /opt/conda_envs/lmdrive/bin/activate
 python -c "import sys; print(sys.executable); print(sys.version)"
 ```

---

## 1. 系统级依赖（两项目通用）

- **NVIDIA Driver**：确保能正常 `nvidia-smi`。
- **CUDA**：LMDrive 依赖 PyTorch GPU 版；建议 CUDA 11.x（你的环境里曾使用 `torch 2.0.1 + cu118`）。
- **Conda**：建议安装 Anaconda3/Miniconda。
- **基本工具**：`git`, `wget`, `curl`, `cmake`, `build-essential`。
- **CARLA 运行所需系统库**（不同发行版可能略有差异）。如果 CARLA 无法启动，优先按 CARLA 官方文档补齐缺失库。

### 1.1 目标新机器信息（你提供的配置）

- **OS**：Ubuntu 20.04.6 LTS
- **GPU**：Tesla V100 SXM2 32GB x4
- **NVIDIA Driver**：520.61.05
- **CUDA Runtime**：11.8（`nvidia-smi` 显示）

这套配置可以直接使用 **PyTorch cu118** 轮子（无需系统安装完整 CUDA Toolkit，除非你要编译 CUDA 扩展）。

### 1.2 Ubuntu 20.04 推荐系统包（运行 CARLA/pygame/常用 Python 轮子）

在新机器上建议先装一组常见运行库（CARLA/Unreal 常缺的动态库 + 基本构建工具）：

```bash
sudo apt-get update
sudo apt-get install -y \
  git wget curl ca-certificates \
  build-essential cmake pkg-config \
  libglib2.0-0 libsm6 libxext6 libxrender1 \
  libxrandr2 libxinerama1 libxcursor1 libxi6 \
  libgl1 libgl1-mesa-glx libglu1-mesa \
  libgtk-3-0 libnss3 libxss1 libasound2 \
  libatomic1
```

> 说明：不同 CARLA 包/发行方式对依赖的要求略有差异；如果 CARLA 启动报 “missing shared library”，优先按报错逐个补库。

### 1.3 CARLA 建议启动参数（降低渲染负载/适配无显示）

如果新机器是服务器环境（无真实显示器/桌面），建议：

- 在启动 CARLA 时使用 `-opengl`。
- 尝试 `-RenderOffScreen`（不弹窗口但仍渲染，传感器照常出图）。
- 降低渲染质量/分辨率以减少 GPU 压力。

示例（在你的脚本里启动 `CarlaUE4.sh` 那行可替换成类似）：

```bash
./CarlaUE4.sh --world-port=2000 -opengl -RenderOffScreen -quality-level=Low -ResX=800 -ResY=600
```

> 补充：你之前遇到过“整机重启”，这通常是 **GPU 驱动/硬件/电源/温度**层面的异常，关掉窗口只能略微减轻负载；降低 CARLA 渲染负载更关键。

### 1.4 PyTorch（cu118）推荐安装方式（与 Driver/CUDA 11.8 匹配）

如果你希望在新机器上尽量贴近你当前跑通的组合，建议在 `lmdrive` 环境中明确安装 cu118 版本：

```bash
python -m pip install --upgrade pip
python -m pip install \
  torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 \
  --index-url https://download.pytorch.org/whl/cu118
```

如果你所在网络无法直连 PyPI/PyTorch 源：

- 先在能联网的机器上下载 wheel，再离线拷贝安装；或
- 使用内部镜像/代理。

---

## 2. 项目 A：InterFuser 环境（conda env: `interfuser`）

### 2.1 创建 Conda 环境

InterFuser README 推荐：

```bash
conda create -n interfuser python=3.7
conda activate interfuser
```

### 2.2 安装 Python 依赖

在 InterFuser 根目录：

```bash
cd /home/nju/InterFuser
pip install -r requirements.txt
```

然后安装 InterFuser 包（开发模式）：

```bash
cd /home/nju/InterFuser/interfuser
python setup.py develop
```

### 2.3 安装 CARLA（InterFuser 评测）

InterFuser README 的方式：

```bash
cd /home/nju/InterFuser
chmod +x setup_carla.sh
./setup_carla.sh
```

并安装 CARLA Python API。

> 提醒：建议将 CARLA 安装在 **InterFuser 根目录的 `carla/` 下**（即 `/home/nju/InterFuser/carla`），这样 LMDrive 可以直接复用，无需再安装第二份。

安装完成后建议先确认这两个文件存在：

```text
/home/nju/InterFuser/carla/CarlaUE4.sh
/home/nju/InterFuser/carla/PythonAPI
```

#### 2.3.1 重要：CARLA 0.9.10.1 的 PythonAPI 与 Python 版本匹配

你当前工程里的 CARLA PythonAPI 分发文件在：

```text
${CARLA_ROOT}/PythonAPI/carla/dist/
  carla-0.9.10-py3.7-linux-x86_64.egg
  carla-0.9.10-py2.7-linux-x86_64.egg
```

这意味着：

- 如果你通过 `PYTHONPATH` 直接加载 `.egg`，那么 **Python 版本必须是 3.7**。
- 而 LMDrive 的推荐环境经常是 Python 3.8；此时 **不要依赖 py3.7 的 egg**，而应该在 `lmdrive` 环境里安装一个与 Python 3.8 匹配的 `carla`（如果你有可用的 wheel 或自行编译）。

最简单的验证方式是：在你准备跑评测的那个 conda 环境里执行：

```bash
python -c "import sys; print('python:', sys.version)"
python -c "import carla; import inspect; print('carla loaded from:', inspect.getfile(carla))"
```

如果 `import carla` 失败（常见于 Python 3.8/3.9 与 0.9.10 的二进制不匹配），解决方案一般是二选一：

- **方案 A（更稳）**：让闭环评测使用 Python 3.7（与官方 egg 一致）。
- **方案 B（更灵活）**：继续用 Python 3.8，但为该版本准备可用的 `carla` wheel/编译产物，并确保脚本不再把 `py3.7 egg` 强行塞进 `PYTHONPATH`。

- 如果你使用 **CARLA egg**（对应 py3.7）：

```bash
easy_install carla/PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg
```

> 注意：README 提到需要 `setuptools==41` 才有 `easy_install`。

- 或者使用 pip wheel（如果可用）：

```bash
pip install carla
```

（以你当前工程为准：InterFuser 的评测脚本里一般会把 egg 加到 `PYTHONPATH`。）

### 2.4 InterFuser 评测（脚本）

InterFuser 提供了便捷脚本：

- 启动 CARLA：

```bash
cd /home/nju/InterFuser/evaluation_scripts
./start_carla_server.sh 0
```

- 运行评测（Town05 或 42routes）：

```bash
cd /home/nju/InterFuser/evaluation_scripts
./run_evaluation.sh town05
# 或
./run_evaluation.sh 42routes
```

> 注意：`/home/nju/InterFuser/evaluation_scripts/*.sh` 里可能存在对 conda 路径的硬编码（例如 `source /home/nju/anaconda2/etc/profile.d/conda.sh`）。
> 在新机器上如果你的 conda 安装路径不同，需要把脚本中的该行改成你实际的 conda 路径（例如 `~/miniconda3/etc/profile.d/conda.sh` 或 `/opt/conda/etc/profile.d/conda.sh`）。

---

## 3. 项目 B：LMDrive 环境（conda env: `lmdrive`）

LMDrive 由三部分组成：

- `vision_encoder/`：自带修改过的 `timm`（包含 Memfuser 注册）
- `LAVIS/`：视觉语言模型库（LMDrive 的 drive model 依赖）
- `leaderboard/` + `scenario_runner/`：闭环评测

### 3.1 创建 Conda 环境

你当前这台机器上实际在用的 `lmdrive` 环境 Python 版本是：**Python 3.8.13**。

LMDrive README 推荐：

```bash
conda create -n lmdrive python=3.8
conda activate lmdrive
```

> 建议：为了复现一致性，保持 `python==3.8.*`（例如 3.8.13）即可。

### 3.2 安装 vision_encoder（关键：不要用 pip 的 timm）

> 目标：确保使用 `LMDrive/vision_encoder/timm`，否则会出现：
> `Unknown model (memfuser_baseline_e1d3_return_feature)`。

步骤：

```bash
cd /home/nju/InterFuser/LMDrive/vision_encoder

# 如果系统里已经装过 pip 的 timm，建议卸载，避免冲突
python -m pip uninstall -y timm || true

pip install -r requirements.txt
python setup.py develop
```

### 3.3 安装 LAVIS（并修复依赖兼容）

```bash
cd /home/nju/InterFuser/LMDrive/LAVIS
pip install -r requirements.txt
python setup.py develop
```

#### 3.3.1 关键兼容组合（来自你成功导入的环境）

你当前跑通过的一组关键版本（供新机器 pin）：

- `huggingface_hub==0.13.4`
- `diffusers==0.14.0`（或 `<=0.16.0`，但建议复现用 0.14.0）
- `transformers==4.28.1`
- `tokenizers==0.13.2`
- `accelerate==0.19.0`
- `opencv-python-headless==4.5.5.64`
- `peft==0.4.0`（用于 `lavis.models.drive_models.drive`）

建议在安装完 LAVIS 依赖后，显式 pin 到这组已验证可工作的版本（避免后续被 `pip install -r requirements.txt` 自动升级导致 `cached_download` 等兼容问题）：

```bash
cd /home/nju/InterFuser/LMDrive/LAVIS
python -m pip install \
  "huggingface_hub==0.13.4" \
  "diffusers==0.14.0" \
  "transformers==4.28.1" \
  "tokenizers==0.13.2" \
  "accelerate==0.19.0" \
  "opencv-python-headless==4.5.5.64" \
  "peft==0.4.0"
```

当时的核心报错是：

- `ModuleNotFoundError: No module named 'peft'`

修复方式（你验证成功）：

```bash
cd /home/nju/InterFuser/LMDrive/LAVIS
python -m pip install "peft==0.4.0"
```

安装完成后测试导入：

```bash
cd /home/nju/InterFuser/LMDrive/LAVIS
python -c "from lavis.common.registry import registry; print('LAVIS 已成功安装！')"
```

> 如果出现 `cached_download` 相关兼容问题：优先确保 `huggingface_hub==0.13.4`。你目前的 `lmdriver_agent.py` 里也加入了兼容性 monkey patch（对新机器也安全）。

### 3.4 安装 CARLA（LMDrive 评测）

LMDrive README 建议：

```bash
cd /home/nju/InterFuser/LMDrive
chmod +x setup_carla.sh
./setup_carla.sh
pip install carla
```

说明（建议按你当前工程的实际结构来做）：

- **推荐做法**：只安装一份 CARLA 到 `/home/nju/InterFuser/carla`，然后 LMDrive 直接复用。
- 如果你已经按 InterFuser 的步骤装好了 `/home/nju/InterFuser/carla`，那么 **LMDrive 这一节的 `./setup_carla.sh` 可以跳过**（避免下载/解压第二份 CARLA）。
- LMDrive 侧你通常只需要在 `lmdrive` 环境里保证 `import carla` 可用（推荐走 pip）。
- LMDrive 的评测脚本（例如 `leaderboard/scripts/run_evaluation*.sh`）默认使用：

```bash
export CARLA_ROOT=../carla
```

这等价于：当你在 `/home/nju/InterFuser/LMDrive` 下运行脚本时，它会指向 `/home/nju/InterFuser/carla`。

如果你的 CARLA 不在这个位置，有两种改法（二选一）：

- **改脚本**：把脚本里的 `export CARLA_ROOT=../carla` 改成你的实际路径。
- **运行时覆盖**（推荐，最少改动）：运行脚本前先导出正确的 `CARLA_ROOT`，例如：

```bash
export CARLA_ROOT=/abs/path/to/carla
bash leaderboard/scripts/run_evaluation.sh
```

> 说明：LMDrive 的 `run_evaluation*.sh` 脚本使用相对路径（例如 `../carla`、`leaderboard/...`），因此**建议在 `$LMDRIVE_ROOT`（即 LMDrive 根目录）下运行**，否则相对路径会失效。

另外：如果你使用 pip 安装 carla，脚本里的 egg 路径可以保留（通常不会被实际用到），但建议保证 `import carla` 在 `lmdrive` 环境中可用。

建议在 `lmdrive` 环境中做一次快速自检：

```bash
python -c "import carla; import inspect; print('carla loaded from:', inspect.getfile(carla))"
```

同时建议确认你运行脚本时用到的 `python3` 确实来自当前 conda env：

```bash
which python
which python3
python -c "import sys; print(sys.executable)"
```

> 说明：你的 LMDrive 脚本中会把 `carla-0.9.10-py3.7-linux-x86_64.egg` 加到 `PYTHONPATH`。
> 如果你在新机器上用的是 Python 3.8，且出现 `ImportError`（二进制 ABI 不匹配），优先确保 `pip install carla` 生效；必要时可以把脚本里的那行 `...carla-0.9.10-py3.7...egg` 注释/删除。

---

## 4. IDE / 编辑器：两个项目的 Python 解释器配置

你需要在 IDE 中为两个项目分别选择解释器，否则经常出现“import 找不到 / pip 装到另一个环境”等问题。

### 4.1 InterFuser 项目解释器

- **项目根**：`/home/nju/InterFuser`
- **解释器**：conda env `interfuser` 的 python（Python 3.7）

常见路径示例：

```text
~/anaconda3/envs/interfuser/bin/python
```

### 4.2 LMDrive 项目解释器

- **项目根**：`/home/nju/InterFuser/LMDrive`
- **解释器**：conda env `lmdrive` 的 python（Python 3.8）

常见路径示例：

```text
~/anaconda3/envs/lmdrive/bin/python
```

### 4.3 一个快速自检命令

在 IDE 的终端里分别执行：

```bash
python -c "import sys; print(sys.executable)"
```

确保 InterFuser 终端打印的是 `.../envs/interfuser/bin/python`，LMDrive 终端打印的是 `.../envs/lmdrive/bin/python`。

---

## 5. LMDrive 评测：baseline 与带 processor 两套脚本

你当前已修复并使用的 LMDrive 评测脚本：

- baseline：`/home/nju/InterFuser/LMDrive/leaderboard/scripts/run_evaluation.sh`
- processor：`/home/nju/InterFuser/LMDrive/leaderboard/scripts/run_evaluation_lmdrive_with_processor.sh`

这两份脚本都已经：

- 自动启动 CARLA（随机端口 PT）
- 设置 `PYTHONPATH`，包含 `vision_encoder`，确保 Memfuser 注册生效
- **不再传 `--resume=...`**（因为 evaluator 的参数是 `type=bool`，`--resume=False` 仍会被解析成 True）

> 额外说明：`leaderboard_evaluator.py` 中 `--resume` 定义为 `type=bool`：
> `parser.add_argument('--resume', type=bool, default=False, ...)`
> 所以不要用 `--resume=False` 这种形式；如果要控制是否 resume，推荐通过脚本逻辑处理（你当前就是这么做的）。

### 5.1 baseline 运行

```bash
cd /home/nju/InterFuser/LMDrive
conda activate lmdrive

# 推荐：离线模式（避免评测时尝试联网下载）
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# 推荐：headless（不弹 pygame 窗口）
export LMDRIVE_HEADLESS=1

bash leaderboard/scripts/run_evaluation.sh
```

### 5.2 带 processor 运行

```bash
cd /home/nju/InterFuser/LMDrive
conda activate lmdrive

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export LMDRIVE_HEADLESS=1

# 例：long + srgan_2x
bash leaderboard/scripts/run_evaluation_lmdrive_with_processor.sh langauto_long srgan_2x

# 例：tiny + no_processing
bash leaderboard/scripts/run_evaluation_lmdrive_with_processor.sh langauto_tiny no_processing
```

支持的 `EVAL_TYPE`：

- `langauto_long`
- `langauto_short`
- `langauto_tiny`

支持的 `CONFIG_TYPE`（由 `sensor_data_processor_module/data_processor_config.py` 决定）：

- `no_processing`
- `denoise15`, `denoise25`, `denoise50`
- `sr2x`, `sr4x`, `jpeg_repair`
- `srgan_2x`, `srgan_enhance`, `srgan_4x`
- `custom`

---

## 6. HuggingFace 模型缓存与离线运行

### 6.1 为什么看起来“每次都在下载”？

`from_pretrained(...)` 每次启动新进程都会：

- 从 **本地缓存**读取权重
- 再加载到内存/GPU

这会出现 `Loading checkpoint shards: ...` 的进度条，但通常并不意味着重新联网下载。

### 6.2 强制离线（推荐用于评测）

评测前设置：

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

如果离线模式还能正常跑，说明权重已经完全缓存。

### 6.3 缓存位置

默认 HuggingFace 缓存：

```text
~/.cache/huggingface/hub
```

在新机器上，如果网络受限，推荐提前把该目录复制过去（或提前下载）。

### 6.4 离线缓存迁移/共享（可执行步骤）

#### 6.4.1 推荐：把缓存放到“共享/大容量磁盘”并通过环境变量统一指向

很多服务器默认 `/root` 盘空间较小，且多用户会重复下载。建议把缓存统一放到一个大盘目录，例如：

- `/data/hf_cache`（按你们服务器实际挂载调整）

在 shell 中设置（建议写入 `~/.bashrc` 或评测脚本中）：

```bash
export HF_HOME=/data/hf_cache
export HUGGINGFACE_HUB_CACHE=/data/hf_cache/hub
export TRANSFORMERS_CACHE=/data/hf_cache/transformers

# 可选：torch 的模型/权重缓存（例如 torchvision、部分 checkpoint）
export TORCH_HOME=/data/torch_cache
```

> 注意：HuggingFace Hub 的默认真实目录是 `~/.cache/huggingface/hub`。
> 设置上述变量后，新下载和读取都会走新目录。

#### 6.4.2 从旧机器拷贝缓存到新机器（rsync 方式）

在**新机器**执行（假设旧机器可以 ssh 访问；把 `OLD_HOST` 和用户名改成你的实际值）：

```bash
# 1) HuggingFace Hub
rsync -aP OLD_USER@OLD_HOST:/home/nju/.cache/huggingface/hub/ /data/hf_cache/hub/

# 2) transformers 的额外缓存（如果存在）
rsync -aP OLD_USER@OLD_HOST:/home/nju/.cache/huggingface/ /data/hf_cache/

# 3) torch cache（可选）
rsync -aP OLD_USER@OLD_HOST:/home/nju/.cache/torch/ /data/torch_cache/
```

如果旧机器同样是 root 用户，路径可能是：`/root/.cache/huggingface/hub`。

#### 6.4.3 无法 rsync 时：tar 打包迁移

在旧机器打包：

```bash
tar -czf hf_hub_cache.tgz -C ~/.cache/huggingface hub
```

拷到新机器后解压到目标目录：

```bash
mkdir -p /data/hf_cache/hub
tar -xzf hf_hub_cache.tgz -C /data/hf_cache
```

#### 6.4.4 验证“完全离线可用”（不触网）

1) 先强制离线：

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

2) 在 `lmdrive` 环境里做一个最小验证（示例以 `bert-base-uncased` 为例；你也可以换成 LMDrive 实际用到的模型名）：

```bash
python - << 'PY'
from transformers import AutoTokenizer

name = "bert-base-uncased"
tok = AutoTokenizer.from_pretrained(name)
print("OK offline load:", name)
PY
```

3) 再跑一次 `langauto_tiny` baseline（同样带离线变量），如果评测不再出现任何 “Downloading/Fetching” 字样，说明离线缓存就绪。

---

## 7. Headless（无显示服务器）运行与截图

### 7.1 不显示 pygame 窗口但仍保存截图

LMDrive 里你已经使用：

```bash
export LMDRIVE_HEADLESS=1
```

此时会走 `DummyDisplayInterface`，不弹出 pygame 窗口。

同时你已经修改了 `LMDriveAgent.save()`：

- headless 时保存的截图来自 **真实的 `rgb_front/left/right` 拼接图**
- 不再保存 Dummy 的黑屏 `surface`

因此：

- 无显示服务器仍然可以跑闭环
- `data/eval*/*/meta/*.jpg` 仍然是可视化截图（多视图拼接）

### 7.2 CARLA 的 offscreen（可选，降低崩溃/重启风险）

如果你遇到整机重启/驱动掉线（通常是 GPU/电源/温度/驱动级问题），可尝试降低渲染负载：

- 使用 `-opengl`
- 使用 `-RenderOffScreen`
- 使用低画质/低分辨率启动参数

（这部分是否需要取决于你的服务器环境；不影响 Python 侧截图保存逻辑。）

---

## 8. Processor 模块：性能与显存（SRGAN/SwinIR）

### 8.1 CUDA OOM 但评测不崩溃

`SensorDataProcessor.process_rgb()` 对 `RuntimeError`（包含 CUDA OOM）做了捕获，并退回原图继续评测。

你曾遇到：

```text
⚠️ 图像处理失败 (RuntimeError): CUDA out of memory ... 返回原始图像继续评估。
```

这说明增强没生效，但评测会继续。

### 8.2 为避免 OOM：SRGAN 预设已改为 CPU

你当前仓库里已经把：

- `DATA_PROCESSOR_CONFIG['srgan']['device']`
- `CONFIG_SRGAN_2X / ENHANCE / 4X`

都改为 `cpu`，以避免与 LMDrive 本体争抢显存。

如果新机器显存更大、你希望 SRGAN 跑 GPU，可以把这些配置改回 `cuda`，并考虑：

- `half_precision=True`
- 只处理 `rgb_front` 或降低处理频率

### 8.3 processor 运行前置条件（新机器最容易漏）

如果你要跑带 processor 的评测（`run_evaluation_lmdrive_with_processor.sh` / `use_data_processor=True`），需要额外满足以下条件，否则会出现“模型文件不存在 / 无法导入 SwinIR/SRGAN”并自动退回原图：

- **处理方法代码目录**：`sensor_data_processor_module/data_processor.py` 里硬编码了：

```text
PROCESS_METHOD_ROOT = '/home/nju/InterFuser/process_mothod'
```

并期望在该目录下存在：

```text
SwinIR/
SRGAN/
```

- **模型权重文件路径**：`sensor_data_processor_module/data_processor_config.py` 里默认也是绝对路径（例如 SwinIR/SRGAN 的 `model_path`）。

因此在新机器上你有两种做法（二选一）：

- **推荐做法**：把 `PROCESS_METHOD_ROOT` 和各个 `model_path` 改成新机器上的实际路径（最干净）。
- **快速兼容做法**：在新机器上创建与旧机器相同的目录结构（例如把你的代码/权重同步到 `${IF_ROOT}/process_mothod`，并确保路径能对应到 `/home/nju/InterFuser/process_mothod`；或者用软链接把旧路径映射到新路径）。

只跑 baseline（`CONFIG_TYPE=no_processing`）则不需要准备上述 `process_mothod`/模型文件。

---

## 9. 常见问题（排障速查）

### 9.1 只打印 `> Registering the global statistics` 就退出

原因：

- 之前启用了 resume，checkpoint 里 `_checkpoint.progress` 已经是 `[total, total]`，导致所有 routes 被跳过。

你当前脚本已经避免 `--resume` 参数；如果你仍想从头开始，删除旧结果文件即可：

```bash
rm -f /home/nju/InterFuser/LMDrive/results/sample_result.json
```

### 9.2 `Unknown model (memfuser_baseline_e1d3_return_feature)`

原因：

- 导入的是 pip 的 `timm`，而不是 `LMDrive/vision_encoder/timm`。

修复：

- 卸载 pip timm
- `vision_encoder/python setup.py develop`
- 确保评测脚本 `PYTHONPATH` 包含 `vision_encoder`

### 9.3 `ImportError: attempted relative import with no known parent package`

原因：

- `leaderboard/team_code/lmdriver_config_processor.py` 被 `imp.load_source` 以文件方式加载，没有包上下文；相对导入会失败。

修复（你已完成）：

- 把 `from .lmdriver_config import ...` 改成 `from lmdriver_config import ...`

### 9.4 `> Running the route` 后很久没输出

这通常是正常现象：

- 进入 `ScenarioManager.run_scenario()` 主循环后不再频繁打印日志。

确认是否在跑：

- 观察 `data/eval*/*/meta/*.jpg` 是否持续增加

### 9.5 黑屏截图

原因：

- headless 下 DummyDisplay 返回黑 `surface`，如果保存的是 `surface` 就会黑屏。

你已修复：headless 下 `save()` 用真实 RGB 拼接图保存。

---

## 10. 新机器复现清单（最短路径）

### InterFuser（Python 3.7）

```bash
conda create -n interfuser python=3.7
conda activate interfuser
cd /path/to/InterFuser
pip install -r requirements.txt
cd interfuser
python setup.py develop
```

### LMDrive（Python 3.8.13）

```bash
conda create -n lmdrive python=3.8
conda activate lmdrive

cd /path/to/InterFuser/LMDrive/vision_encoder
python -m pip uninstall -y timm || true
pip install -r requirements.txt
python setup.py develop

cd ../LAVIS
pip install -r requirements.txt
python setup.py develop
python -m pip install "peft==0.4.0"

# 推荐：把 LAVIS/HF 依赖 pin 到已验证组合
python -m pip install \
  "huggingface_hub==0.13.4" \
  "diffusers==0.14.0" \
  "transformers==4.28.1" \
  "tokenizers==0.13.2" \
  "accelerate==0.19.0" \
  "opencv-python-headless==4.5.5.64" \
  "peft==0.4.0"

# 测试
python -c "from lavis.common.registry import registry; print('LAVIS 已成功安装！')"

# 可选：确认 carla Python API 可用（建议在跑闭环前做一次）
python -c "import carla; print('carla import ok')"
```

### 跑一次 tiny baseline（最小闭环验证）

```bash
cd /path/to/InterFuser/LMDrive
conda activate lmdrive
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export LMDRIVE_HEADLESS=1
bash leaderboard/scripts/run_evaluation.sh
```

---

## 11. 你需要在新机器上确认的关键点

- **CARLA 版本**：0.9.10.1（与 routes/scenarios 对齐）
- **两个 conda env**：InterFuser 用 `interfuser`，LMDrive 用 `lmdrive`
- **timm 冲突**：LMDrive 必须使用 `vision_encoder` 的 timm
- **HF 离线缓存**：评测前建议开启 offline，避免运行中下载导致卡住

---

（本文件由当前仓库内实际可运行的脚本与历史排障过程整理而成；如果你在新机器上遇到新的报错，把终端最后 200 行输出贴出来，我可以继续帮你把指南补齐。）
