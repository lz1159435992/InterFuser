<!--
 * @Author: Lenovo 1159435992@qq.com
 * @Date: 2026-01-11 00:42:18
 * @LastEditors: Lenovo 1159435992@qq.com
 * @LastEditTime: 2026-01-11 00:46:44
 * @FilePath: \ADS_TEST\output\RQ3_scripts\README.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
# RQ3 脚本（CARLA System MR）

本目录包含用于生成 `eval.tex` 中 **RQ3（System MR）** 相关数字的脚本与说明。

## 1. 本目录脚本会产出什么

- **Leaderboard 全局汇总行**（用于 `Table~\ref{tab:rq3_simulator}`）
  - 指标包括：`Driving Score (score_composed)`、`Route Completion (score_route)`，以及若干代表性安全违规统计（infractions）。
  - `Collisions` 定义为 `collisions_pedestrian + collisions_vehicle + collisions_layout` 之和。
  - `Off-road` 对应 `outside_route_lanes`。

- **Route-level System MR 违反率行**（用于 `Table~\ref{tab:rq3_mr_violations}`）
  - `Viol.(DS)`：Driving Score 发生下降的路线占比（判定规则：`ds' < ds - ds_tol`）。
  - `Viol.(Safety)`：至少一个安全指标变差（增加）的路线占比。
  - `Viol.(Any)`：`Viol.(DS)` 或 `Viol.(Safety)` 任一成立的路线占比。
  - `Mean ΔDS` / `Mean ΔRC`：逐路线平均的 DS/RC 变化量。

- **Overall 总体违反率**
  - `Overall` 行按不同 suite 的 `#Routes` 做加权汇总（即按路线数量加权，而不是对各 suite 的 ratio 简单平均）。

## 2. 脚本默认使用的数据位置

脚本默认假设仓库目录结构如下（相对 repo root）：

- Interfuser baseline（Original）：
  - `output/interfuser/interfuser_town05_result.json`
  - `output/interfuser/interfuser_42routes_result.json`

- Interfuser enhanced（with processor）：
  - `output/interfuser/with_processor/town05_srgan_2x_*.json`
  - `output/interfuser/with_processor/42routes_srgan_2x_*.json`
  - Interfuser 的 DN 当前按 **N/A** 处理（直到拿到完整可用结果）。

- LMDrive（with processor）：
  - `output/lmdrive/with_processor/langauto_{suite}_{variant}_*.json`
  - 其中 `suite` 取 `{long, short, tiny}`，`variant` 取 `{no_processing, no_processings, srgan_2x, denoise15}`。

抽取脚本会对每种 pattern 选择 **最新** 的匹配文件。

## 3. 如何运行

在任意目录下运行：

```bash
python output/RQ3_scripts/extract_rq3_tables.py
```

可选参数：

```bash
python output/RQ3_scripts/extract_rq3_tables.py --section simulator
python output/RQ3_scripts/extract_rq3_tables.py --section violations
python output/RQ3_scripts/extract_rq3_tables.py --ds-tol 0.0
```

脚本会输出可直接粘贴到 `eval.tex` 的 LaTeX 表格行。

## 4. 清理辅助脚本（Interfuser 不完整结果）

非破坏性清理脚本会把不完整/损坏的 Interfuser JSON 结果移动到带时间戳的目录：

```bash
python output/RQ3_scripts/cleanup_interfuser_incomplete.py --dry-run
python output/RQ3_scripts/cleanup_interfuser_incomplete.py
```

默认输入目录：

- `output/interfuser/with_processor`

默认 trash 目录：

- `output/interfuser/with_processor/_trash_incomplete/<timestamp>`

## 5. 同步更新要求（重要）

如果你修改了 `eval.tex` 中 RQ3 的任何数字或口径（例如：新增/删除指标、修改聚合方式、修改违反判定规则），必须 **同步更新**：

- `extract_rq3_tables.py`
- 本 `README.md`

以保证论文结果可复现。
