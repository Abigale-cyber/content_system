# 内容 Skills 体系实施计划

基于已梳理的 **35 个内容相关 Skills** 与 **六层递进架构**（采集 → 翻译 → 创作 → 排版与视觉 → 视频与音频 → 分发与同步），本计划给出可落地的阶段目标、默认链路、交付物与验收标准。所有文件路径默认相对于 `content-production/`，详见 [data-contracts.md](./data-contracts.md)。

参考材料：

- [内容 Agent 第一课笔记](../yx-files/0313%20内容Agent第一课_2026-04-03%2017-11-56/0313%20内容Agent第一课.md)
- [Skill 全目录与功能说明（可扩展字段）](./skill-catalog.md)
- [中间产物与目录约定](./data-contracts.md)
- [输入 / 输出 / 触发语填写指南](./skill-io-guide.md)（含 Happycapy 流程对照思路）
- 若已生成信息图：`outputs/content-layers.html` 或 `docs/content-layers.html`（可选）

---

## 一、架构总览（六层 + 四洞察）

### 1.1 六层与 Skill 数量

| 层级 | 数量 | 职责摘要 |
|------|------|----------|
| 采集层 | 8 | 从 YouTube、X、小宇宙、公众号、梗图等抓取原始素材 |
| 翻译层 | 1 | 外文本地化；**中文素材可旁路跳过** |
| 创作层 | 9 | 多写手竞争、案例论证、访谈提炼等核心生产 |
| 排版与视觉层 | 7 | 排版、配图、封面、AI 视频生成 |
| 视频与音频层 | 4 | TTS、分镜合成、爆款拆解、本地视频分析 |
| 分发与同步层 | 6 | X、小红书、飞书、一体化编排等 |

**合计：35 个 Skill**。归类规则：`generate-video` 固定归入排版与视觉层；`auto-curate`、`wechat-full` 虽由子 Skill 组合而成，各自独立计数。

### 1.2 四类架构洞察（运行时必须遵守）

1. **单向主管道 + 旁路**：主链路按层递进；翻译层仅在外文场景启用。
2. **反馈环路**：例如爆款拆解（`video-optimize`）产出可反哺创作脚本（`viral-video-script`）。
3. **一鱼多吃**：同一创作产物可并行进入：公众号排版、小红书笔记、视频脚本等。
4. **飞书中枢**：`feishu-bitable-sync` 作为内容资产存储与下游（如 `xiaohongshu-note-generator`）的数据源。

---

## 二、Skill 清单与功能说明（按层）

下表说明**每个 Skill 做什么**；组合型 Skill 在「功能说明」中注明等价子流程。

### 2.1 采集层（8）

| Skill | 功能说明 |
|------|----------|
| `daily-content-curator` | 从预配置的 YouTube 频道和小宇宙播客自动抓取音视频，获取字幕/转录文本并改写 |
| `x-viral-collector` | 通过 Apify 采集 X（Twitter）上 AI 相关的高互动推文和长文，生成热门内容报告 |
| `ai-income-stories` | 从 X 采集「用 AI 编程工具赚钱」的真实故事，提取收入、工具、背景等结构化数据 |
| `attentionvc-ai-daily` | 从 AttentionVC.ai 抓取 X 上 AI 热门长文，用 Jina Reader 获取全文，生成日报 |
| `wechat-collect` | 公众号文章采集 |
| `wechat-subscribe` | 公众号订阅管理 |
| `wechat-topic-monitor` | 公众号选题监控（主菜单入口） |
| `meme-search` | 全网梗图搜索：多策略并行检索，返回相关梗图集合及解读 |

### 2.2 翻译层（1）

| Skill | 功能说明 |
|------|----------|
| `tiered-translate` | 三种模式（快速/标准/精翻）翻译文章与文档，支持自定义术语表 |

### 2.3 创作层（9）

