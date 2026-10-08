"""去掉论文正文里的行内加粗标记，只保留「摘要：」「关键词：」两个标签。

用法::

    python stripbold.py 文件.md [--check]

为什么需要它：中文法学期刊的正文一般不加粗，需要强调时用着重号或径由行文承担。
起草阶段用 **…** 标出每节的承重句便于自查，但这类标记不应进入成稿。
「摘要：」「关键词：」两个标签加粗是中文论文通例，故予保留。
"""

import argparse
import pathlib
import re
import sys

LABEL = re.compile(r"^\*\*(摘要|关键词)\*\*：")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("--check", action="store_true", help="只报告不修改")
    a = ap.parse_args()

    path = pathlib.Path(a.md)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    out = []
    stripped = 0
    lines_touched = 0
    kept_labels = []

    for line in lines:
        m = LABEL.match(line)
        if m:
            head, rest = line[: m.end()], line[m.end():]
            kept_labels.append(head)
            n = rest.count("**")
            if n:
                stripped += n
                lines_touched += 1
            out.append(head + rest.replace("**", ""))
            continue
        n = line.count("**")
        if n:
            stripped += n
            lines_touched += 1
            out.append(line.replace("**", ""))
        else:
            out.append(line)

    print(f"移除加粗标记 {stripped} 个，涉及 {lines_touched} 行")
    print(f"保留的标签：{kept_labels}")

    if a.check:
        return 0

    path.write_text("".join(out), encoding="utf-8", newline="")
    print(f"已写入 {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
