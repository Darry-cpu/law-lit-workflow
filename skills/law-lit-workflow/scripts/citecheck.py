"""按《中文引注规则（简化版）》核对论文脚注，输出逐项问题清单。

用法::

    python citecheck.py 论文.md --style plan/引注体例_期刊要求.md

检查项（对应体例条款）：
  A 略写：稿件不得使用「前注X」式略写（一·6·3）
  B 重复引用超过 3 次（一·6·1）
  C 概括引用未标「参见」（一·4·1）
  D 直引字词的注号位置：应紧接引号、置于其他标点之前（一·3）
  E 连续页码应用短横线「-」而非「—」（二·(一)·5·3）
  F 阿拉伯数字与汉字之间不应有空格（体例全部示例均无空格）
  G 外籍作者姓名前应加方括号注明国籍（二·(一)·2·7）
  H 集刊（连续出版物）应标主编与出版社（二·(一)·4·3）
"""

import argparse
import pathlib
import re
from collections import Counter, defaultdict

MARK = re.compile(r"\[\^(\d+)\]")
DEF = re.compile(r"^\[\^(\d+)\]:\s*(.+)$", re.M)
CJK = r"\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef"
# 汉字或全角标点紧邻阿拉伯数字
SPACE_AROUND_NUM = re.compile(rf"([{CJK}])\s+(\d)|(\d)\s+([{CJK}])")
ABBREV = re.compile(r"前注|同前注")


def parse_footnote(text):
    info = {"raw": text, "abbrev": bool(ABBREV.search(text)), "see": text.startswith("参见")}
    # 作者：取「：」前
    m = re.match(r"^(?:参见)?(.+?)：", text)
    info["author"] = m.group(1) if m else ""
    # 页码
    pages = re.findall(r"第\s*([\d、\-—－]+)\s*页", text)
    info["pages"] = pages
    info["em_dash_page"] = any("—" in p for p in pages)
    # 来源标识：完整引用取书名号内的刊名，略写取「X文」
    j = re.search(r"载《([^》]+)》", text)
    info["journal"] = j.group(1) if j else ""
    a = re.search(r"([\u4e00-\u9fa5]{2,4}(?:等)?)文", text)
    info["abbrev_key"] = a.group(1) if a else ""
    info["foreign_no_nation"] = bool(
        re.search(r"(?:^|、)(?:伦纳德|凯文|约翰|迈克尔|玛丽|威廉|罗伯特|查尔斯|托马斯)", text)
    ) and not text.lstrip("参见").startswith("[")
    info["serial"] = ("论丛" in (info["journal"] or "")) or ("辑" in text)
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    a = ap.parse_args()
    text = pathlib.Path(a.md).read_text(encoding="utf-8")
    body, defs_raw = text.split("\n## 脚注", 1)
    defs = {int(k): v.strip() for k, v in DEF.findall(defs_raw)}

    # 正文中标记的上下文
    ctx = {}
    for m in MARK.finditer(body):
        cid = int(m.group(1))
        before = body[max(0, m.start() - 40):m.start()]
        ctx[cid] = before

    # 体例一·3：句中字词直引的注号应紧接引号、置于其他标点之前。
    # 故违规情形是——注号之前是句读，而句读之前紧接着右引号。
    # 注意：注号之后跟句读是正确写法，不可反过来判为违规。
    direct_ids, pos_issue = set(), []
    for cid, before in ctx.items():
        b = before.rstrip()
        if not b:
            continue
        if b[-1] in "”」":
            direct_ids.add(cid)          # 位置正确：紧跟引号
        elif b[-1] in "。，、；：」" and ("”" in b[-4:] or "」" in b[-4:]):
            pos_issue.append(cid)        # 引号后夹了句读，注号应前移
    # 若注号附近出现过引号，视为该注释含直引，按体例不加「参见」
    for cid, before in ctx.items():
        if cid in direct_ids or cid in pos_issue:
            continue
        if "”" in before or "」" in before:
            direct_ids.add(cid)

    # 每篇文献被引次数：必须按「作者＋刊名」聚合。同一刊物可能刊载本文引用的
    # 多篇不同文章（如《青年研究》既有沈纪等文，也有谈子敏等文），按刊名聚合会
    # 把两篇各 3 次误报成一篇 6 次。
    counter = Counter()
    for cid, t in defs.items():
        k = parse_footnote(t)
        author = (k["author"] or "").replace("参见", "")
        counter[f"{author}·{k['journal']}" if k["journal"] else (k["abbrev_key"] or t[:8])] += 1

    print("=" * 66)
    print("A. 略写脚注（体例一·6·3：投稿时不采用略写）")
    ab = [c for c, t in defs.items() if parse_footnote(t)["abbrev"]]
    print(f"   {len(ab)} / {len(defs)} 条为略写：{sorted(ab)}")

    print("\nB. 同一文献重复引用次数（体例一·6·1：原则上不超过 3 次）")
    for k, v in counter.most_common():
        flag = "  ← 超限" if v > 3 else ""
        print(f"   {k:<22} {v} 次{flag}")

    print("\nC. 概括引用未加「参见」（体例一·4·1）")
    should_see = [c for c in defs if c not in direct_ids]
    missing_see = [c for c in should_see if not defs[c].startswith("参见")]
    print(f"   非直引 {len(should_see)} 条，其中未加「参见」{len(missing_see)} 条：{sorted(missing_see)}")

    print("\nD. 直引字词的注号位置（体例一·3：应紧接引号、置于标点之前）")
    print(f"   直引 {len(direct_ids)} 条，注号置于句读之后 {len(pos_issue)} 条：{sorted(pos_issue)}")

    print("\nE. 连续页码用短横线（体例二·(一)·5·3）")
    em = [c for c, t in defs.items() if parse_footnote(t)["em_dash_page"]]
    print(f"   使用破折号「—」的 {len(em)} 条：{sorted(em)}")

    print("\nF. 阿拉伯数字与汉字之间的多余空格（体例示例均无空格）")
    n = len(SPACE_AROUND_NUM.findall(body))
    print(f"   正文命中 {n} 处；脚注中另有 "
          f"{sum(len(SPACE_AROUND_NUM.findall(t)) for t in defs.values())} 处")
    ex = [m.group(0) for m in SPACE_AROUND_NUM.finditer(body)][:6]
    print(f"   正文示例：{ex}")

    print("\nG. 外籍作者国籍标注（体例二·(一)·2·7）")
    fg = [c for c, t in defs.items() if parse_footnote(t)["foreign_no_nation"]]
    print(f"   疑似缺国籍标注：{sorted(fg)}")
    for c in fg:
        print(f"     [{c}] {defs[c][:70]}")

    print("\nH. 集刊／连续出版物的出版信息（体例二·(一)·4·3）")
    for c, t in defs.items():
        k = parse_footnote(t)
        if k["serial"]:
            has_pub = "出版社" in t or "年版" in t
            print(f"   第{c}条 需标主编与出版社：{'已含出版信息' if has_pub else '缺出版信息'}｜{t[:78]}")

    print("\n" + "=" * 66)
    print("I. 完全重复的脚注（正文相邻位置内容一字不差）")
    seen = defaultdict(list)
    for c, t in defs.items():
        seen[t].append(c)
    for t, cs in seen.items():
        if len(cs) > 1:
            print(f"   {cs} -> {t[:70]}")


if __name__ == "__main__":
    main()
