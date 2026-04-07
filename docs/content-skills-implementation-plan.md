# 内容 Skills 体系实施计划

本版采用“**全量蓝图 + 当前状态**”写法：保留六层内容技能蓝图，但把当前仓库里已经接入 runtime、已经跑出产物、以及仍处于规划的部分明确区分。

默认只把 **atomic skill** 计入总数；`wechat-studio`、vendor skill、runtime 辅助模块不计入 39 个技能总盘。路径约定仍以 `content-production/` 为公共前缀，详见 [data-contracts.md](./data-contracts.md)。

参考材料：

- [Skill 全目录与功能说明](./skill-catalog.md)
- [中间产物与目录约定](./data-contracts.md)
- [Skill Runtime 使用说明](./runtime-usage.md)
- [飞书多维表字段契约](./feishu-schema.md)

---

## 一、六层蓝图与当前落地状态

### 1.1 六层蓝图总览

| 层级 | 蓝图数量 | 当前已完成 | 职责摘要 |
|------|----------|------------|----------|
| 采集层 | 11 | 4 | 从公众号、资讯源、X、播客、梗图等抓取原始素材，沉淀可继续创作的本地信号 |
| 翻译层 | 1 | 0 | 外文本地化，作为外文内容的可选旁路 |
| 创作层 | 10 | 2 | 从 brief、转写稿、案例、访谈等产出中文长文与视频脚本 |
| 排版与视觉层 | 7 | 2 | 微信排版、文章配图、封面、AI 视频生成 |
| 视频与音频层 | 4 | 0 | 拆解、配音、分镜与视频合成 |
| 分发与同步层 | 6 | 2 | 飞书中枢、X、小红书、一体化编排 |

**合计：39 个 atomic skills。** 当前已完成 10 个，其中 3 条主链路已经有真实样例或回执可验证。

### 1.2 状态定义

- `已完成（原有）`
  该 skill 在仓库基线 `HEAD` 中已存在 `skills/*/skill.json`，且当前仍接入 [skill_runtime/engine.py](../skill_runtime/engine.py)。
- `已完成（新增）`
  该 skill 相对仓库基线为新增能力，当前已存在 `skills/*/skill.json`，且已接入 [skill_runtime/engine.py](../skill_runtime/engine.py)。
- `辅助组件/依赖`
  为工作台、vendor skill 或 runtime 支撑模块，不单独计入 39 个 atomic skills。
- `规划中`
  保留在蓝图中，但当前未作为本仓库独立 runtime 节点落地。
- `已验证`
  仅用于说明已完成能力里哪些已经有 `content-production/` 真实产物或回执。

### 1.3 当前盘点

**已完成（原有）4 个**

- `case-writer-hybrid`
- `generate-image`
- `wechat-collect`
- `wechat-formatter`

**已完成（新增）6 个**

- `humanizer-zh`
- `news-collect`
- `topic-research`
- `wechat-report`
- `feishu-user-auth`
- `feishu-bitable-sync`

**辅助组件 / 依赖（不计入 39）**

- `wechat-studio`
- `news-aggregator-skill`
- `tavily-research`
- `wechat-article-extractor-skill`
- `skill_runtime/writing_core.py`
- `skill_runtime/feishu_auth.py`
- `skill_runtime/wechat_access.py`

**当前已验证链路**

- `stage1-pipeline`
  `case-writer-hybrid -> generate-image -> wechat-formatter`
- `stage2-wechat-pipeline`
  `wechat-collect -> case-writer-hybrid -> generate-image -> wechat-formatter`
- `wechat-report -> feishu-user-auth -> feishu-bitable-sync`
  其中 `feishu-bitable-sync` 仍遵守“先本地报告、后用户确认”的手动门控

### 1.4 当前架构判断

1. **主链路已从“纯规划”进入“已跑通”阶段。**
   阶段 1 和阶段 2A 不再只是方案，已经存在 workflow manifest 与产物样例。
2. **采集层已经从单一公众号采集扩展到“资讯扫描 / 深研 / 公众号对比”三条情报支路。**
   当前采集层已落地 `wechat-collect`、`news-collect`、`topic-research`、`wechat-report` 四个入口。
