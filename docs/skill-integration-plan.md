# Skill 整合方案：`one/` + `content_system/skills/`

> 目标：把 `one/` 的写作方法论融入 `content_system/skills/`，形成一套既能快速出稿、又保质量的内容生产流水线。
> 日期：2026-05-05
> 状态：本文件是本次整合工作的唯一执行依据；李尚龙课程的吸收项已并入本文。

---

## 一、现状诊断

### `one/` 的优势（要吸收的）

1. **Brief 构建方法论**：6 项质量自检、SCQA 强制校验、素材三级降级策略、反模式检查表
2. **写前门控**：核心判断够硬？读者够具体？素材充足？不通过就停
3. **丰富的写作参考库**：8 种开头模板、5 种结尾模板、5 大框架选择指南、标题 5 大原则 + 8 种模板、去 AI 痕迹对照表、15 项发布前检查清单
4. **两阶段写作**：先出标题+大纲确认，再写全文——避免方向跑偏
5. **可移植设计**：不依赖硬编码路径，通过相对路径引用 `_shared/` 资料

### `one/` 的不足

1. 选题发现环节空白
2. 配图、排版、预览完全没有
3. 审稿 skill（adversarial-content-review）未实现
4. 去AI味只是内嵌规则，没有独立工具和追踪
5. 飞书只有文档写入，没有多维表同步

### `content_system/skills/` 的优势

1. 全链路覆盖：采集 → 研究 → 写稿 → 配图 → 排版 → 预览 → 发布
2. 自动化程度高：3 轮 writer→critic→humanizer→judge 循环
3. 独立工具链：humanizer-zh、generate-image、wechat-formatter 各自可追踪

### `content_system/skills/` 的不足

1. 没有独立的 Brief 构建环节，brief 格式松散
2. 写稿没有人工确认节点，方向偏了全靠事后改
3. 写作方法论单薄，缺乏开头/结尾/标题的模板库
4. case-writer-hybrid 的 `runtime.py` 里论证段落是模板拼接，写出来的文章结构套路化严重

---

## 二、整合策略

**原则：不动现有的自动化流水线，在上游补方法论，在关键节点加人控。**

具体来说：
- **新增**：`content-brief-builder` skill（从 `one/` 搬入）
- **升级**：`case-writer-hybrid`（融入 `one/` 的写作参考库和两阶段交互）
- **不动**：所有其他 skill（采集、配图、排版、飞书同步等）

**吸收边界**：
- 本次直接并入执行清单的，是能马上落到 `content-brief-builder`、`case-writer-hybrid`、`docs/stage1-brief-template.md` 的方法论
- 李尚龙课程里与当前主链路强相关的内容，优先作为 references、门控规则、交互模式步骤吸收
- 新 skill 只保留 2 个后续方向：`script-writer-short`、`topic-radar`
- `hook-generator`、`story-injector`、`content-repurcer` 不独立建 skill，降级为 references 或指南文件

---

## 三、逐项改动

### 3.1 新增 `skills/content-brief-builder/`

**来源**：`one/content-brief-builder/`

**做什么**：从 `content_system/skills/` 新建目录，把 `one/` 的 content-brief-builder 整个搬入，保留其 references 和方法论。

**目录结构**：

```
content_system/skills/content-brief-builder/
├── SKILL.md                    # 从 one/ 复制，微调路径引用
└── references/
    ├── brief-quality-guide.md  # 直接复制
    ├── content-brief-format.md # 直接复制
    └── research-methods.md     # 直接复制
```

**需要调整的地方**：

