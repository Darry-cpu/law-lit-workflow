"""把一批精读卡按指定章节抽成浓缩档，供横向综合与证据映射使用。

用法::

    python carddigest.py 卡片目录 -o 输出.md --sections 0,3,5,6
    python carddigest.py 卡片目录 -o 输出.md --sections 3,8

为什么需要它：单张精读卡两三万字节，十几张一起读会挤爆上下文。而做证据映射
真正需要的只是"可引用核心论点（含页码）"“与论证主线的对接”“冲突与需回应处”
几节，其余各节留待逐章写作时再回查原卡。
"""

import argparse
import pathlib
import re

SECTION = re.compile(r"^##\s+(\d+)\.")


def split_sections(text):
    """按 '## N.' 二级标题切分为 {编号: 正文}。"""
    parts = {}
    current = None
    buf = []
    for line in text.splitlines():
        m = SECTION.match(line)
        if m:
            if current is not None:
                parts[current] = "\n".join(buf).strip()
            current = m.group(1)
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        parts[current] = "\n".join(buf).strip()
    return parts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--sections", default="0,3,5,6", help="要抽取的章节编号，逗号分隔")
    ap.add_argument("--pattern", default="*.md", help="卡片文件匹配模式")
    a = ap.parse_args()

    want = [s.strip() for s in a.sections.split(",") if s.strip()]
    cards = sorted(p for p in pathlib.Path(a.cards).glob(a.pattern) if not p.name.startswith("_"))

    out = []
    for card in cards:
        sections = split_sections(card.read_text(encoding="utf-8"))
        body = [f"\n# ===== {card.stem} ====="]
        for key in want:
            if key in sections:
                body.append(f"\n## {key}\n{sections[key]}")
        if len(body) > 1:
            out.append("\n".join(body))
        print(f"{card.name}: " + ", ".join(k for k in want if k in sections))

    pathlib.Path(a.output).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"\n共 {len(out)} 张卡 -> {a.output}")


if __name__ == "__main__":
    main()
