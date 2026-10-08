---
name: law-lit-workflow
description: 法学文献端到端工作流：知网检索（CLSCI/CSSCI/北大核心期刊白名单、近五年、排除学位论文）→ Zotero 入库 → PDF 转 Markdown 精读 → 多文档综合 → 证据映射 → 文献综述/论文写作（8个配套 skill 编排）→ 法学引注规范化 → 产出 Word。当用户说"按工作流检索论文""跑文献工作流""写法学文献综述""综述工作流"或给出研究主题要求完成检索到成稿的全流程时使用。
---

# 法学文献综述端到端工作流

流水线 + 约束叠加的编排。主线：**检索 → 入库 → 转 MD → 精读 → 综合 → 映射 → 写作 → 引注 → Word**；
`paper-orchestration` 是写作段总控，`csl-citation` / `writing-law` 是引注与文体的约束层。

## 硬参数与硬门控

- **五年内** = 2021 年至今（cnki advanced-search `year_from=2021`）。
- **数量过少** = 白名单内命中 **< 8 篇**时逐级放宽（见 P1）。
- **永不收录**：硕士/博士学位论文、报纸文章、会议论文。
- **门控 1（P0）**：brainstorming-research 的"用户未最终确认，不写任何正文"。
- **门控 2（P6）**：`plan/evidence-map.md`（证据-论点映射）不存在，不得开始综述写作。
- **门控 3（P7 论文线）**：paper-orchestration 的 plan 三件套（project-overview/outline/progress）与任务包不存在，不得起草章节。

## 阶段总览

| 阶段 | 执行者 | 产出物 |
|------|--------|--------|
| P0 选题确认 | brainstorming-research（对话式，一次一问）＋ humanities-thesis 阶段零 | `plan/project-overview.md`、`plan/outline.md`、`plan/progress.md` |
| P1 检索 | cnki-mcp ＋ 本 skill 期刊白名单 | `plan/literature-search.md`（候选表，用户筛选） |
| P2 入库与全文 | zotero-mcp ＋ 用户 Connector/丢 PDF | Zotero 条目+附件；`plan/sources.md`（D编号↔Zotero key↔PDF路径↔MD路径） |
| P3 转 Markdown | `tools/mdconvert.py`（项目内的 PDF→Markdown 转换脚本，可替换为等价工具） | `reading/D编号_短题名.md` |
| P4 单篇精读 | paper-reading（法学适配，见下） | `reading/cards/D编号_精读卡.md` |
| P5 综合归纳 | multi-document-summarization | `synthesis/综合摘要.md`（共识表/冲突表/洞见） |
| P6 证据映射 | literature-review 的 evidence-claim map | `plan/evidence-map.md` |
| P7 写作 | 综述线 / 论文线（见下） | 综述或章节 `.md` 草稿 |
| P8 引注规范化 | csl-citation 脚本逐条校核 | 定稿 `.md` |
| P9 产出 Word | **docx-official**（强制，管中文字体与版式） | `output/×××.docx` |

目录约定：`plan/`、`reading/`、`reading/cards/`、`synthesis/`、`output/` 均建在当前项目/会话工作目录下。

---

## P1 检索（核心约束段）

### 步骤

1. **探测式登录（P1 第一动作）**：调 cnki-mcp 的 `login`。
   - 会话有效 → 静默继续，不打扰用户；
   - 会话失效 / 报 "please call login before using browser tools" → **主动提醒用户**：
     "知网登录态已失效，请在弹出的 Chrome for Testing 窗口完成机构登录，完成后告诉我"——
     等用户确认后再继续检索；
   - `login` 引擎侧超时 ≠ 失败（见下方工具注意事项），等 30–60 秒重试。
2. **第一轮（白名单×核心来源）**：`advanced-search`，**检索词用 `subject`（主题字段：篇名+关键词+摘要）——
   不要用 `keywords`（作者关键词精确匹配，召回极低，实测近乎为 0）**；`year_from` 与 `year_to` **必须同时传**
   （只传 year_from 会返回空）；`source_types=["CSSCI","北大核心"]`，`sort_by=相关度`，`limit=50`。
