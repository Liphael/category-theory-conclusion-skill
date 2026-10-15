# 输出风险画像（Output Risk Profile）

> yao-meta-skill Phase 5.5。预测本技能最终产物最容易出的错，并给出可复跑的门禁阈值。
> 阈值与 `scripts/check_reports.py`、`scripts/convert_markdown.py` 的实现一一对应。
> v2 更新：MarkItDown 转换与双归档、轮次戳取代每轮时间戳、图必须成对、节点命名以骨架表为准。

## 产物类型

- **主产物**：`runs/<时间戳>/02_reports/` 下 N 份 Markdown 分析报告（含表格、Mermaid 原图+翻译图、公式）
- **副产物**：`00_INDEX.md` 索引、`manifest_conversion.json` 转换台账
- **归档产物**：`00_source/`（源文件副本）、`01_markdown/`（统一 .md）
- **中间产物**：提取文本与 `manifest.json`

## 高风险缺陷清单

| # | 风险 | 典型表现 | 硬判据（门禁项） | 阈值 |
| --- | --- | --- | --- | --- |
| R1 | **显式/重构混淆**（本技能最严重的缺陷） | 全部条目不标注来源，读者无法判断哪句是材料说的 | 全文 `【显式/半显式/重构】` 或「置信度/★」出现次数 | ≥4 处 |
| R2 | **章节缺失** | 做完骨架却忘了通俗摘要或信息缺失 | 必备章节按**标题**判定 | 5 项全在 |
| R3 | **重述句数失控** | 写 2 句凑数，或写成 8 句小作文 | 编号句子计数 | 3–5 句 |
| R4 | **表格空壳** | 表头在、数据行只有 1–2 行 | Markdown 表格数据行计数 | ≥6 行 |
| R5 | **轮次戳缺失或不一致** | 还带每轮时间戳，或文件名 R2 而报告头写 R1 | 文件名 `R<n>.md` + 报告头 `轮次：R<n>` 一致 | 两者一致且编号连续 |
| R6 | **Mermaid 围栏不配对** | 图渲染失败，整块变纯文本 | ` ``` ` 计数奇偶 | 偶数 |
| R7 | **材料静默丢失** | 有文件没转出来却继续往下做 | `convert_markdown.py` 退出码 | 必须为 0 |
| R8 | **无图 / 图是空壳** | 只有「## 交换图」标题，正文一句「暂略」；或全篇没有一个 Mermaid 图 | 章内 Mermaid 代码块数 | ≥1 组（原图+翻译图各一） |
| R9 | **缺通俗化翻译图** | 只给范畴论原图；或用一张「翻译对照表」顶替翻译图 | 图块按子标题判定类型，原图与翻译图须交替出现且数量相等 | 每张原图配一张**图** |
| R10 | **翻译图是抄的** | 翻译图节点名与原图完全相同，或仍全出自骨架表 | 翻译图标签集合是否仍 ⊆ 骨架表、与原图标签重合是否过半 | 两者都为否 |
| R11 | **节点命名脱离骨架表** | 图上出现表里没有的自造节点名 | 原图标签逐个与全部骨架表比对（基范畴/函子/对象/态射/极限与余极限/伴随/自然变换/单子与代数，取不含中文的记号） | 未命中数 = 0 |
| R14 | **骨架表无记号，命名检查被架空** | 表里全写成中文，一个可引用的记号都没有 | 词表为空且有原图 | 必须报错「无法校验」，不得放行 |
| R12 | **运行目录名不是时间戳** | 归档目录随便起名，事后无法回答「这批什么时候跑的」 | 目录名正则 `\d{8}-\d{6}` | 必须匹配 |
| R13 | **报告内残留每轮时间戳** | 仍写 `- **时间戳**：...` | 行首匹配 `- **时间戳**` | 0 处 |

## 门禁阈值（可复跑）

```bash
PY="C:/Users/14545/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
$PY scripts/convert_markdown.py --input materials --archive runs   # 期望 EXIT=0
$PY scripts/extract_text.py --input <RUN_DIR>/01_markdown --out <RUN_DIR>/03_text   # 期望 EXIT=0
$PY scripts/check_reports.py --run-dir <RUN_DIR> --rounds 4        # 期望 EXIT=0
```

`check_reports.py` 每份报告跑 8 条断言 + 全局断言（轮次份数与连续性、运行目录名、INDEX 存在），
4 份报告共 **34 条**。

## 自身已修的七处假阴性（勿回退）

七处都是同一类错误：**检查代码自己在说谎**。把它们记在这里，是因为它们全都「看起来在检查、实际放行了」。

1. **空页 PDF 判为有内容**（`extract_text.py`）：注入的页眉标记字符数被计入 `chars`。已改为只统计 `body_chars`。
2. **章节检查用全文子串**（`check_reports.py`）：正文写一句「缺通俗摘要」也被判成已具备该章节。已改为按 Markdown 标题判定。
3. **交换图检查用全文子串**（`check_reports.py`）：正文写「无交换图」而态射表有 `S → ℝ` 就被判成有图。已改为先定位章节标题、只在该章节正文找箭头。
4. **包校验器的路由解析静默失效**（`_validate_pkg.py`）：正则漏 `re.M`，22 条用例解析出 0 条却打印「无问题」。已加守卫：解析条数为 0 必须记为问题。
5. **章节区间在第一个子标题处截断**（`check_reports.py`）：「## 3. 交换图」下有「### 3.1 原图」，早期区间结束于下一个**任意**标题，父章节被判为空壳，原图与翻译图都看不到。已改为区间结束于**下一个同级或更高级标题**，子标题包含在父章节内。
6. **轮次戳正则未跳过加粗标记**（`check_reports.py`）：报告头写 `**轮次**：R1`，正则却在 `轮次` 后直接找冒号，漏掉 `**`，导致合规报告被判「缺少轮次字段」。已改为 `轮次\s*\**\s*[：:]`。
7. **图的存在靠正文关键词判定**（`check_reports.py`）：判据是「正文含 →」算有原图、「出现『翻译』二字且有一张任意 ≥2 行表」算有翻译图。于是**一份通篇没有一个 Mermaid 图的报告**被判通过，输出还显示「图(译/原)=1/1」。已改为：图只看 Mermaid 代码块，且每个块按所在子标题判定原图/翻译图类型，两者必须交替出现、数量相等；对照表不再顶替翻译图。反向用例 `tricky__prose_only_diagram` 守这条。

> 第 7 处是本次加固中最严重的一处：它让「必须出图」和「必须出翻译图」两条要求同时失效。
> 它的形态与前六处完全一致——**用容易匹配的代理信号（关键词）代替了应检查的真实对象（代码块结构）**。新增检查项时先问：我要检查的那个东西，代码里到底有没有真的去读它？

> 新增任何检查项时，必须配一个**反向用例**证明它真的会拦截。
> 通则一：任何检查器解析不到输入时，必须报错，不得报通过（第 4 处就栽在这里）。
> 通则二：先跑 GOOD 再跑反向用例。GOOD 先失败说明检查写错了，反向用例全红说明检查没生效。
> 通则三：反向用例全红也可能是因为**检查器把什么都判成不合格**。要区分「拦住了」和「全拒了」，
> 必须同时配期望通过的用例（本文件的探测里标了「不得误杀」的几条就是干这个的）。

## 自身已修的假阳性（勿回退）

假阴性是漏放，假阳性是冤枉。冤枉同样致命：它会诱使使用者绕过门禁、或改报告去迎合检查器。

1. **高阶结构的记号被当成自造节点名**（`check_reports.py`）
   词表原先只取对象表与态射表的第一列，于是画伴随图（`F ⊣ G`）、单子图（`η`/`μ`/`δ`）、
   基范畴图（`Kl(P)`）全被判成「节点/箭头名未见于骨架表」——骨架明明写了，是检查器没去读。
   已按用户要求把词表来源扩到**基范畴、函子、对象、态射、极限与余极限、伴随、自然变换、单子与代数**。
   取词规则收敛为一条：**表中不含中文的单元格**。理由见下条。

2. **（若按「无条件纳入第一列」实现会引入的假阳性）**
   扩到全骨架表时最容易顺手写成「第一列 + 不含中文的单元格」。但极限表常写成
   「材料的说法 | 范畴结构 |」，第一列是中文；中文名一旦进词表，翻译图用「拉回」
   这类词就会被判「未做通俗化」——这正是上一轮刚修掉的假阴性/假阳性同源问题。
   实测：`probe__translation_cjk_from_limit_col1` 在「无条件纳入第一列」的实现下 **EXIT=1**，
   在现行实现下 **EXIT=0**。改这条规则前先跑它。

> 两条合起来的教训：词表**范围**和词表**取法**是两个独立问题，都要单独设用例。
> 只测「能不能查到新表」（范围），不测「中文名有没有混进来」（取法），就会修好一个假阳性、换来另一个。

## 门禁未覆盖、需人工复核的项

| 项 | 为什么门禁判不了 | 人工怎么查 |
| --- | --- | --- |
| 翻译图换的词**对不对** | 只能判「确实换了」，判不了「换得准」 | 逐个对照：译名是否是材料自己的说法；保留范畴符号即视为未翻译 |
| 通俗摘要里是否混入范畴术语 | 语义判断 | 搜「范畴 / 态射 / 函子 / 单子 / 伴随 / 极限 / Yoneda」，应为 0 命中 |
| 出处页码是否真实 | 需对照原文 | 抽查 3 条，翻到对应页 |
| 伴随层级是否标注 | 需语义判断 | 每条伴随后应有 `Cat` / `Pos` / dagger / 类比 之一 |
| 迭代是否为「从头重写」而非打补丁 | 需比对全文 | 收敛轮应能独立阅读，且含「四轮演化记录」 |
| 重构的依赖是否披露 | 需语义判断 | 收敛轮应有「可证伪性分析」表，★★★☆☆ 及以下条目须在其中出现 |
| 转换是否丢内容 | 门禁只查空产物，查不出「转出来了但少了一段」 | 抽样比对 `00_source/` 与 `01_markdown/` 的段落数 |

## 自测如何复跑

包内只留**夹具生成脚本**（`scripts/_make_*.py`，下划线前缀表示开发期专用），不留生成产物。复跑：

```bash
PY="C:/Users/14545/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
SK="C:/Users/14545/.workbuddy/skills/category-theory-summarizer"