3. **飞书中枢底座已可用，但阶段 3 仍未完整闭环。**
   当前完成的是 `wechat-report -> feishu-user-auth -> feishu-bitable-sync`，`xiaohongshu-note-generator` 仍未落地。
4. **辅助工作台与 atomic skill 已经分层。**
   `wechat-studio` 作为可选工作台存在，但不再算进技能总数，也不占主链路节点名额。

---

## 二、Skill 蓝图清单（按层 + 当前状态）

下表保留全量蓝图，但每个条目都明确当前状态与备注。备注优先记录：`已接 runtime`、`已有样例产物`、`需用户确认`、`依赖外部平台`。

### 2.1 采集层（11）

| Skill | 状态 | 功能说明 | 备注 |
|------|------|----------|------|
| `daily-content-curator` | 规划中 | 从预配置的 YouTube 频道和小宇宙播客自动抓取音视频，获取字幕/转录文本并改写 | 规划中的自动采集主入口；后续可与 `auto-curate` 组合 |
| `x-viral-collector` | 规划中 | 通过 Apify 采集 X 上 AI 相关的高互动推文和长文，生成热门内容报告 | 依赖 Apify / X 数据源 |
| `ai-income-stories` | 规划中 | 从 X 采集“用 AI 编程工具赚钱”的真实故事，提取收入、工具、背景等结构化数据 | 依赖 X 数据抓取与结构化抽取 |
| `attentionvc-ai-daily` | 规划中 | 从 AttentionVC.ai 抓取 X 上 AI 热门长文，用 Jina Reader 获取全文，生成日报 | 依赖站点可访问性与外部抓取 |
| `wechat-collect` | 已完成（原有） | 公众号文章采集，输出可直接交给 `case-writer-hybrid` 的 brief，并归档原始 HTML | 已接 runtime；`stage2-wechat-pipeline` 已验证；已有 brief 与 raw HTML 样例 |
| `news-collect` | 已完成（新增） | 基于 repo-local `news-aggregator-skill` 做宽扫描，统一写成本地 `news-report.md` 与 raw JSON | 已接 runtime；已有 `news-report.md` 与 raw JSON 样例；依赖 vendor skill |
| `topic-research` | 已完成（新增） | 基于 repo-local `tavily-research` 对选定主题做二跳深研，输出本地 `research.md` 与 raw JSON | 已接 runtime；已有 `research.md` 与 raw JSON 样例；依赖 Tavily CLI |
| `wechat-report` | 已完成（新增） | 围绕一个主题收集多篇公众号原文，输出文章总表、互动对比表、内容结构表与写法拆解 | 已接 runtime；已有本地报告与 raw JSON；后续飞书同步需用户确认 |
| `wechat-subscribe` | 规划中 | 公众号订阅管理 | 规划中的长期监控前置能力 |
| `wechat-topic-monitor` | 规划中 | 公众号选题监控（主菜单入口） | 规划中的监控入口，尚未落地 |
| `meme-search` | 规划中 | 全网梗图搜索：多策略并行检索，返回相关梗图集合及解读 | 规划中的素材入口，未接 runtime |

### 2.2 翻译层（1）

| Skill | 状态 | 功能说明 | 备注 |
|------|------|----------|------|
| `tiered-translate` | 规划中 | 三种模式（快速 / 标准 / 精翻）翻译文章与文档，支持自定义术语表 | 外文旁路仍保留在蓝图中；当前主阵地以中文内容为主 |

### 2.3 创作层（10）

