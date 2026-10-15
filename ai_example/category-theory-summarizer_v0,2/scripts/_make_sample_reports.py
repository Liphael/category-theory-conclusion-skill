#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成门禁正/反向样例报告（仅用于自测，不参与技能运行）。

good/                      结构完整，期望门禁 EXIT=0
bad/                       故意缺轮次戳、缺章节、重述 2 句、无图、缺 INDEX，期望 EXIT=1
tricky__empty_diagram/     交换图章节是空壳（只有标题），期望 EXIT=1 且只报「章内没有图」
tricky__no_translation/    有原图但无翻译图，期望 EXIT=1 且只报「缺少通俗化翻译图」
tricky__node_not_in_table/ 原图节点名不在骨架表里，期望 EXIT=1 且只报节点命名问题
tricky__translation_is_copy/  翻译图把原图抄了一遍，期望 EXIT=1 且只报「未做通俗化」
tricky__prose_only_diagram/   全篇无 Mermaid，靠正文箭头+「翻译」二字冒充，期望 EXIT=1
runs/20261012-120000/      合法运行目录（目录名是时间戳），供 --run-dir 正向测试
runs/not-a-timestamp/      非法运行目录名，供 --run-dir 负向测试

每个 tricky 用例只针对一种缺陷，便于确认门禁「真的会拦这一类」而不是碰巧全红。
"""
import argparse
import os

# ---------------------------------------------------------------- 模板

GOOD = """# 范畴论取向总结 · 第 {n} 轮（{label}）

- **轮次**：R{n}
- **归档目录**：见运行目录名（本轮不写时间戳）
- **材料**：测试夹具

## 1. 对象表 Ob(C)

| ID | 对象 | 出处 | 显式性 | 置信度 |
| --- | --- | --- | --- | --- |
| S | 样本空间 | W1 p15 | 【显式】 | ★★★★★ |
| Θ | 参数空间 | W1 p47 | 【显式】 | ★★★★★ |
| P(X) | 分布空间 | W1 p19 | 【半显式】 | ★★★★☆ |
| P(Θ) | 参数上的分布 | W1 p52 | 【重构】 | ★★★☆☆ |

## 2. 态射表 Hom(C)

| 态射 | 类型 | 出处 | 显式性 | 置信度 |
| --- | --- | --- | --- | --- |
| m | Θ → P(X) | W1 p47 | 【显式】 | ★★★★★ |
| P(r) | P(X) → P(Θ) | W1 p29 | 【重构】 | ★★★☆☆ |
| E | P(Θ) → Θ | W1 p33 | 【半显式】 | ★★★★☆ |

## 3. 交换图

### 3.1 原图（范畴论骨架）

```mermaid
flowchart TD
    A["Θ"] -->|"m"| B["P(X)"]
    B -->|"P(r)"| C["P(Θ)"]
    C -->|"E"| A
```

节点与箭头名称全部取自上面的对象表与态射表。

### 3.2 翻译图（用户领域概念）

```mermaid
flowchart TD
    A["参数真值"] -->|"抽样模型"| B["数据分布"]
    B -->|"估计量分布"| C["估计量取值的分布"]
    C -->|"取平均"| A
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

ORIG_MERMAID = """### 3.1 原图（范畴论骨架）

```mermaid
flowchart TD
    A["Θ"] -->|"m"| B["P(X)"]
    B -->|"P(r)"| C["P(Θ)"]
    C -->|"E"| A
```

节点与箭头名称全部取自上面的对象表与态射表。

"""

TRANS_BLOCK = """### 3.2 翻译图（用户领域概念）

```mermaid
flowchart TD
    A["参数真值"] -->|"抽样模型"| B["数据分布"]
    B -->|"估计量分布"| C["估计量取值的分布"]
    C -->|"取平均"| A
```"""

ORIG_BLOCK = ORIG_MERMAID + TRANS_BLOCK

# 交换图章节只有标题，正文为空壳
TRICKY_EMPTY = GOOD.replace(ORIG_BLOCK, """### 3.1 原图（范畴论骨架）

（本轮暂略）""")

# 有原图，但完全没有翻译图
TRICKY_NO_TRANS = GOOD.replace(ORIG_BLOCK, ORIG_MERMAID.rstrip())

# 原图节点名是自造词，不在骨架表里（翻译图仍在）
TRICKY_NODE = GOOD.replace("""```mermaid
flowchart TD
    A["Θ"] -->|"m"| B["P(X)"]
    B -->|"P(r)"| C["P(Θ)"]
    C -->|"E"| A
