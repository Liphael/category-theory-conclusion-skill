#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_markdown.py —— 材料统一转 Markdown 并双归档（范畴论总结技能 · 步骤 0）

职责：把输入目录里任意受支持格式的材料，统一转成 .md 用于后续总结；
      源文件与转换后文件分别归档，互不混杂。

归档结构（--archive 下按运行时间戳建子目录）：
    <archive>/<YYYYMMDD-HHMMSS>/
        00_source/                 源文件副本（保留相对目录结构，绝不改动）
        01_markdown/               统一后的 .md（后续步骤的唯一输入）
        manifest_conversion.json   逐文件转换台账

设计红线（不可违反）：
  1. 不静默丢弃：转换失败 / 产物为空 / 格式不支持，都必须写进台账并在摘要列出，退出码非 0。
  2. 不改源文件：对 00_source 只做复制，转换产物一律另写到 01_markdown。
  3. 不猜测内容：只做格式转换，不改写、不摘要、不补全。
  4. 运行 ID 用系统时钟取，不编造、不复用。

用法：
  python convert_markdown.py --input materials --archive runs
  python convert_markdown.py --input materials --archive runs --run-id 20261012-142200
  python convert_markdown.py --input materials --archive runs --recursive --min-chars 20

退出码：
  0 = 全部转换成功（有文件低于 --min-chars 会告警但仍是 0）
  1 = 存在 empty / unsupported / error 状态的文件（门禁应判失败）
  2 = 参数错误，或 markitdown 不可用
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from extract_text import KNOWN_BUT_UNSUPPORTED, ENCODINGS
except Exception:  # extract_text.py 不在同目录时退化为空表，仍可运行
    KNOWN_BUT_UNSUPPORTED = {}
    ENCODINGS = ("utf-8-sig", "utf-8", "gb18030", "latin-1")

# 本身就是文本，无需调用 markitdown，直接复制为 .md
PASSTHROUGH_EXTS = {".md", ".markdown", ".txt"}
CONVERT_TIMEOUT = 300  # 单文件转换超时（秒），避免大文件把流程挂死


def run_id_now():
    """运行 ID 取系统时钟，格式 YYYYMMDD-HHMMSS。"""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def check_markitdown():
    """确认 markitdown 可用；不可用则给出明确安装命令。"""
    try:
        p = subprocess.run([sys.executable, "-m", "markitdown", "--help"],
                           capture_output=True, timeout=60)
        return p.returncode == 0 or b"markitdown" in (p.stdout + p.stderr).lower()
    except Exception:
        return False


def iter_files(root, recursive):
    """遍历待转换文件。非递归只看一层；跳过隐藏文件与目录。"""
    if recursive:
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if not d.startswith(".")]
            for f in fn:
                if f.startswith("."):
                    continue
                yield os.path.join(dp, f)
    else:
        for f in sorted(os.listdir(root)):
            p = os.path.join(root, f)
            if os.path.isfile(p) and not f.startswith("."):
                yield p


def convert_one(src, dst, ext):
    """转换单个文件。返回 (状态, 字符数, 警告列表)。

    状态：ok / empty / error
    """
    warnings = []
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    if ext.lower() in PASSTHROUGH_EXTS:
        shutil.copy2(src, dst)
        converter = "copy"
    else:
        converter = "markitdown"
        try:
            p = subprocess.run([sys.executable, "-m", "markitdown", src, "-o", dst],
                               capture_output=True, timeout=CONVERT_TIMEOUT)
        except subprocess.TimeoutExpired:
            return "error", 0, ["转换超时（>%d 秒）" % CONVERT_TIMEOUT]
        if p.returncode != 0:
            msg = (p.stderr or p.stdout or b"").decode("utf-8", "replace").strip()
            return "error", 0, ["markitdown 退出码 %d：%s" % (p.returncode, msg[:200])]
        if not os.path.exists(dst):
            return "error", 0, ["markitdown 未生成输出文件"]

    if not os.path.exists(dst):
        return "error", 0, ["输出文件不存在"]

    raw = open(dst, "rb").read()
    text = ""
    for enc in ENCODINGS:
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    chars = len(text.strip())
    if chars == 0:
        # 空产物必须给出可读原因，否则台账里出现「状态 empty 但备注为空」，
        # 使用者无从判断该怎么处置（这是信息缺失，不是干净通过）。
        warnings.append("转换后正文为空（疑似扫描件/图片页、空文件，"
                        "或该格式 markitdown 未能抽出文本），需 OCR 或人工确认")
    return ("ok" if chars > 0 else "empty"), chars, warnings


