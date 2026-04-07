# 内容 Skills 目录（功能说明 + 输入 / 输出 / 触发语）

本文档与 [content-skills-implementation-plan.md](./content-skills-implementation-plan.md) 第二节一致。

**路径约定**：下表所有路径省略公共前缀 `content-production/`；例如写 `inbox/*` 实际指 `content-production/inbox/*`。完整目录结构见 [data-contracts.md](./data-contracts.md)。

**填写说明**：见 [skill-io-guide.md](./skill-io-guide.md)。

**归类规则**：`generate-video` 固定归入排版与视觉层；`auto-curate`、`wechat-full` 各自独立计数。本文档同时记录**已实现**与**规划中**的 Skill，其中 collect 层当前已实现 `wechat-collect`、`news-collect`、`topic-research`、`wechat-report` 四个入口。

---

<a id="skill-handoff-signals"></a>

## Skill 之间传输信息的「信号」是什么

单表里的「输入 / 输出」写的是**单 Skill 视角**；多 Skill 串联时，还需要约定 **handoff 信号**：下游靠什么**唯一、稳定地**认出上游产物。

### 三类信号（本仓库默认）

| 类型 | 含义 | 示例 |
|------|------|------|
| **路径信号** | 落在磁盘上的文件路径，下游 Skill 或人 `@` 该路径继续 | `inbox/20260403-show-transcript.md` |
| **内容信号** | 文件内约定字段，供去重、追溯、拼 Prompt | YAML frontmatter：`source_url`、`slug`、`title`；正文内 `## 摘要` |
| **外部 ID 信号** | 不走路径时，用平台侧主键 | 飞书多维表 **行 ID** / `record_id`；`source_url` 去重；X 发帖后的 `status_id` |

**稳定主键建议**：同一选题在流水线中共享一个 **`slug`**（或日期 `YYYYMMDD` + 短名），所有中间文件命名为 `…-{slug}-…`，避免「下一 Skill 不知道读哪份」。

### 典型链路：谁把什么信号传给谁

| 链路 | 上游 Skill | 传递信号（名称 + 形态） | 下游 Skill |
|------|-------------|--------------------------|------------|
| 播客转写 → 长文 | `daily-content-curator` | 路径：`inbox/*-transcript.md`；建议含 `source_url`、`episode_title` | `solo-writer` |
| X 热点 → 案例文 | `x-viral-collector` / `attentionvc-ai-daily` | 路径：`inbox/*-report.md`；内嵌条目链接列表 | `case-writer-hybrid` |
| 外文 URL → 精读改写 | `article-rewriter` | 直接吃外文 URL（不经翻译层），输出 `ready/*-wechat.html` 或 `drafts/*-article.md` | `wechat-formatter`（若 Skill 未内置排版） |
| 外文 → 翻译 → 通用创作 | `tiered-translate` | 路径：`drafts/*-zh.md`；可选 `glossary_id` | `solo-writer` / `case-writer-hybrid` |
| 中文成稿 → 微信排版 | 任一创作 Skill | 路径：`drafts/*-article.md`（Markdown）；若上游已直接出 HTML，信号改为 `ready/*-wechat.html` 并**跳过** formatter | `wechat-formatter` |
| 成稿 → 封面 | 任一创作/排版 Skill | 标题 + 核心关键词 | `cover-generator` / `cover-4styles` / `xhs-cover-template` / `xiaolvshu-cover` |
| 长文 → 视频脚本 | 创作层成稿 | 路径：`drafts/*-article.md` 或公网 URL | `viral-video-script` |
| 脚本 → 配音 → 成片 | `viral-video-script` → `minimax-tts` | 脚本路径 `storyboards/*-script.md`；TTS 输出 `video-assets/*-voice.*`；分镜图目录 `video-assets/*-frames/` | `video-from-storyboard` |
| 拆解 → 反哺创作 | `video-optimize` | 路径：`inbox/*-video-deconstruct.md`；内嵌「结构/钩子/节奏」小节 | `viral-video-script`（非自动，属反馈环） |
| 采集归档 → 小红书 | `feishu-bitable-sync` | 飞书行字段：`source_url`、`title`、`summary`、**行 record_id** | `xiaohongshu-note-generator` → `xhs-cover-template` |
| 一键采集入库 | `auto-curate` | 等价于：`daily-content-curator` 的输出路径 **+** `feishu-bitable-sync` 写入成功的 **record_id / source_url** | 下游读飞书或本地镜像 |