1. `SKILL.md` 里的输出路径：原文是 `content-brief-<选题关键词>.md`，改为 `content-production/inbox/YYYYMMDD-<slug>-gzh-brief.md`，和现有 `case-writer-hybrid` 的输入路径对齐
2. `content-brief-format.md` 里的格式需要在 `case-writer-hybrid` 的 `parse_brief()` 能解析的范围内兼容（见 3.2）
3. `research-methods.md` 里的工具调用（`opencli twitter search` 等）改为 `content_system` 已有的工具（`tavily-research`、`news-collect`）
4. 把李尚龙课程里的选题方法并入 references：
   - `brief-quality-guide.md` 增补三种通用选题公式、热点选题 7 步流程、选题四维打分
   - `research-methods.md` 增补信息雷达 6 源和热点转角度的取材提示

**Brief 格式兼容**：

`one/` 的 brief 格式（YAML 字段）和 `content_system` 的 brief 模板（Markdown 标题+列表）格式不同。需要做二选一：

- **方案 A**：`content-brief-builder` 输出 `one/` 格式，`case-writer-hybrid` 的 `parse_brief()` 增加对新格式的支持
- **方案 B**：`content-brief-builder` 输出 `content_system` 现有格式，但补充 `one/` 要求的字段（SCQA、素材来源可信度、风险提醒等）

**推荐方案 B**——先保持 `content_system` 现有 brief section 契约，再追加 `one/` 要求的字段。

**格式兼容性约束**：`content-brief-builder` 的输出必须以 `docs/stage1-brief-template.md` 的 section header 为唯一契约。现有 section 名称（`基础信息`、`核心观点`、`背景与语境`、`论证方向`、`可用案例 / 素材`、`明确不要写什么`、`风格要求`、`配图方向`、`备注`）一个都不能改、不能省。新字段只能以追加新 section 的方式添加。

**生效边界**：第一轮整合时，新增的 SCQA / 风险提醒 / 素材可信度字段先服务 brief 自检和交互模式。2026-05-06 的下一轮增强已经扩展 `runtime.py` 的 `parse_brief()`，让自动模式也读取这些 section：SCQA 会进入正文的问题提出和核心判断，风险提醒和素材可信度会进入 writing-pack，低可信素材在正文里只作为待验证线索处理。

具体来说，在现有 brief 模板末尾追加以下 section（不修改、不删除任何现有 section）：

```markdown
## SCQA 结构

- 情境(S)：
- 冲突(C)：
- 问题(Q)：
- 答案(A)：

## 风险提醒

- 至少 1 个潜在翻车点：

## 素材来源可信度

- 案例 1 可信度：高/中/低
- 案例 2 可信度：高/中/低
- 案例 3 可信度：高/中/低
```

### 3.2 升级 `skills/case-writer-hybrid/`

**目标**：在保持自动化流水线的同时，融入 `one/` 的写作方法论。

#### 3.2.1 新增 `references/` 目录

从 `one/wechat-article-writer/` 搬入参考文件，并补入李尚龙课程里更偏“结构 / 改稿 / 故事”的部分：

```
content_system/skills/case-writer-hybrid/references/
├── core-workflow.md           # 从 one/wechat-article-writer/_shared/core-workflow.md 复制
├── framework-selection.md     # 从 one/wechat-article-writer/wechat-article-writer/references/ 复制，并补 6 种内容结构
├── hook-and-ending.md         # 从 one/wechat-article-writer/_shared/hook-and-ending.md 复制，并补 5 种 Hook + 结尾三件套
├── title-and-packaging.md     # 从 one/wechat-article-writer/_shared/title-and-packaging.md 复制
├── wechat-channel-profile.md  # 从 one/wechat-article-writer/_shared/wechat-channel-profile.md 复制
├── pre-write-checks.md        # 从 one/wechat-article-writer/wechat-article-writer/references/ 复制
├── intermediate-format.md     # 从 one/wechat-article-writer/_shared/intermediate-format.md 复制
├── revision-loop.md           # 新增，写入“三轮回改法”
└── story-injection.md         # 新增，写入故事三要素 / 伪故事三段式
```

这些文件是**只读参考库**，供 SKILL.md 引用，不影响 `runtime.py` 的自动化流程。

**本次要补进去的具体方法论**：

