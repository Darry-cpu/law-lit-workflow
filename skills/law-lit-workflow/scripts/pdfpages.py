"""按 PDF 物理页切分文本、标注印刷页码，并修复抽取造成的断行，供精读取页码锚点。

用法::

    python pdfpages.py 输出.md 输入.pdf --start 171 --expect 11
    python pdfpages.py 输出.md 输入.pdf --start 16 --expect 15 --no-fix

为什么需要它：markitdown 把整篇拼成连续文本，期刊 PDF 的页眉页脚常被丢弃，
精读时无从定位"这句话在第几页"，而页下注必须给出页码。期刊抽印 PDF 的物理页
与印刷页通常一一对应，故 --start 即可建立精确映射；--expect 用于校验该假设。

抽出的文本常把标点、单字拆成独立行（如「，」独占一行），本脚本按终止标点重拼，
并在两个 ASCII 词之间补空格，避免把英文黏成一团。
"""

import argparse
import pathlib
import re

from pypdf import PdfReader

PAGENUM = re.compile(r"^\d{1,3}$")
HEADING = re.compile(
    r"^(?:第[一二三四五六七八九十百千]+[章节条编]"
    r"|[一二三四五六七八九十]+[、.]"
    r"|\(?\d+(?:\.\d+)*[、.）)]"
    r"|[（(]\d+[）)])"
)
TERMINAL = "。！？；：”’》」』）】…!?;:"


def _join(left, right):
    if (
        left
        and right
        and left[-1].isascii()
        and left[-1].isalnum()
        and right[0].isascii()
        and right[0].isalnum()
    ):
        return left + " " + right
    return left + right


def fix_lines(text):
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or PAGENUM.fullmatch(line):
            continue
        # 短碎行（1—2 字符）几乎总是被拆出来的标点或单字，一律并回上一行
        if out and (len(line) <= 2 or not out[-1].endswith(tuple(TERMINAL))) and not HEADING.match(line):
            out[-1] = _join(out[-1], line)
        else:
            out.append(line)
    return "\n\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    ap.add_argument("pdf")
    ap.add_argument("--start", type=int, default=None, help="第 1 个物理页对应的印刷页码")
    ap.add_argument("--expect", type=int, default=None, help="预期物理页数，用于校验映射是否成立")
    ap.add_argument("--no-fix", action="store_true", help="关闭断行修复，保留原始抽取结果")
    a = ap.parse_args()

    reader = PdfReader(a.pdf)
    pages = reader.pages
    n = len(pages)
    name = pathlib.Path(a.pdf).name

    ok = a.expect is None or n == a.expect
    last = (a.start + n - 1) if a.start else n
    if not ok:
        print(
            f"警告 {name}: 实际 {n} 页 != 预期 {a.expect} 页，"
            f"物理页与印刷页可能不是一一对应，页码锚点存疑",
            flush=True,
        )
    print(f"{'OK ' if ok else '?? '}{name}: {n} 页 -> 印刷页 {a.start}-{last}")

    parts = []
    for i, page in enumerate(pages):
        label = (a.start + i) if a.start else (i + 1)
        text = (page.extract_text() or "").strip()
        if not a.no_fix:
            text = fix_lines(text)
        parts.append(f"\n\n<!-- ===== 印刷页 {label} ===== -->\n\n{text}")
    pathlib.Path(a.output).write_text("".join(parts), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