### 与「写作技能」类 JSON 契约的关系

若某 Skill 在实现上使用 **JSON 请求体**（如 `context` / `requirement` / `writing_style`），则 **Skill 间信号**仍可映射为：**上一 Skill 的 `output.content` → 下一 Skill 的 `input.context`**，并附带 `requirement` 说明本步要做什么。文件型流水线则以 **路径 + frontmatter** 代替 JSON，二者选一种为主，不要混用且无文档。

---

## 采集层（10；已实现 4，规划中 6）

| Skill | 状态 | 功能说明 | 输入 | 输出 | 触发语 |
|------|------|----------|------|------|--------|
| `daily-content-curator` | 规划中 | 从预配置的 YouTube 频道和小宇宙播客自动抓取音视频，获取字幕/转录文本并改写 | 预配置频道/订阅；可选「日期范围」或「只跑今日」 | `inbox/*-transcript.md`、改写摘要或报告 | 「跑今日播客采集」「同步小宇宙转写」 |
| `x-viral-collector` | 规划中 | 通过 Apify 采集 X（Twitter）上 AI 相关的高互动推文和长文，生成热门内容报告 | Apify 可用；关键词或列表 ID；可选时间窗 | `inbox/*-x-viral-report.md` | 「抓本周 X 上 AI 热门长文」「生成 X 热门报告」 |
| `ai-income-stories` | 规划中 | 从 X 采集「用 AI 编程工具赚钱」的真实故事，提取收入、工具、背景等结构化数据 | 搜索关键词或种子账号；条数上限 | 结构化表格/Markdown（收入、工具、背景字段） | 「采集 AI 赚钱故事」「导出收入案例表」 |
| `attentionvc-ai-daily` | 规划中 | 从 AttentionVC.ai 抓取 X 上 AI 热门长文，用 Jina Reader 获取全文，生成日报 | 无或「当日」；站点可访问 | `inbox/*-ai-daily.md` | 「生成 AttentionVC 今日 AI 日报」 |
| `wechat-collect` | 已实现 | 公众号文章采集，输出可直接交给 `case-writer-hybrid` 的 brief，并归档原始 HTML | 公开文章 URL 文本文件 | `inbox/*-gzh-brief.md` + `inbox/raw/wechat/*.html` | 「采集这篇公众号正文」「把这篇公众号文章转成 brief」 |
| `news-collect` | 已实现 | 基于 repo-local `news-aggregator-skill` 做宽扫描，统一写成本地 `news-report.md` 与 raw JSON，并为推荐条目补 `写作价值判断 / 推荐切口 / 推荐框架与标题方向` | `collector_request_markdown`（`profile`、`sources`、`keyword`、`limit`、`deep`、`title`） | `inbox/YYYYMMDD-*-news-report.md` + `inbox/raw/news/YYYY-MM-DD/*.json` | 「扫一下海外最新资讯」「做国内媒体今日扫描」 |
| `topic-research` | 已实现 | 基于 repo-local `tavily-research` 对选定主题做二跳深研，输出本地 `research.md` 与 raw JSON，并补 `选题是否值得写 / 推荐框架 / 开头钩子 / 标题方向` | `research_request_markdown`（`topic`、`question`、`model`、`source_file`、`seed_urls`） | `inbox/YYYYMMDD-*-research.md` + `inbox/raw/research/YYYY-MM-DD/*.json` | 「把这个题目做深研」「围绕这份扫描报告继续研究」 |
| `wechat-report` | 已实现 | 围绕一个主题收集多篇公众号原文，输出文章总表、互动对比表、内容结构表，并新增 `爆款写法标签表 / 标题与开头拆解 / 结尾与转发钩子`，飞书同步状态仍默认为待确认 | `wechat_report_request_markdown`（`topic`、`max_articles`、`seed_urls`、`collect_engagement`、`discovery_mode`） | `inbox/YYYYMMDD-*-wechat-report.md` + `inbox/raw/wechat-report/YYYY-MM-DD/*.json` | 「围绕这个主题补几篇公众号原文并做表」「先采几篇公众号文章做对比」 |
| `wechat-subscribe` | 规划中 | 公众号订阅管理 | 订阅/取消的账号 ID 或列表 | 更新后的订阅配置 | 「订阅某某公众号」「列出当前订阅」 |
| `wechat-topic-monitor` | 规划中 | 公众号选题监控（主菜单入口） | 无（进入菜单）或监控规则 | 选题列表、告警或待处理队列 | 「打开公众号选题监控」「今天监控选题有什么」 |
| `meme-search` | 规划中 | 全网梗图搜索：多策略并行检索，返回相关梗图集合及解读 | 关键词或主题句；可选数量 | 梗图链接/文件列表 + 短解读文本 | 「搜梗：xxx」「用这个主题找梗图」 |