def main():
    ap = argparse.ArgumentParser(description="材料统一转 Markdown 并双归档")
    ap.add_argument("--input", required=True, help="材料目录")
    ap.add_argument("--archive", default="runs", help="归档根目录（其下按运行 ID 建子目录）")
    ap.add_argument("--run-id", default=None,
                    help="运行 ID，缺省取系统时钟 YYYYMMDD-HHMMSS")
    ap.add_argument("--min-chars", type=int, default=20, help="低于此字符数告警")
    ap.add_argument("--recursive", action="store_true", help="递归扫描子目录")
    args = ap.parse_args()

    if not os.path.isdir(args.input):
        print("[FATAL] 输入目录不存在：%s" % args.input, file=sys.stderr)
        return 2

    run_id = args.run_id or run_id_now()
    run_dir = os.path.join(args.archive, run_id)
    src_dir = os.path.join(run_dir, "00_source")
    md_dir = os.path.join(run_dir, "01_markdown")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(md_dir, exist_ok=True)

    files = list(iter_files(args.input, args.recursive))
    need_md = any(os.path.splitext(f)[1].lower() not in PASSTHROUGH_EXTS for f in files)
    if need_md and not check_markitdown():
        print("[FATAL] markitdown 不可用。安装："
              '%s -m pip install "markitdown[pdf,docx,pptx,xlsx]"' % sys.executable,
              file=sys.stderr)
        return 2

    print("=" * 78)
    print("Markdown 转换归档　输入=%s" % os.path.abspath(args.input))
    print("运行目录=%s" % os.path.abspath(run_dir))
    print("=" * 78)
    print("%-34s %-8s %-10s %8s  %s" % ("文件", "原格式", "状态", "字符数", "备注"))
    print("-" * 78)

    records = []
    for src in files:
        rel = os.path.relpath(src, args.input)
        ext = os.path.splitext(src)[1].lower()
        stem = os.path.splitext(os.path.basename(src))[0]
        md_rel = os.path.splitext(rel)[0] + ".md"

        # 同名冲突：不同源文件可能转成同名 .md（a.pdf 与 a.docx），加序号区分
        md_path = os.path.join(md_dir, md_rel)
        n = 1
        while os.path.exists(md_path):
            n += 1
            md_path = os.path.join(md_dir, os.path.splitext(rel)[0] + "__%d.md" % n)

        dst_src = os.path.join(src_dir, rel)
        os.makedirs(os.path.dirname(dst_src), exist_ok=True)

        if ext in KNOWN_BUT_UNSUPPORTED:
            shutil.copy2(src, dst_src)
            rec = {"source": os.path.abspath(src), "source_rel": rel,
                   "archived_source": os.path.relpath(dst_src, run_dir),
                   "markdown": None, "converter": None, "ext": ext,
                   "status": "unsupported", "chars": 0,
                   "warnings": [KNOWN_BUT_UNSUPPORTED[ext]]}
            records.append(rec)
            print("%-34s %-8s %-10s %8d  %s"
                  % (rel[:34], ext, "unsupported", 0, KNOWN_BUT_UNSUPPORTED[ext]))
            continue

        shutil.copy2(src, dst_src)
        status, chars, warn = convert_one(src, md_path, ext)
        if 0 < chars < args.min_chars:
            warn.append("转换后字符数 %d 低于阈值 %d，内容可能不完整" % (chars, args.min_chars))
        rec = {"source": os.path.abspath(src), "source_rel": rel,
               "archived_source": os.path.relpath(dst_src, run_dir),
               "markdown": os.path.relpath(md_path, run_dir),
               "converter": ("copy" if ext in PASSTHROUGH_EXTS else "markitdown"),
               "ext": ext, "status": status, "chars": chars, "warnings": warn}
        records.append(rec)
        print("%-34s %-8s %-10s %8d  %s"
              % (rel[:34], ext, status, chars, "；".join(warn)[:40]))

    bad = [r for r in records if r["status"] != "ok"]
    manifest = {"run_id": run_id,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "input": os.path.abspath(args.input),
                "run_dir": os.path.abspath(run_dir),
                "source_dir": "00_source",
                "markdown_dir": "01_markdown",
                "total": len(records),
                "ok": len(records) - len(bad),
                "failed": len(bad),
                "files": records}
    mp = os.path.join(run_dir, "manifest_conversion.json")
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("-" * 78)
    print("合计 %d 个文件：成功 %d，可疑/失败 %d" % (len(records), len(records) - len(bad), len(bad)))
    print("源文件归档：%s" % os.path.abspath(src_dir))
    print("统一 Markdown：%s" % os.path.abspath(md_dir))
    print("台账：%s" % mp)

    if bad:
        print("\n[需要处置] 以下文件未成功转换，必须先处置再进入下一步：")
        for r in bad:
            print("  - %s (%s)：%s"
                  % (r["source_rel"], r["status"], "；".join(r["warnings"])[:120]))
        return 1

    print("\n[RUN_DIR] %s" % os.path.abspath(run_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
