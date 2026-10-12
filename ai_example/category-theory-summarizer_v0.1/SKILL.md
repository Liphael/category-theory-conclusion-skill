---
name: category-theory-summarizer
description: 把一批材料文件（PDF / DOCX / TXT / Markdown）按固定的五步范畴论模型做结构化总结——判断文本类型与形式化程度，抽取或重构范畴骨架（对象/态射/复合/恒等、函子、自然变换、极限与余极限、伴随、单子、Yoneda），严格区分「原文显式结构」与「合理重构」，不足处先检索补足、仍不足则标记为「信息缺失」对象，输出对象表、态射表、Mermaid 或文字交换图、范畴论重述 3–5 句、非范畴论通俗摘要，并基于输出从头迭代 3 次，每轮带真实时间戳落入 reports/。触发词：范畴论总结、范畴论取向、范畴化、对象表、态射表、交换图、category theory summary、categorical summary。不适用于：普通内容摘要、翻译、范畴论入门教学、数学证明推导、代码重构。
version: 1.0.0
---

# 范畴论取向的文本总结器

把一批材料文件变成一套**可复核的范畴论骨架报告**。核心不是「用范畴论术语重写一遍材料」，而是回答一个具体问题：**这份材料里，哪些结构是它自己说出来的，哪些是我替它补上的。**

## 何时用 / 何时不用

**用**：

- 用户给了一批材料（讲义、论文、教材、技术文档、规格说明），要求做范畴论取向的总结
- 用户明确要求输出对象表 / 态射表 / 交换图 / 范畴论重述
- 用户想看清一份材料的**结构骨架**，而不只是要点罗列

**不用**：

- 普通摘要、要点提取、读书笔记 → 直接做，不要套范畴论
- 翻译、润色 → 不要套
- 范畴论入门教学 → 那是教学任务，不是总结任务
- 数学证明 / 定理推导 → 本技能只做结构抽取，不做证明

## 输入 / 输出契约

**输入**

| 项 | 说明 |
| --- | --- |
| 材料目录 | 默认 `materials/`，可混放 `.pdf` `.docx` `.txt` `.md`（`.markdown` 同） |
| 模型提示文件（可选） | 如 `ModelPrompt.md`，给出自定义步骤；缺省用内置五步模型 |
| 迭代轮数（可选） | 默认 `3` 次迭代（即 1 基线 + 3 轮 = 4 份报告） |

**输出**（全部落在 `reports/`）

```
reports/
  00_INDEX.md                      # 索引 + 收敛结论速览（必产）
  R1_<YYYYMMDD-HHMMSS>.md          # 基线轮
  R2_<YYYYMMDD-HHMMSS>.md          # 迭代 1/N
  R3_<YYYYMMDD-HHMMSS>.md          # 迭代 2/N
  R4_<YYYYMMDD-HHMMSS>.md          # 迭代 3/N（收敛版，需可独立阅读）
```

每份报告**必须**包含：对象表、态射表、交换图、范畴论重述（3–5 句）、非范畴论通俗摘要、对象「信息缺失」。

## 执行流程

```
步骤 0  提取文本      scripts/extract_text.py     ← 四格式统一入口
步骤 1  判断文本类型与形式化程度
步骤 2  抽取 / 重构范畴骨架
步骤 3  区分「原文显式」与「合理重构」
步骤 4  不足则检索补足；仍不足 → 标记为「信息缺失」
步骤 5  输出五件套（对象表 / 态射表 / 交换图 / 重述 / 摘要）
步骤 6  从头迭代 N 次，每轮真实时间戳           ← 迭代不是打补丁
步骤 7  跑交付门禁  scripts/check_reports.py
步骤 8  写 00_INDEX.md，交付
```

### 步骤 0：提取（本技能相对旧流程的新增能力）

```bash
PY="C:/Users/14545/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
$PY <skill>/scripts/extract_text.py --input materials --out .workbuddy/tmp_text --min-chars 50
```

- 依赖：`pypdf`（PDF）、`python-docx`（DOCX）；已装在上方 venv
- 产出 `<out>/manifest.json`，逐文件记录 `chars / pages / tables / encoding / status / warnings`
- **退出码 1 = 有文件没提取出来，必须先处置再进步骤 1**。常见处置：扫描件 PDF 需 OCR；`.doc` 需另存为 `.docx`
- 格式细节与已知坑见 [`references/source-formats.md`](references/source-formats.md)

### 步骤 1–5：五步模型