## 翻译层（1）

| Skill | 功能说明 | 输入 | 输出 | 触发语 |
|------|----------|------|------|--------|
| `tiered-translate` | 三种模式（快速/标准/精翻）翻译文章与文档，支持自定义术语表 | 外文 URL 或 `inbox/*.md`；模式三选一；可选 `knowledge/glossary.md` | `drafts/*-zh.md` | 「把这篇链接精翻成中文」「标准模式翻译这个文件」 |

若本机 Skill 目录仍为 `baoyu-translate`，可与上表视为同一能力，仅命名不同。

## 创作层（9）

| Skill | 功能说明 | 输入 | 输出 | 触发语 |
|------|----------|------|------|--------|
| `article-rewriter` | 外文 URL 精读 → 讨论角度 → 三写手竞争创作 → 审稿 → 选稿 → 信息图 → 公众号 HTML | 外文文章 URL（直接吃原文，不需先翻译）；可选角度偏好 | `ready/*-wechat.html`（或链上中间稿 `drafts/*` + 终版 HTML） | 「精读这篇 URL 写成公众号」「外文长文改写成可发版本」 |
| `case-writer-hybrid` | 结构化 brief → 选题评分 → 框架路由 → writer / critic / judge 多轮对抗 → 轻量去 AI 味 → 主稿 + 写作包 + 审稿轨迹；三轮不过线即中断并通知人工处理 | `brief_markdown`（含 `topic`、`target_reader`、`core_view`、`arguments`、`cases`） | `drafts/*-article.md` + `drafts/*-writing-pack.md` + `drafts/*-writing-pack.json` + `drafts/*-review-trace.json` | 「用这个 brief 出主稿」「跑写作闭环」「如果不过线就停下来」 |
| `humanizer-zh` | 对中文正文做受约束的去 AI 味清洗，保留事实、结构、标题和核心论点，同时输出命中规则报告 | `markdown_or_text` | `drafts/*-humanized.md` + `drafts/*-humanizer-report.json` | 「去一下 AI 味」「把这篇洗得更像人写的」 |
| `solo-writer` | 播客文字稿 → 精读 → 讨论角度 → 单写手写作（去 AI 味）→ 信息图 → 公众号 HTML | `inbox/*-transcript.md`、已翻译稿 `drafts/*-zh.md`、或粘贴转写 | `drafts/*-article.md` 与/或 `ready/*-wechat.html` | 「把这段播客转写成公众号」「单写手去 AI 味」 |
| `interview` | 多轮深度访谈挖掘用户故事 → 智能推荐文章方向 → 输出公众号爆款文章 | 访谈逐字稿或录音转写；可选人物背景 | `drafts/*-interview-article.md` | 「根据访谈稿写人物稿」「从访谈里出一篇爆款」 |
| `ad-writing` | 读取广告主 PDF Brief → 设计测试用例 → 输出约 3000 字公众号推广文章 | 广告主 PDF Brief 路径或上传 | `drafts/*-ad-article.md` | 「按这个 Brief 写推广文」「读 PDF 写约 3000 字软文」 |
| `ad-writing-v2` | Brief → 全网调研 → 3 版大纲审批 → 用户实测 → 基于真实结果写作 | Brief + 产品/落地页；需配合实测数据回传 | `drafts/*-ad-v2.md` | 「v2 流程写广告文」「先大纲再实测再成稿」 |
| `meme-to-script` | 用户上传梗图 → AI 深度解读 → 网络搜索补充素材 → 三编剧竞写 → 评审打分 → 公众号 HTML | 梗图文件或 URL；可选观点 | `ready/*-wechat.html` | 「这张梗图扩展成公众号」「梗图竞写成稿」 |
| `hokkaido-writer` | Skills 工具书写作助手：专门优化案例、补充章节、润色文字 | 现有书稿章节或 `drafts/*.md`；修改指令 | 同路径更新稿或 `drafts/*-rev.md` | 「补这一章案例」「按工具书风格润色」 |
| `viral-video-script` | 输入文章 → 三写手并行竞写 → 评审打分 → 输出含时间标记、画面提示、情绪线的视频脚本 | `drafts/*-article.md` 或正文 URL | `storyboards/*-script.md` | 「把这篇改成口播/分镜脚本」「爆款视频脚本竞写」 |