| Skill | 功能说明 |
|------|----------|
| `article-rewriter` | 外文 URL 精读 → 讨论角度 → 三写手竞争创作 → 审稿 → 选稿 → 信息图 → 公众号 HTML |
| `case-writer-hybrid` | 用户提供核心观点 → 搜索案例 → 3 条论证路径 → 3 个版本 → 六维评分 → 选择 |
| `solo-writer` | 播客文字稿 → 精读 → 讨论角度 → 单写手写作（去 AI 味）→ 信息图 → 公众号 HTML |
| `interview` | 多轮深度访谈挖掘用户故事 → 智能推荐文章方向 → 输出公众号爆款文章 |
| `ad-writing` | 读取广告主 PDF Brief → 设计测试用例 → 输出约 3000 字公众号推广文章 |
| `ad-writing-v2` | Brief → 全网调研 → 3 版大纲审批 → 用户实测 → 基于真实结果写作 |
| `meme-to-script` | 用户上传梗图 → AI 深度解读 → 网络搜索补充素材 → 三编剧竞写 → 评审打分 → 公众号 HTML |
| `hokkaido-writer` | Skills 工具书写作助手：专门优化案例、补充章节、润色文字 |
| `viral-video-script` | 输入文章 → 三写手并行竞写 → 评审打分 → 输出含时间标记、画面提示、情绪线的视频脚本 |

### 2.4 排版与视觉层（7）

| Skill | 功能说明 |
|------|----------|
| `wechat-formatter` | 将 Markdown 转为微信公众号可粘贴的 HTML，CSS 内联、微信兼容性适配、自定义主题 |
| `generate-image` | AI 图片生成与变换 |
| `cover-generator` | 上传照片 + 参考封面 → 交互式弹框 → 多尺寸专业视频封面 |
| `cover-4styles` | 上传头像 + 标题 → 一键批量生成 4 种预设风格视频封面 |
| `xhs-cover-template` | 小红书封面（Premium Split 风格：上深下白） |
| `xiaolvshu-cover` | 公众号小绿书封面：输入标题/副标题/作者 → 4 种视觉风格竖版封面 |
| `generate-video` | AI 视频生成（归属本层，不重复计入视频层） |

### 2.5 视频与音频层（4）

| Skill | 功能说明 |
|------|----------|
| `video-optimize` | 支持 B 站/YouTube/小红书/抖音链接，豆包大模型视频理解，8 维度爆款拆解报告 |
| `video-local-analyze` | 仅支持本地视频文件，豆包 API 原生视频理解，输出拆解报告 |
| `video-from-storyboard` | 分镜图片 + 音频 + 文案 → Whisper 语音对齐字幕 → 自动合成带字幕视频 |
| `minimax-tts` | MiniMax T2A API 文字转语音，支持多种音色 |

### 2.6 分发与同步层（6）

| Skill | 功能说明 |
|------|----------|
| `feishu-bitable-sync` | 将 content-archive 内容同步到飞书多维表格，基于原始链接去重 |
| `xiaohongshu-note-generator` | 从飞书多维表格拉取内容 → 转化为小红书爆款图文笔记（连续长图切片卡片） |
| `obsidian-to-x` | 发布内容到 X（Twitter），支持常规推文、X Articles、公众号 HTML |
| `auto-curate` | 一体化编排：`daily-content-curator` + `feishu-bitable-sync` |
| `wechat-full` | 完整流程：`wechat-collect` + `wechat-report` |
| `wechat-report` | 生成 Skills 潜力分析报告 |

---

## 三、默认关联（任务 → 推荐链路）

| 场景 | 推荐链路 | 阶段 |
|------|----------|------|
| **观点/热点 → 案例文 → 公众号**（主链路） | 观点 brief → `case-writer-hybrid` → `generate-image` → `wechat-formatter` | **1** |
| **公众号采集 → 再创作** | `wechat-collect` → `case-writer-hybrid` → `generate-image` → `wechat-formatter` | **2** |
| **采集 → 归档 → 小红书** | `feishu-bitable-sync` → `xiaohongshu-note-generator` → `xhs-cover-template` | **3** |
| 图文发布 → 加封面 | 成稿后 → `cover-generator` / `cover-4styles` / `xhs-cover-template`（按平台选） | 1～3 |
| 公众号素材监控与报告 | `wechat-collect` → `wechat-report` | 2+ |
| 外文长文 → 公众号（方案 A） | `article-rewriter`（直接吃外文 URL）→ `wechat-formatter` | 暂缓 |
| 外文长文 → 公众号（方案 B） | `tiered-translate` → `case-writer-hybrid` → `wechat-formatter` | 暂缓 |
| 播客/音视频稿 → 公众号 | 采集层拿转录 → `solo-writer` → `wechat-formatter` | 暂缓 |
| X 热点 → 案例文 | `x-viral-collector` / `attentionvc-ai-daily` → `case-writer-hybrid` → `wechat-formatter` | 暂缓 |
| 梗图 → 长文 | `meme-search` → `meme-to-script` → `wechat-formatter` | 暂缓 |
| 文章 → 视频 | `viral-video-script` → `minimax-tts` + `generate-image` → `video-from-storyboard` | 暂缓 |