# 1) 生成 7 个格式夹具（含 1 个 .doc 不支持、1 个无文本层 PDF）
$PY $SK/scripts/_make_fixtures.py --out .selftest/fixtures

# 2) 转换+双归档（含异常夹具）：期望 EXIT=1
$PY $SK/scripts/convert_markdown.py --input .selftest/fixtures --archive .selftest/runs
echo "EXIT=$?"   # 期望 1

# 3) 只喂 5 个正常夹具：期望 EXIT=0
$PY $SK/scripts/_make_fixtures.py --out .selftest/fixtures4 --skip-bad
$PY $SK/scripts/convert_markdown.py --input .selftest/fixtures4 --archive .selftest/runs
echo "EXIT=$?"   # 期望 0

# 4) 提取器（输入已是 .md，主要做空内容拦截）：期望 EXIT=0
$PY $SK/scripts/extract_text.py --input .selftest/runs/<RUN_ID>/01_markdown --out .selftest/text
echo "EXIT=$?"   # 期望 0

# 5) 生成样例报告，跑门禁五组
$PY $SK/scripts/_make_sample_reports.py --out .selftest/reports
$PY $SK/scripts/check_reports.py --reports .selftest/reports/good --rounds 4
echo "EXIT=$?"   # 期望 0（34 条断言全过）
$PY $SK/scripts/check_reports.py --reports .selftest/reports/bad --rounds 1
echo "EXIT=$?"   # 期望 1（多条缺陷）
$PY $SK/scripts/check_reports.py --reports .selftest/reports/tricky__empty_diagram --rounds 1
echo "EXIT=$?"   # 期望 1，只报「章内没有图」1 条
$PY $SK/scripts/check_reports.py --reports .selftest/reports/tricky__no_translation --rounds 1
echo "EXIT=$?"   # 期望 1，只报「缺少通俗化翻译图」1 条
$PY $SK/scripts/check_reports.py --reports .selftest/reports/tricky__node_not_in_table --rounds 1
echo "EXIT=$?"   # 期望 1，只报节点命名 1 条
$PY $SK/scripts/check_reports.py --reports .selftest/reports/tricky__translation_is_copy --rounds 1
echo "EXIT=$?"   # 期望 1，只报「未做通俗化」1 条
$PY $SK/scripts/check_reports.py --reports .selftest/reports/tricky__prose_only_diagram --rounds 1
echo "EXIT=$?"   # 期望 1，只报「没有任何 Mermaid 图」1 条

