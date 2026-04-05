# Skill 的「输入 / 输出 / 触发语」怎么写

参考：

- HappyCapy 分享（课程中用于说明「单篇文章」完整生产）：[happycapy.ai/share/0c93d18b-c1f7-4e40-9a1d-0449a69e94c1](https://happycapy.ai/share/0c93d18b-c1f7-4e40-9a1d-0449a69e94c1)  
- 本地同主题图解：`yx-files/0313 内容Agent第一课_2026-04-03 17-11-56/images/hgTI8BZdenetPrhHf8xqsWR3TJlG9JVL.png`  
- 目录与文件命名约定：[data-contracts.md](./data-contracts.md)
- Skill 间传输信号（路径 / frontmatter / 飞书 ID、典型链路表）：[skill-catalog.md](./skill-catalog.md#skill-handoff-signals)

**路径约定**：下文所有路径省略公共前缀 `content-production/`，与 [data-contracts.md](./data-contracts.md) 一致。

说明：**填写原则与图上「多段中间产物」一致**：上一框的 **OUT** 就是下一框的 **IN**，在 `skill-catalog.md` 里写成**可落盘的类型 + 示例路径**即可。

---

## 0. Skill 与 Skill 之间的「信号」

各 Skill 单独一行只能表达**单点输入输出**；**多段串联**时请看 [skill-catalog.md#skill-handoff-signals](./skill-catalog.md#skill-handoff-signals)：那里用表格写清了 **上游 → 信号形态 → 下游**（例如 `*-transcript.md` → `solo-writer`，飞书 `record_id` → `xiaohongshu-note-generator`）。

---

## 1. 三列分别写什么

| 列 | 写法 | 例子 |
|----|------|------|
| **输入** | 「需要什么类型的素材」+「常见形态」；若有多步，写**本 Skill 第一步**要的 | `关键词字符串`；`content-production/inbox/xxx-transcript.md`；`https://…` |
| **输出** | 「交给下一 Skill 或人类」的**主产物**；尽量对应 [data-contracts.md](./data-contracts.md) 里的文件名 | `drafts/xxx-article.md`；`ready/xxx-wechat.html` |
| **触发语** | 你在对话里**固定会说的开头**，方便路由 | 「用梗图写公众号」「把这篇译成中文精翻」 |

**粒度建议**：一个 Skill 一行；若 HappyCapy 里是一条**大流水线**（多节点），可以：

- 要么：在「功能说明」里已覆盖，输入写**整条链入口**（如关键词/URL），输出写**链末端产物**（如公众号 HTML）；  
- 要么：拆成多行虚拟子步骤（仅文档用），与 `data-contracts.md` 中中间文件一一对应。

---

## 2. 参考：梗图 → 公众号长文（八段产物链）

与课程图解一致，典型中间物如下（用于理解 IN/OUT 如何衔接；具体文件名按你项目改）：

| 顺序 | 阶段含义 | 输入（IN） | 输出（OUT） |
|------|----------|------------|-------------|
| 1 | 搜梗 | 用户关键词 / 主题 | 梗图库、文字梗列表（检索结果） |
| 2 | 定角度 | 梗素材 + 选题描述 | 若干条**写作路线/角度**（人选一条） |
| 3 | 搜案例 | 选定角度 + 检索词 | 案例与数据摘录（案例库） |
| 4 | 竞写 | Brief（梗+案例+规则） | 多版草稿 + 评分对比 |
| 5 | 去 AI 味 | 选定草稿 | 打磨后的 Markdown 终稿 |
| 6 | 信息图 | 段落与配图提示 | 多张 PNG 配图 |
| 7 | 微信排版 | 终稿 MD + 配图 | 可粘贴的公众号 HTML |
| 8 | 封面 | 标题 + 核心关键词 | 封面图或封面 HTML |

在 **`skill-catalog.md` 里**：若你用的是组合能力 **`article-rewriter`** / **`meme-to-script`** 等，**输入**写链的起点（如 `URL` / `梗图文件` / `关键词`），**输出**写链的终点（如 `ready/*-wechat.html`），中间步骤记在「功能说明」或单独一篇 `docs/pipelines/meme-to-article.md`（可选）。

---

## 3. 与六层架构对齐的「一句话」规则

- **采集层输出**：原始链接、转写文本、报告 Markdown → 对应 `content-production/inbox/`。  
- **翻译层输出**：中文可编辑稿 → `drafts/*-zh.md`。  
- **创作层输出**：文章正文 Markdown 或已带版式的草稿 → `drafts/` 或 `ready/`。  
- **排版与视觉层输出**：HTML、PNG 封面、信息图 → `ready/`。  
- **视频层输出**：脚本、wav/mp3、分镜图、mp4 → `storyboards/`、`video-assets/`。  
- **分发层输出**：飞书行、已发帖链接、发布状态 → 表字段 + `published/` 归档。

填写时自问：**下游第一个动作要拿什么文件？** 那就是你的「输出」描述。

---

## 4. 示例（可直接粘贴到 `skill-catalog` 再改路径）

以下为**示意**，路径请与 [data-contracts.md](./data-contracts.md) 统一。

| Skill | 输入 | 输出 | 触发语 |
|--------|------|------|--------|
| `tiered-translate` | 外文 `URL` 或 `inbox/*.md`；可选 `knowledge/glossary.md` | `drafts/*-zh.md` | 「把这篇链接精翻成中文」 |
| `article-rewriter` | 外文 URL 或已译稿路径 | `ready/*-wechat.html`（或链式中间件见功能说明） | 「按精读流程改写成公众号」 |
| `wechat-formatter` | `drafts/*.md` + 可选配图目录 | `ready/*-wechat.html` | 「把这篇排版成微信 HTML」 |
| `viral-video-script` | `drafts/*-article.md` 或 URL | `storyboards/*-script.md` | 「把这篇改成口播/分镜脚本」 |
| `feishu-bitable-sync` | `content-archive` 或约定 JSON | 飞书多维表新增/更新行 | 「把本周归档同步到飞书」 |

---

## 5. 当前状态与后续维护

[skill-catalog.md](./skill-catalog.md) 中 35 个 Skill 的「输入 / 输出 / 触发语」已全部预填。后续维护时：

- **本地化**：按你本机路径与飞书字段微调表中内容。
- **新增子流程**：若 Happycapy 图上某节点比 `skill-catalog` 里的 Skill 粒度更细，用 `docs/pipelines/` 另存一条子流程文档即可，不必强行塞进一行表格。
- **校验**：可打开 [Happycapy 分享](https://happycapy.ai/share/0c93d18b-c1f7-4e40-9a1d-0449a69e94c1) 对照图上节点的 IN/OUT，确认与表中描述一致。

---

*与 [skill-catalog.md](./skill-catalog.md) 配合使用。*
