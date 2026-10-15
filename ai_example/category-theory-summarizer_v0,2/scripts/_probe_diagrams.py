#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对抗性探测：九组基线之外，专门戳图检查（`check_reports.py::check_diagrams`）。

每条用例写明「期望什么退出码 + 它守住什么」。其中若干条是**不得误杀**用例
（期望 EXIT=0），专门证明「修了假阴性」没有顺手换来「假阳性」——
只跑反向用例是不够的，反向用例全红也可能是因为检查器把什么都判成不合格。

跑法：
    PY="C:/Users/14545/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
    $PY scripts/_probe_diagrams.py --out .selftest/probe
    # 退出码 0 = 八条全部符合预期

用例清单见下方 CASES。新增检查项时，在这里加一条对应的反向用例。
"""
import argparse
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_good = os.path.join(HERE, "_make_sample_reports.py")
_spec = importlib.util.spec_from_file_location("_sr", _good)
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)

ORIG_MERMAID = sr.ORIG_MERMAID
TRANS_BLOCK = sr.TRANS_BLOCK
ORIG_BLOCK = sr.ORIG_BLOCK
INDEX = sr.INDEX
GOOD = sr.GOOD


def cat(*parts):
    """拼接 Markdown 片段。

    TRANS_BLOCK 结尾不带换行，直接 `+` 会粘成 "```### 3.3"，造出的就是畸形件，
    测的就不是门禁而是自己的手误了。拼接处统一补空行。
    """
    return "\n\n".join(p.rstrip("\n") for p in parts) + "\n"


ORIG2_SKELETON = """### 3.3 第二张原图（范畴论骨架）

```mermaid
flowchart TD
    A["S"] -->|"m"| B["P(X)"]
```
"""

ORIG2_BAD_NODE = """### 3.3 第二张原图（范畴论骨架）

```mermaid
flowchart TD
    A["Θ"] -->|"瞎编的箭头"| B["不存在的节点"]
```
"""

TRANS2 = """### 3.4 第二张翻译图（用户领域概念）

```mermaid
flowchart TD
    A["样本空间"] -->|"抽样模型"| B["数据分布"]
```
"""

TRANS_USING_COL2 = """### 3.2 翻译图（用户领域概念）

```mermaid
flowchart TD
    A["参数空间"] -->|"抽样模型"| B["分布空间"]
    B -->|"估计量分布"| C["参数上的分布"]
    C -->|"取平均"| A
```
"""

UNTYPED = """### 3.1 示意图

```mermaid
flowchart TD
    A["Θ"] -->|"m"| B["P(X)"]
    B -->|"P(r)"| C["P(Θ)"]
    C -->|"E"| A
```
"""

# 挂在交换图章节**内部**的无类型子标题（故意不写「原图/翻译图」）
APPENDIX_CHILD = """### 3.5 实现流程

```mermaid
flowchart LR
    A["读材料"] --> B["转 md"] --> C["抽骨架"] --> D["出图"]
```
"""

# 挂在平级 `##` 章节下的 Mermaid（不属于交换图章节）
APPENDIX_SIBLING = """
## 7. 附录：实现流程

```mermaid
flowchart LR
    A["读材料"] --> B["转 md"] --> C["抽骨架"] --> D["出图"]
```
"""

# ---------------------------------------------------------------- 全骨架模板
# 只含对象表与态射表时测不出新词表。FULL 补齐基范畴 / 极限与余极限 / 伴随 /
# 自然变换 / 单子与代数，用来验证「节点命名以骨架表为准」里的**骨架表**是全部骨架。

FULL = """# 范畴论取向总结 · 第 {n} 轮（{label}）

- **轮次**：R{n}
- **归档目录**：见运行目录名（本轮不写时间戳）
- **材料**：测试夹具

## 1. 基范畴（含各层与置信度）

| 层 | 基范畴 | 说明 | 置信度 |
| --- | --- | --- | --- |
| 概率层 | Meas | 可测空间与可测映射 | ★★★★★ |
| 推断层 | Kl(P) | Giry 单子的 Kleisli 范畴 | ★★★★☆ |
| 决策层 | Pos | 偏序集范畴 | ★★★★☆ |

## 2. 对象表 Ob(C)

