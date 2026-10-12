#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_reports.py —— 报告交付门禁（范畴论总结技能 · 交付前必跑）

对运行目录下的迭代报告做确定性断言检查，全部通过才允许交付。
检查项均为纯函数判定，不依赖 AI 推断，可重复复跑。

用法：
  python check_reports.py --run-dir runs/20261012-142200 --rounds 4
  python check_reports.py --reports <报告目录> --rounds 4

--run-dir 给出时：校验目录名是时间戳 YYYYMMDD-HHMMSS，
                  并默认从 <run-dir>/02_reports 读取报告。

检查项（每份报告）：
  1. 轮次戳：文件名 R<n>.md 且报告头「轮次」字段与之一致（每轮不再要求时间戳）
  2. 必备章节按标题判定：对象表 / 态射表 / 范畴论重述 / 通俗摘要 / 信息缺失
  3. 代码围栏配对
  4. 交换图章节：每张原图之后必须追加通俗化翻译图
  5. 原图的 Mermaid 节点/箭头标签必须见于骨架表
  6. 范畴论重述 3–5 句
  7. 表格数据行 ≥6
  8. 显式性/置信度标注 ≥4
全局：轮次份数与编号连续、00_INDEX.md、运行目录名是时间戳

退出码：0 = 全部通过；1 = 存在未通过项（禁止交付）；2 = 参数错误
"""

import argparse
import glob
import os
import re
import sys

ROUND_FILE_RE = re.compile(r"^R(\d+)\.md$")
# 允许 「**轮次**：R1」 这种带加粗的写法，故跳过 * 与空白
ROUND_STAMP_RE = re.compile(r"轮次\s*\**\s*[：:]\s*R(\d+)")
RUN_DIR_RE = re.compile(r"^\d{8}-\d{6}$")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
NUM_RE = re.compile(r"^\s*(\d+)[.、)]\s+\S")
TS_FIELD_RE = re.compile(
    r"^\s*[-*]?\s*\*{0,2}(时间戳|生成时间|输出时间|撰写时间)\*{0,2}\s*[：:]")

# 图的类型由「所在子标题」判定：### x.1 原图 / ### x.2 翻译图
ORIG_HEAD_KEYS = ("原图", "原 图", "范畴论", "骨架", "original", "skeleton")
TRANS_HEAD_KEYS = ("翻译", "通俗", "领域", "translation", "domain", "plain")

REQUIRED_SECTION_KEYWORDS = [
    ("对象表", ["对象表", "Ob("], "对象表 Ob(C)"),
    ("态射表", ["态射表", "Hom("], "态射表 Hom(C)"),
    ("范畴论重述", ["范畴论重述"], "范畴论重述（3–5 句）"),
    ("通俗摘要", ["通俗摘要", "非范畴论"], "非范畴论通俗摘要"),
    ("信息缺失", ["信息缺失"], "对象「信息缺失」"),
]

MARK_RE = re.compile(r"【(原文)?(显式|半显式|重构)】|显式性|置信度|★")

DIAGRAM_HEAD_KEYWORDS = ("交换图", "Diagram", "diagram", "复合链")
OBJ_HEAD_KEYWORDS = ("对象表", "Ob(")
MOR_HEAD_KEYWORDS = ("态射表", "Hom(")

# Mermaid 里形如 A["Θ"] 的节点标签、以及 -->|"m"| 的箭头标签
MERMAID_NODE_RE = re.compile(r"\[\s*\"?([^\"\]\[]+?)\"?\s*\]")
MERMAID_EDGE_RE = re.compile(r"\|+\s*\"?([^\"\|]+?)\"?\s*\|+")


# ---------------------------------------------------------------- 基础解析

def split_sections(lines):
    """返回 [(level, title, start_idx, end_idx), ...]

    区间结束于「下一个同级或更高级标题」，因此子标题（### ）包含在父章节内。
    若简单地结束于下一个任意标题，则「## 交换图」的区间会在其第一个
    「### 3.1 原图」处截断，导致父章节被判为空壳（假阴性）。
    """
    heads = []
    for i, ln in enumerate(lines):
        m = HEAD_RE.match(ln)
        if m:
            heads.append((len(m.group(1)), m.group(2).strip(), i))
    secs = []
    for k, (lv, title, start) in enumerate(heads):
        end = len(lines)
        for nxt in heads[k + 1:]:
            if nxt[0] <= lv:
                end = nxt[2]
                break
        secs.append((lv, title, start, end))
    return secs


def table_data_rows(lines, s, e):
    """取 [s,e) 区间内的 Markdown 表格数据行，跳过表头与分隔行。"""
    rows = []
    in_table = False
    for ln in lines[s:e]:
        st = ln.strip()
        if st.startswith("|") and st.endswith("|") and st.count("|") >= 3:
            if not in_table:
                in_table = True
                continue  # 表头
            if set(st.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
                continue  # 分隔行
            rows.append([c.strip() for c in st.strip("|").split("|")])
        else:
            in_table = False
    return rows


def count_table_data_rows(lines):
    return len(table_data_rows(lines, 0, len(lines)))


def mermaid_blocks(lines):
    """返回 [(start, end)]，start 指向 ```mermaid 行，end 指向闭合围栏行。"""
    blocks = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("```mermaid"):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            blocks.append((i, min(j, len(lines) - 1)))
            i = j + 1
        else:
            i += 1
    return blocks