---

## 四、分阶段实施计划

总原则：**先底座与契约，再最小闭环，再外源与中枢，再多媒体，最后编排与进化**。下表是阶段与里程碑对应关系，便于排期。

| 阶段 | 建议周期 | 对应里程碑 | 核心价值 |
|------|----------|------------|----------|
| 阶段 0 | 3～7 天 | M0 | 协作协议 + 数据契约，避免后面返工 |
| 阶段 1 | 2～3 周 | M1 | 图文（含配图）可发布，证明链路成立 |
| 阶段 2 | 1～2 周 | M2 | 公众号采集接入创作链 |
| 阶段 3 | 2～3 周 | M3 | 飞书资产化 + 小红书分发 |
| 阶段 4（暂缓） | 3～4 周 | M4 | 视频端到端（待阶段 1～3 跑稳后启动） |
| 阶段 5（暂缓） | 持续 | M5 | 组合 Skill + 反馈闭环（待阶段 1～3 跑稳后启动） |

### 4.1 阶段总览矩阵

> 可以把 **阶段 0～4** 理解为“建设期”，把 **阶段 5** 理解为“运营优化期”。每个阶段都必须回答 4 个问题：
> 1. 这一阶段做完后，系统**能实现什么效果**
> 2. 这一阶段**必须完成哪些 Skill**
> 3. 相比上一阶段，**新增了哪些能力**
> 4. 这一阶段结束时，**测试通过应该长什么样**

| 阶段 | 做完后实现的效果 | 本阶段必须完成的 Skill | 相比上阶段新增的能力 | 测试通过的效果 |
|------|------------------|------------------------|----------------------|----------------|
| 阶段 0 | AI 与人类对目录、命名、路由、handoff 有统一约定 | 把 `case-writer-hybrid`、`wechat-formatter`、`generate-image` 的输入输出写清 | 从"只有想法"变成"有规则可执行" | 新开一个会话，只看文档能说清：素材放哪、成稿去哪、谁接谁 |
| 阶段 1 | 跑通图文闭环：观点 → 案例文 → 配图 → 公众号 HTML | `case-writer-hybrid`、`wechat-formatter`、`generate-image` | 从"只有规则"变成"能稳定产出带配图的公众号成品" | 3 份观点 brief 连续跑，每份都得到 Markdown + 配图 + 微信 HTML |
| 阶段 2 | 公众号素材能自动采集并进入创作链 | `wechat-collect`，与阶段 1 的 `case-writer-hybrid` 打通 | 从"只会吃手工输入"变成"能从公众号采集素材再创作" | 至少 1 条链路从公众号采集开始，最终产出可发图文 |
| 阶段 3 | 内容进飞书中枢，可驱动小红书分发 | `feishu-bitable-sync`、`xiaohongshu-note-generator`，建议顺带 `xhs-cover-template` | 从"只会本地生成"变成"能资产化、能向小红书分发" | 飞书表有结构化内容，且能从表直接生成小红书笔记 |
| 阶段 4（暂缓） | 图文 → 视频 | `viral-video-script`、`minimax-tts`、`video-from-storyboard` 等 | 图文 + 视频双栈 | 先把阶段 1～3 跑稳再启动 |
| 阶段 5（暂缓） | 组合 Skill + 反馈闭环 | `auto-curate`、`wechat-full`、`wechat-report` 等 | 复利与进化 | 先把阶段 1～3 跑稳再启动 |

---

### 阶段 0：协作与目录约定

**建议周期**：3～7 天（可与阶段 1 首周并行一部分）。

**目标**：人与 AI 对「文件放哪、中间物叫什么、何时调哪条 Skill」达成一致；后续阶段只增量补规则，不重搭目录。

**前置条件**：已确认本仓库或知识库根路径；已安装/可调用计划内 Skills（至少阶段 1 要用到的几个）。

**本阶段实现效果**：

- 你不用再靠记忆告诉 AI 文件该放哪里。
- AI 至少知道阶段 1 的主链路应该调哪些 Skill。
- 中间产物有统一名字，后续 Skill 能接上。

**本阶段必须完成的 Skill / 能力准备**：