3. **客户端白名单过滤**：结果的 `journal` 字段 ∈ 下方三体系并集（含规范化），且非学位论文/报纸 → 记入候选表，标注所属体系（可多标）。
4. **第二轮（仅当过滤后 < 8 篇）**：同参数但**去掉 `source_types`**（捞 CLSCI 独有来源），仍过白名单。
5. **第三轮（仍 < 8 篇）**：**放弃白名单**，检索其他法学期刊论文；`document_type` 或标题/来源校验排除学位论文。
6. 可选加密度：对头部 CLSCI 刊（中国法学、法学研究、中外法学、东方法学等）逐刊 `journal=<刊名>`＋关键词定向检索。
7. 汇总为 `plan/literature-search.md`：

```markdown
| # | 题名 | 作者 | 期刊 | 年份 | 体系 | 链接 | 入选/排除 |
|---|------|------|------|------|------|------|-----------|
```

8. **停下让用户筛选确认**，确认后逐条 `zotero-mcp_write_item`（action=create, itemType=journalArticle，
   含 title/creators/publicationTitle/date/url/tags），把 itemKey 登记进 `plan/sources.md`。

### 期刊白名单（三体系并集，规范化）

> 规范化：《法治与社会发展》按《法制与社会发展》同一本处理（北大核心清单疑似笔误）。
> 刊名匹配用包含匹配（去书名号后比对），集刊按原名收。

**CLSCI**：中国社会科学、中国法学、法学研究、中外法学、法学家、法商研究、法学、法律科学、法学评论、政法论坛、法制与社会发展、现代法学、比较法研究、环球法律评论、清华法学、政治与法律、当代法学、法学论坛、法学杂志、华东政法大学学报、中国刑事法杂志、东方法学、China Legal Science、Frontiers of Law in China、行政法学研究、中国法律评论、民主与法制、法律适用、国家检察官学院学报

**CSSCI（含扩展版及集刊）**：法治研究、财经法学、法学杂志、中国应用法学、南大法学、行政法学研究、现代法学、经贸法律评论、人大法律评论、法律史评论、法理、人权研究、中国不动产法研究、刑法论丛、法学教育研究、出土文献与法律史研究、中山大学法律评论、上海政法学院学报（法治论丛）、经济法论丛、北大法律评论、中德法学论坛、证券法苑、法律和社会科学

**北大核心**：中国法学、法学研究、中外法学、比较法研究、法学、中国法律评论、中国刑事法杂志、知识产权、政治与法律、政法论坛、现代法学、清华法学、环球法律评论、华东政法大学学报、河北法学、行政法学研究、国家检察官学院学报、法制与社会发展、法学评论、法学家、法商研究、法律适用、北方法学、当代法学、东方法学、法律科学、法学杂志、法学论坛、民主与法制、政法学刊

---

## P3 PDF → Markdown

- **只用** `mdconvert.py`（项目已装，别默认 markitdown 直喂；输出必须 UTF-8，用 `-o` 不用 PowerShell `>`）。
- 系统 Python 3.12 运行 markitdown 相关逻辑；转换后先合并断行、剔除页码再进模型。
- 登记 `reading/` 路径到 `plan/sources.md`。

## P4 单篇精读（paper-reading 法学适配）

总原则照 paper-reading：**一句话核心贡献 + 忠实原文、若无则说明、禁止臆测**（与 humanities-thesis R1–R3 同向）。
维度映射（覆盖原 9 维中的两维）：

- **Q5 实验设计** → **论证支撑体系**：作者用了哪些法条、司法案例、域外立法例、学说；每项支撑什么论点、支撑是否有效。
- **Q9 反直觉/表格扫描** → **论证薄弱点扫描**：逐节检查引注缺失、循环论证、以偏概全、结论超出论证范围；
  必须标注具体章节/页码；区分「作者自认的局限」与「我归纳的局限（非原文明确说明）」。
- Q1–Q4、Q6–Q8 照原样（动机/问题/不足与改进/路径概述/局限/价值/延伸）。

## P5 多文档综合（multi-document-summarization）

按其模板产出：文档清单（D 编号）→ 共识表 → 冲突表（只标不判真伪）→ 跨文档洞见 → 信息缺口。
法学论文组默认为**平行关系→主题聚合框架**；若按时间/观点对立可换框架。

## P6 证据映射（literature-review 硬门控）

