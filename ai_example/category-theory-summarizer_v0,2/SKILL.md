---
name: category-theory-summarizer
description: 把一批材料文件（PDF / DOCX / PPTX / XLSX / TXT / Markdown，经 MarkItDown 统一转为 .md）按固定的五步范畴论模型做结构化总结——判断文本类型与形式化程度，抽取或重构范畴骨架（对象/态射/复合/恒等、函子、自然变换、极限与余极限、伴随、单子、Yoneda），严格区分「原文显式结构」与「合理重构」，不足处先检索补足、仍不足则标记为「信息缺失」对象，输出对象表、态射表、范畴论交换图（节点命名以骨架表为准：基范畴/对象/态射/极限与余极限/伴随/自然变换/单子与代数）及其通俗化翻译图、范畴论重述 3–5 句、非范畴论通俗摘要，并基于输出从头迭代 3 次；源文件与转换后文件分别归档，报告只带轮次戳，本次全部输出归入以时间戳命名的运行目录。触发词：范畴论总结、范畴论取向、范畴化、对象表、态射表、交换图、翻译图、基范畴、极限与余极限、伴随、自然变换、单子与代数、轮次戳、MarkItDown、category theory summary、categorical summary。不适用于：普通内容摘要、翻译、范畴论入门教学、数学证明推导、代码重构。
version: 2.1.0
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
| 材料目录 | 默认 `materials/`。`.pdf` `.docx` `.pptx` `.xlsx` 等由 MarkItDown 转换；`.md` `.markdown` `.txt` 直接沿用 |
| 模型提示文件（可选） | 如 `ModelPrompt.md`，给出自定义步骤；缺省用内置五步模型 |
| 迭代轮数（可选） | 进行 `N` 次迭代（即 1 基线 + N 轮 = N+1 份报告）, `N` 值默认为 3 |

**输出**（本次运行的**全部**产物归入一个以时间戳命名的运行目录）

```
runs/
  20261012-142200/                  # 运行目录，目录名即本次运行时间戳
    00_source/                      # .md源文件副本，只复制不改动
    01_reports/
      00_INDEX.md                   # 索引 + 收敛结论速览（必产）
      R1.md                         # 基线轮（轮次戳，不带时间戳）
      R2.md                         # 迭代 1/3
      R3.md                         # 迭代 2/3
      R4.md                         # 迭代 3/3（收敛版，需可独立阅读）
    manifest_conversion.json        # 逐文件转换台账
```

每份报告**必须**包含：对象表、态射表、交换图（原图 + 通俗化翻译图）、范畴论重述（3–5 句）、非范畴论通俗摘要、对象「信息缺失」。

## 执行流程

```
步骤 0  统一转 .md 并双归档   scripts/convert_markdown.py   ← MarkItDown
步骤 1  文本提取与空内容校验   scripts/extract_text.py       ← 输入 01_markdown/
步骤 2  判断文本类型与形式化程度
步骤 3  抽取 / 重构范畴骨架
步骤 4  区分「原文显式」与「合理重构」
步骤 5  不足则检索补足；仍不足 → 标记为「信息缺失」
步骤 6  输出五件套；每张范畴论原图后追加通俗化翻译图
步骤 7  从头迭代 N 次，只留轮次戳            ← 迭代不是打补丁
步骤 8  跑交付门禁  scripts/check_reports.py --run-dir <运行目录>
步骤 9  写 00_INDEX.md，交付
```

### 步骤 0：统一转 .md 并双归档

```bash
PY="C:/Users/14545/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
$PY <skill>/scripts/convert_markdown.py --input materials --archive runs
```

- 依赖 `markitdown`（已装在下方 venv）。`.md` `.markdown` `.txt` 直接复制为 `.md`，其余格式调 CLI 转换
- `00_source/` 与 `01_markdown/` 严格分开：前者是源文件副本（绝不改动），后者是后续唯一输入
- 产出 `manifest_conversion.json`，逐文件记录 `converter / chars / status / warnings`
- **退出码 1 = 有文件没转出来，必须先处置再进步骤 1**。常见处置：扫描件 PDF 需 OCR；`.doc` 需另存为 `.docx`
- 结尾会打印 `[RUN_DIR] <绝对路径>`，后续步骤都以它为准
- 格式细节与已知坑见 [`references/source-formats.md`](references/source-formats.md)

