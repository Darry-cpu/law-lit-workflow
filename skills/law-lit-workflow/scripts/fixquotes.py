"""把 Markdown 正文中的半角双引号成对替换为中文全角引号（“ ”）。

用法::

    python fixquotes.py 文件.md [--check]

中文法学论文用全角引号，半角 " 在排版上不合规范。替换按行内出现顺序配对：
第 1、3、5…个为左引号，第 2、4、6…个为右引号。若某行引号数为奇数，
说明有落单，替换会把该行后半段全带错，故本脚本先报告再跳过该行，
交由人工确认。
"""

import argparse
import pathlib
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("--check", action="store_true", help="只报告不修改")
    a = ap.parse_args()

    path = pathlib.Path(a.md)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    out = []
    fixed_lines = 0
    odd_lines = []
    total = 0

    for i, line in enumerate(lines, 1):
        n = line.count('"')
        if n == 0:
            out.append(line)
            continue
        if n % 2 != 0:
            odd_lines.append((i, line.strip()[:70]))
            out.append(line)
            continue
        buf = []
        open_next = True
        for ch in line:
            if ch == '"':
                buf.append("\u201c" if open_next else "\u201d")
                open_next = not open_next
                total += 1
            else:
                buf.append(ch)
        out.append("".join(buf))
        fixed_lines += 1

    print(f"替换引号 {total} 个，涉及 {fixed_lines} 行")
    if odd_lines:
        print(f"\n引号数异常（奇数，未处理）的行 {len(odd_lines)} 处，需人工确认：")
        for i, snippet in odd_lines:
            print(f"  第{i}行: {snippet}")

    if a.check:
        return 0 if not odd_lines else 1

    if odd_lines:
        print("\n存在异常行，未写入文件。修正后重跑。")
        return 1

    path.write_text("".join(out), encoding="utf-8", newline="")
    print(f"已写入 {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