# 6) 运行目录名正向/负向
$PY $SK/scripts/check_reports.py --run-dir .selftest/reports/runs/20261012-120000 --rounds 4
echo "EXIT=$?"   # 期望 0
$PY $SK/scripts/check_reports.py --run-dir .selftest/reports/runs/not-a-timestamp --rounds 4
echo "EXIT=$?"   # 期望 1，只报目录名不是时间戳

# 7) 十五条对抗性探测（含八条不得误杀用例）：期望 EXIT=0
$PY $SK/scripts/_probe_diagrams.py --out .selftest/probe
echo "EXIT=$?"   # 期望 0 = 十五条全部符合预期

# 8) 整包结构校验：frontmatter / manifest / interface.yaml / 站内链接 / 路由覆盖率
$PY $SK/scripts/_validate_pkg.py
echo "EXIT=$?"   # 期望 0
```

**零回归基线（九组都必须跑，缺一不可）**：

| 组 | 期望 | 它守住的是什么 |
| --- | --- | --- |
| `good/` | EXIT=0，34/34 通过 | 不误杀合规报告（防假阳性） |
| `bad/` | EXIT=1，多条缺陷 | 能拦下明显残次报告（防假阴性） |
| `tricky__empty_diagram/` | EXIT=1，**只** 1 条「没有任何 Mermaid 图」 | 识破标题齐全但内容空壳 |
| `tricky__no_translation/` | EXIT=1，**只** 1 条配对失败 | 守住「图必须成对」 |
| `tricky__node_not_in_table/` | EXIT=1，**只** 1 条节点命名 | 守住「节点名以骨架表为准」 |
| `tricky__translation_is_copy/` | EXIT=1，**只** 1 条「未做通俗化」 | 守住「翻译图不能是原图抄一遍」 |
| `tricky__prose_only_diagram/` | EXIT=1，**只** 1 条「没有任何 Mermaid 图」 | 守住「图必须是真的图，不是正文关键词」 |
| `runs/20261012-120000/` | EXIT=0 | 合法运行目录能通过 |
| `runs/not-a-timestamp/` | EXIT=1，只报目录名 | 非法运行目录会被拦 |

任何对 `check_reports.py` 的修改，改完必须九组都重跑。**只跑 GOOD 等于没验证**——GOOD 全过而反向用例也全过，正是假阴性的典型症状。

## 对抗性探测（十五条，除九组基线外必跑）

九组基线验证的是「该拦的拦住了」，但反向用例全红也可能只是「检查器把什么都判成不合格」。
这十五条里**八条期望 EXIT=0**，专门堵假阳性。已固化为可复跑脚本 `_probe_diagrams.py`：

```bash
$PY $SK/scripts/_probe_diagrams.py --out .selftest/probe
echo "EXIT=$?"   # 期望 0 = 十五条全部符合预期
```

| 用例 | 期望 | 守的是什么 |
| --- | --- | --- |
| `probe__second_orig_bad_node` | 1 | 第二张原图节点越界：必须**精确定位到第 2 张**，不能笼统说「有问题」 |
| `probe__orphan_translation` | 1 | 孤立的翻译图：没有前置原图时必须拦下 |
| `probe__untyped_heading` | 1 | 图写在无类型标注的子标题下：判不出类型必须报错，不得报通过 |
| `probe__translation_uses_col2` | **0** | 翻译图用对象表**第二列**中文名（参数空间/分布空间）时必须通过 |
| `probe__three_pairs_ok` | **0** | 多组成对图（两组）应通过，检查器不应限制组数上限 |
| `probe__dangling_second_orig` | 1 | 第二张原图后漏了翻译图：必须指出是第几张 |
| `probe__mermaid_elsewhere_ok` | **0** | 平级章节（`## 7. 附录`）里的 Mermaid 不参与交换图的成对判定 |
| `probe__untyped_child_heading_fails_closed` | 1 | 附录 Mermaid 挂在交换图章节**内部**的 `###` 下时判不出类型，必须报错 |
| `probe__vocab_adjunction_ok` | **0** | 伴随表的记号 `F ⊣ G` 可作箭头名（只认对象表/态射表时会误判自造） |
| `probe__vocab_monad_ok` | **0** | 单子表的单位 `δ`、乘法 `μ` 可作箭头名（它们不在第一列） |
| `probe__vocab_limit_second_col_ok` | **0** | 极限表写成「材料的说法 \| 范畴结构 \|」时，第二列的 `A × B` 仍可作节点名 |
| `probe__vocab_basecat_second_col_ok` | **0** | 基范畴表写成「层 \| 范畴 \|」时，第二列的 `Kl(P)` 仍可作节点名 |
| `probe__vocab_still_rejects_invented` | 1 | **没有放水**：骨架表全在的情况下，自造节点名仍须被点名 |
| `probe__vocab_empty_skeleton_tables` | 1 | 失败关闭：骨架表一个记号都没有时报「无法校验」，不是放行 |
| `probe__translation_cjk_from_limit_col1` | **0** | 翻译图用极限表第一列的中文词（拉回/等化子）时须通过——守「中文名不得进词表」 |

