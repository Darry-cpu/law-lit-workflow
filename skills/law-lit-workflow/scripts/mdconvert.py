"""批量把文档转成 Markdown，强制 UTF-8 落盘，并修复 PDF 转换常见的断行/页码问题。

用法::

    python mdconvert.py 报告.docx 材料.pdf
    python mdconvert.py 某个目录 -r -o out
    python mdconvert.py 扫描版.pdf --no-fix

为什么需要它（本机实测结论）：

* PowerShell 5.1 的 ``>`` 会把 markitdown 的 UTF-8 输出改写成 UTF-16 LE + BOM，
  按 UTF-8 读的脚本会直接抛 UnicodeDecodeError。本脚本用 Python 自己写 UTF-8。
* PDF 没有段落语义，markitdown 会把每一行都变成一个 Markdown 段落，
  句子被切得七零八落，页码还会混进正文。这里按句末标点重新拼回整段。
"""

import argparse
import pathlib
import re
import sys

from markitdown import MarkItDown

# 不含 .md：转换输出本身就是 .md，收进来会在递归模式下自我吞噬、并和源文件撞名
EXTS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".html", ".htm",
    ".csv", ".json", ".xml", ".epub", ".zip", ".txt",
}

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


def fix_pdf(text):
    """把逐行成段的 PDF 文本拼回整段，并丢掉纯页码行。"""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or PAGENUM.fullmatch(line):
            continue
        if (
            out
            and not out[-1].endswith(tuple(TERMINAL))
            and not HEADING.match(out[-1])
            and not HEADING.match(line)
        ):
            out[-1] = _join(out[-1], line)
        else:
            out.append(line)
    return "\n\n".join(out)


def collect(inputs, recursive):
    files = []
    for item in inputs:
        p = pathlib.Path(item)
        if p.is_dir():
            it = p.rglob("*") if recursive else p.glob("*")
            files.extend(sorted(f for f in it if f.suffix.lower() in EXTS))
        elif p.is_file():
            files.append(p)
        else:
            print(f"跳过（不存在）: {p}", file=sys.stderr)
    return files


def main():
    ap = argparse.ArgumentParser(
        description="批量转换文档为 Markdown（强制 UTF-8）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("inputs", nargs="+", help="文件或目录")
    ap.add_argument("-o", "--outdir", help="输出目录，默认写到源文件旁边")
    ap.add_argument("-r", "--recursive", action="store_true", help="递归子目录")
    ap.add_argument("--no-fix", action="store_true", help="关闭 PDF 断行/页码修复")
    args = ap.parse_args()

    files = collect(args.inputs, args.recursive)
    if not files:
        print("没有找到可转换的文件", file=sys.stderr)
        return 1

    md = MarkItDown()
    ok = 0
    taken = {}
    for f in files:
        outdir = pathlib.Path(args.outdir) if args.outdir else f.parent
        outdir.mkdir(parents=True, exist_ok=True)
        out = outdir / (f.stem + ".md")
        # 同一源文件名（如 a.pdf 与 a.docx）会映射到同一个输出，加序号避免互相覆盖
        if out in taken:
            taken[out] += 1
            out = out.with_name(f"{out.stem}-{taken[out]}.md")
        else:
            taken[out] = 1
        try:
            text = md.convert(str(f)).text_content
            note = ""
            if f.suffix.lower() == ".pdf" and not args.no_fix:
                before = len([b for b in re.split(r"\n\s*\n", text) if b.strip()])
                text = fix_pdf(text)
                after = len([b for b in text.split("\n\n") if b.strip()])
                note = f"  [段落 {before} -> {after}]"
            out.write_text(text, encoding="utf-8", newline="\n")
            print(f"OK   {f.name} -> {out}{note}")
            ok += 1
        except Exception as exc:
            print(f"失败 {f.name}: {exc}", file=sys.stderr)

    print(f"\n完成 {ok}/{len(files)}")
    return 0 if ok == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())