- `framework-selection.md`：
  - 金字塔结构（结论先行 → 3 个论据 → 金句收尾）
  - 序列步骤结构（开场说明收益 → 逐步操作 → 总结预告）
  - 故事叙述结构（开端 → 冲突 → 转折 → 结局）
  - 问答结构（抛问题 → 回答 → 举例 → 纠误 → 行动建议）
  - 对比结构（展示 A → 展示 B → 数据对比 → 结论）
  - 环形首尾呼应结构（开头金句/场景 → 展开论述 → 回到开头）
- `hook-and-ending.md`：
  - 5 种 Hook：反常识、痛点直击、数字冲击、故事开头、提问式
  - 禁止开头：「大家好」「今天我要给大家分享」「众所周知」
  - 结尾三件套：金句收束 + 引导互动 + 预告下条
- `revision-loop.md`：
  - 第一轮改结构：按“用户阅读逻辑”而不是“作者写作逻辑”重排
  - 第二轮改语言：朗读法，拗口就改，长句拆短，书面语转口语
  - 第三轮加共鸣锚点：在关键转折处补“你有没有这种感觉”“说白了就是……”
- `story-injection.md`：
  - 故事三要素：人物 + 冲突 + 转折
  - 伪故事三段式：问题 + 行动 + 结果
  - 故事来源优先级：个人经历 > 粉丝故事 > 行业案例 > 假想场景 > 比喻故事

#### 3.2.2 升级 SKILL.md

在现有 SKILL.md 中新增一个「交互模式」流程，和现有的「自动模式」并存：

**自动模式**（现有流程，不变）：
```
brief → 3轮自动循环(writer→critic→humanizer→judge) → 输出
```

**交互模式**（新增）：
```
brief → 写前门控 → 出标题+大纲 → [等待用户确认] → 写全文 → 自检 → 输出
```

两种模式的触发条件（在 SKILL.md 中明确描述）：

- **CLI 自动模式**：用户执行 `run-skill case-writer-hybrid` → 走 `runtime.py`，自动执行 3 轮循环
- **Agent 交互模式**：用户说「先看大纲」「先确认标题」「交互式写」→ 不调用 `runtime.py`，Agent 按 SKILL.md 流程 + references 逐步执行

交互模式的具体步骤（写在 SKILL.md 里，由 AI 按步骤执行，不涉及 runtime.py）：

```
Step 0: 写前门控（读取 references/pre-write-checks.md）
  - 核心判断够硬吗？
  - 读者够具体吗？
  - 素材充足吗（≥3条）？
  任一不通过 → 停下来，建议先改 brief

Step 1: 读取 brief，提取关键信息

Step 2: 阶段一——出标题 + 大纲
  - 按 references/title-and-packaging.md 的 5 大原则生成 3 个标题候选
  - 基于 SCQA 和 references/framework-selection.md 的 6 种结构生成章节大纲
  - 停下来，等用户确认标题和大纲

Step 3: 阶段二——按确认后的大纲写全文
  - 按 references/framework-selection.md 的分段写作法逐章写
  - 开头用 references/hook-and-ending.md 的 8 种模板
  - 结尾用同一文件的 5 种模板
  - 需要补故事和画面感时，参考 references/story-injection.md
  - 正文规则：每段≤5行，每句≤25字，先说观点再说理由

Step 4: 自检（读取 references/pre-write-checks.md 的写后自检清单）

Step 5: 去AI痕迹
  - 先按 references/revision-loop.md 跑一轮“结构 → 语言 → 共鸣锚点”的三轮回改
  - 再按 references/framework-selection.md 的去AI痕迹表自检一轮
  - 再可选串联 humanizer-zh skill 做深度处理
  - 这样交互模式和自动模式共享同一套去AI能力，规则一致

Step 6: 输出到 content-production/drafts/<slug>-article.md
```

#### 3.2.3 runtime.py 增强边界

