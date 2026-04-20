# AI 运营助手实验室（ai-ops-assistant-lab）

面向游戏运营场景的 **Python + Camel-AI + OWL 编排 + Doris（可 Mock）** 实验工程，演示从自然语言到分析报告的数据链路。

## 仓库布局

| 目录 | 说明 |
|------|------|
| `ai-ops-assistant-v1/` | MVP：Query → SQL（Mock）→ Analysis → Report |
| `ai-ops-assistant-v2/` | Doris + SQL 三阶段 Planner/Optimizer + Schema |
| `ai-ops-assistant-v3/` | **语义层 + 指标驱动**（Metric → Planner → SQL Compiler → Doris） |

各版本自带 `requirements.txt`、`main.py`、`.env.example`。建议 **Python 3.10+**。

## 快速运行（以 V1 为例）

```bash
cd ai-ops-assistant-v1
pip install -r requirements.txt
python main.py "最近7天用户流失情况如何？"
python main.py --json
```

未配置 `OPENAI_API_KEY` 时使用 **Mock Agent**，仅依赖内置 Mock 数据即可跑通闭环。

## Mock 数据（V1）

V1 的 `mock_data/` 提供 **`game_daily_metrics`** 与 **`order_daily_summary`**：当前各 **14 个交易日**（`2026-04-07`～`2026-04-20`），日期区间对齐，可用于「最近 7 天」「最近 14 天」等问法校验。

模块内 **`DATASET_META`** 汇总行数与首尾日期；并可用自检脚本：

```bash
cd ai-ops-assistant-v1
python -m mock_data.verify
```

## 环境与密钥

复制各版本目录下的 `.env.example` 为 `.env`，按需填写 Doris / OpenAI。**切勿将 `.env` 提交到 Git**（已在根目录 `.gitignore` 中忽略）。

## 开源许可

本项目采用 **MIT License**，见根目录 [`LICENSE`](./LICENSE)。

## Git

在本目录（仓库根）执行一次初始化并提交即可：

```bash
cd /path/to/ai-ops-assistant-lab
git init
git add .gitignore README.md LICENSE ai-ops-assistant-v1 ai-ops-assistant-v2 ai-ops-assistant-v3
git commit -m "chore: initial commit"
```

如需忽略本地 IDE 目录等，已由根目录 `.gitignore` 覆盖；勿提交 `.env`。