| Skill | 状态 | 功能说明 | 备注 |
|------|------|----------|------|
| `article-rewriter` | 规划中 | 外文 URL 精读 -> 讨论角度 -> 三写手竞争创作 -> 审稿 -> 选稿 -> 信息图 -> 公众号 HTML | 与翻译层形成两种外文入口方案 |
| `case-writer-hybrid` | 已完成（原有） | 结构化 brief -> writer / critic / judge 多轮对抗 -> 主稿 + 写作包 + 审稿轨迹 | 已接 runtime；`stage1-pipeline` 与 `stage2-wechat-pipeline` 已验证；三轮不过线时会中断 |
| `humanizer-zh` | 已完成（新增） | 对中文正文做受约束的去 AI 味清洗，保留事实、结构、标题和核心论点，同时输出命中规则报告 | 已接 runtime；当前是独立辅助创作节点；尚未纳入默认 workflow |
| `solo-writer` | 规划中 | 播客文字稿 -> 精读 -> 讨论角度 -> 单写手写作（去 AI 味）-> 信息图 -> 公众号 HTML | 与 `daily-content-curator`、`tiered-translate` 相关联 |
| `interview` | 规划中 | 多轮深度访谈挖掘用户故事 -> 推荐文章方向 -> 输出公众号爆款文章 | 规划中的人物稿 / 采访稿能力 |
| `ad-writing` | 规划中 | 读取广告主 PDF Brief -> 设计测试用例 -> 输出约 3000 字公众号推广文章 | 依赖 PDF 读取与商业化写作流程 |
| `ad-writing-v2` | 规划中 | Brief -> 全网调研 -> 3 版大纲审批 -> 用户实测 -> 基于真实结果写作 | 比 `ad-writing` 更重运营协同 |
| `meme-to-script` | 规划中 | 用户上传梗图 -> 深度解读 -> 网络搜索补充素材 -> 三编剧竞写 -> 评审打分 -> 公众号 HTML | 依赖 `meme-search` 或用户上传素材 |
| `hokkaido-writer` | 规划中 | Skills 工具书写作助手：优化案例、补充章节、润色文字 | 规划中的工具书写作专用节点 |
| `viral-video-script` | 规划中 | 输入文章 -> 三写手并行竞写 -> 评审打分 -> 输出含时间标记、画面提示、情绪线的视频脚本 | 视频链路入口，阶段 4 再启动 |

### 2.4 排版与视觉层（7）

| Skill | 状态 | 功能说明 | 备注 |
|------|------|----------|------|
| `wechat-formatter` | 已完成（原有） | 将 Markdown 转为微信公众号可粘贴的 HTML，支持 writing-pack sidecar | 已接 runtime；`stage1-pipeline` 与 `stage2-wechat-pipeline` 已验证；可被 `wechat-studio` 复用 |
| `generate-image` | 已完成（原有） | AI 图片生成与变换 | 已接 runtime；已有文章配图样例；当前允许本地 fallback，仍按“已完成”计入 |
| `cover-generator` | 规划中 | 上传照片 + 参考封面 -> 交互式弹框 -> 多尺寸专业视频封面 | 规划中的视频封面能力 |
| `cover-4styles` | 规划中 | 上传头像 + 标题 -> 一键批量生成 4 种预设风格视频封面 | 规划中的模板化封面能力 |
| `xhs-cover-template` | 规划中 | 小红书封面（Premium Split 风格：上深下白） | 与阶段 3 的小红书分发相关联 |
| `xiaolvshu-cover` | 规划中 | 公众号小绿书封面：输入标题 / 副标题 / 作者 -> 4 种视觉风格竖版封面 | 当前仍停留在蓝图中 |
| `generate-video` | 规划中 | AI 视频生成（归属本层，不重复计入视频层） | 仍保留为视觉层能力，不重复计入视频层 |

### 2.5 视频与音频层（4）

| Skill | 状态 | 功能说明 | 备注 |
|------|------|----------|------|
| `video-optimize` | 规划中 | 支持 B 站 / YouTube / 小红书 / 抖音链接，输出 8 维度爆款拆解报告 | 后续可作为创作反馈环 |
| `video-local-analyze` | 规划中 | 仅支持本地视频文件，输出拆解报告 | 与 `video-optimize` 互补 |
| `video-from-storyboard` | 规划中 | 分镜图片 + 音频 + 文案 -> 对齐字幕 -> 自动合成带字幕视频 | 阶段 4 核心合成节点 |
| `minimax-tts` | 规划中 | MiniMax T2A API 文字转语音，支持多种音色 | 依赖外部平台与配额 |

### 2.6 分发与同步层（6）