`runtime.py` 是自动模式的执行引擎。第一轮整合保持其主体流程不变，作为批量/定时任务的底层。

2026-05-06 的下一轮增强分两步接入：

1. 已解析 SCQA / 风险提醒 / 素材可信度，并把它们传入正文、writing-pack 和 JSON sidecar；低可信素材只作为待验证线索。
2. 已在自动裁判中新增 `story_resonance` 维度，用故事信号和共鸣锚点检测“只讲道理、不见人物”的稿子；当该维度进入 `focus_areas` 时，`case-writer-hybrid` 会在下一轮正文里补入“人物 + 冲突 + 转折”的短故事，以及“你有没有这种感觉”“说白了”这类共鸣锚点。
3. 已在自动裁判中新增 `template_repetition` 维度，用来识别固定句式和段落开头重复；当该维度进入 `focus_areas` 时，`case-writer-hybrid` 会轮换证据桥接段和读者价值段，降低自动稿的模板味。

### 3.3 升级 `docs/stage1-brief-template.md`

在现有模板中补充 `one/` 要求的字段（SCQA、风险提醒、素材可信度），使 `content-brief-builder` 的产出能直接被 `case-writer-hybrid` 消费。

**兼容性检查依据**——`runtime.py` 的 `parse_brief()` 当前读取以下 9 个 section header：

1. `基础信息`（提取 date/slug/topic/target_reader/publish_goal）
2. `核心观点`
3. `背景与语境`
4. `论证方向`
5. `可用案例 / 素材`
6. `明确不要写什么`
7. `风格要求`
8. `配图方向`
9. `备注`

新字段追加在 `备注` 之后，不影响上述 section 的解析。

### 3.4 纳入后续路线图，但不放进本次主链路改造

这些内容是李尚龙课程里有价值、但不该和本次 `one/` 整合一起打包落地的部分：

| 方向 | 处理方式 | 原因 |
|------|----------|------|
| `humanizer-zh` 去 AI 味规则 | 后续单独升级 | 需要改检测逻辑和规则文件，不影响本次整合闭环 |
| `news-collect` / `topic-research` 四维打分 | 后续单独升级 | 属于选题决策层增强，不阻塞 brief-builder 接入 |
| `wechat-formatter` 标题 6 技法 | 后续单独升级 | 适合做标题建议层，不影响主稿链路 |
| `ai-frontier-radar` 信源覆盖对照 | 后续单独检查 | 是数据源盘点，不属于当前 skill 对接 |
| `script-writer-short` | 作为新 skill 的 Phase 2 | 和公众号长文是不同产物，值得独立做 |
| `topic-radar` | 作为新 skill 的 Phase 2 | 只做“热点 → 选题角度”转化，不做泛化灵感系统 |
| `docs/cross-platform-guide.md` | 后续新增文档 | 作为公众号/视频号/YouTube/小红书的共用适配指南 |

### 3.5 不动的 skill

以下 skill 保持原样：

| Skill | 原因 |
|-------|------|
| ai-frontier-radar | 选题发现，`one/` 没有对应物 |
| news-collect | 同上 |
| topic-research | 深度研究，`one/` 没有对应物 |
| tavily-research | 通用调研工具 |
| humanizer-zh | 独立去AI味工具，比 `one/` 内嵌规则更可追踪 |
| generate-image | 配图生成，`one/` 没有 |
| wechat-formatter | 排版，`one/` 没有 |
| wechat-studio | 预览工作台，`one/` 没有 |
| wechat-collect | 公众号采集，`one/` 没有 |
| wechat-article-extractor-skill | 底层解析器 |
| wechat-report | 竞品分析报告 |
| feishu-bitable-sync | 多维表同步 |
| feishu-user-auth | 飞书授权 |

---

## 四、整合后的流水线

