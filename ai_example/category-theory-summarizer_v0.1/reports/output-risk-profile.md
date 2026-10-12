# 输出风险画像（Output Risk Profile）

> yao-meta-skill Phase 5.5。预测本技能最终产物最容易出的错，并给出可复跑的门禁阈值。
> 阈值与 `scripts/check_reports.py` 的实现一一对应。

## 产物类型

- **主产物**：`reports/` 下 N 份 Markdown 分析报告（含表格、Mermaid 图、公式）
- **副产物**：`00_INDEX.md` 索引
- **中间产物**：`.workbuddy/tmp_text/` 提取文本、`manifest.json`

## 六类高风险缺陷

| # | 风险 | 典型表现 | 硬判据（门禁项） | 阈值 |
| --- | --- | --- | --- | --- |
| R1 | **显式/重构混淆**（本技能最严重的缺陷） | 全部条目不标注来源，读者无法判断哪句是材料说的 | 全文 `【显式/半显式/重构】` 或「置信度/★」出现次数 | ≥4 处 |
| R2 | **章节缺失** | 做完骨架却忘了通俗摘要或信息缺失 | 必备章节按**标题**判定 | 5 项全在 |
| R3 | **重述句数失控** | 写 2 句凑数，或写成 8 句小作文 | 编号句子计数 | 3–5 句 |
| R4 | **表格空壳** | 表头在、数据行只有 1–2 行 | Markdown 表格数据行计数 | ≥6 行 |
| R5 | **时间戳造假/复用** | 四轮同一个时间戳，或凭印象写 | 正则提取 + 互异 + 递增 | N 个且严格递增 |
| R6 | **Mermaid 围栏不配对** | 图渲染失败，整块变纯文本 | ` ``` ` 计数奇偶 | 偶数 |
| R7 | **材料静默丢失** | 有文件没提取出来却继续往下做 | `extract_text.py` 退出码 | 必须为 0 |
| R8 | **交换图缺失或空壳** | 只有「## 交换图」标题，正文一句「暂略」；或正文写「无交换图」但别处有箭头被误判为有图 | Mermaid 块 ≥1，**或**「交换图」章节正文含箭头 | 二者至少满足其一 |

## 门禁阈值（可复跑）

```bash
PY="C:/Users/14545/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
$PY scripts/extract_text.py  --input materials --out .workbuddy/tmp_text     # 期望 EXIT=0
$PY scripts/check_reports.py --reports reports --rounds 4                     # 期望 EXIT=0
```

`check_reports.py` 每份报告跑 6 条断言 + 2 条全局断言（份数、INDEX 存在），4 份报告共 **26 条**。

## 自身已修的四处假阴性（勿回退）

四处都是同一类错误：**检查代码自己在说谎**。把它们记在这里，是因为它们全都「看起来在检查、实际放行了」。

1. **空页 PDF 判为有内容**（`extract_text.py`）：注入的页眉标记字符数被计入 `chars`。已改为只统计 `body_chars`。
2. **章节检查用全文子串**（`check_reports.py`）：报告正文里写一句「缺通俗摘要」，也会被判成已具备该章节。已改为按 Markdown 标题判定。
3. **交换图检查用全文子串**（`check_reports.py`）：判据原为 `"交换图" in text and "→" in text`。样例报告正文写「本样例无交换图」、而态射表里有 `S → ℝ`，于是被判成「已有交换图」。已改为：先定位「交换图」章节标题，只在该章节正文里找箭头；Mermaid 块则不受章节限制。

4. **包校验器的路由解析静默失效**（`_validate_pkg.py`）：正则漏了 `re.M`，22 条用例解析出 0 条，却照常打印「无问题」。已加守卫：**解析条数为 0 必须记为问题**，不得以「没解析到」冒充「没问题」。

> 新增任何检查项时，必须配一个**反向用例**证明它真的会拦截。第 3 处对应的反向用例是 `tricky/`（五件套标题齐全、只有交换图是空壳），期望门禁**只**报「缺少交换图」一条。
> 另有一条通则：**任何检查器解析不到输入时，必须报错，不得报通过**。第 4 处就栽在这里。

## 门禁未覆盖、需人工复核的项

| 项 | 为什么门禁判不了 | 人工怎么查 |
| --- | --- | --- |
| 通俗摘要里是否混入范畴术语 | 语义判断 | 搜「范畴 / 态射 / 函子 / 单子 / 伴随 / 极限 / Yoneda」，应为 0 命中 |
| 出处页码是否真实 | 需对照原文 | 抽查 3 条，翻到对应页 |
| 伴随层级是否标注 | 需语义判断 | 每条伴随后应有 `Cat` / `Pos` / dagger / 类比 之一 |
| 迭代是否为「从头重写」而非打补丁 | 需比对全文 | 收敛轮应能独立阅读，且含「四轮演化记录」 |
| 重构的依赖是否披露 | 需语义判断 | 收敛轮应有「可证伪性分析」表，★★★☆☆ 及以下条目须在其中出现 |

## 自测如何复跑

包内只留**夹具生成脚本**（`scripts/_make_*.py`，下划线前缀表示开发期专用），不留生成产物。复跑：

```bash
PY="C:/Users/14545/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
SK="C:/Users/14545/.workbuddy/skills/category-theory-summarizer"

