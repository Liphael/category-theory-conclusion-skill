#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""整包完整性校验（一次性，不随包交付）：frontmatter / JSON / YAML 结构 / 站内链接。"""
import os
import re
import io
import json
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bad = []
W = sys.stdout.write

# 1) frontmatter
s = io.open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8").read()
if not s.startswith("---"):
    bad.append("SKILL.md 无 frontmatter")
fm = s.split("---", 2)[1]
for k in ("name", "description"):
    if not re.search(r"^" + k + r":", fm, re.M):
        bad.append("frontmatter 缺 " + k)
m = re.search(r"^name:\s*(\S+)", fm, re.M)
W("name = %s\n" % (m.group(1) if m else "??"))
m = re.search(r"^description:\s*(.*)", fm, re.M)
W("description 长度 = %d 字符\n" % (len(m.group(1)) if m else 0))

# 2) manifest.json
try:
    json.load(io.open(os.path.join(ROOT, "manifest.json"), encoding="utf-8"))
    W("manifest.json 解析 OK\n")
except Exception as e:
    bad.append("manifest.json: %s" % e)

# 3) interface.yaml（无 PyYAML 时做结构抽查）
yp = os.path.join(ROOT, "agents", "interface.yaml")
y = io.open(yp, encoding="utf-8").read()
try:
    import yaml
    yaml.safe_load(y)
    W("interface.yaml 解析 OK\n")
except ImportError:
    for k in ("interface:", "display_name:", "compatibility:", "io_contract:", "gates:"):
        if k not in y:
            bad.append("interface.yaml 缺 " + k)
    W("interface.yaml 结构抽查 OK（PyYAML 未装）\n")
except Exception as e:
    bad.append("interface.yaml: %s" % e)

# 4) 站内链接
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
n = 0
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if not d.startswith(".")]
    for f in fn:
        if not f.endswith(".md"):
            continue
        p = os.path.join(dp, f)
        for _label, target in LINK.findall(io.open(p, encoding="utf-8").read()):
            if target.startswith(("http", "#", "mailto")):
                continue
            t = target.split("#")[0]
            if not t:
                continue
            n += 1
            if not os.path.exists(os.path.normpath(os.path.join(dp, t))):
                bad.append("死链 %s -> %s" % (os.path.relpath(p, ROOT), target))
W("检查站内链接 %d 条\n" % n)

# 5) 路由留出集：关键词覆盖率检查
#
# 只做「必要条件」检查，不做语义判定。理由：关键词能证明 description 的路由面
# 覆盖到某条请求，但证明不了语义上的正确排除（例如 B3「教我什么是伴随函子」
# 含「函子」却是教学请求）。把关键词命中当成语义判定会造成假可信，因此：
#   A 组（应命中）覆盖率 < 1  → 记问题：description 路由面有缺口，必改
#   B 组（不应命中）覆盖率 ≥ 1 → 仅提示：需人工确认排除项是否写得够强
TRIGGER_TOKENS = [
    "范畴论", "范畴化", "范畴", "对象表", "态射表", "交换图", "信息缺失",
    "函子", "自然变换", "单子", "伴随", "极限", "Yoneda",
    "五步模型", "迭代", "时间戳",
    "category theory", "categorical", "object table", "morphism",
]
CASE_RE = re.compile(r"^\|\s*(A|B)(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", re.M)
hp = os.path.join(ROOT, "evals", "route-holdout.md")
if os.path.exists(hp):
    rows = CASE_RE.findall(io.open(hp, encoding="utf-8").read())
    W("\n路由留出集 %d 条：\n" % len(rows))
    # 解析出 0 条必须报错：否则表格格式一改，这里会静默报「无问题」（假阴性）。
    if not rows:
        bad.append("路由留出集解析出 0 条用例，解析器或表格格式已失效，"
                   "不得据此判定路由无问题")
    for grp, _idx, query, expect in rows:
        hit = [t for t in TRIGGER_TOKENS if t in query]
        if grp == "A" and not hit:
            bad.append("路由缺口：应命中用例「%s」未匹配任何触发词" % query)
            W("  [问题] A「%s」无任何触发词命中\n" % query)
        elif grp == "B" and hit:
            W("  [提示] B「%s」命中 %s，需人工确认排除项足以挡住\n"
              % (query, "/".join(hit)))
    W("  A 组缺口 %d 条（应为 0）；B 组提示 %d 条（需人工确认）\n"
      % (sum(1 for b in bad if b.startswith("路由缺口")),
         sum(1 for g, _i, q, _e in rows
             if g == "B" and any(t in q for t in TRIGGER_TOKENS))))
else:
    bad.append("缺少 evals/route-holdout.md")

W("\n")
if bad:
    W("问题 %d 条：\n" % len(bad))
    for b in bad:
        W("  - %s\n" % b)
else:
    W("无问题\n")
sys.exit(1 if bad else 0)