`probe__untyped_child_heading_fails_closed` 是**有意保留的严格**：交换图章节内的任何
Mermaid 块都必须能判定类型，判不出就报错。宁可让作者多写一个「原图/翻译图」标注，
也不放行一张身份不明的图。

`probe__vocab_still_rejects_invented` 是词表扩大后**最该跑**的一条：它防止「扩大词表」
悄悄变成「什么都能过」。每次调词表范围，先跑它。

### 新用例不是摆设：对照实现验证

十五条全绿本身不能证明检查起了作用——也可能只是用例写得太松。因此新增的七条词表用例
都用**对照实现**反向验证过：

| 对照实现 | 哪几条会失败 | 说明 |
| --- | --- | --- |
| 只认对象表/态射表第一列（本次修改前） | `vocab_adjunction` / `vocab_monad` / `vocab_limit_second_col` / `vocab_basecat_second_col` | 证明这四条守的是真实存在的假阳性 |
| 全骨架表 + **无条件纳入第一列**（曾考虑、已否掉） | `translation_cjk_from_limit_col1` | 证明「取法」的选择是对的，不是随手写的 |

对照实现由 `scripts/_make_control_impls.py` 生成（随包分发）：

```bash
$PY $SK/scripts/_make_control_impls.py --out .selftest/old
$PY .selftest/old/check_ctrl_a.py --reports .selftest/probe/probe__vocab_adjunction_ok --rounds 1
echo "EXIT=$?"   # 期望 1 = 该用例确实守着一处真实存在的假阳性
```