```
选题发现 ──→ Brief 构建 ──→ 写稿 ──→ 配图 ──→ 排版 ──→ 预览发布
(ai-frontier-  (content-      (case-writer-    (generate-  (wechat-    (wechat-
 radar /        brief-builder  hybrid /         image)      formatter)  studio)
 news-collect)  ★新增)         ★升级交互模式)
                              │
                              └→ 去AI味 (humanizer-zh)
```

**新增环节**：content-brief-builder（Brief 构建方法论）
**升级环节**：case-writer-hybrid（新增交互模式 + 参考库）
**其他环节**：不动

---

## 五、文件操作清单

按执行顺序：

### 第一步：新增 content-brief-builder

| 操作 | 来源 | 目标 |
|------|------|------|
| 复制 | `one/content-brief-builder/SKILL.md` | `skills/content-brief-builder/SKILL.md` |
| 复制 | `one/content-brief-builder/references/brief-quality-guide.md` | `skills/content-brief-builder/references/brief-quality-guide.md` |
| 复制 | `one/content-brief-builder/references/content-brief-format.md` | `skills/content-brief-builder/references/content-brief-format.md` |
| 复制 | `one/content-brief-builder/references/research-methods.md` | `skills/content-brief-builder/references/research-methods.md` |
| 修改 | `skills/content-brief-builder/SKILL.md` | 调整输出路径，对接 `content_system` 的 inbox 路径 |
| 修改 | `skills/content-brief-builder/references/content-brief-format.md` | 补充 `content_system` brief 格式的兼容字段 |
| 修改 | `skills/content-brief-builder/references/brief-quality-guide.md` | 补充选题三公式、热点 7 步流程、四维打分 |
| 修改 | `skills/content-brief-builder/references/research-methods.md` | 补充信息雷达 6 源和热点取角度提示 |

### 第二步：升级 case-writer-hybrid

| 操作 | 来源 | 目标 |
|------|------|------|
| 复制 | `one/wechat-article-writer/_shared/core-workflow.md` | `skills/case-writer-hybrid/references/core-workflow.md` |
| 复制 | `one/wechat-article-writer/_shared/hook-and-ending.md` | `skills/case-writer-hybrid/references/hook-and-ending.md` |
| 复制 | `one/wechat-article-writer/_shared/title-and-packaging.md` | `skills/case-writer-hybrid/references/title-and-packaging.md` |
| 复制 | `one/wechat-article-writer/_shared/wechat-channel-profile.md` | `skills/case-writer-hybrid/references/wechat-channel-profile.md` |
| 复制 | `one/wechat-article-writer/_shared/intermediate-format.md` | `skills/case-writer-hybrid/references/intermediate-format.md` |
| 复制 | `one/wechat-article-writer/wechat-article-writer/references/framework-selection.md` | `skills/case-writer-hybrid/references/framework-selection.md` |
| 复制 | `one/wechat-article-writer/wechat-article-writer/references/pre-write-checks.md` | `skills/case-writer-hybrid/references/pre-write-checks.md` |
| 新建 | 无 | `skills/case-writer-hybrid/references/revision-loop.md` |
| 新建 | 无 | `skills/case-writer-hybrid/references/story-injection.md` |
| 编辑 | `skills/case-writer-hybrid/references/framework-selection.md` | 补 6 种结构模板 |
| 编辑 | `skills/case-writer-hybrid/references/hook-and-ending.md` | 补 5 种 Hook、禁止开头、结尾三件套 |
| 编辑 | `skills/case-writer-hybrid/SKILL.md` | 新增交互模式流程描述 |

### 第三步：升级 brief 模板

| 操作 | 目标 |
|------|------|
| 编辑 | `docs/stage1-brief-template.md`，补充 SCQA、风险提醒、素材可信度字段 |

---

## 六、后续可选优化（本次不做）

