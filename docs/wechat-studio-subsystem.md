# `wechat-studio` 工作台说明

## 1. 它是什么

`wechat-studio` 是当前内容 Skills 体系中的**微信包装工作台**。

它不是单个 Skill，而是一个服务于排版、包装、预览、封面/配图与后续推送草稿的人机协作工作台。

当前实现目录为：

- `skills/wechat-studio/`

它不是底层执行器，而是公众号包装工作台。

## 2. 它在当前体系中的位置

在阶段 1 里，它不再作为主链路节点，而是辅助两个原子 Skill：

- `generate-image`
- `wechat-formatter`

也就是说，当前主链路仍然是：

`case-writer-hybrid` -> `generate-image` -> `wechat-formatter`

而 `wechat-studio` 的位置是：

调用 `generate-image` / `wechat-formatter` 的人工预览、参数调节和结果确认工作台

## 3. 它负责什么

当前已识别出的职责包括：

- Markdown 导入与文章状态管理
- 调用下层执行器生成配图与微信 HTML
- 微信排版预览
- 封面候选生成
- 正文配图预览与管理
- 包装参数调节
- 后续推送微信草稿箱

## 4. 它不负责什么

当前不建议让 `wechat-studio` 负责：

- 上游观点写作
- 外文翻译
- 飞书中枢归档
- 小红书分发
- 视频链路

这些仍由主 skill 体系的其他原子节点负责。

## 5. 当前命名约定

- 逻辑名称：`wechat-studio`
- 中文名称：微信包装工作台
- 当前实现目录：`skills/wechat-studio/`

## 6. 后续演进

后续如果接入小红书包装，有两种方向：

1. 保持 `wechat-studio` 只服务公众号，再新增独立的小红书子系统
2. 等多平台包装成熟后，再把多个子系统抽象到更高一层

在当前阶段，不提前做大抽象，先把 `wechat-studio` 作为公众号包装工作台跑稳。