## 排版与视觉层（7）

| Skill | 功能说明 | 输入 | 输出 | 触发语 |
|------|----------|------|------|--------|
| `wechat-formatter` | 将 Markdown 转为微信公众号可粘贴的 HTML，CSS 内联、微信兼容性适配、自定义主题；若同目录存在 `*-writing-pack.json`，会自动消费摘要块、金句高亮、转发配文和互动 CTA | `drafts/*.md`；可选主题名 | `ready/*-wechat.html` | 「排版成微信 HTML」「Markdown 转公众号」 |
| `generate-image` | AI 图片生成与变换 | 文生图提示词；或原图 + 变换指令 | 文章配图 → `ready/*-img-*.png`；视频分镜 → `video-assets/*-frames/*.png` | 「生成信息图」「把这张图改成插画风」 |
| `cover-generator` | 上传照片 + 参考封面 → 交互式弹框 → 多尺寸专业视频封面 | 人物/场景照片；参考封面图；标题文案 | 多尺寸封面 PNG → `ready/*-cover-*.png` | 「做视频封面多尺寸」「参考这张图的风格」 |
| `cover-4styles` | 上传头像 + 标题 → 一键批量生成 4 种预设风格视频封面 | 头像图；主标题字符串 | 4 张封面 PNG → `ready/*-cover-*.png` | 「四风格封面」「一键四封面」 |
| `xhs-cover-template` | 小红书封面（Premium Split 风格：上深下白） | 标题；可选副标题/关键词 | 小红书比例封面图 → `ready/*-xhs-cover.png` | 「小红书 Premium Split 封面」 |
| `xiaolvshu-cover` | 公众号小绿书封面：输入标题/副标题/作者 → 4 种视觉风格竖版封面 | 标题、副标题、作者名 | 4 张竖版封面 → `ready/*-lvs-cover-*.png` | 「小绿书封面四风格」 |
| `generate-video` | AI 视频生成（归属本层，不重复计入视频层） | 文生视频提示词或首帧；时长等参数 | `video-assets/*-gen.mp4` | 「按这句提示生成短视频」 |

## 视频与音频层（4）

