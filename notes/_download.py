# -*- coding: utf-8 -*-
"""
下载参考论文到 papers/ 目录。
- arXiv 条目：https://arxiv.org/pdf/<id>  （先经 API 取正式标题用于文件名）
- 非 arXiv 条目：直接 URL 尝试
- 结果写入 _download_manifest.csv 与 00_下载清单与状态.md
"""
import os, re, csv, time, subprocess, xml.etree.ElementTree as ET, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "papers")
os.makedirs(OUT, exist_ok=True)

API = "https://export.arxiv.org/api/query"


def curl(url, dest=None, timeout=90):
    cmd = ["curl", "-sSL", "-m", str(timeout), "--retry", "2", "--retry-delay", "3",
           "-A", "Mozilla/5.0 (compatible; rct-ref-downloader/1.0)",
           "-w", "%{http_code}|%{content_type}|%{size_download}",
           "-o", dest if dest else "-", url]
    p = subprocess.run(cmd, capture_output=True)
    meta = p.stdout if dest else b""
    try:
        head, body = (meta.decode("utf-8", "ignore"), p.stdout)
        if dest:
            return head, b""
        return head, body
    except Exception:
        return "", b""


def fetch_bytes(url, timeout=90):
    p = subprocess.run(["curl", "-sSL", "-m", str(timeout), "--retry", "2", "--retry-delay", "3",
                        "-A", "Mozilla/5.0 (compatible; rct-ref-downloader/1.0)", url],
                       capture_output=True)
    return p.stdout


def ns(t):
    return "{http://www.w3.org/2005/Atom}" + t


def arxiv_meta(aid):
    q = urllib.parse.urlencode({"id_list": aid, "max_results": 1})
    try:
        root = ET.fromstring(fetch_bytes(API + "?" + q))
        e = root.find(ns("entry"))
        if e is None:
            return None
        title = " ".join(e.find(ns("title")).text.split())
        pub = e.find(ns("published"))
        return title, (pub.text[:10] if pub is not None else "")
    except Exception:
        return None


def slug(s, n=48):
    s = re.sub(r"[^A-Za-z0-9]+", "", s)
    return s[:n]


def is_pdf(path):
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except Exception:
        return False


# ---------------------------------------------------------------- 清单
# (ref, source_kind, locator, note)
ARXIV = [
    ("ref06000001", "2405.07987"),
    ("ref06000002", "2512.03750"),
    ("ref06000003", "2210.00482"),
    ("ref06000004", "2305.18063"),
    ("ref06000005", "2007.04612"),
    ("ref06000006", "1711.11279"),
    ("ref06000007", "1902.03129"),
    ("ref06000008", "2205.15480"),
    ("ref06000009", "2209.09056"),
    ("ref06000010", "2105.04289"),
    ("ref06000013", "2309.08600"),
    ("ref06000015", "2512.10805"),
    ("ref06000016a", "2512.02004"),
    ("ref06000016b", "2512.07355"),
    ("ref06000020", "2010.02855"),
    ("ref06000021", "2202.04753"),
    ("ref07000001", "1102.1889"),
    ("ref07000006", "2602.18033"),
    ("ref07000007", "2602.17160"),
    ("ref07000009", "1810.08074"),
    ("ref07000010", "1009.1166"),
    ("ref07000011", "1212.5303"),
    ("ref07000012", "1503.03571"),
    ("ref07000013", "1706.00526"),
    ("ref07000014", "2403.19884"),
    ("ref07000015", "1603.01446"),
    ("ref07000017", "2603.05685"),
]

DIRECT = [
    ("ref07000005", "https://oliviacaramello.com/Talks/OntologiesAndToposes.pdf",
     "Caramello-Lafforgue 演讲稿 PDF"),
    ("ref06000011", "https://transformer-circuits.pub/2022/toy_model/index.html",
     "Anthropic 网页（无官方 PDF）"),
    ("ref06000012", "https://transformer-circuits.pub/2023/monosemantic-features/index.html",
     "Anthropic 网页（无官方 PDF）"),
    ("ref06000014", "https://transformer-circuits.pub/2024/scaling-monosemanticity/index.html",
     "Anthropic 网页（无官方 PDF）"),
    ("ref06000017", "https://api.elsevier.com/content/article/doi/10.1016/j.neucom.2025.131269",
     "Elsevier API，无 key 预期失败"),
    ("ref06000019", "https://www.cell.com/patterns/pdf/S2666-3899(23)00106-X.pdf",
     "Cell Press Patterns 开放获取尝试"),
    ("ref07000008", "https://dl.acm.org/doi/10.1145/151646.151651", "ACM 付费墙，预期失败"),
    ("ref07000019", "https://ncatlab.org/nlab/show/ontology+log", "nLab 条目页"),
    ("ref07000020", "https://raw.githubusercontent.com/DavidJaz/DynamicalSystemsBook/master/book.pdf",
     "Myers 书稿 PDF（GitHub）"),
]

rows = []


def record(ref, status, path, url, title, note=""):
    rows.append([ref, status, os.path.basename(path) if path else "", url, title, note])
    print("%-14s %-12s %s" % (ref, status, title[:70]))


print("=" * 100)
print("A. arXiv 批量下载")
print("=" * 100)
for ref, aid in ARXIV:
    meta = arxiv_meta(aid)
    time.sleep(3)
    title = meta[0] if meta else aid
    fn = "%s_%s_%s.pdf" % (ref, aid.replace(".", ""), slug(title))
    dest = os.path.join(OUT, fn)
    if os.path.exists(dest) and is_pdf(dest):
        record(ref, "已存在", dest, "https://arxiv.org/abs/" + aid, title)
        continue
    url = "https://arxiv.org/pdf/" + aid
    head, _ = curl(url, dest)
    code = head.split("|")[0]
    time.sleep(1)
    if os.path.exists(dest) and is_pdf(dest):
        record(ref, "OK", dest, url, title)
    else:
        if os.path.exists(dest):
            os.remove(dest)
        record(ref, "失败(%s)" % code, None, url, title, "非 PDF 内容，可能需浏览器访问")

print()
print("=" * 100)
print("B. 非 arXiv 直接下载")
print("=" * 100)
for ref, url, note in DIRECT:
    base = "%s_%s" % (ref, slug(note.split("（")[0], 40) or "doc")
    dest = os.path.join(OUT, base + ".pdf")
    head, _ = curl(url, dest)
    code, ctype, size = (head.split("|") + ["", "", ""])[:3]
    if os.path.exists(dest) and is_pdf(dest):
        record(ref, "OK", dest, url, note)
        continue
    # 不是 PDF 但可能拿到 HTML
    if os.path.exists(dest) and int(size or 0) > 500:
        html_dest = dest[:-4] + ".html"
        os.replace(dest, html_dest)
        record(ref, "仅网页", html_dest, url, note, "HTTP %s %s" % (code, ctype))
    else:
        if os.path.exists(dest):
            os.remove(dest)
        record(ref, "失败(%s)" % code, None, url, note)

with open(os.path.join(HERE, "_download_manifest.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["编号", "状态", "文件", "来源URL", "标题/说明", "备注"])
    w.writerows(rows)

ok = sum(1 for r in rows if r[1] in ("OK", "已存在"))
print()
print("完成：共 %d 项，成功 %d 项" % (len(rows), ok))
