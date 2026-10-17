# -*- coding: utf-8 -*-
"""按标题查询 arXiv API，解析/核对论文编号。只读查询，不下载。"""
import urllib.request, urllib.parse, xml.etree.ElementTree as ET, time, sys

API = "https://export.arxiv.org/api/query"

QUERIES = [
    ("ref06000004", "Vector-based Representation is the Key: A Study on Disentanglement and Compositional Generalization"),
    ("ref06000005", "Concept Bottleneck Models"),
    ("ref06000009", "Concept Embedding Models: Beyond the Accuracy-Explainability Trade-Off"),
    ("ref06000010", "Do Concept Bottleneck Models Learn as Intended?"),
    ("ref06000015", "Interpretable and Steerable Concept Bottleneck Sparse Autoencoders"),
    ("ref06000016a", "AlignSAE Concept-Aligned Sparse Autoencoders"),
    ("ref06000016b", "A Geometric Unification of Concept Learning with Concept Cones"),
    ("ref06000018", "Towards Data- and Knowledge-Driven AI: A Survey on Neurosymbolic Computing"),
    ("ref06000019", "Methods for identifying emergent concepts in deep neural networks"),
    ("ref07000006", "On the Category-Theoretic Independence of Meaning, Object, Name and Existence"),
    ("ref07000007", "Grothendieck's Geometric Universes and a Sheaf-Theoretic Foundation of Information Network"),
    ("ref07000012", "Algebraic Data Integration"),
    ("ref07000017", "From Line Knowledge Digraphs to Sheaf Semantics: A Categorical Framework for Knowledge Graphs"),
    ("ref07000018", "Whitehead's Category of the Ultimate as Lawvere's Topos in Category Theory"),
]

# 需要核对的既有编号
VERIFY = [
    "2405.07987", "2512.03750", "2210.00482", "2205.15480", "2512.10805",
    "2010.02855", "2202.04753", "1102.1889", "2602.18033", "2602.17160",
    "1810.08074", "1009.1166", "1212.5303", "1706.00526", "2403.19884",
    "1603.01446", "2603.05685", "2309.08600",
]


def fetch(url):
    """经 curl 抓取（本机 Python 的 CA 校验在此网络环境不可用，curl 正常）。"""
    import subprocess
    p = subprocess.run(
        ["curl", "-sSL", "-m", "60", "--retry", "2", "--retry-delay", "2",
         "-A", "rct-ref-downloader/1.0", url],
        capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("curl fail %d: %s" % (p.returncode, p.stderr[:200].decode("utf-8", "ignore")))
    return p.stdout


def ns(tag):
    return "{http://www.w3.org/2005/Atom}" + tag


def search(title, n=3):
    q = urllib.parse.urlencode({"search_query": 'ti:"%s"' % title, "start": 0, "max_results": n})
    raw = fetch(API + "?" + q)
    root = ET.fromstring(raw)
    out = []
    for e in root.findall(ns("entry")):
        aid = e.find(ns("id")).text.strip()
        t = " ".join(e.find(ns("title")).text.split())
        pub = e.find(ns("published"))
        out.append((aid.rsplit("/", 1)[-1], t, pub.text[:10] if pub is not None else "?"))
    return out


def verify(aid):
    q = urllib.parse.urlencode({"id_list": aid, "max_results": 1})
    try:
        raw = fetch(API + "?" + q)
    except Exception as ex:
        return ("ERROR", str(ex))
    root = ET.fromstring(raw)
    e = root.find(ns("entry"))
    if e is None:
        return ("NOT_FOUND", "")
    t = " ".join(e.find(ns("title")).text.split())
    pub = e.find(ns("published"))
    return ("OK", "%s | %s" % (t, pub.text[:10] if pub is not None else "?"))


print("=" * 90)
print("A. 按标题解析编号")
print("=" * 90)
for rid, title in QUERIES:
    try:
        res = search(title)
    except Exception as ex:
        print("[%s] QUERY-FAIL %s" % (rid, ex))
        time.sleep(3)
        continue
    print("[%s] %s" % (rid, title[:70]))
    for aid, t, d in res:
        print("     -> %s  (%s)  %s" % (aid, d, t[:95]))
    print()
    time.sleep(3)

print("=" * 90)
print("B. 核对既有编号")
print("=" * 90)
for aid in VERIFY:
    st, info = verify(aid)
    print("%-12s %-10s %s" % (aid, st, info[:110]))
    time.sleep(3)
