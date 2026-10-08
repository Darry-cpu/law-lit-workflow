"""law-lit-workflow 技能自检（自包含版：全部使用本目录 assets\\ 下的样例，不依赖外部项目）。

运行::

    & $MIMO_PYTHON <本技能目录>\\tests\\skilltest.py

通过标准：FAIL 数为 0。任何 FAIL 都说明安装不完整或环境缺依赖，
不要带病开跑正文流程。本脚本不访问网络（P1 探路请按 SKILL.md 单独验证）。
"""

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SKILL = pathlib.Path(__file__).resolve().parent.parent
SCR = SKILL / "scripts"
ASSETS = SKILL / "tests" / "assets"
SAMPLE_PDF = ASSETS / "sample.pdf"
SAMPLE_MD = ASSETS / "sample.md"
CARDS = ASSETS / "cards"

results = []


def check(name, cond, detail=""):
    if cond is None:
        results.append((name, None, detail))
        print(f"[SKIP ] {name}  -> {detail}")
        return
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  -> {detail}" if detail else ""))


def run(cmd, timeout=300):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def py_with(module):
    """返回一个能 import 该模块的 Python 解释器；找不到返回 None。"""
    for cand in ([sys.executable, "python", "py"] if sys.executable else ["python", "py"]):
        try:
            r = subprocess.run([cand, "-c", f"import {module}"], capture_output=True)
            if r.returncode == 0:
                return cand
        except Exception:
            continue
    return None


print("=" * 70)
print("一、安装完整性")
print("=" * 70)

t = (SKILL / "SKILL.md").read_text(encoding="utf-8")
check("frontmatter（name/description）",
      (t.splitlines()[0] == "---") and bool(re.search(r"(?m)^name: law-lit-workflow$", t)))
check("五个门控齐备", all(f"门控 {i}" in t for i in (1, 2, 3, 4, 5)))
check("关键章节齐备（P3.5/P9.4/P9.5/冲突裁决/技能自检）",
      all(k in t for k in ("## P3.5", "## P9.4", "## P9.5", "## 冲突裁决", "## 技能自检")))
check("样例夹具齐备", SAMPLE_PDF.exists() and SAMPLE_MD.exists() and CARDS.is_dir())

need = ["mdconvert", "pdfpages", "papercheck", "citecheck", "docxcheck",
        "md2docx", "fixquotes", "stripbold", "carddigest"]
found = {p.name[:-3] for p in SCR.glob("*.py")}
check("9 个脚本随包分发", set(need) <= found, f"缺 {sorted(set(need) - found) or '无'}")
check("脚本内无写死本机绝对路径",
      not [p for p in SCR.glob("*.py")
           if re.search(r"[A-Za-z]:\\", p.read_text(encoding="utf-8"))])

print()
print("=" * 70)
print("二、运行时探测（两个 Python 各司其职）")
print("=" * 70)

PY_MAIN = py_with("pypdf, docx")
PY_MD = py_with("markitdown")
check("找到能跑 pypdf＋python-docx 的解释器（P3.5 与 docx 组脚本用）", PY_MAIN is not None, str(PY_MAIN))
check("找到能 import markitdown 的解释器（P3 用）", PY_MD is not None, str(PY_MD))

SMOKE_TOTAL = 11  # 冒烟段检查项数，用于报告“未执行”数量

missing = []
if PY_MAIN is None:
    missing.append(("pypdf ＋ python-docx",
                    "P3.5 页码锚点，以及 docx 组脚本（md2docx／docxcheck／papercheck／"
                    "citecheck／stripbold／fixquotes／carddigest）"))
if PY_MD is None:
    missing.append(("markitdown", "P3 PDF → Markdown"))
if not (SAMPLE_PDF.exists() and SAMPLE_MD.exists()):
    missing.append(("样例夹具", "tests\\assets\\sample.pdf 与 sample.md（重新获取完整技能包）"))

if missing:
    print()
    print("=" * 70)
    print(f"运行时或夹具缺失 —— 冒烟段 {SMOKE_TOTAL} 项未执行，无法判定流程可用")
    print("=" * 70)
    for mod, use in missing:
        print(f"  缺：{mod}")
        print(f"      影响：{use}")
    print()
    print("  补救步骤：")
    print("    1) 缺库的，装到任一解释器上：")
    print("       <该解释器> -m pip install pypdf python-docx lxml      # docx 组")
    print("       <该解释器> -m pip install markitdown                  # 仅 P3 需要")
    print("    2) 两个运行时可以分开：一个装 pypdf＋python-docx，另一个装 markitdown；")
    print("       自检脚本会自动在 sys.executable / python / py 三者中挑选能 import 的那一个，")
    print("       因此**不需要手工改脚本路径**。")
    print("    3) MiMo Desktop 用户：$MIMO_PYTHON 已预装 pypdf／python-docx／lxml，")
    print("       只需另装 markitdown 到系统 Python 即可齐备。")
    print()
    print("  重要：缺脚本**不等于流程不能跑**。SKILL.md「脚本缺失时的降级规则」要求——")
    print("        按各阶段文字步骤手工执行，且**不得跳过 P3.5 页码锚点与 P9.5 交付校验**两个门控。")
    print()
    n_ok = sum(1 for _, c, _ in results if c is True)
    n_fail = sum(1 for _, c, _ in results if c is False)
    print(f"结果：通过 {n_ok} / 失败 {n_fail} / 未执行 {SMOKE_TOTAL}"
          f"（安装完整性 6 项 ＋ 运行时探测 2 项已完成）")
    print("=" * 70)
    sys.exit(1)

