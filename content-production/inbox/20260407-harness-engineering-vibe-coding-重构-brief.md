# 阶段 1 Brief：Harness Engineering 重构了 vibe coding：AI 一人公司为什么最终还是要回到工程师思维

## 基础信息

- `date`：20260407
- `slug`：harness-engineering-vibe-coding-重构
- `topic`：Harness Engineering 重构了 vibe coding：AI 一人公司为什么最终还是要回到工程师思维
- `target_reader`：AI 一人公司创业者、独立开发者、在做小程序或轻应用商业化交付的小团队
- `publish_goal`：写成一篇适合公众号发布的观点型长文，把一个强判断讲清楚：vibe coding 能稳定做简单应用，但一旦进入商业化交付，就必须回到工程师思维；而我们做小程序时，其实已经在实践工程化的全栈 vibe coding

## 核心观点

`vibe coding` 当然有价值，它把做产品的门槛拉低了，能让一个人快速起 demo、页面、MVP 和轻量应用。

但它的能力边界也很清楚：它擅长把“无”快速变成“有”，却不擅长把“有”长期变成“稳”。一旦进入商业化交付，问题就不再是“AI 会不会写”，而是“这套东西能不能持续迭代、出错后能不能回退、环境变了还能不能继续推进、线上问题能不能排查、需求变更会不会把系统带崩”。

这也是为什么到了 2026 年，`Harness Engineering` 会重构 `vibe coding` 的生产范式。真正决定 AI 一人公司结果的，不再是谁更会写 prompt，而是谁更早把 agent 放进了一套有约束、有验证、有状态管理、有回滚机制的工程系统里。

更重要的是，这并不是一个“大厂提出的新概念，普通人才刚刚接触”的故事。更准确的说法是：在 Anthropic 于 `2025-11-26` 发布 *Effective harnesses for long-running agents*、OpenAI 于 `2026-02-11` 发布 *Harness engineering: leveraging Codex in an agent-first world* 之前后，我们在做小程序商业化交付时，其实已经在碰到并解决同一类问题了。那时我们未必叫它 `Harness Engineering`，但我们做的，已经是工程化的全栈 vibe coding 雏形。

## 背景与语境

- 2025 年末到 2026 年初，Anthropic、OpenAI、Martin Fowler 先后把 `harness engineering` 系统化讲清楚，说明行业焦点已经从“模型能力”转向“交付系统能力”。
- `vibe coding` 在 2025 到 2026 年被大量讨论，但大多数讨论停留在“AI 写代码很快”“一个人就能做产品”这一层。
- 当前最容易误导人的叙事是：只要 AI 会写代码，软件生产的主要矛盾就解决了。
- 真正的分水岭不是能不能做出 demo，而是能不能把一个产品稳稳交付给真实用户、持续迭代并承担结果。
- AI 一人公司的真正瓶颈不是代码生成速度，而是有没有一套“个人 + agent”的微型研发体系。

## 论证方向

1. 为什么 `vibe coding` 能稳定做简单应用，却很难独自撑起商业化交付。
2. 为什么一旦进入商业化交付，就必须回到工程师思维：约束、验证、状态管理、回滚、发布节奏、责任边界。
3. 为什么从我们做小程序的过程看，在 Anthropic 等人把概念讲清楚之前，我们已经在实践工程化的全栈 `vibe coding`。
4. 为什么到了 2026 年，`Harness Engineering` 真正重构的，不是写代码的方法，而是 AI 一人公司的生产范式。

## 可用案例 / 素材

- 案例 1：Anthropic 在 `2025-11-26` 发布 *Effective harnesses for long-running agents*，把长运行 agent 的核心放在状态管理、环境控制、阶段切分、反馈回路。
- 案例 2：OpenAI 在 `2026-02-11` 发布 *Harness engineering: leveraging Codex in an agent-first world*，明确强调真正的差距来自模型之外的 harness。
- 案例 3：Martin Fowler 在 `2026-04-02` 发布 *Harness engineering for coding agent users*，把这件事翻译成工程语言，说明 coding agent 用户必须补“外层系统”。
- 案例 4：我们做小程序的真实经验：AI 可以快速起页面、组件、流程和接口草稿，但一旦接入真实数据、状态流转、权限边界、异常处理、发布节奏，就必须补文档、规则、测试、检查点和回归验证。
- 案例 5：AI 一人公司常见现场：demo 很快，商业化很慢；原因不是 AI 不够强，而是没有把 agent 放进一个可验证、可回退、可协作的工程系统。

## 明确不要写什么

- 不要写成纯术语科普文
- 不要写成“我们比 Anthropic 更早提出概念”的夸张叙事
- 不要写成“反 AI”或“反 vibe coding”的保守派文章
- 不要写成工具盘点或 prompt 技巧堆砌
- 不要把文章写成空泛趋势文，必须有工程现场感和交付感

## 风格要求

- 风格关键词：锋利、判断明确、工程视角、创始人视角、交付现场感
- 要有“我们真的做过小程序交付”的第一人称经验感，但不要编造没验证过的细节
- 允许出现 3 到 5 句适合传播的强判断
- 不要太学术，优先写成公众号可读长文

## 配图方向

- 希望图片类型：公众号封面感信息图
- 核心视觉：一个人站在前面，背后不是代码瀑布，而是 `Plan -> Act -> Verify -> Rollback` 的工程流水线
- 可考虑元素：agent、回路、约束、检查点、小程序交付、微型研发体系
- 禁止元素：廉价赛博机器人头像、抽象蓝紫光效、无意义代码雨

## 备注

- 文章的关键叙事不是“谁最早提出了这个词”，而是“在大厂把它系统化命名之前，我们已经在真实交付里碰到了同一个工程问题”。
- 文章里要明确区分：
  - `vibe coding` 擅长的是从 0 到 1
  - `Harness Engineering` 解决的是从 1 到稳定交付
- 建议把“工程化的全栈 vibe coding”解释成：依然用 AI 快速开发，但所有产出都必须纳入文档、约束、验证、协作和回滚系统。
- 可以参考已有本地分析文件：
  - `content-production/inbox/20260407-harness-engineering-一人公司选题分析.md`
  - `content-production/inbox/20260407-harness-engineering-国内外-公众号综合分析-research.md`
  - `content-production/inbox/20260407-harness-engineering-公众号镜像汇总.md`