def norm(tok):
    """归一化标签：去数学符、去 <br/> 之后的补充说明、去空格。"""
    t = tok.strip()
    for ch in ("$", "`", "*"):
        t = t.replace(ch, "")
    t = t.split("<br/>")[0].split("<br>")[0]
    return t.replace(" ", "").strip()


def skeleton_tokens(lines):
    """从对象表 / 态射表抽取可作为节点名的记号集合。

    只取**第一列**（对象表的记号列、态射表的符号列）。第二列是中文名，
    若一并纳入词表，翻译图用「参数空间」这类中文名会被误判为「未翻译」。
    行表格式约定见 references/report-template.md：第一列必须是可用于
    Mermaid 节点命名的记号。
    """
    toks = set()
    for _lv, title, s, e in split_sections(lines):
        if any(k in title for k in OBJ_HEAD_KEYWORDS + MOR_HEAD_KEYWORDS):
            for row in table_data_rows(lines, s, e):
                if row:
                    t = norm(row[0])
                    if t:
                        toks.add(t)
    return toks


def mermaid_labels(lines, block):
    """取一个 Mermaid 块内的 (节点标签集合, 箭头标签集合)。"""
    nodes, edges = set(), set()
    for ln in lines[block[0] + 1:block[1]]:
        for m in MERMAID_EDGE_RE.finditer(ln):
            t = norm(m.group(1))
            if t:
                edges.add(t)
        stripped = MERMAID_EDGE_RE.sub(" ", ln)
        for m in MERMAID_NODE_RE.finditer(stripped):
            t = norm(m.group(1))
            if t:
                nodes.add(t)
    return nodes, edges


# ---------------------------------------------------------------- 单项检查

def count_restatement_sentences(lines):
    for _lv, title, s, e in split_sections(lines):
        if "范畴论重述" in title:
            n = 0
            for ln in lines[s:e]:
                if NUM_RE.match(ln):
                    n += 1
            return n, title
    return 0, None


def nearest_heading(lines, i):
    """向上找离第 i 行最近的标题行，返回标题文本（没有则空串）。"""
    for k in range(i - 1, -1, -1):
        m = HEAD_RE.match(lines[k])
        if m:
            return m.group(2).strip()
    return ""


def classify_block(lines, block):
    """按所在子标题判定图块类型：'orig' / 'trans' / None（无法判定）。"""
    title = nearest_heading(lines, block[0])
    if any(w in title for w in ORIG_HEAD_KEYS):
        return "orig", title
    if any(w in title for w in TRANS_HEAD_KEYS):
        return "trans", title
    return None, title


