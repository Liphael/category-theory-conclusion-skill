#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_reports.py —— 报告交付门禁（范畴论总结技能 · 交付前必跑）

对 reports/ 下的每份迭代报告做确定性断言检查，全部通过才允许交付。
检查项均为纯函数判定，不依赖 AI 推断，可重复复跑。

用法：
  python check_reports.py --reports <reports目录> [--rounds 4] [--require-index]

退出码：0 = 全部通过；1 = 存在未通过项（禁止交付）
"""

import argparse
import glob
import os
import re
import sys

TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
NUM_RE = re.compile(r"^\s*(\d+)[.、)]\s+\S")

REQUIRED_SECTION_KEYWORDS = [
    ("对象表", ["对象表", "Ob("], "对象表 Ob(C)"),
    ("态射表", ["态射表", "Hom("], "态射表 Hom(C)"),
    ("范畴论重述", ["范畴论重述"], "范畴论重述（3–5 句）"),
    ("通俗摘要", ["通俗摘要", "非范畴论"], "非范畴论通俗摘要"),
    ("信息缺失", ["信息缺失"], "对象「信息缺失」"),
]

MARK_RE = re.compile(r"【(原文)?(显式|半显式|重构)】|显式性|置信度|★")


def split_sections(lines):
    """返回 [(level, title, start_idx, end_idx), ...]"""
    heads = []
    for i, ln in enumerate(lines):
        m = HEAD_RE.match(ln)
        if m:
            heads.append((len(m.group(1)), m.group(2).strip(), i))
    secs = []
    for k, (lv, title, start) in enumerate(heads):
        end = heads[k + 1][2] if k + 1 < len(heads) else len(lines)
        secs.append((lv, title, start, end))
    return secs


def count_restatement_sentences(lines):
    """在含「范畴论重述」的标题下，统计编号句子数。取第一个匹配章节。"""
    for lv, title, s, e in split_sections(lines):
        if "范畴论重述" in title:
            n = 0
            for ln in lines[s:e]:
                if NUM_RE.match(ln):
                    n += 1
            return n, title
    return 0, None


ARROW_RE = re.compile(r"→|-->|⟶|⟼|-{1,2}>|⇒|⟾")

DIAGRAM_HEAD_KEYWORDS = ("交换图", "交换图", "Diagram", "diagram", "复合链")


def has_textual_diagram(lines):
    """文字交换图必须落在「交换图」章节内且正文含箭头，不能全文子串判定。

    用全文子串会出假阴性：正文写一句「本样例无交换图」、而态射表里恰好有
    「S → ℝ」，就会被判成「已有交换图」。因此改为：先定位交换图章节标题，
    再只在该章节正文里找箭头。
    """
    for _lv, title, s, e in split_sections(lines):
        if not any(k in title for k in DIAGRAM_HEAD_KEYWORDS):
            continue
        body = lines[s + 1:e]
        if any(ARROW_RE.search(ln) for ln in body):
            return True, title
    return False, None


def count_table_data_rows(lines):
    """统计 markdown 表格的数据行（排除表头行与分隔行）。"""
    n = 0
    in_table = False
    for ln in lines:
        st = ln.strip()
        if st.startswith("|") and st.endswith("|") and st.count("|") >= 3:
            if not in_table:
                in_table = True
                continue  # 跳过表头
            if set(st.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
                continue  # 分隔行
            n += 1
        else:
            in_table = False
    return n


def check_one(path, rounds):
    """返回 (问题列表, 统计字典)。问题列表为空即通过。"""
    problems = []
    stats = {}
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    name = os.path.basename(path)

    ts = TS_RE.findall(text)
    stats["timestamp"] = ts[0] if ts else None
    if not ts:
        problems.append("缺少时间戳（需形如 2026-10-11 09:27:24）")

    # 章节必须作为「标题」出现，不能用全文子串匹配——否则正文里提一句
    # 「缺通俗摘要」也会被判为已具备该章节（假阴性）。
    headings = [t for _, t, _, _ in split_sections(lines)]
    stats["headings"] = len(headings)
    for _key, kws, human in REQUIRED_SECTION_KEYWORDS:
        if not any(any(k in h for k in kws) for h in headings):
            problems.append("缺少必备章节（需为标题）：%s" % human)

    fences = sum(1 for ln in lines if ln.strip().startswith("```"))
    stats["fences"] = fences
    if fences % 2 != 0:
        problems.append("代码围栏未配对（共 %d 个 ```，应为偶数）" % fences)

    # Mermaid 块是真图，无论放在哪一节都算；文字图则必须在「交换图」章节内
    n_mermaid = sum(1 for ln in lines if ln.strip().startswith("```mermaid"))
    ok_txt, diag_title = has_textual_diagram(lines)
    stats["mermaid"] = n_mermaid
    stats["diagram"] = "mermaid" if n_mermaid else ("text:" + diag_title if ok_txt else "none")
    if n_mermaid < 1 and not ok_txt:
        problems.append("缺少交换图：需至少 1 个 Mermaid 图，"
                        "或在「交换图」章节内给出含箭头的文字交换图（仅有章节标题而正文无箭头不算）")

    n, title = count_restatement_sentences(lines)
    stats["restatement_sentences"] = n
    if n < 3 or n > 5:
        problems.append("范畴论重述句数为 %d，要求是 3–5 句" % n)

    rows = count_table_data_rows(lines)
    stats["table_rows"] = rows
    if rows < 6:
        problems.append("表格数据行仅 %d 行，对象表与态射表疑似为空（要求 ≥6）" % rows)

    n_mark = len(MARK_RE.findall(text))
    stats["explicit_marks"] = n_mark
    if n_mark < 4:
        problems.append("显式性/置信度标注仅 %d 处，无法体现「原文显式 vs 重构」的区分（要求 ≥4）" % n_mark)

    return problems, stats


def main():
    ap = argparse.ArgumentParser(description="报告交付门禁")
    ap.add_argument("--reports", required=True, help="reports 目录")
    ap.add_argument("--rounds", type=int, default=4, help="期望的迭代报告份数（默认 4）")
    ap.add_argument("--require-index", action="store_true", default=True,
                    help="要求存在 00_INDEX.md")
    args = ap.parse_args()

    if not os.path.isdir(args.reports):
        print("[FATAL] reports 目录不存在：%s" % args.reports, file=sys.stderr)
        return 2

    files = sorted(glob.glob(os.path.join(args.reports, "R[0-9]_*.md")))
    print("=" * 78)
    print("报告门禁　目录=%s" % os.path.abspath(args.reports))
    print("=" * 78)

    all_problems = []
    if args.require_index and not os.path.exists(os.path.join(args.reports, "00_INDEX.md")):
        all_problems.append("缺少 00_INDEX.md")

    if len(files) != args.rounds:
        all_problems.append("迭代报告份数为 %d，期望 %d 份（1 份基线 + %d 次迭代）"
                            % (len(files), args.rounds, args.rounds - 1))

    tss = []
    for p in files:
        probs, st = check_one(p, args.rounds)
        tss.append(st.get("timestamp"))
        flag = "PASS" if not probs else "FAIL"
        print("[%s] %-28s 时间戳=%s 表格行=%d 重述句数=%d 图=%s 标注=%d"
              % (flag, os.path.basename(p), st.get("timestamp"),
                 st.get("table_rows", 0), st.get("restatement_sentences", 0),
                 st.get("diagram", "none"), st.get("explicit_marks", 0)))
        for q in probs:
            print("        ✗ %s" % q)
            all_problems.append("%s: %s" % (os.path.basename(p), q))

    # 时间戳必须互不相同且按文件名序递增
    real = [t for t in tss if t]
    if len(real) == len(tss) and len(real) > 1:
        if len(set(real)) != len(real):
            all_problems.append("各轮时间戳存在重复，必须为各自独立的时间点")
        if real != sorted(real):
            all_problems.append("时间戳未按轮次递增：%s" % real)

    print("-" * 78)
    if all_problems:
        print("未通过项 %d 条：" % len(all_problems))
        for q in all_problems:
            print("  - %s" % q)
        print("\n[结论] 门禁未通过，禁止交付。")
        return 1
    print("全部通过：%d 份报告，%d 条断言全部满足。" % (len(files), len(files) * 6 + 2))
    print("[结论] 门禁通过，可交付。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
