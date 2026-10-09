# law-lit-workflow

法学文献**检索 → 入库 → 转 MD → 页码锚点 → 精读 → 综合 → 证据映射 → 写作 → 引注 → Word → 去 AI 味＋版式清理 → 交付校验**的端到端工作流 Skill，面向 MiMoCode / MiMo Desktop（及其他兼容 MiMoCode 技能格式的 agent）。

一条触发语跑完整条流水线；内置法学期刊白名单、多技能编排规则、9 个配套脚本、一套自检脚本与样例夹具。

> **本版为 2026-10-08 修订版**：相较初版（只有一份 SKILL.md）增加了页码锚点、去 AI 味与版式清理、交付校验三个阶段，随包 9 个脚本与自检脚本，并修正了登录探测、PDF 存放等若干会让人踩坑的规则。差异见文末「更新记录」。

## 解决什么问题

1. **检索质量靠经验**：内置 CLSCI / CSSCI / 北大核心三大体系期刊白名单（约 70 刊并集）、近五年限定、自动排除学位论文与报纸的硬规则；命中不足 8 篇自动逐级放宽。
2. **多技能各说各话**：把选题、检索、精读、综合、证据映射、写作、引注、Word 产出涉及的 8+ 个 skill 的调用顺序、阶段产物契约与冲突裁决一次定死（含"投稿期刊体例优先于通用引注手册"）。
3. **工具排坑**：知网 MCP / Zotero MCP 的登录态探测协议、参数坑、并发限制，以及"PDF 只从 Zotero 文件库读"的存放规则，全部记录在案。
4. **页码可复核**：内置**页码锚点**环节，把 PDF 物理页映射为印刷页，使每条脚注的页码都能回源核对——这是页下注体例的硬前提，也是初版最容易断掉的一环。
5. **交付有机械校验**：字数／摘要／关键词／脚注闭环、引注体例、正文加粗、真页下注四要件、**渲染看图**五项，缺一不可。
6. **可自检、可移植**：脚本自包含、不写死本机路径；装完跑一次自检即知是否可用，缺依赖时会指出缺哪一组库并给出补救命令。

## 流程一览（P0–P9.5）

| 阶段 | 执行者 | 产出物 |
|------|--------|--------|
| P0 选题确认 | brainstorming-research ＋ humanities-thesis | `plan/project-overview.md` 等 |
| P1 检索 | 知网 MCP ＋ 期刊白名单 | `plan/literature-search.md`（候选表，用户筛选） |
| P2 入库与全文 | Zotero MCP（PDF 由用户经 Connector 下载） | Zotero 条目＋附件；`plan/sources.md` |
| P3 转 Markdown | `scripts/mdconvert.py` | `reading/*.md` |
| **P3.5 页码锚点** | `scripts/pdfpages.py` | **`reading/paged/*.md`（精读主源）** |
| P4 单篇精读 | paper-reading（法学适配，规模化时并行子代理） | `reading/cards/*.md` |
| P5 综合归纳 | multi-document-summarization | `synthesis/综合摘要.md` |
| P6 证据映射 | literature-review（硬门控） | `plan/evidence-map.md` |
| P7 写作 | literature-review / writing-law / paper-orchestration ＋ antidefensivewriting / law-paper-opening-ending（按需） | 草稿 `.md` |
| P8 引注规范化 | csl-citation ＋ `scripts/citecheck.py` | 定稿 `.md` |
| P9 产出 Word | docx-official ＋ `scripts/md2docx.py`（真页下注） | `output/*.docx` |
| **P9.4 去 AI 味＋版式清理** | legal-paper-framework-humanizer-zh ＋ `scripts/stripbold.py` | **另存 `output/*_去AI味版.*`（不覆盖原稿）** |
| **P9.5 交付校验** | `scripts/papercheck.py`／`citecheck.py`／`docxcheck.py` ＋ 渲染看图 | 校验通过记录 |

## 前置依赖

**宿主**