从精读卡与综合摘要提炼 `plan/evidence-map.md`，字段照 literature-review：
`Source ID | Citation | 核心发现 | 可用事实 | 支撑论点(可写进正文的一句话) | 引用位置citation slot | 风险`。
要求：每个核心论点 ≥1 条强支撑；研究空白须 ≥2 条文献共同支撑。**无此表不写综述。**

## P7 写作（两条线）

### 线 A：文献综述
1. 结构用 literature-review 四段式：引言 → 研究现状（按主题组织，用综合摘要做底料）→ 研究评述 → 研究空白与定位。
2. 写"综合不罗列"、批判性分析——literature-review 方法论；行文语言规范、术语准确——writing-law；
   摘要/引言模板与文本评估——humanities-thesis（`scripts/review.py` 六维检查可跑则跑）。

### 线 B：整篇论文
1. paper-orchestration 总控：先做 Stage Detection（法学论文常见 S0→S1→S4→S5；S3 实验段映射为案例/实证材料准备）；
   plan 三件套 + 每章任务包落盘；整稿起草须按其 Multi-Agent Chapter Gate 分派子代理，单代理降级须先问用户。
2. S0 用 brainstorming-research（其 HARD GATE 优先：未获最终确认不建 chapters、不写正文）。
3. 文体结构用 writing-law（问题导向/规范分析/案例研究/比较法四种结构任选）、
   论证递进与理论落地用 humanities-thesis 方法论原则。

## P8 引注规范化（csl-citation）

- 逐条调 `csl-citation` skill 的 `scripts/generate_citation.py` 校核/生成脚注（《法学引注手册》第二版）。
- 支持句柄：`作者：《篇名》，载《刊名》YYYY年第N期，第M页。`、法条、案号、英文文献等。

## P9 产出 Word（docx-official 强制）

- 生成 `.docx` 前**必须加载 docx-official skill** 并遵循其东亚字体槽与版式惯例；不得手搓 python-docx。
- 成品放 `output/`，用 `present_files` 呈现（声明其依赖的 `.md` 源为 related_files）。

---

## 冲突裁决（已确认，勿再摇摆）

1. **引注体例**：csl-citation（第二版+脚本）**绝对优先于** writing-law 示例与 literature-review 的 GB/T 7714。
2. **中文检索**：literature-review 的"HARD-GATE：AI 不能直接搜中文库"被本机 cnki-mcp 实证推翻——以工具为准；
   该 skill 只取其整理方法、evidence-claim map 与综述结构。
3. **流程门控**：paper-orchestration 管阶段与任务包；brainstorming-research 管起点确认；互不覆盖。
4. **精读框架**：paper-reading 9 维经上述法学适配后使用；忠实原文原则两处同向，无冲突。

## 工具注意事项速查

- **cnki-mcp**：先 `login`；限速 1 次/秒、每日 1000 配额；`source_types` 枚举只有
  AMI/CSCD/CSSCI/EI/SCI/WJCI/北大核心（**没有 CLSCI**，故白名单必须客户端过滤）；单篇详情用 `get-info-from-url`。
  **login/检索报引擎侧 `Request timed out` 时不要重开会话**：服务端会继续执行（浏览器窗口照常弹出并完成机构登录，
  用 `Get-Process` 看 "Google Chrome for Testing" 窗口标题确认进度），等 30–60 秒直接重试检索即可；
  首个 login 调用可能占住串行队列，连续超时属排队现象。**`keywords` 参数弃用**（见 P1 第 2 步）。
- **zotero-mcp**：工具名带 `zotero-mcp_` 前缀；**Zotero 必须开着**（关掉则调用报 fetch failed，重开约 2 秒恢复，
  无需重启引擎）；`add_by_identifier` 不认知网链接（用 write_item 建条目）；本地 PDF 用
  `write_item action=import + filePath` 挂附件。
- **PDF 全文获取**：知网无下载接口，走方案 A 半自动——**必须由用户在自己的浏览器（Edge）下载**
  （Chrome for Testing 实测无法打开知网下载界面、无法装 Zotero Connector，别尝试）。
  因此存在"用户 Edge 登录知网 ↔ 检索浏览器登录态"互踢风险：靠 P1 的**探测式登录提醒**兜底，
  掉线时请用户在 Chrome for Testing 窗口重登即可；下载好的 PDF 交我用 `write_item action=import` 挂附件。
- **csl-citation 脚本**：`python <csl-citation skill目录>/scripts/generate_citation.py "文献描述"`。