1. **已完成：扩展 `parse_brief()` 消费新字段**：让 SCQA、风险提醒、素材可信度参与自动模式的生成逻辑，提升自动模式质量
2. **已完成：升级 `humanizer-zh` 核心规则**：已补入机械连接词、长句气口、口语化替换和 `sentence_metrics` 追踪；后续可继续扩词表
3. **升级 `news-collect` / `topic-research`**：加入选题四维打分和“热点 → 角度”建议层
4. **升级 `wechat-formatter`**：加入标题 6 技法，输出 3-5 个标题候选
5. **检查 `ai-frontier-radar` 信源覆盖**：对照量子位、36 氪、微博热搜、知乎热榜、X、Hugging Face、GitHub Trending、微信指数、百度指数、社群信源
6. **已完成：新增 `script-writer-short`**：已沉淀短视频脚本生成 skill，支持文章/brief/选题稿转 90 秒口播稿，并提供 `article-to-short-script-pipeline`
7. **已完成：新增 `topic-radar`**：已沉淀“热点 → 选题角度”转化 skill，输出四维打分、选题公式、结构建议、标题方向和素材缺口，并提供 `topic-radar-to-brief-pipeline`
8. **已完成：补建 adversarial-content-review**：已建独立审稿 skill，输出 `reviews/*-review-report.md` 与 JSON sidecar，并接入 `topic-to-wechat-pipeline`
9. **已完成第一轮：继续升级 runtime.py 的模板拼接**：已完成 `story_resonance` 焦点回改和 `template_repetition` 焦点回改；后续可继续把更多框架结构做成策略化生成
10. **统一 intermediate format**：把 `one/` 的 `article-draft.md`、`review-report.md` 格式规范和 `content_system` 的产物格式对齐
11. **写跨平台适配指南**：补 `docs/cross-platform-guide.md`，总结公众号 / 视频号 / YouTube / 小红书差异
12. **全局化**：整套 skill 测试稳定后，迁移到全局 skill 目录，所有项目可用

---

## 七、验收清单

### Brief Builder 验收

- [x] 用新 `content-brief-builder` 生成一个 brief
- [x] 确认输出文件兼容 `stage1-brief-template.md` 的原有 section 契约，并追加 SCQA / 风险提醒 / 素材可信度
- [x] 确认 SCQA / 风险提醒 / 素材可信度字段存在于输出中
- [x] 确认 references 中已补入选题三公式、热点 7 步流程、四维打分

### 自动模式兼容性验收

- [x] 用新生成的 brief 跑 `run-skill case-writer-hybrid --input <brief>`
- [x] 确认 article、writing-pack、review-trace 都正常生成
- [x] 确认 `备注` 中的上游推荐框架等字段会参与自动模式
- [x] 确认 SCQA / 风险提醒 / 素材可信度已被自动模式直接解析，并传入正文与 writing-pack

### 交互模式验收

- [x] 手动触发交互模式，确认会停在「标题+大纲确认」步骤
- [x] 确认 references 参考库已落盘并被 `SKILL.md` 正确引用
- [x] 确认 `framework-selection.md`、`hook-and-ending.md`、`revision-loop.md`、`story-injection.md` 被串进交互模式说明
- [x] 确认 Step 5 可串联 `humanizer-zh`

### 字段生效边界验收