- [MiMo Desktop](https://github.com/XiaomiMiMo) / MiMoCode（技能宿主，本技能遵循其技能目录规范）

**工具（MCP）**

- 知网检索 MCP：如 cnki-mcp（需机构登录态）——任何能按主题／期刊／年份检索知网的工具均可，替换 SKILL.md 中 P1 的具体调用即可
- Zotero ＋ Zotero MCP：文献元数据入库、**PDF 全文的唯一读取来源**

**Python 运行时**（两个角色，可装在同一解释器上）

| 角色 | 需要的库 | 用于 |
|------|----------|------|
| docx 组 | `pypdf`、`python-docx`、`lxml` | P3.5 页码锚点、P9 生成 Word、P9.4／P9.5 校验 |
| 转换组 | `markitdown` | P3 PDF → Markdown |

```bash
<解释器> -m pip install pypdf python-docx lxml      # docx 组
<解释器> -m pip install markitdown                  # 转换组
```

MiMo Desktop 用户的 `$MIMO_PYTHON` 已预装 docx 组，只需另装 `markitdown` 即可齐备。
**自检脚本会自动探测哪个解释器能 import 哪一组，不需要改脚本里的路径。**

**docx → PDF 渲染**（P9.5 的渲染看图需要）

- LibreOffice：`soffice --headless --convert-to pdf --outdir <目录> <文件>`
- Windows 备用：WPS COM（`KWPS.Application` ＋ `ExportAsFixedFormat($pdf, 17)`），见 SKILL.md 速查

**配套技能**（本工作流编排的对象，按需安装）

brainstorming-research、paper-reading、multi-document-summarization、literature-review、writing-law、humanities-thesis、paper-orchestration、csl-citation、docx-official、legal-paper-framework-humanizer-zh、antidefensivewriting、law-paper-opening-ending

> 最后两个为**按需**技能：其核心要求（结论铁律、人称与自限语句、首尾结构要点）已内嵌 SKILL.md 的 P7 通用约束，
> 装不到也不影响流程运行，缺的只是完整版细则。

## 安装

**必须复制整个文件夹**（只复制 SKILL.md 会缺脚本与自检）：

```bash
# 全局（所有会话可用）
git clone <this-repo>
cp -r law-lit-workflow/skills/law-lit-workflow ~/.config/mimocode/skills/

# 或项目级
cp -r law-lit-workflow/skills/law-lit-workflow <你的项目>/.mimocode/skills/
```

新会话自动生效（无需注册）。输入 `/law-lit-workflow` 或说触发语即可：

> "按工作流检索'××主题'的论文" / "跑文献工作流" / "写法学文献综述"

## 自检（装完先跑一遍）

```bash
& $MIMO_PYTHON <技能目录>/tests/skilltest.py
```

自检共 **19 项**：6 项安装完整性 ＋ 2 项运行时探测 ＋ 11 项端到端冒烟，
**完全自包含**（使用 `tests/assets/` 下自带的样例 PDF／成稿／精读卡，不依赖任何外部项目、不联网）。
任何 FAIL 都不要带病开跑正文流程。

缺依赖时它会**分别**指出缺的是 `pypdf＋python-docx` 还是 `markitdown`、影响哪些阶段，
并给出 pip 命令与降级规则——报错可照做，不会只说一句"缺依赖"。

## PDF 的存放规则（重要）

- **整个工作流全程只从 Zotero 文件库读取 PDF**（`zotero-mcp` 查条目 `attachments[].path`）；
  **不要把 PDF 复制进项目文件夹**，项目里只保留派生物（转 MD、页码锚点版）。
- 任何来源的 PDF（Connector 下载／用户交回／聊天临时补给），**到手第一件事是挂进 Zotero 对应条目**，
  之后一律从该附件路径读。
- **工作流完成后的修改**：由操作者自己另行提供文件，工作流不主动复制或移动。

## 期刊白名单说明

- 白名单为**人工整理**的三体系并集，见 SKILL.md 内 P1 章节；CLSCI/CSSCI/北大核心目录**每年调整，以官方最新发布为准**。
- 已知规范化处理：《法治与社会发展》与《法制与社会发展》按同一刊处理。
- 想改白名单、年份阈值（默认 2021 至今）、放宽阈值（默认 <8 篇）：直接编辑 `SKILL.md` 对应段落。

## 更新记录

**2026-10-09 修订**

- **P7 新增「通用约束」（综述线与论文线都适用）**：防御性写作（主张须有证据、不虚构、删防御性空话）、
  结论写作铁律（连贯段落收拢为一两个核心命题、禁止分点罗列、不复述摘要与正文）、
  开头与结尾写作（五步漏斗／三段式、首尾锚点成对）、人称与自限语句（观点宣告式第一人称 ≤3 处、纯客套语零容忍）。
- **`papercheck.py` 升级**：新增结论章分点罗列检测、结论与摘要 ≥14 字／与正文 ≥20 字连续雷同检测、
  第一人称与客套语计数，全部纳入 P9.5 硬门控。
- 冲突裁决新增 3 条（第 6–8 条）：写作约束分工、首尾写作分工、人称与自限语句的覆盖关系。
- 配套技能清单补充 `antidefensivewriting`、`law-paper-opening-ending`（按需安装；核心规则已内嵌 P7，缺失不影响运行）。

**2026-10-08 修订版**

- 新增三个阶段：**P3.5 页码锚点**（页下注体例的硬前提）、**P9.4 去 AI 味＋版式清理**（另存新文件，不覆盖原稿）、**P9.5 交付校验**（五项机械校验＋渲染看图）。
- 新增 9 个脚本（`scripts/`）：`mdconvert`、`pdfpages`、`md2docx`、`papercheck`、`citecheck`、`docxcheck`、`fixquotes`、`stripbold`、`carddigest`。
- 新增自检脚本与样例夹具（`tests/`），可验证安装是否完整。
- **修正登录探测协议**：初版"先调 `login`"会导致反复超时误判掉线；现改为"只读查询探路，只有报 `please call login` 才调一次"。
- **修正 PDF 存放规则**：初版建议复制进项目文件夹，现改为只从 Zotero 文件库读。
- **修正 Word 产出路径**：python-docx 与 docx-official 均不支持脚注，"不得手搓 python-docx"的旧表述会把人逼进死胡同；现明确真页下注须经 `md2docx.py` 注入 `footnotes.xml` 四要件。
- 补充：两个 Python 运行时的分工与自动探测、WPS COM 备用渲染、cnki 并发禁令与空结果重试、Zotero Connector 重复条目规避、`HANDOVER.md` 断点续作、投稿期刊体例优先于通用手册。

## License

MIT