- `case-writer-hybrid`：作为阶段 1 唯一主创作 Skill，写清输入输出契约
- `wechat-formatter`：确认其输入输出契约
- `generate-image`：确认配图/信息图的输入输出契约（阶段 1 必做）
- 文档型基础设施：`CLAUDE.md`、`skill-catalog.md`、`data-contracts.md`

**相比上一阶段新增了什么**：

- 当前为起点阶段，无“上一阶段”；新增的是**协作规则和执行边界**。

**测试与通过标准**：

- 找一个没参与文档编写的人，或新开一个会话，只读这 3 份文档，就能回答：
  - 输入素材放哪
  - 成稿放哪
  - HTML 放哪
  - 阶段 1 该调用 `case-writer-hybrid` → `generate-image` → `wechat-formatter`

**执行步骤**：

1. **写 `CLAUDE.md`（或等价协作入口）**  
   - 身份与业务一句话、中文协作偏好（标点、少反问等）。  
   - **铁律**：不擅自移动/删除已有文件；内容只归档不硬删；改 Skill 配置前需确认等（按你实际风险调整）。  
   - **任务路由**：把第三节「默认关联」表贴入，并标注你的主阵地（例如优先公众号或优先小红书）。  
   - **索引**：列出 `content-production/`、`knowledge/`、`docs/` 等目录职责（若尚未建目录，在阶段 0 末或阶段 1 初建好空结构）。

2. **补全 [skill-catalog.md](./skill-catalog.md)**  
   - 每个 Skill 至少补：**典型触发语**、**输入**（URL/文件/表格行）、**输出**（文件格式或飞书字段）。  
   - **依赖类型**：如 Apify、飞书 app、豆包、MiniMax（只写名称，不写密钥）。

3. **维护 [data-contracts.md](./data-contracts.md)**  
   - 定义层间 handoff 的**文件名或字段名**，例如：`transcript.md`、`article-draft.md`、`wechat-paste.html`、`feishu-row-id`、`storyboards/*-script.md`、`final.mp4`。  
   - 约定：**同一内容在不同阶段只保留一份「当前真相」路径**，避免多版本散落。

4. **（可选）建最小目录骨架**  
   - 示例：`content-production/inbox/`、`drafts/`、`ready/`、`published/`；`materials/sources/` 放采集原文链接备份。

**交付物清单**：

| 交付物 | 说明 |
|--------|------|
| `CLAUDE.md` | 含路由表 + 禁止事项 + 目录索引 |
| `docs/skill-catalog.md` | 每 Skill 至少触发语、输入、输出、依赖类型 |
| `docs/data-contracts.md` | 中间产物命名与存储约定 |

**风险与依赖**：若多人协作，需约定「谁改 `CLAUDE.md`」；飞书/第三方 API 未就绪时，阶段 0 仍可完成文档与本地契约。

**验收检查表（全部打勾即阶段 0 完成）**：

- [ ] 新人（或另一个会话）只读 `CLAUDE.md` + `data-contracts.md` 能说出「一篇稿从哪进、从哪出」。  
- [ ] 第三节中至少 **3 条**场景能在文档里对应到具体 Skill 顺序。  
- [ ] `skill-catalog.md` 中阶段 1 将用到的 Skill 已填触发语与输入输出。

---

### 阶段 1：最小闭环——图文发布

**建议周期**：2～3 周（第 1 周打通一次，第 2～3 周重复跑 3～5 次固化习惯）。

**目标**：稳定跑通 **「观点 brief → `case-writer-hybrid` → 配图 → 公众号 HTML」** 闭环。

**前置条件**：阶段 0 验收通过；`case-writer-hybrid`、`wechat-formatter`、`generate-image` 均可调用。`wechat-studio` 作为**可选工作台**存在，用于预览、人工调节与草稿推送，不作为主链路独立节点。

**本阶段实现效果**：

- 你已经拥有一条**可复现的图文生产链**（含配图）。
- 输入观点 brief 时，AI 自动走 `case-writer-hybrid` → `generate-image` → `wechat-formatter`。
- 输出结果不再只是聊天文本，而是标准化落盘的 Markdown、配图与 HTML。

**本阶段必须完成的 Skill**：

- 主创作：`case-writer-hybrid`
- 配图：`generate-image`（必做，不再可选）
- 排版：`wechat-formatter`

**本阶段可选工作台**：

- `wechat-studio`：用于人工预览、包装参数调整、封面/配图微调和后续推送草稿，不单独计入主链路节点