| ID | 对象 | 出处 | 显式性 | 置信度 |
| --- | --- | --- | --- | --- |
| S | 样本空间 | W1 p15 | 【显式】 | ★★★★★ |
| Θ | 参数空间 | W1 p47 | 【显式】 | ★★★★★ |
| P(X) | 分布空间 | W1 p19 | 【半显式】 | ★★★★☆ |
| P(Θ) | 参数上的分布 | W1 p52 | 【重构】 | ★★★☆☆ |

## 3. 态射表 Hom(C)

| 态射 | 类型 | 出处 | 显式性 | 置信度 |
| --- | --- | --- | --- | --- |
| m | Θ → P(X) | W1 p47 | 【显式】 | ★★★★★ |
| P(r) | P(X) → P(Θ) | W1 p29 | 【重构】 | ★★★☆☆ |
| E | P(Θ) → Θ | W1 p33 | 【半显式】 | ★★★★☆ |

## 4. 极限与余极限（系统盘点）

| 材料的说法 | 范畴结构 | 出处 | 显式性 |
| --- | --- | --- | --- |
| 联合、成对考虑 | A × B | W1 p21 | 【半显式】 |
| 解方程组、令两者相等 | Eq | W1 p58 | 【重构】 |
| 对称、与顺序无关 | Coeq | W1 p61 | 【重构】 |

## 5. 伴随（含严格层级）

| 伴随 | 层级 | 出处 | 显式性 |
| --- | --- | --- | --- |
| F ⊣ G | `Cat` 严格 | W1 p44 | 【重构】 |
| ∃_t ⊣ t^* | `Pos` 严格 | W1 p30 | 【重构】 |

## 6. 自然变换

| 自然变换 | 源 → 目标 | 出处 | 显式性 |
| --- | --- | --- | --- |
| η | Id ⇒ P | W1 p50 | 【重构】 |
| μ | P² ⇒ P | W1 p51 | 【重构】 |

## 7. 单子与代数

| 单子 | 单位 | 乘法 | 代数映射 | 出处 |
| --- | --- | --- | --- | --- |
| P | δ | μ | 𝔼 | W1 p36 |

## 8. 交换图

### 8.1 原图（范畴论骨架）

```mermaid
flowchart TD
    A["Θ"] -->|"m"| B["P(X)"]
```

### 8.2 翻译图（用户领域概念）

```mermaid
flowchart TD
    A["参数真值"] -->|"抽样模型"| B["数据分布"]
```

## 9. 范畴论重述

1. 第一句重述内容。
2. 第二句重述内容。
3. 第三句重述内容。
4. 第四句重述内容。

## 10. 信息缺失

| # | 缺失结构 | 原因 |
| --- | --- | --- |
| M1 | 贝叶斯反演 | 课程未覆盖 |

## 11. 非范畴论通俗摘要

这是通俗摘要段落，不含范畴术语。
"""

FULL_ORIG_BLOCK = """### 8.1 原图（范畴论骨架）

```mermaid
flowchart TD
    A["Θ"] -->|"m"| B["P(X)"]
```
"""

FULL_TRANS_BLOCK = """### 8.2 翻译图（用户领域概念）

```mermaid
flowchart TD
    A["参数真值"] -->|"抽样模型"| B["数据分布"]
```
"""


def orig(body):
    """把原图块换成给定 Mermaid 正文（保留带类型标注的子标题）。"""
    return "### 8.1 原图（范畴论骨架）\n\n```mermaid\n" + body.strip() + "\n```"


def trans(body):
    """把翻译图块换成给定 Mermaid 正文（保留带类型标注的子标题）。"""
    return "### 8.2 翻译图（用户领域概念）\n\n```mermaid\n" + body.strip() + "\n```"


# 骨架表里一个记号都没有（全是中文，连出处也写成中文）：词表为空。
# 此时「节点命名以骨架表为准」无从校验，必须报错而不是放行。
# 注意不能写 ★，星级不含中文会进词表，这个词表就空不了了。
EMPTY_VOCAB = """# 范畴论取向总结 · 第 {n} 轮（{label}）

- **轮次**：R{n}
- **材料**：测试夹具

## 1. 对象表 Ob(C)

