"""核对论文 Markdown 的硬性指标：正文字数、摘要长度、脚注编号闭环、结论规范。

用法::

    python papercheck.py 论文.md

为什么需要它：字数下限、摘要上限、脚注数量与编号连续性都是硬性要求，
目测不可靠；编号一旦断号，转成 Word 脚注就会错位。
结论分点罗列与"结论复述摘要/正文"同样是硬性要求（法学论文结论惯例是
连贯段落收拢为一两个核心命题，且不重复摘要与正文），靠目测对照不可靠，
故一并机械检查。
"""

import argparse
import pathlib
import re
import sys

MARK = re.compile(r"\[\^(\d+)\]")
DEF = re.compile(r"^\[\^(\d+)\]:\s*(.+)$", re.M)
HAN = re.compile(r"[\u4e00-\u9fa5]")


LIST_ITEM = re.compile(r"^\s*(?:[-*+]\s|\d+[.、）)]\s*\S|[（(]\d+[）)]\s*\S|[一二三四五六七八九十]+[、．.]\s*\S)")
# 观点宣告式第一人称（≤3 处可容忍；摘要/关键词行本身不计）
FIRST_PERSON = ("本文认为", "笔者认为", "笔者以为", "本文以为", "本文与之相比",
                "本文相比", "如本文所述", "本文所言", "本文所主张")
# 纯客套语（零容忍）
BOILERPLATE = ("批评指正", "如有不妥", "不揣浅陋", "乞正于方家", "祈请斧正")


def to_zh(s):
    """去掉脚注标记与非汉字数字字符，只留可比对的正文内容。"""
    s = re.sub(r"\[\^\d+\]", "", s)
    return re.sub(r"[^0-9一-龥]", "", s)


def find_conclusion(lines):
    """返回结论章（标题含 结论/结语/总结，且非「脚注」）的行区间 [start, end)。"""
    start, level = None, None
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s*(.+)$", line)
        if start is None:
            if m and "脚注" not in m.group(2) and re.search(r"结论|结语|总结", m.group(2)):
                start, level = i, len(m.group(1))
        elif m and len(m.group(1)) <= level:
            return start, i
    if start is not None:
        return start, len(lines)
    return None, None


def common_spans(x, y, w):
    """在 x 中找与 y 连续相同的极大片段（每个片段长度 ≥ w）。"""
    if len(x) < w or len(y) < w:
        return []
    yset = {y[i:i + w] for i in range(len(y) - w + 1)}
    spans, i = [], 0
    while i <= len(x) - w:
        if x[i:i + w] in yset:
            j = i + 1
            while j <= len(x) - w and x[j:j + w] in yset:
                j += 1
            spans.append(x[i:j + w - 1])
            i = j
        else:
            i += 1
    return spans


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

    # 结论章检查：分点罗列 + 与摘要/正文的连续雷同
    problems = []
    c_start, c_end = find_conclusion(lines)
    if c_start is None:
        print("结论章：未找到标题含「结论/结语/总结」的章节，跳过结论检查（请人工确认章节命名）")
    else:
        c_lines = lines[c_start + 1:c_end]
        c_zh = to_zh("\n".join(c_lines))
        n_list = sum(1 for l in c_lines if LIST_ITEM.match(l))
        print(f"结论章：{lines[c_start].strip()}  行数 {len(c_lines)}  列表项 {n_list}")
        if n_list:
            problems.append(
                f"结论章出现分点罗列（{n_list} 行列表项）——法学论文结论须用连贯段落"
                f"收拢为一两个核心命题，不分点；如该行实为引注列表请人工确认")
        other_zh = to_zh("\n".join(lines[:c_start] + lines[c_end:]))
        abs_hits = common_spans(c_zh, to_zh(abstract), 14)
        if abs_hits:
            problems.append(
                f"结论与摘要存在 ≥14 字连续雷同（{len(abs_hits)} 处），如：「{abs_hits[0]}」"
                f"——摘要与结论分工不同，命中处须人工确认属实质重复后改写")
        body_hits = common_spans(c_zh, other_zh, 20)
        if body_hits:
            problems.append(
                f"结论与正文其他部分存在 ≥20 字连续雷同（{len(body_hits)} 处），如：「{body_hits[0]}」"
                f"——结论只做收拢提升不复述正文，命中处须人工确认属实质重复后改写")

    # 人称与客套语计数（body_text 已去掉标题/摘要/关键词行）
    n_fp = sum(body_text.count(p) for p in FIRST_PERSON)
    bp_hits = {p: body_text.count(p) for p in BOILERPLATE if body_text.count(p)}
    print(f"观点宣告式第一人称（正文）：{n_fp} 处  要求 ≤3  {'OK' if n_fp <= 3 else '超限'}")
    print(f"纯客套语（正文）：{sum(bp_hits.values())} 处  要求 0  {'OK' if not bp_hits else bp_hits}")
    if n_fp > 3:
        problems.append(
            f"观点宣告式第一人称出现 {n_fp} 处（>3）——「本文认为／笔者认为／本文与之相比」"
            f"改用无人称表述（由此可见／上述分析表明）")
    if bp_hits:
        problems.append(
            f"出现纯客套语 {bp_hits}——「批评指正／如有不妥」类一律删除，"
            f"自限句最多一句且须具体")

    print(f"正文汉字数（不含标题/摘要/关键词/脚注）：{han}")
    print(f"摘要长度（含标点，按字符计）：{len(abstract)}  要求 ≤300  {'OK' if len(abstract) <= 300 else '超限'}")
    print(f"关键词：{keywords}  （{len(re.split(r'[；;]', keywords))} 个）")
    print(f"脚注标记数（正文中）：{len(nums)}")
    print(f"脚注定义数：{len(defs)}")

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