| Skill | 功能说明 | 输入 | 输出 | 触发语 |
|------|----------|------|------|--------|
| `video-optimize` | 支持 B 站/YouTube/小红书/抖音链接，豆包大模型视频理解，8 维度爆款拆解报告 | 平台视频 URL | `inbox/*-video-deconstruct.md` | 「拆解这条爆款视频」「8 维度分析报告」 |
| `video-local-analyze` | 仅支持本地视频文件，豆包 API 原生视频理解，输出拆解报告 | 本地 `.mp4` 等路径 | `inbox/*-local-video-deconstruct.md` | 「分析本地这个视频文件」 |
| `video-from-storyboard` | 分镜图片 + 音频 + 文案 → Whisper 语音对齐字幕 → 自动合成带字幕视频 | 分镜图目录 `video-assets/*-frames/`；TTS 音频；文案/脚本 | `video-assets/*-final.mp4` | 「分镜+配音合成成片」「对齐字幕导出视频」 |
| `minimax-tts` | MiniMax T2A API 文字转语音，支持多种音色 | 口播全文；音色 ID；语速等 | `video-assets/*-voice.wav` 或 `.mp3` | 「这段脚本用某某音色配音」 |

## 分发与同步层（6；已实现 2，规划中 4）

| Skill | 功能说明 | 输入 | 输出 | 触发语 |
|------|----------|------|------|--------|
| `feishu-user-auth` | 已实现。一次性拉起飞书浏览器授权，缓存 `user_access_token + refresh_token`，供后续多维表同步直接复用 | 任意授权请求 Markdown；本机可打开浏览器；飞书应用已配置网页应用能力与回调地址 | `published/YYYYMMDD-feishu-user-auth.md` + 本机 `~/.codex/feishu-auth/content-system-sync.json` | 「先把飞书授权配好」「运行飞书用户授权」 |
| `feishu-bitable-sync` | 已实现。将 `wechat-report` 本地 raw JSON / Markdown 报告同步到飞书多维表格，按 `source_url` 去重，一篇文章一行；默认走用户授权，失败时导出 CSV 兜底 | `wechat-report` Markdown 或 raw JSON；默认需先完成 `feishu-user-auth`；兼容 `tenant` 模式 | 飞书多维表中新增/更新行（含 `source_url`） + `published/*-feishu-sync.md`；失败兜底时额外输出 `published/*-feishu-import.csv` | 「把这份公众号对比结果同步到飞书」「确认发送到飞书」 |
| `xiaohongshu-note-generator` | 从飞书多维表格拉取内容 → 转化为小红书爆款图文笔记（连续长图切片卡片） | 飞书表筛选条件或行 ID | 长图卡片 PNG/PDF 或笔记文案包 | 「从飞书生成小红书笔记」「拉表出长图」 |
| `obsidian-to-x` | 发布内容到 X（Twitter），支持常规推文、X Articles、公众号 HTML | `ready/*-wechat.html` 或 Markdown；发布模式 | X 上已发帖链接或草稿状态 | 「发推文」「发 X Article」「同步这篇到 X」 |
| `auto-curate` | 一体化编排：`daily-content-curator` + `feishu-bitable-sync` | 同 `daily-content-curator`；飞书配置就绪 | 转写/摘要 + 飞书表更新 | 「一键采集并入库飞书」「auto-curate 跑今日」 |
| `wechat-full` | 完整流程：`wechat-collect` + `wechat-report` | 采集目标与报告范围 | 采集结果 + `wechat-report` 报告文件 | 「公众号采集并出潜力报告」「跑 wechat-full」 |

---

## 维护说明

- **当前已实现的 collect**：`wechat-collect`、`news-collect`、`topic-research`、`wechat-report`；其余 collect 条目仍作为规划目录保留。  
- **仍需本地化**：飞书表字段名、Apify/MiniMax 等密钥与配额、以及本机真实文件夹是否与 `content-production/` 一致；不一致时只改本表与 [data-contracts.md](./data-contracts.md)。  
- **归类规则**：`generate-video` 归排版与视觉层；组合 Skill 独立计数。其余层级条目若尚未落地，也需在实现时同步更新状态。

---

*与 [skill-io-guide.md](./skill-io-guide.md)、[data-contracts.md](./data-contracts.md) 配套使用。*