| Skill | 状态 | 功能说明 | 备注 |
|------|------|----------|------|
| `feishu-user-auth` | 已完成（新增） | 一次性拉起飞书浏览器授权，缓存 `user_access_token + refresh_token`，供后续多维表同步复用 | 已接 runtime；已有授权回执；依赖浏览器回调与飞书网页应用配置 |
| `feishu-bitable-sync` | 已完成（新增） | 将 `wechat-report` 本地报告同步到飞书多维表格，按 `source_url` 去重，一篇文章一行 | 已接 runtime；已有同步回执；需先用户确认；直写失败时导出 CSV 兜底 |
| `xiaohongshu-note-generator` | 规划中 | 从飞书多维表格拉取内容 -> 转化为小红书爆款图文笔记 | 阶段 3 的关键缺口，当前未落地 |
| `obsidian-to-x` | 规划中 | 发布内容到 X（Twitter），支持常规推文、X Articles、公众号 HTML | 当前优先级低于公众号 / 小红书 |
| `auto-curate` | 规划中 | 一体化编排：`daily-content-curator` + `feishu-bitable-sync` | 组合型 skill，待采集层更完整后再做 |
| `wechat-full` | 规划中 | 完整流程：`wechat-collect` + `wechat-report` | 组合型 skill；当前仍以手动串联链路为主 |

### 2.7 辅助组件与依赖（不计入 39）

| 名称 | 类型 | 当前作用 |
|------|------|----------|
| `wechat-studio` | 工作台 | 预览、微调排版与配图、资产管理、后续草稿推送；可选人工操作台 |
| `news-aggregator-skill` | vendor skill | 为 `news-collect` 提供宽扫描能力 |
| `tavily-research` | vendor skill | 为 `topic-research` 提供深研能力 |
| `wechat-article-extractor-skill` | vendor skill | 为公众号解析与抽取提供底层能力 |
| `skill_runtime/writing_core.py` | runtime 模块 | 负责 writing-pack 相关的共享逻辑 |
| `skill_runtime/feishu_auth.py` | runtime 模块 | 负责飞书 OAuth 授权、刷新与缓存 |
| `skill_runtime/wechat_access.py` | runtime 模块 | 负责公众号访问与抽取相关的共享能力 |

---

## 三、默认关联（任务 -> 推荐链路）

本节只保留当前最关键的 5 条链路。`wechat-studio` 仍是**可选工作台**，只在需要人工预览、调版、挑图或推草稿时介入，不算 atomic skill。

| 场景 | 推荐链路 | 当前状态 | 说明 |
|------|----------|----------|------|
| 阶段 1 主链路：观点 / 热点 -> 公众号长文 | `case-writer-hybrid -> generate-image -> wechat-formatter` | 已完成并验证 | 已有 `stage1-pipeline` manifest 与 Markdown / PNG / HTML 产物 |
| 阶段 2A：公众号再创作 | `wechat-collect -> case-writer-hybrid -> generate-image -> wechat-formatter` | 已完成并验证 | 已有 `stage2-wechat-pipeline` manifest 与采集样例 |
| 阶段 2B：资讯扫描 / 深研 | `news-collect -> 人工选题 -> topic-research` | 已完成，待人工衔接 | 已有 `news-report.md` 与 `research.md` 样例；当前仍保留人工选题节点 |
| 阶段 2C：公众号对比 / 飞书 | `wechat-report -> 用户阅读本地报告 -> feishu-user-auth -> feishu-bitable-sync` | 已完成并验证 | 同步仍必须经过“先本地报告、后用户确认”的门控 |
| 阶段 3：飞书到小红书 | `feishu-bitable-sync -> xiaohongshu-note-generator -> xhs-cover-template` | 部分完成 | 飞书中枢底座已完成，小红书生成与封面仍在规划中 |

**当前不纳入默认链路的方向**

- 外文旁路：`tiered-translate`、`article-rewriter`
- 播客 / 转写稿：`daily-content-curator`、`solo-writer`
- 视频链：`viral-video-script`、`minimax-tts`、`video-from-storyboard`
- 组合型编排：`auto-curate`、`wechat-full`

---

## 四、分阶段实施计划（计划 + 现状对照）

总原则仍然是：**先底座与契约，再最小闭环，再情报支路与中枢，最后进入视频与组合编排。** 但当前文档不再把所有阶段都视为“尚未开始”，而是把已经完成的阶段直接标记出来。

### 4.1 阶段总览矩阵

