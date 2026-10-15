#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「对照实现」，用来证明探测用例不是摆设（开发期专用）。

十五条探测全绿本身不能说明检查起了作用——也可能只是用例写得太松、
检查器换成什么都不拒也照样全绿。所以每加一条期望通过的用例，都要问：
**它在哪个被否掉的实现下会失败？** 答不上来，这条用例就是摆设。

本脚本把 `check_reports.py` 按两种被否掉的取词方案各抄一份，
再拿探测用例去跑，看它是不是真的会红。

用法：
    python scripts/_make_control_impls.py --out .selftest/old
    # 产出 check_ctrl_a.py（对照 A）与 check_ctrl_b.py（对照 B）
    python .selftest/old/check_ctrl_a.py --reports .selftest/probe/probe__vocab_adjunction_ok --rounds 1
    echo $?    # 期望 1：说明该用例守的是真实存在的假阳性

对照 A：词表只认对象表与态射表的第一列（本次修改前的实现）。
对照 B：词表覆盖全部骨架表，但**无条件纳入第一列**（曾考虑、已否掉的方案）。
"""
import argparse
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "check_reports.py")

CTRL_A_SECTIONS = ('SKELETON_SECTIONS = (("对象表", OBJ_HEAD_KEYWORDS),\n'
                   '                     ("态射表", MOR_HEAD_KEYWORDS))')


def build_ctrl_a(text):
    """对照 A：退化到只认对象表/态射表，且只取第一列。"""
    out = re.sub(r"SKELETON_SECTIONS = \(.*?\n\)", CTRL_A_SECTIONS,
                 text, flags=re.S)
    assert out != text, "对照 A：SKELETON_SECTIONS 替换失败，源码结构可能已变"
    key = "if t and not CJK_RE.search(t):"
    assert key in out, "对照 A：取词规则行没找到，源码结构可能已变"
    out = out.replace(key, "if t and ci == 0:")
    out = _enumerate_cells(out)
    return out


def build_ctrl_b(text):
    """对照 B：全骨架表 + 无条件纳入第一列。"""
    key = "if t and not CJK_RE.search(t):"
    assert key in text, "对照 B：取词规则行没找到，源码结构可能已变"
    out = text.replace(key, "if t and (ci == 0 or not CJK_RE.search(t)):")
    return _enumerate_cells(out)


def _enumerate_cells(text):
    """把 `for cell in row:` 改成 `for ci, cell in enumerate(row):`。"""
    old = "                for cell in row:"
    assert old in text, "取词循环行没找到，源码缩进可能已变"
    return text.replace(old, "                for ci, cell in enumerate(row):")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="对照实现输出目录")
    a = ap.parse_args()

    base = open(SRC, encoding="utf-8").read()
    os.makedirs(a.out, exist_ok=True)
    for name, fn in (("check_ctrl_a.py", build_ctrl_a),
                     ("check_ctrl_b.py", build_ctrl_b)):
        p = os.path.join(a.out, name)
        open(p, "w", encoding="utf-8").write(fn(base))
        print("  已生成 %s" % p)
    print("")
    print("  拿探测用例去跑，看对照实现是否真的会红：")
    print("    python %s --reports <probe>/probe__vocab_adjunction_ok --rounds 1"
          % os.path.join(a.out, "check_ctrl_a.py"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