**相比阶段 0 新增了什么**：

- 从“只有文档和约定”升级到“能稳定产出带配图的公众号成品”
- 从“只有输入输出定义”升级到“能连续跑 3 次同类任务，且含配图”

**测试与通过标准**：

- 准备 3 份观点/热点 brief 作为真实样本
- 每份样本都必须产出：
  1. 输入素材
  2. `drafts/*-article.md`
  3. `ready/*-img-*.png`（至少 1 张配图或信息图）
  4. `ready/*-wechat.html`
  5. 发布前检查记录
- 如果第 3 次还需要回看旧聊天才能跑通，则阶段 1 不算通过

**本阶段启用的 Skill**：

| 角色 | Skill | 说明 |
|------|--------|------|
| 主创作 | `case-writer-hybrid` | 观点 + 案例 → 公众号长文 |
| 配图 | `generate-image` | 信息图/配图，本阶段必做 |
| 排版 | `wechat-formatter` | Markdown → 微信 HTML |
| 工作台（可选） | `wechat-studio` | 当前实现目录为 `wechat-studio/`，用于人工预览、包装调节、封面/配图资产管理与后续草稿推送 |

**执行步骤**：

1. **主创作 Skill 已确定**：`case-writer-hybrid`，写入 `CLAUDE.md` 作为唯一主链路。  
2. **跑通第一次端到端**：人工准备 1 份最小素材（一段转写或一小段观点）→ `case-writer-hybrid` → `generate-image` → `wechat-formatter` → 导出 HTML，按 `data-contracts.md` 落盘；如需人工微调，再进入 `wechat-studio`。  
3. **固定质检**：在 `docs/` 或 `knowledge/checklists/` 增加「图文发布前检查」（标题、封面位、敏感词、链接有效性等），由人工或 Skill 自检执行。  
4. **重复 3～5 次**：记录每次卡点（模型漂移、格式问题），把规则写回 `CLAUDE.md` 或检查清单。

**阶段 1 详细拆解（建议直接照此推进）**：

#### 1.1 先定一条主链路

本阶段只做一条主链路：

> **观点/热点 → 案例文 → 配图 → 公众号**
> 观点 brief → `case-writer-hybrid` → `drafts/*-article.md` → `generate-image` → `ready/*-img-*.png` → `wechat-formatter` → `ready/*-wechat.html`

> `wechat-studio` 不作为这条链路的独立节点，而是这两个 skill 的可选操作台：当你需要人工预览、参数微调或推草稿时再进入。

不做播客/转写稿链路（`solo-writer` 留作后续扩展）。

#### 1.2 第一阶段要完成的 6 个子任务

| 子任务 | 要做什么 | 完成标准 |
|------|----------|----------|
| 任务 1：确定入口素材 | 选 3 份真实样本，类型保持一致 | 3 份样本都能进入同一条链路 |
| 任务 2：固定文件命名 | 给样本统一 `slug`，按 `inbox/`、`drafts/`、`ready/` 落盘 | 任意一篇都能从路径判断当前状态 |
| 任务 3：跑通创作 | 用主创作 Skill 产出 Markdown 成稿 | 至少得到 1 份可继续排版的 `drafts/*-article.md` |
| 任务 4：跑通配图与排版 | 依次执行 `generate-image` 与 `wechat-formatter` | 至少得到 1 份 `ready/*-img-*.png` 和 1 份 `ready/*-wechat.html` |
| 任务 5：建立质检 | 建一份图文发布前检查清单 | 每篇稿件都按同一清单检查 |
| 任务 6：回写规则 | 把失败原因、格式偏差、提示词补充写回文档 | `CLAUDE.md` 或检查清单至少更新 2 次 |

#### 1.3 建议按周推进

**第 1 周：打通第一条样例**

1. 选定主链路，只保留一个主创作 Skill。  
2. 准备 3 份同类型样本，其中 1 份作为首个打通样例。  
3. 跑通从输入素材到 `drafts/*-article.md`。  
4. 跑通 `generate-image` 与 `wechat-formatter`，得到第一份 `ready/*-img-*.png` 与 `ready/*-wechat.html`。  
5. 若需要人工确认包装效果，再进入 `wechat-studio` 预览或微调。  
5. 记录这次运行中所有问题，例如：
   - 成稿是不是已经带 HTML
   - 是否需要人为补标题/摘要
   - 排版是否有重复嵌套