tmp = pathlib.Path(tempfile.mkdtemp(prefix="lawskill_selftest_"))

print()
print("=" * 70)
print("三、端到端冒烟（全部从本技能 scripts\\ 执行）")
print("=" * 70)

# 1) P3.5 页码锚点
out = tmp / "sample_paged.md"
rc, o = run([PY_MAIN, str(SCR / "pdfpages.py"), str(out), str(SAMPLE_PDF),
             "--start", "1", "--expect", "2"])
paged = out.read_text(encoding="utf-8") if out.exists() else ""
m1 = re.search(r"印刷页 1 =+ -->(.{0,60})", paged, re.S)
m2 = re.search(r"印刷页 2 =+ -->(.{0,60})", paged, re.S)
check("P3.5 pdfpages 物理页→印刷页映射", rc == 0 and "印刷页 1" in paged and "印刷页 2" in paged)
check("P3.5 各页内容落位正确",
      bool(m1 and "第一页" in m1.group(1)), f"页1含第一页内容:{bool(m1 and '第一页' in m1.group(1))}；页2含第二页内容:{bool(m2 and '第二页' in m2.group(1))}")

# 2) P3 转 MD
odir = tmp / "conv"
rc, o = run([PY_MD, str(SCR / "mdconvert.py"), str(SAMPLE_PDF), "-o", str(odir)])
got = list(odir.glob("*.md")) if odir.exists() else []
check("P3 mdconvert 转 MD", rc == 0 and len(got) == 1, (got[0].name if got else o[-120:]))

# 3) P9.4 stripbold：注入加粗后应清除、两个标签保留
draft = tmp / "bold_test.md"
src = SAMPLE_MD.read_text(encoding="utf-8").splitlines()
for i, ln in enumerate(src):
    if ln.startswith("本样例服务于技能自检"):
        src[i] = "**注入的加粗测试**" + ln
        break
draft.write_text("\n".join(src), encoding="utf-8")
rc, o = run([PY_MAIN, str(SCR / "stripbold.py"), str(draft)])
after = draft.read_text(encoding="utf-8")
check("P9.4 stripbold 清除正文加粗", rc == 0 and after.count("**") == 4,
      f"处理后 ** 残留 {after.count('**')}（应仅剩摘要/关键词两对=4）")
check("P9.4 stripbold 保留「摘要：」「关键词：」",
      "**摘要**：" in after and "**关键词**：" in after)

# 4) P9 md2docx
docx_out = tmp / "out.docx"
rc, o = run([PY_MAIN, str(SCR / "md2docx.py"), str(SAMPLE_MD), str(docx_out)])
check("P9 md2docx 生成真页下注", rc == 0 and docx_out.exists())

# 5) P9.5 papercheck
rc, o = run([PY_MAIN, str(SCR / "papercheck.py"), str(SAMPLE_MD)])
check("P9.5 papercheck（摘要/关键词/脚注闭环）",
      rc == 0 and "脚注编号闭环" in o, o.strip().splitlines()[-1] if o.strip() else "")

# 6) P9.5 citecheck
rc, o = run([PY_MAIN, str(SCR / "citecheck.py"), str(SAMPLE_MD)])
check("P9.5 citecheck（略写/重复/注号位置）", rc == 0 and "0 /" in o and "条为略写" in o,
      "有 FAIL 项时检查输出")

# 7) P9.5 docxcheck
rc, o = run([PY_MAIN, str(SCR / "docxcheck.py"), str(docx_out)])
check("P9.5 docxcheck 四要件", rc == 0 and "四要件齐备" in o)

# 8) fixquotes（--check 不改文件）
rc, o = run([PY_MAIN, str(SCR / "fixquotes.py"), str(SAMPLE_MD), "--check"])
check("fixquotes --check 可执行", rc == 0, o.strip().splitlines()[0] if o.strip() else "")

# 9) carddigest
rc, o = run([PY_MAIN, str(SCR / "carddigest.py"), str(CARDS),
             "-o", str(tmp / "dig.md"), "--sections", "0,3,5,6"])
check("carddigest 可执行", rc == 0, o.strip().splitlines()[-1] if o.strip() else "")

shutil.rmtree(tmp, ignore_errors=True)

print()
print("=" * 70)
n_ok = sum(1 for _, c, _ in results if c is True)
n_fail = sum(1 for _, c, _ in results if c is False)
n_skip = sum(1 for _, c, _ in results if c is None)
print(f"结果：通过 {n_ok} / 失败 {n_fail} / 跳过 {n_skip}（共 {len(results)}）")
for name, c, d in results:
    if c is False:
        print(f"  ✗ {name}  {d}")
print("=" * 70)
sys.exit(0 if n_fail == 0 else 1)