def check_diagrams(lines):
    """交换图章节：原图 + 通俗化翻译图 + 原图节点名须见于骨架表。

    图的存在与否只看 **Mermaid 代码块**，不看正文里有没有箭头或「翻译」二字。
    曾经的实现把「正文含 →」当成有原图、把「出现『翻译』且有一张任意表」当成
    有翻译图，导致一份通篇没有图的报告也能判通过（假阴性）。
    现在的规则：
      - 每个 Mermaid 块必须落在含「原图」或「翻译图」字样的子标题下；
      - 原图与翻译图必须交替出现且数量相等，每张原图紧接一张翻译图；
      - 原图的节点/箭头名必须全部见于骨架表第一列；
      - 翻译图的命名必须真的换成了骨架表之外的领域说法。
    """
    problems = []
    secs = split_sections(lines)
    blocks = mermaid_blocks(lines)
    toks = skeleton_tokens(lines)
    diag_secs = [(lv, t, s, e) for lv, t, s, e in secs
                 if any(k in t for k in DIAGRAM_HEAD_KEYWORDS)]

    if not diag_secs:
        return ["缺少交换图章节：需有独立的交换图章节，"
                "内含 ≥1 组 Mermaid 的「原图 + 通俗化翻译图」"], {"sections": 0}

    n_orig = n_trans = 0
    for _lv, title, s, e in diag_secs:
        sec_blocks = [b for b in blocks if s <= b[0] < e]
        if not sec_blocks:
            problems.append("交换图章节「%s」内没有任何 Mermaid 图："
                            "需 ≥1 组原图与通俗化翻译图，且各自写在带类型标注的"
                            "子标题下（如 ### x.1 原图、### x.2 翻译图）" % title)
            continue

        kinds = [classify_block(lines, b) for b in sec_blocks]
        seq = [k for k, _t in kinds]

        for idx, (kind, sec_title) in enumerate(kinds):
            if kind is None:
                problems.append(
                    "「%s」第 %d 张图无法判定类型：所在子标题「%s」不含"
                    "「原图」或「翻译图」字样，无法判断是否配对了翻译图"
                    % (title, idx + 1, sec_title or "(无子标题)"))
        n_o = seq.count("orig")
        n_t = seq.count("trans")
        n_orig += n_o
        n_trans += n_t

        if n_o == 0:
            problems.append("「%s」没有范畴论原图：需有写在含「原图」字样的"
                            "子标题下的 Mermaid 块" % title)
        # 数量不等这条不单独报：下面的逐张配对检查已覆盖它，重复报会让人
        # 以为是两个缺陷。
        for idx, kind in enumerate(seq):
            if kind == "orig" and (idx + 1 >= len(seq) or seq[idx + 1] != "trans"):
                problems.append("「%s」第 %d 张（原图）之后没有紧接通俗化翻译图"
                                % (title, idx + 1))
            if kind == "trans" and (idx == 0 or seq[idx - 1] != "orig"):
                problems.append("「%s」第 %d 张是翻译图，但前面没有对应的范畴论原图"
                                % (title, idx + 1))

        for idx, ((kind, _sec_title), b) in enumerate(zip(kinds, sec_blocks)):
            nodes, edges = mermaid_labels(lines, b)
            labels = nodes | edges
            if kind == "orig":
                if not labels:
                    problems.append("「%s」第 %d 张原图没有解析出节点/箭头标签："
                                    "节点须写成 A[\"名称\"]、箭头写成 -->|\"名称\"| 的形式"
                                    % (title, idx + 1))
                    continue
                unknown = sorted(t for t in labels if t not in toks)
                if unknown:
                    problems.append("「%s」第 %d 张原图的节点/箭头名未见于骨架表：%s。"
                                    "Mermaid 节点命名必须与对象表/态射表第一列一致"
                                    % (title, idx + 1, "、".join(unknown[:8])))
            if kind == "trans" and idx > 0 and seq[idx - 1] == "orig":
                prev_nodes, prev_edges = mermaid_labels(lines, sec_blocks[idx - 1])
                prev = prev_nodes | prev_edges
                if labels and labels <= toks:
                    problems.append("「%s」第 %d 张翻译图未做通俗化："
                                    "节点/箭头名仍全部出自骨架表，未换成领域说法"
                                    % (title, idx + 1))
                elif labels and prev and len(labels & prev) > len(labels) / 2:
                    problems.append("「%s」第 %d 张翻译图有 %d/%d 个标签与对应原图相同，"
                                    "未完成通俗化翻译"
                                    % (title, idx + 1, len(labels & prev), len(labels)))

    return problems, {"orig": n_orig, "trans": n_trans}


# ---------------------------------------------------------------- 主检查

def check_one(path):
    """返回 (问题列表, 统计字典)。"""
    problems = []
    stats = {}
    name = os.path.basename(path)
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()

    # 1) 轮次戳（取代原来的每轮时间戳）
    m = ROUND_FILE_RE.match(name)
    file_round = int(m.group(1)) if m else None
    stats["round"] = file_round
    if file_round is None:
        problems.append("文件名不是轮次戳格式 R<n>.md（不得再带每轮时间戳）")
    ms = ROUND_STAMP_RE.search(text)
    stamp_round = int(ms.group(1)) if ms else None
    stats["stamp"] = stamp_round
    if stamp_round is None:
        problems.append("报告内缺少「轮次」字段（需形如 - **轮次**：R1）")
    elif file_round is not None and stamp_round != file_round:
        problems.append("轮次戳不一致：文件名 R%d，报告内写 R%d"
                        % (file_round, stamp_round))

    for i, ln in enumerate(lines, 1):
        if TS_FIELD_RE.match(ln):
            problems.append("第 %d 行仍有每轮时间戳字段；每轮时间戳已移除，"
                            "时间信息统一落在运行目录名与 00_INDEX.md" % i)
            break

    # 2) 必备章节按标题判定（不能用全文子串，否则正文提一句也算通过）
    headings = [t for _, t, _, _ in split_sections(lines)]
    for _key, kws, human in REQUIRED_SECTION_KEYWORDS:
        if not any(any(k in h for k in kws) for h in headings):
            problems.append("缺少必备章节（需为标题）：%s" % human)

    # 3) 围栏配对
    fences = sum(1 for ln in lines if ln.strip().startswith("```"))
    if fences % 2 != 0:
        problems.append("代码围栏未配对（共 %d 个 ```，应为偶数）" % fences)

    # 4)+5) 交换图：原图 + 翻译图 + 节点命名
    dprob, dstats = check_diagrams(lines)
    problems.extend(dprob)
    stats["translation"] = "%d/%d" % (dstats.get("trans", 0), dstats.get("orig", 0))

    # 6) 重述句数
    n, _title = count_restatement_sentences(lines)
    stats["restatement_sentences"] = n
    if n < 3 or n > 5:
        problems.append("范畴论重述句数为 %d，要求是 3–5 句" % n)

    # 7) 表格数据行
    rows = count_table_data_rows(lines)
    stats["table_rows"] = rows
    if rows < 6:
        problems.append("表格数据行仅 %d 行，对象表与态射表疑似为空（要求 ≥6）" % rows)

    # 8) 显式性标注
    n_mark = len(MARK_RE.findall(text))
    stats["explicit_marks"] = n_mark
    if n_mark < 4:
        problems.append("显式性/置信度标注仅 %d 处，无法体现「原文显式 vs 重构」的区分（要求 ≥4）"
                        % n_mark)

    return problems, stats


