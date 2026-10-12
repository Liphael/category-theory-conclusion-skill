#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成门禁正/反向样例报告（仅用于自测，不参与技能运行）。

good/    —— 结构完整，期望门禁 EXIT=0
bad/     —— 故意缺章节、重述句数不足、无交换图、缺 INDEX，期望门禁 EXIT=1
tricky/  —— 五件套标题齐全、正文合规，但「交换图」章节是空壳（无箭头、无 Mermaid）；
            期望门禁 EXIT=1 且只报「缺少交换图」一条。
            这是为堵住「用全文子串判定交换图」的假阴性而设的反向用例。
"""
import os
import argparse

GOOD = """# 范畴论取向总结 · 第 {n} 轮

- **时间戳**：2026-10-11 09:{m1}:{m2} (GMT+8)
- **材料**：测试夹具

## 1. 文本类型判断

| 维度 | 判断 | 依据 |
| --- | --- | --- |
| 类型 | 教学讲义 | 定义块 + 例题 |
| 形式化 | 中等偏低 | 无范畴术语 |

## 2. 对象表 Ob(C)

| ID | 对象 | 出处 | 显式性 | 置信度 |
| --- | --- | --- | --- | --- |
| S | 样本空间 | W1 p15 | 【显式】 | ★★★★★ |
| Θ | 参数空间 | W1 p47 | 【显式】 | ★★★★★ |
| P(X) | 分布空间 | W1 p19 | 【半显式】 | ★★★★☆ |

## 3. 态射表 Hom(C)

| 态射 | 类型 | 出处 | 显式性 | 置信度 |
| --- | --- | --- | --- | --- |
| X | S → ℝ | W1 p16 | 【显式】 | ★★★★★ |
| m | Θ → P(X) | W1 p47 | 【显式】 | ★★★★★ |
| r | X → Θ | W1 p29 | 【重构】 | ★★★☆☆ |

## 4. 交换图

```mermaid
flowchart TD
    A["Θ"] -->|"m"| B["P(X)"]
    B -->|"P(r)"| C["P(Θ)"]
    C -->|"E"| A
```

## 5. 范畴论重述

1. 第一句重述内容。
2. 第二句重述内容。
3. 第三句重述内容。
4. 第四句重述内容。

## 6. 信息缺失

| # | 缺失结构 | 原因 |
| --- | --- | --- |
| M1 | 贝叶斯反演 | 课程未覆盖 |

## 7. 非范畴论通俗摘要

这是通俗摘要段落，用于验证门禁对通俗摘要章节的判定。
"""

BAD = """# 范畴论取向总结 · 第 1 轮

（本样例故意缺时间戳、缺通俗摘要、重述仅 2 句、无交换图）

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


# 交换图章节为空壳：其余全部合规，只有图缺失
TRICKY = """# 范畴论取向总结 · 第 1 轮

- **时间戳**：2026-10-11 09:30:00 (GMT+8)

## 1. 对象表 Ob(C)

| ID | 对象 | 出处 | 显式性 | 置信度 |
| --- | --- | --- | --- | --- |
| S | 样本空间 | W1 p15 | 【显式】 | ★★★★★ |
| Θ | 参数空间 | W1 p47 | 【显式】 | ★★★★★ |
| P(X) | 分布空间 | W1 p19 | 【半显式】 | ★★★★☆ |

## 2. 态射表 Hom(C)

| 态射 | 类型 | 出处 | 显式性 | 置信度 |
| --- | --- | --- | --- | --- |
| X | S → ℝ | W1 p16 | 【显式】 | ★★★★★ |
| m | Θ → P(X) | W1 p47 | 【显式】 | ★★★★★ |
| r | X → Θ | W1 p29 | 【重构】 | ★★★☆☆ |

## 3. 交换图

（本轮暂略，下一轮补）

## 4. 范畴论重述

1. 第一句重述内容。
2. 第二句重述内容。
3. 第三句重述内容。

## 5. 信息缺失

| # | 缺失结构 | 原因 |
| --- | --- | --- |
| M1 | 贝叶斯反演 | 课程未覆盖 |

## 6. 非范畴论通俗摘要

这是通俗摘要段落。
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./selftest_reports",
                    help="样例报告输出目录；其下会建 good/ 与 bad/")
    a = ap.parse_args()
    base = a.out
    good = os.path.join(base, "good")
    bad = os.path.join(base, "bad")
    tricky = os.path.join(base, "tricky")
    for d in (good, bad, tricky):
        os.makedirs(d, exist_ok=True)

    stamps = [("16", "05"), ("17", "10"), ("18", "22"), ("19", "40")]
    for i, (m1, m2) in enumerate(stamps, start=1):
        with open(os.path.join(good, "R%d_20261011-%s%s00.md" % (i, m1, m2)),
                  "w", encoding="utf-8") as f:
            f.write(GOOD.format(n=i, m1=m1, m2=m2))
    with open(os.path.join(good, "00_INDEX.md"), "w", encoding="utf-8") as f:
        f.write("# 索引\n\n四轮报告索引。\n")

    with open(os.path.join(bad, "R1_20261011-200000.md"), "w", encoding="utf-8") as f:
        f.write(BAD)

    with open(os.path.join(tricky, "R1_20261011-093000.md"), "w", encoding="utf-8") as f:
        f.write(TRICKY)
    with open(os.path.join(tricky, "00_INDEX.md"), "w", encoding="utf-8") as f:
        f.write("# 索引\n\ntricky 用例索引。\n")

    print("good   ->", os.path.abspath(good), len(os.listdir(good)), "files")
    print("bad    ->", os.path.abspath(bad), len(os.listdir(bad)), "files")
    print("tricky ->", os.path.abspath(tricky), len(os.listdir(tricky)), "files")


if __name__ == "__main__":
    main()