**第 2 周：重复跑第 2、3 篇样例**

1. 用同一条链路再跑 2 篇。  
2. 对比三篇的共性问题，提炼最常见的 3 类错误。  
3. 把这些错误写入：
   - `CLAUDE.md` 的任务路由或协作约束
   - `knowledge/checklists/` 下的图文检查清单
   - 必要时补充到 `skill-catalog.md` 的输入/输出说明

**第 3 周：做一次“脱离上下文”的复现测试**

1. 不参考历史聊天，只看文档重新跑一篇。  
2. 检查是否仍能顺利完成：
   - 找到输入位置
   - 产生成稿
   - 生成 HTML
   - 知道发布前怎么检查
3. 若不能，则说明第一阶段仍未真正稳定，继续补规则，不进入阶段 2。

#### 1.4 第一阶段建议创建的最小文件

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | 明确主链路为 `case-writer-hybrid` + `generate-image` + `wechat-formatter` |
| `docs/data-contracts.md` | 固定 `inbox/`、`drafts/`、`ready/` 命名 |
| `docs/skill-catalog.md` | 校准主创作 Skill 与 `wechat-formatter` 的输入输出 |
| `knowledge/checklists/article-prepublish.md` | 图文发布前检查清单 |
| `wechat-studio/` | 当前 `wechat-studio` 工作台实现目录，用于人工预览、调节与后续推草稿，不替代原子 skill |

如果你暂时不想把目录拆太细，第一阶段至少也要先有 `article-prepublish.md`，否则每次验收标准都会变化。

#### 1.5 第一阶段的最小验收样例

建议不要只做 1 篇，而是做 3 篇，且来源一致：

- 准备 3 条观点/热点 brief（对应主链路 `case-writer-hybrid`）

每篇都至少保留 4 个节点：

1. 输入素材
2. 中间 Markdown 稿
3. 配图
4. 最终 HTML
5. 发布前检查记录

#### 1.6 第一阶段最容易卡住的点

| 卡点 | 典型表现 | 处理方式 |
|------|----------|----------|
| 创作 Skill 输出不稳定 | 有时出 Markdown，有时直接出 HTML | 在 `skill-catalog.md` 固定主输出，并在 `CLAUDE.md` 约定是否跳过 formatter |
| 成稿质量波动 | 三篇里风格不一致 | 先不追求极致，优先统一结构，再逐步补风格规则 |
| 排版重复嵌套 | HTML 再进 `wechat-formatter` 变脏 | 规定只有 Markdown 才进 formatter |
| 文件乱放 | 样例放在不同路径，无法复盘 | 所有样例只落 `inbox/`、`drafts/`、`ready/` 三层 |
| 质检标准漂移 | 每篇检查项都不同 | 固定一份 `article-prepublish.md`，所有稿件共用 |

#### 1.7 第一阶段结束后，你应该得到什么

阶段 1 完成时，目标不是“写出了几篇文章”，而是得到一条**能重复调用的图文（含配图）最小闭环**：

- 你知道什么输入会走哪条链路
- AI 知道该调用 `case-writer-hybrid` → `generate-image` → `wechat-formatter`
- 成稿知道放到哪里
- 需要人工预览或微调时，知道何时进入 `wechat-studio`
- 排版知道何时触发
- 检查知道按什么标准执行
- 新开一个会话，仍能复现这条链路

**交付物**：至少 **3 篇**可追溯的完整样例（同一路径下可找到：素材、成稿、配图、最终 HTML）；更新后的 `CLAUDE.md` 与检查清单。

**风险**：创作 Skill 输出已是 HTML 时，与 `wechat-formatter` 的衔接需约定「只调一次排版」避免重复嵌套；在 `data-contracts.md` 写明。

**验收检查表**：

- [ ] 观点 brief → 案例文 → 配图 → 公众号 HTML 可在 **不翻旧对话** 的情况下重复执行。  
- [ ] 产出物路径固定，能向他人展示「从素材到 HTML」的文件夹结构。  
- [ ] 至少 1 次完整走通 `case-writer-hybrid` → `generate-image` → `wechat-formatter` 全链路。

---

### 阶段 2：公众号采集接入

**建议周期**：1～2 周。

**目标**：通过 `wechat-collect` 将公众号素材自动采集进入工作流，与阶段 1 的 `case-writer-hybrid` 打通，形成“采集 → 创作 → 配图 → 排版”闭环。