def check_round_set(files, rounds):
    """轮次文件份数与编号连续性。"""
    problems = []
    nums = []
    for f in files:
        m = ROUND_FILE_RE.match(os.path.basename(f))
        if m:
            nums.append(int(m.group(1)))
        else:
            problems.append("存在非轮次戳命名的报告文件：%s（应为 R<n>.md）"
                            % os.path.basename(f))
    if len(nums) != rounds:
        problems.append("迭代报告份数为 %d，期望 %d 份（1 份基线 + %d 次迭代）"
                        % (len(nums), rounds, rounds - 1))
    if nums and sorted(set(nums)) != list(range(1, rounds + 1)):
        problems.append("轮次编号不连续：实际 %s，期望 R1..R%d"
                        % (sorted(set(nums)), rounds))
    return problems


def main():
    ap = argparse.ArgumentParser(description="报告交付门禁")
    ap.add_argument("--reports", default=None, help="报告目录")
    ap.add_argument("--run-dir", default=None,
                    help="运行目录（名为时间戳 YYYYMMDD-HHMMSS）；"
                         "给出且未给 --reports 时，报告目录取 <run-dir>/02_reports")
    ap.add_argument("--rounds", type=int, default=4,
                    help="期望的迭代报告份数（默认 4）")
    ap.add_argument("--require-index", action="store_true", default=True)
    args = ap.parse_args()

    reports = args.reports
    if args.run_dir and not reports:
        reports = os.path.join(args.run_dir, "02_reports")
    if not reports:
        print("[FATAL] 需给出 --reports 或 --run-dir", file=sys.stderr)
        return 2
    if not os.path.isdir(reports):
        print("[FATAL] 报告目录不存在：%s" % reports, file=sys.stderr)
        return 2

    print("=" * 78)
    print("报告门禁　目录=%s" % os.path.abspath(reports))
    if args.run_dir:
        print("运行目录=%s" % os.path.abspath(args.run_dir))
    print("=" * 78)

    all_problems = []

    # 运行目录名必须是时间戳——这是本轮唯一保留的时间信息
    if args.run_dir:
        base = os.path.basename(os.path.normpath(args.run_dir))
        if not RUN_DIR_RE.match(base):
            all_problems.append("运行目录名「%s」不是时间戳格式 YYYYMMDD-HHMMSS" % base)

    if args.require_index and not os.path.exists(os.path.join(reports, "00_INDEX.md")):
        all_problems.append("缺少 00_INDEX.md")

    files = sorted(glob.glob(os.path.join(reports, "R*.md")))
    all_problems.extend(check_round_set(files, args.rounds))

    for p in files:
        if not ROUND_FILE_RE.match(os.path.basename(p)):
            continue
        probs, st = check_one(p)
        flag = "PASS" if not probs else "FAIL"
        print("[%s] %-8s 轮次=R%-4s 表格行=%-3d 重述=%d 图(译/原)=%s 标注=%d"
              % (flag, os.path.basename(p), st.get("round"),
                 st.get("table_rows", 0), st.get("restatement_sentences", 0),
                 st.get("translation", "0/0"), st.get("explicit_marks", 0)))
        for q in probs:
            print("        ✗ %s" % q)
            all_problems.append("%s: %s" % (os.path.basename(p), q))

    print("-" * 78)
    if all_problems:
        print("未通过项 %d 条：" % len(all_problems))
        for q in all_problems:
            print("  - %s" % q)
        print("\n[结论] 门禁未通过，禁止交付。")
        return 1
    print("全部通过：%d 份报告，%d 条断言全部满足。" % (len(files), len(files) * 8 + 2))
    print("[结论] 门禁通过，可交付。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