改词表规则前重跑一遍，能立刻看出改动是修了问题还是换了问题。

写新探测用例时注意：`_make_sample_reports.py` 里的模板片段（如 `TRANS_BLOCK`）结尾不带换行，
直接 `+` 拼接会粘成 ` ```### 3.3 `，造出来的是畸形 Markdown——测的就不是门禁而是自己的手误了。
拼接一律走 `cat()`。

## 已知局限（量化披露）

- 门禁**不做跨轮一致性检查**：后一轮静默丢弃前一轮已识别的结构，门禁判不出来。已列为第一优先迭代方向。
- 翻译图**只判「换了词」，不判「换得对」**。下一步可要求附对照表并断言行数与骨架条目数一致。
- 门禁的「表格数据行 ≥6」是粗判据：无法区分行数达标但内容注水。人工复核时需确认对象表 ≥8 行、态射表 ≥12 行。
- 转换环节**查不出「转出来了但少了一段」**：门禁只在产物为 0 字符时报错。需人工抽样比对源文件与 .md 的段落数。
- 编码落到 `latin-1` 时内容可能已乱码，门禁不拦截，需看台账的 `encoding` 字段人工确认。
- 节点词表取的是「骨架表中不含中文的单元格」，因此出处（`W1 p15`）、星级（`★★★★★`）这类非记号单元格也在词表内。这意味着一个叫 `W1p15` 的自造节点名在技术上能过门禁。当前**没有观察到**此类用法（九组基线与十五条探测中均未出现），故选择「一条规则、易于审计」而非叠加白名单正则——正则越复杂，假阳性面越大。**处置约定**：一旦在真实报告中观察到此类规避，按证据收紧规则并补一条反向用例。
- 门禁判不了「记号**用对了地方**」：伴随表的 `η` 被拿去当态射名、单子的 `μ` 被当对象名，门禁不拦。需人工核对符号的角色。