见 [`references/model-steps.md`](references/model-steps.md)。骨架清单（哪些结构该找、应用类文本通常哪些显式哪些需重构）见 [`references/category-skeleton-guide.md`](references/category-skeleton-guide.md)。

### 步骤 6：迭代规则（最容易做错的一步）

- **从头重写**，不是在上一份上打补丁。每份报告都自足可读
- 每轮时间戳**必须真实**——用 `date "+%Y-%m-%d %H:%M:%S"` 取，不得复用或编造
- 每轮末尾写「本轮自评」，列出**已解决什么、还差什么、下一轮补什么**；下一轮按这份自评推进
- 收敛轮（最后一轮）须可独立阅读，并附**四轮演化记录**：哪些判断被修正了、为什么

### 步骤 7：门禁（交付前必跑）

```bash
$PY <skill>/scripts/check_reports.py --reports reports --rounds 4
```

- 断言：时间戳存在且互异递增、五个必备章节（按标题判定）、Mermaid 围栏配对、重述句数 3–5、表格数据行 ≥6、显式性/置信度标注 ≥4 处、`00_INDEX.md` 存在
- **退出码非 0 即禁止交付**，先修报告再重跑
- 门禁自身也有自测：改过 `check_reports.py` 后，必须按 [`reports/output-risk-profile.md`](reports/output-risk-profile.md)「自测如何复跑」一节把 GOOD / BAD 两组都重跑。只跑 GOOD 等于没验证

## 六条红线

1. **不静默丢弃**。任何文件没提取出来、任何结构找不到，必须写进报告（落到「信息缺失」表），不得略过。
2. **显式与重构必须分开**。每一条骨架结论都要标 `【显式】/【半显式】/【重构】`，并给置信度星级。这条做不到，整份报告失去价值。
3. **重述严格 3–5 句**。不是 2 句，也不是 8 句。
4. **时间戳真实**。用命令取。
5. **迭代是从头重写**。在上一轮上贴补丁不算迭代。
6. **先检索再认输**。步骤 4 判定「不足以构成范畴」时，必须先尝试检索补足；只有检索后仍不足，才标「信息缺失」并写明原因。

## 文件索引

| 文件 | 内容 |
| --- | --- |
| [`references/model-steps.md`](references/model-steps.md) | 五步模型逐步展开 + 每步判据 |
| [`references/category-skeleton-guide.md`](references/category-skeleton-guide.md) | 骨架抽取清单、显式/重构判据、常见单子与伴随对照表 |
| [`references/source-formats.md`](references/source-formats.md) | PDF/DOCX/TXT/MD 四种格式要点、编码、已知坑 |
| [`references/report-template.md`](references/report-template.md) | 报告模板、Mermaid 书写规范、置信度标注规范 |
| [`scripts/extract_text.py`](scripts/extract_text.py) | 四格式统一提取器（步骤 0） |
| [`scripts/check_reports.py`](scripts/check_reports.py) | 报告交付门禁（步骤 7） |
| `scripts/_make_fixtures.py`、`_make_sample_reports.py`、`_validate_pkg.py` | 开发期自测脚本（下划线前缀=不参与技能运行），用法见风险画像「自测如何复跑」 |
| [`reports/output-risk-profile.md`](reports/output-risk-profile.md) | 输出风险画像、门禁阈值、自测复跑命令 |
| [`reports/artifact-design-profile.md`](reports/artifact-design-profile.md) | 报告产物设计画像（排版方向、非协商项） |
| [`reports/prompt-quality-profile.md`](reports/prompt-quality-profile.md) | 提示质量画像（需求模型、RTF 映射、质量矩阵） |
| [`evals/route-holdout.md`](evals/route-holdout.md) | 路由留出测试（12 应命中 / 10 不应命中） |
| [`agents/interface.yaml`](agents/interface.yaml) | 中性接口元数据（输入格式、产物、门禁） |
| [`manifest.json`](manifest.json) | 生命周期元数据与已知缺口 |

## 环境

Python venv：`C:\Users\14545\.workbuddy\binaries\python\envs\default`
已装：`pypdf`、`python-docx`（`reportlab` 仅自测夹具用）。

## 下一步迭代方向（按价值排序）

1. 给 `check_reports.py` 增「跨轮一致性」断言：后一轮不得静默丢弃前一轮已识别的结构
2. 沉淀领域骨架库：统计推断、机器学习、编译原理、并发系统各自的常见骨架模板
3. 支持扫描件 PDF 的 OCR 兜底路径，把「需 OCR」从阻断降级为可选旁路
  