```""", """```mermaid
flowchart TD
    A["数据来源"] -->|"拟合"| B["结论表"]
```""")

# 翻译图只是把原图抄一遍，没换成领域说法
TRICKY_COPY_TRANS = GOOD.replace(TRANS_BLOCK, """### 3.2 翻译图（用户领域概念）

```mermaid
flowchart TD
    A["Θ"] -->|"m"| B["P(X)"]
    B -->|"P(r)"| C["P(Θ)"]
    C -->|"E"| A
```""")

# 全篇没有一个 Mermaid 图：靠「正文含箭头」冒充原图、靠「出现翻译二字
# + 一张任意对照表」冒充翻译图。这条用例守的是历史上的一个假阴性：
# 曾经这种报告会被判通过，并显示「图(译/原)=1/1」。
TRICKY_PROSE_ONLY = GOOD.replace(ORIG_BLOCK, """### 3.1 原图（范畴论骨架）

Θ → P(X)：本轮用文字描述交换关系，不画图。

下表用于翻译：

| 符号 | 含义 |
| --- | --- |
| Θ | 参数真值 |
| m | 抽样模型 |

### 3.2 翻译图（用户领域概念）

（同上，略）""")

BAD = """# 范畴论取向总结 · 第 1 轮

（本样例故意缺轮次戳、缺通俗摘要、重述仅 2 句、无交换图章节、缺 INDEX）

## 对象表 Ob(C)

| ID | 对象 | 出处 |
| --- | --- | --- |
| S | 样本空间 | W1 p15 |
| Θ | 参数空间 | W1 p47 |

## 态射表 Hom(C)

| 态射 | 类型 | 出处 |
| --- | --- | --- |
| X | S → ℝ | W1 p16 |

## 范畴论重述

1. 只有一句。
2. 只有两句。

## 信息缺失

| # | 缺失结构 |
| --- | --- |
| M1 | 贝叶斯反演 |
"""

INDEX = """# 索引

- 轮次戳：R1 基线 / R2 迭代 1 / R3 迭代 2 / R4 收敛
- 时间信息见运行目录名，报告内不再写每轮时间戳
"""

LABELS = {1: "基线", 2: "迭代 1/3", 3: "迭代 2/3", 4: "收敛"}


# ---------------------------------------------------------------- 生成

def write(d, name, text):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write(text)


def make_round_set(d, tmpl):
    for n in (1, 2, 3, 4):
        write(d, "R%d.md" % n, tmpl.format(n=n, label=LABELS[n]))
    write(d, "00_INDEX.md", INDEX)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./selftest_reports",
                    help="样例报告输出目录；其下会建多个用例子目录")
    a = ap.parse_args()
    base = a.out

    make_round_set(os.path.join(base, "good"), GOOD)
    write(os.path.join(base, "bad"), "R1.md", BAD)

    for name, tmpl in (("tricky__empty_diagram", TRICKY_EMPTY),
                       ("tricky__no_translation", TRICKY_NO_TRANS),
                       ("tricky__node_not_in_table", TRICKY_NODE),
                       ("tricky__translation_is_copy", TRICKY_COPY_TRANS),
                       ("tricky__prose_only_diagram", TRICKY_PROSE_ONLY)):
        d = os.path.join(base, name)
        write(d, "R1.md", tmpl.format(n=1, label=LABELS[1]))
        write(d, "00_INDEX.md", INDEX)

    # --run-dir 正向/负向测试：合法时间戳目录名 vs 非法目录名
    for run_name in ("20261012-120000", "not-a-timestamp"):
        run = os.path.join(base, "runs", run_name)
        os.makedirs(os.path.join(run, "00_source"), exist_ok=True)
        os.makedirs(os.path.join(run, "01_markdown"), exist_ok=True)
        make_round_set(os.path.join(run, "02_reports"), GOOD)

    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d)
        if os.path.isdir(p):
            print("  %-28s %d files" % (d, sum(len(f) for _, _, f in os.walk(p))))


if __name__ == "__main__":
    main()
