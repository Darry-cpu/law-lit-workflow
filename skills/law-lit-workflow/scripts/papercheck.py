"""核对论文 Markdown 的硬性指标：正文字数、摘要长度、脚注编号闭环。

用法::

    python papercheck.py 论文.md

为什么需要它：字数下限、摘要上限、脚注数量与编号连续性都是硬性要求，
目测不可靠；编号一旦断号，转成 Word 脚注就会错位。
"""

import argparse
import pathlib
import re
import sys

MARK = re.compile(r"\[\^(\d+)\]")
DEF = re.compile(r"^\[\^(\d+)\]:\s*(.+)$", re.M)
HAN = re.compile(r"[\u4e00-\u9fa5]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    a = ap.parse_args()
    text = pathlib.Path(a.md).read_text(encoding="utf-8")

    # 脚注定义区与正文分开
    if "\n## 脚注" in text:
        body, defs_raw = text.split("\n## 脚注", 1)
    else:
        body, defs_raw = text, ""

    defs = {int(k): v for k, v in DEF.findall(defs_raw)}
    markers = MARK.findall(body)
    nums = [int(n) for n in markers]

    # 摘要
    m = re.search(r"\*\*摘要\*\*：(.+)", body)
    abstract = m.group(1).strip() if m else ""
    kw = re.search(r"\*\*关键词\*\*：(.+)", body)
    keywords = kw.group(1).strip() if kw else ""

    # 正文汉字数：去掉一级标题行、摘要与关键词段
    lines = body.splitlines()
    keep = []
    for line in lines:
        s = line.strip()
        if s.startswith("# "):
            continue
        if s.startswith("**摘要**") or s.startswith("**关键词**"):
            continue
        if s == "---":
            continue
        keep.append(line)
    body_text = "\n".join(keep)
    han = len(HAN.findall(body_text))

    print(f"正文汉字数（不含标题/摘要/关键词/脚注）：{han}")
    print(f"摘要长度（含标点，按字符计）：{len(abstract)}  要求 ≤300  {'OK' if len(abstract) <= 300 else '超限'}")
    print(f"关键词：{keywords}  （{len(re.split(r'[；;]', keywords))} 个）")
    print(f"脚注标记数（正文中）：{len(nums)}")
    print(f"脚注定义数：{len(defs)}")

    problems = []
    if len(set(nums)) != len(nums):
        dup = sorted({n for n in nums if nums.count(n) > 1})
        problems.append(f"重复引用的编号：{dup}")
    if nums != sorted(nums):
        problems.append("正文中脚注编号未按升序出现")
    missing_def = [n for n in nums if n not in defs]
    if missing_def:
        problems.append(f"有标记但无定义：{missing_def}")
    orphan = [k for k in defs if k not in nums]
    if orphan:
        problems.append(f"有定义但正文无标记：{orphan}")
    expected = list(range(1, len(nums) + 1))
    if sorted(nums) != expected:
        gaps = [i for i in expected if i not in nums]
        problems.append(f"编号不连续，缺号：{gaps}")

    if problems:
        print("\n发现问题：")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("\n脚注编号闭环，无缺号、无孤立定义。")


if __name__ == "__main__":
    main()