| 阶段 | 目标 | 关键 Skills | 当前现状 | 当前判断 |
|------|------|-------------|----------|----------|
| 阶段 0 | 协作协议、目录、handoff 契约统一 | 文档底座 + 阶段 1 核心技能契约 | 已完成 | `CLAUDE.md`、`skill-catalog.md`、`data-contracts.md` 已形成配套文档 |
| 阶段 1 | 观点 brief -> 图文（含配图） -> 微信 HTML | `case-writer-hybrid`、`generate-image`、`wechat-formatter` | 已完成并验证 | 主链路已经有 manifest 和产物，不再是纯规划 |
| 阶段 2A | 公众号采集接入主创作链 | `wechat-collect` + 阶段 1 主链路 | 已完成并验证 | 从公众号 URL 到 HTML 的链路已跑通 |
| 阶段 2B | 宽扫描 + 深研支路 | `news-collect`、`topic-research` | 已完成，待人工衔接 | 资讯扫描与深研本身已可跑，但仍依赖人工决定是否进入创作链 |
| 阶段 2C | 公众号对比与飞书同步 | `wechat-report`、`feishu-user-auth`、`feishu-bitable-sync` | 已完成并验证 | 本地报告、授权回执、飞书同步回执均已存在 |
| 阶段 3 | 飞书中枢驱动小红书分发 | `xiaohongshu-note-generator`、`xhs-cover-template` | 仅完成飞书中枢底座 | 资产同步能力已有，小红书分发能力尚未实现 |
| 阶段 4（暂缓） | 图文 -> 视频 | `viral-video-script`、`minimax-tts`、`video-from-storyboard` 等 | 未启动 | 等阶段 1～3 更稳定后再投入 |
| 阶段 5（暂缓） | 组合 skill + 反馈闭环 | `auto-curate`、`wechat-full`、反馈回写机制 | 未启动 | 等积累足够内容资产后再验证复利效果 |

### 4.2 各阶段详细说明

#### 阶段 0：协作与目录约定

**目标**

- 统一目录、命名、handoff、任务路由
- 让 AI 与人类都知道“文件放哪、下一步调哪条 skill”

**当前现状**

- 已完成
- 现有文档已经覆盖主链路、采集支路、飞书同步与目录契约

**验收判断**

- 新开会话只读文档，能说清 `inbox/`、`drafts/`、`ready/`、`published/` 的职责
- 能明确知道阶段 1 主链路与阶段 2B / 2C 的路由方式

#### 阶段 1：最小闭环——图文发布

**目标**

- 跑通 `case-writer-hybrid -> generate-image -> wechat-formatter`
- 输出标准化 Markdown、配图、微信 HTML，而不是只停留在聊天里

**当前现状**

- 已完成并验证
- 现有 [stage1-pipeline-last-run.json](../content-production/published/stage1-pipeline-last-run.json) 已记录一次完整成功运行
- 当前样例已覆盖：
  - `drafts/*-article.md`
  - `drafts/*-writing-pack.md`
  - `drafts/*-writing-pack.json`
  - `ready/*-img-1.png`
  - `ready/*-wechat.html`

**当前判断**

- 阶段 1 已经从“需要证明是否能跑通”升级为“需要继续固化质量和使用习惯”
- `generate-image` 当前允许本地 fallback，不影响其“已完成”状态

#### 阶段 2A：公众号采集接入主链路

**目标**

- 从公众号 URL 出发，自动生成 brief 并进入阶段 1 主链路

**当前现状**

- 已完成并验证
- 现有 [stage2-wechat-pipeline-last-run.json](../content-production/published/stage2-wechat-pipeline-last-run.json) 已记录完整链路
- `wechat-collect` 还会归档 raw HTML，方便后续抽取调优

**当前判断**

- 阶段 2A 目前已经满足“公众号采集 -> 再创作 -> 排版”的最小闭环
- 后续重点不是再证明它能跑，而是提升抽取质量与稳定性

#### 阶段 2B：资讯扫描 / 深研支路

**目标**

- 形成“广度扫描 -> 人工选题 -> 深度研究”的情报链

**当前现状**

- 已完成，但尚未并入默认自动创作链
- `news-collect` 已能沉淀 `news-report.md` 与 raw JSON
- `topic-research` 已能沉淀 `research.md` 与 raw JSON

**当前判断**

- 这一阶段的能力节点已经落地
- 当前缺口不在 runtime，而在“选题判断是否自动化”与“何时自动进入创作层”

#### 阶段 2C：公众号对比 / 飞书同步