| 记号 | 对象 | 出处 | 显式性 |
| --- | --- | --- | --- |
| 样本 | 样本空间 | 讲义十五页 | 【显式】 |
| 参数 | 参数空间 | 讲义四十七页 | 【显式】 |
| 分布 | 分布空间 | 讲义十九页 | 【半显式】 |
| 参数分布 | 参数上的分布 | 讲义五十二页 | 【重构】 |

## 2. 态射表 Hom(C)

| 态射 | 类型 | 出处 | 显式性 |
| --- | --- | --- | --- |
| 抽样 | 参数到分布 | 讲义四十七页 | 【显式】 |
| 推断 | 分布到参数分布 | 讲义二十九页 | 【重构】 |
| 取平均 | 参数分布到参数 | 讲义三十三页 | 【半显式】 |

## 3. 交换图

### 3.1 原图（范畴论骨架）

```mermaid
flowchart TD
    A["Θ"] -->|"m"| B["P(X)"]
```

### 3.2 翻译图（用户领域概念）

```mermaid
flowchart TD
    A["参数真值"] -->|"抽样模型"| B["数据分布"]
```

## 4. 范畴论重述

1. 第一句重述内容。
2. 第二句重述内容。
3. 第三句重述内容。
4. 第四句重述内容。

## 5. 信息缺失

| # | 缺失结构 | 原因 |
| --- | --- | --- |
| M1 | 贝叶斯反演 | 课程未覆盖 |

## 6. 非范畴论通俗摘要