**前置条件**：阶段 1 稳定；`wechat-collect` 所需的公众号接口或代理能力可用。

**本阶段实现效果**：

- 系统不再只吃手动输入，而是能从公众号自动抓取素材。
- 采集的素材直接落入 `inbox/`，按已有契约进入创作链。

**本阶段必须完成的 Skill**：

- `wechat-collect`
- 与阶段 1 已有的 `case-writer-hybrid` → `generate-image` → `wechat-formatter` 打通

> 其他采集源（`daily-content-curator`、`x-viral-collector`、`attentionvc-ai-daily`）和翻译旁路（`tiered-translate`）暂缓，待阶段 1～3 跑稳后按需扩展。

**相比阶段 1 新增了什么**：

- 从“只处理人工喂给系统的内容”升级到“公众号素材可自动进料”

**测试与通过标准**：

- 至少跑通 1 条完整链路：`wechat-collect` → `inbox/*` → `case-writer-hybrid` → `generate-image` → `wechat-formatter` → `ready/*-wechat.html`
- 采集输出与阶段 1 的输入格式兼容，无需手动转换
- 测试通过后，你应该能展示：从一篇公众号文章的 URL 出发，全链路走到可发成品

**本阶段启用的 Skill**：

| 类型 | Skill | 说明 |
|------|--------|------|
| 采集 | `wechat-collect` | 抓取公众号文章内容，落入 `inbox/` |
| 衔接创作 | 阶段 1 已有 `case-writer-hybrid` + `generate-image` + `wechat-formatter` | 无需新增 |

**执行步骤**：

1. **配通 `wechat-collect`**：确认采集能力可用，输出格式与 `inbox/` 契约对齐。  
2. **跑通第一条样例**：选 1 篇公众号文章 URL → `wechat-collect` → 落入 `inbox/` → `case-writer-hybrid` → `generate-image` → `wechat-formatter`。  
3. **重复 2～3 次**：确认采集输出稳定、与阶段 1 链路无缝衔接。  
4. **更新 `CLAUDE.md`**：把采集路由写入，标注 `wechat-collect` 的触发条件与输出位置。

**交付物**：`inbox` 中可追溯的公众号采集样本；至少 **2 条**完整链路样例；更新后的 `CLAUDE.md`。

**风险**：公众号反爬与接口限制；建议阶段 2 只做“个人研究/内用”范围，对外发布前人工复核。

**验收检查表**：

- [ ] 至少一条链路：**`wechat-collect` → 创作 → 配图 → 排版** 有完整样例。  
- [ ] `CLAUDE.md` 中已写明 `wechat-collect` 的触发条件与采集输出落盘规则。  
- [ ] 采集输出格式与阶段 1 输入契约一致，无需人工格式转换。
---

### 阶段 3：飞书中枢 + 小红书分发

**建议周期**：2～3 周。

**目标**：内容进入 **可检索、可去重** 的飞书资产库；从飞书表驱动 **小红书** 分发。

**前置条件**：飞书多维表格与 `feishu-bitable-sync` 所需权限；小红书发布账号。

**本阶段实现效果**：

- 内容不再只是散落在本地文件里，而是进入可查询、可筛选、可去重的飞书中枢。
- 小红书分发可以直接消费飞书中的结构化内容。

**本阶段必须完成的 Skill**：

- 中枢：`feishu-bitable-sync`
- 分发：`xiaohongshu-note-generator`
- 建议顺带：`xhs-cover-template`（小红书封面）

> `obsidian-to-x` 暂缓，待小红书链路稳定后按需扩展。`auto-curate` 同理，先用手动串联确保每一步可控。

**相比阶段 2 新增了什么**：

- 从“有内容生产链”升级到“有内容资产中枢”
- 从“能生成”升级到“能向小红书分发”

**测试与通过标准**：

- 飞书表中至少有 5～10 条真实内容记录
- 任取一条记录，都能通过 `source_url` 回溯到来源
- 能从飞书表驱动 `xiaohongshu-note-generator` 产出小红书笔记
- 小红书笔记配合 `xhs-cover-template` 有封面

**本阶段启用的 Skill**：

| 必选/选 | Skill | 说明 |
|---------|--------|------|
| 中枢 | `feishu-bitable-sync` | content-archive → 飞书，按链接去重 |
| 分发 | `xiaohongshu-note-generator` | 表 → 小红书图文 |
| 建议 | `xhs-cover-template` | 小红书封面模板 |