- [x] 确认新字段（SCQA 等）在一次真实交互模式写作中被使用
- [x] 确认新字段已被 `parse_brief()` 直接解析；低可信素材在自动模式中只作为待验证线索处理
- [x] 确认自动裁判已新增 `story_resonance` 维度，并能把缺故事、缺共鸣锚点的稿子列入下一轮回改焦点
- [x] 确认 `case-writer-hybrid` 收到 `story_resonance` 焦点后，会补入人物/冲突/转折小故事和共鸣锚点
- [x] 确认自动裁判已新增 `template_repetition` 维度，并能把固定模板句重复的稿子列入下一轮回改焦点
- [x] 确认 `case-writer-hybrid` 收到 `template_repetition` 焦点后，会轮换论证段表达，避免连续复用“这不是抽象判断”等固定句式
- [x] 确认 `adversarial-content-review` 已注册为 runtime skill，可通过 `run-skill` 输出 Markdown 审稿报告和 JSON sidecar
- [x] 确认 `topic-to-wechat-pipeline` 已在 `case-writer-hybrid` 后、`generate-image` 前接入独立审稿门控
- [x] 确认 `topic-radar` 已注册为 runtime skill，可通过 `run-skill` 输出候选切口、四维打分、推荐结构和 JSON sidecar
- [x] 确认 `topic-radar-to-brief-pipeline` 已注册，可先跑选题雷达再交给 `content-brief-builder`
- [x] 确认 `script-writer-short` 已注册为 runtime skill，可通过 `run-skill` 输出 Hook / Introduction / Body / Summary / 拍摄提示结构的短视频口播稿
- [x] 确认 `article-to-short-script-pipeline` 已注册，可把 Markdown 主稿直接转成短视频脚本

### 2026-05-06 验收记录

- 已运行单元测试：`.venv/bin/python -m unittest tests.test_content_brief_builder_runtime tests.test_workflow_registry`
- 已运行最小烟测：题目草稿 → `content-brief-builder` → `case-writer-hybrid`
- 烟测结果：brief、article、writing-pack、writing-pack.json、review-trace 均正常生成；`case-writer-hybrid` 质量门控通过，`ai_trace_risk` 为 `low`
- 已运行交互模式干跑：题目草稿 → `content-brief-builder` → `case-writer-hybrid` 交互模式 Step 0-2
- 交互模式验收样本：`AI 内容系统为什么总写不出稳定文章`
- 交互模式门控结果：核心判断明确、目标读者具体、素材条数满足最低要求；但素材可信度包含低可信条目，写全文前仍建议补 1-2 个真实案例
- 交互模式标题候选：`别再换 prompt 了，你缺的是内容系统`、`AI 写稿不稳定，问题不在模型`、`为什么你用 AI 写公众号还是忽高忽低`
- 交互模式大纲确认点：基于 SCQA 生成「换工具仍不稳定的情境 → prompt 崇拜与流程缺失的冲突 → 先改判断/流程/工具的核心问题 → 稳定产出靠系统的答案」四段式大纲，并在标题+大纲处停下等待用户确认
- 下一轮增强记录：`case-writer-hybrid` 自动模式已解析 SCQA / 风险提醒 / 素材可信度；SCQA 进入正文的问题提出和核心判断，风险提醒与可信度进入 writing-pack / JSON sidecar，低可信素材在正文中提示为待验证线索
- 故事共鸣增强记录：`skill_runtime/writing_core.py` 已新增 `story_resonance` 评分；`skills/case-writer-hybrid/runtime.py` 已把该焦点转成短故事和共鸣锚点回改动作；相关回归测试已覆盖
- 模板味降低记录：`skill_runtime/writing_core.py` 已新增 `template_repetition` 评分；`skills/case-writer-hybrid/runtime.py` 已把该焦点转成证据桥接段/读者价值段的多模板轮换；相关回归测试已覆盖
- 独立审稿记录：`skills/adversarial-content-review/` 已新增 `SKILL.md`、`skill.json`、`runtime.py`；`skill_runtime/engine.py` 已新增 executor；`topic-to-wechat-pipeline` 已接入审稿步；相关回归测试已覆盖
- 选题雷达记录：`skills/topic-radar/` 已新增 `SKILL.md`、`skill.json`、`runtime.py`；`skill_runtime/engine.py` 已新增 executor；`topic-radar-to-brief-pipeline` 已注册；相关回归测试已覆盖
- 短视频脚本记录：`skills/script-writer-short/` 已新增 `SKILL.md`、`skill.json`、`runtime.py`；`skill_runtime/engine.py` 已新增 executor；`article-to-short-script-pipeline` 已注册；相关回归测试已覆盖