**目标**

- 先把主题相关公众号文章沉淀成本地对比报告，再在用户确认后写入飞书中枢

**当前现状**

- 已完成并验证
- `wechat-report` 已能生成本地结构化报告
- `feishu-user-auth` 已能完成授权并缓存 token
- `feishu-bitable-sync` 已能按 `source_url` 去重写入飞书，失败时导出 CSV

**当前判断**

- 阶段 2C 当前已具备端到端可用性
- 仍需坚持“先本地报告、后用户确认”这一门控，避免自动写飞书带来误同步

#### 阶段 3：飞书中枢 + 小红书分发

**目标**

- 把本地内容资产接入飞书，并由飞书驱动小红书图文产出

**当前现状**

- 只完成飞书中枢底座
- `xiaohongshu-note-generator` 与 `xhs-cover-template` 仍未落地到本仓库 runtime

**当前判断**

- 阶段 3 还不能算完成
- 当前最合理的定义是：**飞书资产化已就位，小红书分发仍属下一步实现范围**

#### 阶段 4：视频与音频（暂缓）

**目标**

- 文章 -> 视频脚本 -> 配音 -> 分镜 -> 成片

**当前现状**

- 暂缓，尚未启动

**当前判断**

- 视频相关节点仍保留在蓝图中，但不建议在阶段 3 完整闭环前提前并行推进

#### 阶段 5：组合 Skill 与反馈闭环（暂缓）

**目标**

- 用组合 skill 减少操作步骤，用反馈环提升后续产出质量

**当前现状**

- 暂缓，尚未启动

**当前判断**

- 等飞书中枢与更多真实内容积累起来后，再验证 `auto-curate`、`wechat-full` 的收益更合理

---

## 五、当前证据文件

本节列出当前已经存在、可用于证明“不是纯规划稿”的关键文件。

### 5.1 Workflow 与回执

- [阶段 1 manifest](../content-production/published/stage1-pipeline-last-run.json)
- [阶段 2A manifest](../content-production/published/stage2-wechat-pipeline-last-run.json)
- [飞书用户授权回执](../content-production/published/20260407-feishu-user-auth.md)
- [飞书同步回执](../content-production/published/20260407-harness-engineering-feishu-sync.md)

### 5.2 情报支路样例

- [资讯扫描样例：海外补充扫描](../content-production/inbox/20260407-harness-engineering-海外补充扫描-news-report.md)
- [资讯扫描样例：国内补充扫描](../content-production/inbox/20260407-harness-engineering-国内补充扫描-news-report.md)
- [深研样例：国内外公众号综合分析](../content-production/inbox/20260407-harness-engineering-国内外-公众号综合分析-research.md)
- [公众号对比报告样例](../content-production/inbox/20260407-harness-engineering-wechat-report.md)

### 5.3 主链路产物样例

- [阶段 1 brief 样例](../content-production/inbox/20260407-harness-engineering-一人公司-brief.md)
- [阶段 1 主稿样例](../content-production/drafts/harness-engineering-一人公司-article.md)
- [阶段 1 配图样例](../content-production/ready/harness-engineering-一人公司-img-1.png)
- [阶段 1 微信 HTML 样例](../content-production/ready/harness-engineering-一人公司-wechat.html)

---

## 六、下一步（基于当前现状）

1. **继续把阶段 3 补完整。**
   重点不是再扩 skill 名单，而是落地 `xiaohongshu-note-generator` 与 `xhs-cover-template`，让“飞书中枢 -> 小红书分发”真正闭环。
2. **决定阶段 2B 是否自动进入创作层。**
   当前 `news-collect` 与 `topic-research` 已可用，但仍依赖人工选题；下一步应明确哪些条件下允许自动生成 brief。
3. **完善已完成 skill 的验证覆盖。**
   `humanizer-zh` 已接 runtime，但还缺少清晰的独立验证样例；后续应补充 `*-humanized.md` 与报告样例。
4. **暂不提前启动视频与组合编排。**
   在阶段 3 真正闭环前，阶段 4 / 5 继续保留为蓝图即可。

---

*文档版本：2026-04-07 v4（全量蓝图 + 当前状态版）。后续若 `skill-catalog.md`、runtime 注册表或阶段验证证据变化，应同步更新本文件。*
