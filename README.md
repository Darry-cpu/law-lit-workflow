# law-lit-workflow

法学文献**检索 → 入库 → 精读 → 综述/论文写作 → 引注 → Word** 的端到端工作流 Skill，面向 MiMoCode / MiMo Desktop（及其他兼容 MiMoCode 技能格式的 agent）。

一条触发语，跑完整条流水线；内置法学期刊白名单与多技能编排规则。

## 解决什么问题

1. **检索质量靠经验**：内置 CLSCI / CSSCI / 北大核心三大体系期刊白名单（约 70 刊并集）、近五年限定、自动排除学位论文与报纸的硬规则；命中不足 8 篇自动逐级放宽。
2. **多技能各说各话**：把选题、检索、精读、多文档综合、证据映射、写作、引注、Word 产出涉及的 8+ 个 skill 的调用顺序、阶段产物契约、冲突裁决（如"引注体例以《法学引注手册》第二版为绝对优先"）一次定死。
3. **工具排坑**：cnki-mcp / zotero-mcp 的登录态探测、参数坑（`keywords` 召回极低、`year_from` 须成对传等）直接记录在案。

## 流程一览（P0–P9）

| 阶段 | 执行者 | 产出物 |
|------|--------|--------|
| P0 选题确认 | brainstorming-research ＋ humanities-thesis | `plan/project-overview.md` 等 |
| P1 检索 | 知网 MCP ＋ 期刊白名单 | `plan/literature-search.md`（候选表，用户筛选） |
| P2 入库与全文 | Zotero MCP ＋ 用户下载 PDF | Zotero 条目+附件；`plan/sources.md` |
| P3 转 Markdown | 本地 PDF→MD 转换脚本 | `reading/*.md` |
| P4 单篇精读 | paper-reading（法学适配） | `reading/cards/*.md` |
| P5 综合归纳 | multi-document-summarization | `synthesis/综合摘要.md` |
| P6 证据映射 | literature-review（硬门控） | `plan/evidence-map.md` |
| P7 写作 | literature-review / writing-law / paper-orchestration 等 | 草稿 `.md` |
| P8 引注 | csl-citation | 定稿 `.md` |
| P9 产出 | docx-official | `output/*.docx` |

## 前置依赖

**宿主**

- [MiMo Desktop](https://github.com/XiaomiMiMo) / MiMoCode（技能宿主，本技能遵循其技能目录规范）

**工具（MCP）**

- 知网检索 MCP：如 cnki-mcp（需机构登录态）——任何能按主题/期刊/年份检索知网的工具均可，替换 SKILL.md 中 P1 的具体调用即可
- Zotero + Zotero MCP：文献元数据入库、全文读取
- 本地 PDF→Markdown 转换脚本（SKILL.md 中以 `tools/mdconvert.py` 为例，可替换）

**配套技能**（本工作流编排的对象，按需安装）：

brainstorming-research、paper-reading、multi-document-summarization、literature-review、writing-law、humanities-thesis、paper-orchestration、csl-citation、docx-official

## 安装

```bash
# 全局（所有会话可用）
git clone <this-repo>
cp -r law-lit-workflow/skills/law-lit-workflow ~/.config/mimocode/skills/

# 或项目级
cp -r law-lit-workflow/skills/law-lit-workflow <你的项目>/.mimocode/skills/
```

新会话自动生效（无需注册）。输入 `/law-lit-workflow` 或说触发语即可：

> "按工作流检索'××主题'的论文" / "跑文献工作流" / "写法学文献综述"

## 期刊白名单说明

- 白名单为**人工整理**的三体系并集，见 SKILL.md 内 P1 章节；CLSCI/CSSCI/北大核心目录**每年调整，以官方最新发布为准**。
- 已知规范化处理：《法治与社会发展》与《法制与社会发展》按同一刊处理。
- 想改白名单、年份阈值（默认 2021 至今）、放宽阈值（默认 <8 篇）：直接编辑 `skills/law-lit-workflow/SKILL.md` 对应段落。

## License

MIT