**执行步骤**：

1. **设计飞书表字段**：至少包含 `标题`、`原始链接`、`摘要`、`状态`、`发布渠道`、`素材类型`，与 `data-contracts.md` 对齐。  
2. **先同步再分发**：用历史 5～10 条内容跑通 `feishu-bitable-sync`，确认去重逻辑。  
3. **接通小红书**：从表拉取 → `xiaohongshu-note-generator` + `xhs-cover-template`，记录“表字段 → Skill 输入”映射到 `skill-catalog.md`。

**交付物**：飞书表结构说明（可放在 `docs/feishu-schema.md`）；至少 **3 条**“表中一行 → 小红书笔记”样例。

**风险**：飞书 API 变更、小红书风控；建议先发草稿再人工点发布。

**验收检查表**：

- [ ] 任意一条入库记录能通过 **原始链接** 追溯到采集或创作源。  
- [ ] 小红书从飞书表驱动的完整路径有 **至少 3 条** 样例。  
- [ ] `docs/feishu-schema.md` 已建立或已在 `data-contracts.md` 中补充飞书字段说明。
---

### 阶段 4：视频与音频（暂缓）

> **当前决策：先把阶段 1～3 跑稳再启动视频。** 以下内容保留供后续参考。

**目标**：**脚本 → 配音 → 分镜图 → 合成成片** 可独立替换任一环。

**涉及 Skill**：`viral-video-script`、`minimax-tts`、`video-from-storyboard`、`generate-image`（分镜图）、`generate-video`、`video-optimize`、`video-local-analyze`。

**启动前置**：阶段 3 验收通过，飞书中枢 + 小红书分发链路稳定。

**预估周期**：3～4 周（视是否从零准备分镜素材而定）。

**核心验收**：同一篇文章能转成 1 条有配音、有字幕、可复跑的视频；不改脚本可单独替换配音或分镜后重合成。

---

### 阶段 5：组合 Skill 与反馈闭环（暂缓）

> **当前决策：先把阶段 1～3 跑稳再启动进化机制。** 以下内容保留供后续参考。

**目标**：用组合 Skill 减少操作步骤；用“拆解 → 选题/脚本”和“人改稿 → 规则”形成进化闭环。

**涉及 Skill / 机制**：`auto-curate`、`wechat-full`、`wechat-report`、人工改稿规则回写。

**启动前置**：阶段 3 验收通过，且已有足够内容积累（飞书表 20+ 条）来检验组合效果。

**核心验收**：至少 1 条组合 Skill 比手动串联更省步骤；至少 1 条反馈环真实生效。

---

## 五、里程碑与依赖

| 里程碑 | 标志 |
|--------|------|
| M0 | `CLAUDE.md` + `docs/skill-catalog.md` + `docs/data-contracts.md` 就绪 |
| M1 | 图文闭环（`case-writer-hybrid` + `generate-image` + `wechat-formatter`）稳定 |
| M2 | 公众号采集（`wechat-collect`）接入创作链 |
| M3 | 飞书归档 + 小红书分发 |
| M4（暂缓） | 视频链路端到端 |
| M5（暂缓） | 组合 Skill 与反馈环 |

**外部依赖**：公众号采集接口（阶段 2）、飞书（阶段 3）、小红书账号（阶段 3）。视频相关（豆包、MiniMax）待阶段 4 启动时配置。

---

## 六、下一步（立即可执行）

1. **阶段 0 启动**：写 `CLAUDE.md`，把第三节「默认关联」表中阶段 1～3 的 3 条主链路粘入，明确主创作 Skill 为 `case-writer-hybrid`。
2. **校准 Skill 契约**：在 [skill-catalog.md](./skill-catalog.md) 中确认 `case-writer-hybrid`、`generate-image`、`wechat-formatter` 三个 Skill 的输入/输出/触发语与你本机路径一致。参考 [skill-io-guide.md](./skill-io-guide.md) 理解链式 handoff。
3. **本周 KPI**：准备 1 份观点 brief，跑通 `case-writer-hybrid` → `generate-image` → `wechat-formatter` → 得到 `ready/*-wechat.html`。

---

*文档版本：2026-04-03 v3（对齐用户选择：case-writer-hybrid + 配图、wechat-collect、小红书、视频暂缓）。随 Skill 清单与归类规则变更而更新。*