### 步骤 1：文本提取与空内容校验

```bash
$PY <skill>/scripts/extract_text.py --input <RUN_DIR>/01_markdown --out <RUN_DIR>/03_text --min-chars 50
```

- 输入已是 `.md`，本步主要做**编码探测 + 空内容拦截**，并产出合并文本与 `manifest.json`
- 若 MarkItDown 不可用，退化路径：`extract_text.py --input materials`（直读 PDF/DOCX/TXT/MD 四种格式）

### 步骤 2–6：五步模型

见 [`references/model-steps.md`](references/model-steps.md)。骨架清单（哪些结构该找、应用类文本通常哪些显式哪些需重构）见 [`references/category-skeleton-guide.md`](references/category-skeleton-guide.md)。

### 图的规矩（两条，都进门禁）

1. **节点命名以骨架表为准**。骨架表包括**基范畴、函子、对象表、态射表、极限与余极限、伴随、自然变换、单子与代数**；原图的节点/箭头名必须能在其中找到，不得自造。判据只有一条：名字必须是骨架表里出现过的、**不含中文**的记号（`Θ`、`m`、`F ⊣ G`、`η`、`μ`、`Kl(P)` 都算）。骨架表里一个记号都没有时，门禁报「无法校验」而不是放行。
2. **图必须成对**。每张范畴论原图之后，必须紧接一张**通俗化翻译图**——图结构不变，节点/箭头名换成用户领域里的说法（如 `Θ` → 「参数真值」、`m` → 「抽样模型」）。两者都必须是**真的 Mermaid 代码块**，写在带类型标注的 `###` 子标题下（含「原图」/「翻译图」字样）。三种典型失败：只有原图；翻译图只是把原图抄了一遍；或是全篇压根没有图，靠正文里的箭头和对「翻译」二字的提及蒙混。

写法规范见 [`references/report-template.md`](references/report-template.md)。把记号放在骨架表**第一列**是推荐写法（便于阅读），但不是判定依据：记号落在第二列同样有效。含中文的单元格一律不入词表——中文名若进词表，翻译图用它们就会被误判成未翻译。

### 步骤 7：迭代规则（最容易做错的一步）

- **从头重写**，不是在上一份上打补丁。每份报告都自足可读
- **只写轮次戳**：文件名为 `R1.md`…`R4.md`，报告头写 `- **轮次**：R1`。**每轮不再写时间戳**，时间信息统一落在运行目录名与 `00_INDEX.md`
- 每轮末尾写「本轮自评」，列出**已解决什么、还差什么、下一轮补什么**；下一轮按这份自评推进
- 收敛轮（最后一轮）须可独立阅读，并附**四轮演化记录**：哪些判断被修正了、为什么

### 步骤 8：门禁（交付前必跑）

```bash
$PY <skill>/scripts/check_reports.py --run-dir runs/20261012-142200 --rounds 4
```

- 断言：轮次戳（文件名与报告头一致、编号连续）、运行目录名是时间戳、报告内无残留时间戳字段、五个必备章节（按标题判定）、Mermaid 围栏配对、**每张原图后有翻译图**、**原图节点名见于骨架表**（基范畴/函子/对象/态射/极限与余极限/伴随/自然变换/单子与代数，取不含中文的记号）、重述句数 3–5、表格数据行 ≥6、显式性/置信度标注 ≥4 处、`00_INDEX.md` 存在
- **退出码非 0 即禁止交付**，先修报告再重跑
- 门禁自身也有自测：改过 `check_reports.py` 后，必须按 [`reports/output-risk-profile.md`](reports/output-risk-profile.md)「自测如何复跑」一节把 GOOD / BAD 与**五个** tricky 用例、运行目录正负用例共九组都重跑，再跑 `_probe_diagrams.py` 的十五条对抗性探测。只跑 GOOD 等于没验证
- 九组是**基线**，十五条探测是**攻击**：其中八条期望 EXIT=0，专门证明收紧检查没有换来误杀。反向用例全红也可能是因为检查器把什么都判成不合格；判断一条新用例是不是摆设，看它在 `scripts/_make_control_impls.py` 生成的对照实现下会不会红

## 九条红线