# 1) 生成 7 个格式夹具（含 1 个 .doc 不支持、1 个空文本层 PDF）
$PY $SK/scripts/_make_fixtures.py --out .selftest/fixtures

# 2) 提取器：期望 EXIT=1（legacy.doc 不支持 + scanned_no_text.pdf 空）
$PY $SK/scripts/extract_text.py --input .selftest/fixtures --out .selftest/out_all
echo "EXIT=$?"   # 期望 1

# 3) 只喂 5 个正常夹具：期望 EXIT=0
$PY $SK/scripts/_make_fixtures.py --out .selftest/fixtures4 --skip-bad
$PY $SK/scripts/extract_text.py --input .selftest/fixtures4 --out .selftest/out_ok
echo "EXIT=$?"   # 期望 0

# 4) 生成三套样例报告，跑门禁
$PY $SK/scripts/_make_sample_reports.py --out .selftest/reports
$PY $SK/scripts/check_reports.py --reports .selftest/reports/good --rounds 4
echo "EXIT=$?"   # 期望 0（26 条断言全过）
$PY $SK/scripts/check_reports.py --reports .selftest/reports/bad --rounds 4
echo "EXIT=$?"   # 期望 1（拦下 8 条问题）
$PY $SK/scripts/check_reports.py --reports .selftest/reports/tricky --rounds 1
echo "EXIT=$?"   # 期望 1，且只报「缺少交换图」1 条

# 5) 整包结构校验：frontmatter / manifest / interface.yaml / 站内链接是否有死链
$PY $SK/scripts/_validate_pkg.py
echo "EXIT=$?"   # 期望 0
```

**零回归基线（三组都必须跑，缺一不可）**：

| 组 | 期望 | 它守住的是什么 |
| --- | --- | --- |
| `good/` | EXIT=0，26/26 通过 | 不误杀合规报告（防假阳性） |
| `bad/` | EXIT=1，8 条问题 | 能拦下明显残次报告（防假阴性） |
| `tricky/` | EXIT=1，**只** 1 条「缺少交换图」 | 能识破「标题齐全但内容空壳」（防假阴性，最易漏的一类） |

任何对 `check_reports.py` 的修改，改完必须三组都重跑。**只跑 GOOD 等于没验证**——GOOD 全过而 BAD/TRICKY 也全过，正是假阴性的典型症状。

## 已知局限（量化披露）

- 门禁当前**不做跨轮一致性检查**：后一轮静默丢弃前一轮已识别的结构，门禁判不出来。已列为第一优先迭代方向。
- 门禁的「表格数据行 ≥6」是粗判据：无法区分行数达标但内容注水。人工复核时需确认对象表 ≥8 行、态射表 ≥12 行。
- 编码落到 `latin-1` 时内容可能已乱码，门禁不拦截，需在步骤 0 看 manifest 的 `encoding` 字段人工确认。
