# 内容流水线协作入口

本文档是当前项目的执行入口，用于统一人和 AI 在内容生产流程中的协作方式。当前优先级覆盖阶段 0 到阶段 3 的主链路，以及新增的资讯采集 / 深研支路：

- 阶段 1：`case-writer-hybrid` -> `generate-image` -> `wechat-formatter`
- 阶段 2A：`wechat-collect` -> 阶段 1 主链路
- 阶段 2B：`news-collect` -> 人工选题 -> `topic-research`
- 阶段 2C：`wechat-report` -> 用户确认 -> （首次先 `feishu-user-auth`）-> `feishu-bitable-sync`
- 阶段 3：`feishu-bitable-sync` -> `xiaohongshu-note-generator` -> `xhs-cover-template`

## 1. 项目目标

把内容生产从单次聊天输出，升级为可复现、可交接、可分发的流水线。

当前主阵地：

- 首发形态：公众号图文
- 次级分发：小红书
- 当前暂缓：视频链路、X 分发、外文翻译链、播客转写链
- 当前工作台：**`wechat-studio` / 微信包装工作台**（当前实现目录为 `skills/wechat-studio/`）

## 2. 协作铁律

- 不擅自删除、覆盖、搬动已有素材。
- 中间产物必须按约定路径落盘，不只保留在聊天里。
- 同一篇内容只保留一条当前真相路径，避免多份“最终版”。
- 若创作结果已经是 HTML，先确认是否跳过 `wechat-formatter`，避免重复排版。
- 优先复用已有文档约定；新增规则时同步更新 `docs/` 下文档。

## 3. 当前主链路与情报支路

输入类型：

- 观点 brief
- 热点评论 brief
- 公众号采集后的可改写素材
- 公众号多篇原文对比采集请求

默认执行顺序：

1. `case-writer-hybrid`
2. `generate-image`
3. `wechat-formatter`

新增情报支路：

1. `news-collect`
2. 人工选题
3. `topic-research`

新增公众号情报支路：

1. `wechat-report`
2. 用户阅读本地报告
3. 首次同步前运行 `feishu-user-auth`
4. 用户确认后运行 `feishu-bitable-sync`

可选人工工作台：

- `wechat-studio`：用于预览、微调排版与图片、后续推草稿

标准产物：

1. 输入素材：`content-production/inbox/`
2. Markdown 成稿：`content-production/drafts/{slug}-article.md`
3. 配图：`content-production/ready/{slug}-img-*.png`
4. 微信 HTML：`content-production/ready/{slug}-wechat.html`

情报支路产物：

1. 资讯扫描报告：`content-production/inbox/YYYYMMDD-{slug}-news-report.md`
2. 扫描 raw JSON：`content-production/inbox/raw/news/YYYY-MM-DD/{slug}.json`
3. 深研报告：`content-production/inbox/YYYYMMDD-{slug}-research.md`
4. 深研 raw JSON：`content-production/inbox/raw/research/YYYY-MM-DD/{slug}.json`

公众号情报支路产物：

1. 公众号对比报告：`content-production/inbox/YYYYMMDD-{slug}-wechat-report.md`
2. 公众号对比 raw JSON：`content-production/inbox/raw/wechat-report/YYYY-MM-DD/{slug}.json`
3. 飞书授权回执：`content-production/published/YYYYMMDD-feishu-user-auth.md`
4. 飞书同步回执：`content-production/published/YYYYMMDD-{slug}-feishu-sync.md`
5. 飞书 CSV 兜底：`content-production/published/YYYYMMDD-{slug}-feishu-import.csv`

## 4. 任务路由

| 场景 | 应走链路 | 状态 |
|------|----------|------|
| 观点/热点 -> 公众号长文 | `case-writer-hybrid` -> `generate-image` -> `wechat-formatter` | 当前主用 |
| 公众号文章再创作 | `wechat-collect` -> `case-writer-hybrid` -> `generate-image` -> `wechat-formatter` | 当前可用 |
| 海外 / 国内资讯宽扫描 | `news-collect` -> 人工选题 -> `topic-research` | 当前可用 |
| 公众号多篇对比 -> 飞书 | `wechat-report` -> 用户确认 -> （首次先 `feishu-user-auth`）-> `feishu-bitable-sync` | 当前可用 |
| 飞书归档 -> 小红书 | `feishu-bitable-sync` -> `xiaohongshu-note-generator` -> `xhs-cover-template` | 第三阶段 |
| 外文改写 | `article-rewriter` 或 `tiered-translate` | 暂缓 |
| 播客/转写稿写作 | `solo-writer` | 暂缓 |
| 图文转视频 | `viral-video-script` -> `minimax-tts` -> `video-from-storyboard` | 暂缓 |

## 5. 目录索引

内容目录：

- `content-production/inbox/`：输入素材、采集结果、原始摘录
- `content-production/inbox/raw/news/`：`news-collect` 原始 JSON 归档
- `content-production/inbox/raw/research/`：`topic-research` 原始 JSON 归档
- `content-production/inbox/raw/wechat/`：`wechat-collect` 原始 HTML 归档
- `content-production/inbox/raw/wechat-report/`：`wechat-report` 原始 JSON 归档
- `content-production/drafts/`：Markdown 成稿、中间稿
- `content-production/ready/`：排版结果、配图、封面、待发布内容
- `content-production/published/`：已发布归档
- `content-production/published/*-feishu-sync.md`：飞书同步回执
- `content-production/published/*-feishu-import.csv`：飞书导入兜底 CSV
- `content-production/storyboards/`：视频脚本
- `content-production/video-assets/`：分镜图、TTS、成片

知识目录：

- `knowledge/style/`：风格规则、改稿规律
- `knowledge/checklists/`：质检清单
- `knowledge/methodology/`：方法论文档

工作台目录：

- `skills/wechat-studio/`：当前 `wechat-studio` 工作台实现目录；包含公众号包装工作台、排版预览、封面/正文配图与草稿推送相关能力

文档目录：

- `docs/content-skills-implementation-plan.md`：总体实施计划
- `docs/skill-catalog.md`：每个 Skill 的输入、输出、触发语
- `docs/data-contracts.md`：路径与命名约定
- `docs/feishu-schema.md`：飞书多维表字段契约
- `docs/article-prepublish-checklist.md`：图文发布前检查清单
- `docs/stage1-brief-template.md`：阶段 1 观点 brief 模板

## 6. Handoff 规则

- 路径信号优先：下游优先读取上游落盘文件，而不是依赖聊天上下文。
- `slug` 统一：同一篇内容在 `inbox/`、`drafts/`、`ready/` 中共享同一个 `slug`。
- 文件优先于口头描述：若文件与聊天描述冲突，以最新落盘文件为准。

## 7. 当前验收标准

满足以下 3 条，即认为阶段 0 基础设施可用：

- 只看本文件与 `docs/data-contracts.md`，能说清楚一篇内容从哪进、从哪出。
- 遇到观点 brief，能明确走 `case-writer-hybrid` -> `generate-image` -> `wechat-formatter`。
- 遇到资讯扫描请求，能明确走 `news-collect` -> 人工选题 -> `topic-research`。
- 遇到“公众号多篇采集对比”请求，能明确走 `wechat-report`，且只有用户确认后才允许 `feishu-bitable-sync`。
- 首次飞书同步前，知道先运行 `feishu-user-auth`，并优先走用户授权写表。
- 所有样例都能按 `content-production/inbox`、`drafts`、`ready` 三层结构归档。