1. **不静默丢弃**。任何文件没转出来、任何结构找不到，必须写进报告（落到「信息缺失」表），不得略过。
2. **显式与重构必须分开**。每一条骨架结论都要标 `【显式】/【半显式】/【重构】`，并给置信度星级。这条做不到，整份报告失去价值。
3. **重述严格 3–5 句**。不是 2 句，也不是 8 句。
4. **轮次戳取代每轮时间戳**。报告内不得再出现 `- **时间戳**` 字段；时间信息只在运行目录名与 `00_INDEX.md`。
5. **源文件与转换文件分开归档**。`00_source/` 只复制不改动，`01_markdown/` 才是输入，两者不得混写。
6. **节点命名以骨架表为准**。原图的节点/箭头名必须来自骨架表——**基范畴、函子、对象表、态射表、极限与余极限、伴随、自然变换、单子与代数**——中**不含中文的记号**，不得自造。中文名不得进词表，否则翻译图会被误判成未翻译。
7. **图必须成对**。每张范畴论原图后必须有通俗化翻译图，两者都得是真的 Mermaid 代码块，且翻译图要真的换成领域说法，不是复制原图。对照表不能顶替翻译图。
8. **迭代是从头重写**。在上一轮上贴补丁不算迭代。
9. **先检索再认输**。步骤 5 判定「不足以构成范畴」时，必须先尝试检索补足；只有检索后仍不足，才标「信息缺失」并写明原因。

## 文件索引

| 文件 | 内容 |
| --- | --- |
| [`references/model-steps.md`](references/model-steps.md) | 五步模型逐步展开 + 每步判据 |
| [`references/category-skeleton-guide.md`](references/category-skeleton-guide.md) | 骨架抽取清单、显式/重构判据、常见单子与伴随对照表 |
| [`references/source-formats.md`](references/source-formats.md) | MarkItDown 转换、各格式要点、编码、已知坑、归档结构 |
| [`references/report-template.md`](references/report-template.md) | 报告模板、原图+翻译图写法、Mermaid 规范、置信度标注规范 |
| [`scripts/convert_markdown.py`](scripts/convert_markdown.py) | MarkItDown 统一转换与双归档（步骤 0） |
| [`scripts/extract_text.py`](scripts/extract_text.py) | 文本提取与空内容校验（步骤 1；MarkItDown 不可用时的退化路径） |
| [`scripts/check_reports.py`](scripts/check_reports.py) | 报告交付门禁（步骤 8） |
| `scripts/_make_fixtures.py`、`_make_sample_reports.py`、`_validate_pkg.py` | 开发期自测脚本（下划线前缀=不参与技能运行），用法见风险画像「自测如何复跑」 |
| [`scripts/_probe_diagrams.py`](scripts/_probe_diagrams.py) | 十五条对抗性探测（含八条不得误杀用例），改门禁后必跑 |
| [`scripts/_make_control_impls.py`](scripts/_make_control_impls.py) | 生成对照实现，用来证明探测用例不是摆设 |
| [`reports/output-risk-profile.md`](reports/output-risk-profile.md) | 输出风险画像、门禁阈值、自测复跑命令 |
| [`reports/artifact-design-profile.md`](reports/artifact-design-profile.md) | 报告产物设计画像（排版方向、非协商项） |
| [`reports/prompt-quality-profile.md`](reports/prompt-quality-profile.md) | 提示质量画像（需求模型、RTF 映射、质量矩阵） |
| [`evals/route-holdout.md`](evals/route-holdout.md) | 路由留出测试（12 应命中 / 10 不应命中） |
| [`agents/interface.yaml`](agents/interface.yaml) | 中性接口元数据（输入格式、产物、门禁） |
| [`manifest.json`](manifest.json) | 生命周期元数据与已知缺口 |

## 环境

Python venv：`C:\Users\14545\.workbuddy\binaries\python\envs\default`
已装：`markitdown[pdf,docx,pptx,xlsx]`、`pypdf`、`python-docx`（`reportlab` 仅自测夹具用）。

缺 markitdown 时步骤 0 会直接报错并给出安装命令，不会静默走退化路径。

## 下一步迭代方向（按价值排序）

1. 给 `check_reports.py` 增「跨轮一致性」断言：后一轮不得静默丢弃前一轮已识别的结构
2. 翻译图目前只检查「确实换了词」，未检查「换得对不对」。下一步可要求翻译图附对照表，并断言对照表行数与骨架条目数一致
3. 支持扫描件 PDF 的 OCR 兜底路径，把「需 OCR」从阻断降级为可选旁路
