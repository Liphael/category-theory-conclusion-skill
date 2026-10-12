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