这是通俗摘要段落，不含范畴术语。
"""

# 极限表**第一列写成中文**（如实盘常见的「材料的说法 | 范畴结构 |」写法）。
# 用来验证：中文名不会被纳入节点词表，否则翻译图会被误判成「未翻译」。
LIMIT_ZH_FIRST_COL = FULL.replace(
    "| 联合、成对考虑 | A × B | W1 p21 | 【半显式】 |\n"
    "| 解方程组、令两者相等 | Eq | W1 p58 | 【重构】 |\n"
    "| 对称、与顺序无关 | Coeq | W1 p61 | 【重构】 |",
    "| 拉回 | A × B | W1 p21 | 【半显式】 |\n"
    "| 等化子 | Eq | W1 p58 | 【重构】 |\n"
    "| 余等化子 | Coeq | W1 p61 | 【重构】 |")

CASES = [
    # (用例名, 期望退出码, 守住什么, 报告模板)
    ("probe__second_orig_bad_node", 1,
     "第二张原图节点越界：必须精确定位到第 2 张，而不是笼统说「有问题」",
     GOOD.replace(ORIG_BLOCK, cat(ORIG_BLOCK, ORIG2_BAD_NODE, TRANS2))),

    ("probe__orphan_translation", 1,
     "孤立的翻译图：没有前置原图时必须拦下",
     GOOD.replace(ORIG_BLOCK, cat(TRANS_BLOCK, ORIG_MERMAID))),

    ("probe__untyped_heading", 1,
     "图写在无类型标注的子标题下：判不出类型必须报错，不得报通过",
     GOOD.replace(ORIG_BLOCK, cat(UNTYPED, TRANS_BLOCK))),

    ("probe__translation_uses_col2", 0,
     "**不得误杀**：翻译图用对象表第二列中文名（参数空间/分布空间）时必须通过。"
     "这条专为「词表收紧到第一列」是否引入假阳性而设",
     GOOD.replace(TRANS_BLOCK, TRANS_USING_COL2)),

    ("probe__three_pairs_ok", 0,
     "**不得误杀**：多组成对图（两组）应通过，检查器不应限制组数上限",
     GOOD.replace(ORIG_BLOCK, cat(ORIG_BLOCK, ORIG2_SKELETON, TRANS2))),

    ("probe__dangling_second_orig", 1,
     "第二张原图后面漏了翻译图：必须拦下，且要指出是第几张",
     GOOD.replace(ORIG_BLOCK, cat(ORIG_BLOCK, ORIG2_SKELETON))),

    ("probe__mermaid_elsewhere_ok", 0,
     "**不得误杀**：平级章节（## 7. 附录）里的 Mermaid 不参与交换图的成对判定",
     GOOD + APPENDIX_SIBLING),

    ("probe__untyped_child_heading_fails_closed", 1,
     "失败关闭：附录 Mermaid 挂在交换图章节**内部**的 `###` 子标题下时判不出类型，"
     "必须报错。宁可错报、不可放行",
     GOOD.replace(ORIG_BLOCK, cat(ORIG_BLOCK, APPENDIX_CHILD))),

    # ---- 以下七条守「节点命名以骨架表为准」的词表范围 ----
    ("probe__vocab_adjunction_ok", 0,
     "**不得误杀**：伴随表的记号（`F ⊣ G`）可作箭头名——只认对象表/态射表时会被误判自造",
     FULL.replace(FULL_ORIG_BLOCK, orig(
         'flowchart LR\n    A["Θ"] -->|"F ⊣ G"| B["P(Θ)"]'))),

    ("probe__vocab_monad_ok", 0,
     "**不得误杀**：单子表的单位 `δ`、乘法 `μ` 可作箭头名（它们不在第一列，"
     "靠「不含中文的单元格」这条规则进来）",
     FULL.replace(FULL_ORIG_BLOCK, orig(
         'flowchart TD\n    A["Θ"] -->|"δ"| B["P(Θ)"]\n    B -->|"μ"| C["P(X)"]'))),

    ("probe__vocab_limit_second_col_ok", 0,
     "**不得误杀**：极限表写成「材料的说法 | 范畴结构 |」时，记号 `A × B` 在第二列，"
     "仍须可作节点名",
     FULL.replace(FULL_ORIG_BLOCK, orig(
         'flowchart TD\n    A["Θ"] -->|"m"| B["A × B"]'))),

    ("probe__vocab_basecat_second_col_ok", 0,
     "**不得误杀**：基范畴表写成「层 | 范畴 |」时，`Kl(P)` 在第二列，仍须可作节点名",
     FULL.replace(FULL_ORIG_BLOCK, orig(
         'flowchart TD\n    A["Θ"] -->|"m"| B["Kl(P)"]'))),

    ("probe__vocab_still_rejects_invented", 1,
     "**没有放水**：骨架表全在的情况下，自造节点名仍须被点名。"
     "这条防止「扩大词表」变成「什么都能过」",
     FULL.replace(FULL_ORIG_BLOCK, orig(
         'flowchart TD\n    A["数据来源"] -->|"拟合"| B["结论表"]'))),

    ("probe__vocab_empty_skeleton_tables", 1,
     "失败关闭：骨架表里一个记号都没有时，无法校验命名，必须报错（不是放行）",
     EMPTY_VOCAB),

    ("probe__translation_cjk_from_limit_col1", 0,
     "**不得误杀**：翻译图用了极限表第一列的中文词（拉回/等化子）时必须通过。"
     "若把「第一列」无条件纳入词表，中文名进词表，翻译图就会被误判成未翻译",
     LIMIT_ZH_FIRST_COL.replace(FULL_TRANS_BLOCK, trans(
         'flowchart TD\n    A["拉回"] -->|"等化子"| B["余等化子"]'))),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="探测用例输出目录")
    ap.add_argument("--checker", default=os.path.join(HERE, "check_reports.py"),
                    help="门禁脚本路径")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="通过的用例也打印门禁输出尾部")
    a = ap.parse_args()

    failed = 0
    for name, want, note, tmpl in CASES:
        d = os.path.join(a.out, name)
        sr.write(d, "R1.md", tmpl.format(n=1, label=sr.LABELS[1]))
        sr.write(d, "00_INDEX.md", INDEX)
        r = subprocess.run([sys.executable, a.checker,
                            "--reports", d, "--rounds", "1"],
                           capture_output=True, text=True, encoding="utf-8")
        ok = (r.returncode == want)
        failed += 0 if ok else 1
        print("  [%s] %-40s exit=%d 期望=%d" %
              ("OK" if ok else "FAIL", name, r.returncode, want))
        print("        守：%s" % note)
        if not ok or a.verbose:
            tail = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
            for ln in tail[-10:]:
                print("        " + ln)
    total = len(CASES)
    print("")
    print("=== %s ===" % ("%d 条探测全部符合预期" % total if failed == 0
                          else "有 %d 条不符" % failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
