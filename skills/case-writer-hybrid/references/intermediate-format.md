# 中间产物格式规范

本文件定义写作 Skills 套件中所有中间产物的统一格式。每个 Skill 的输出必须符合对应规范，下游 Skill 才能正确消费。

**变更规则：** 本文件是唯一的全局契约。任何子计划不得自行修改。如需变更，必须先改本文件，再同步所有受影响的 Skill。

---

## topic-pool.md（选题池）

由 `content-topic-radar` 输出，被 `content-brief-builder` 消费。

```yaml
生成时间: string                      # ISO 日期
目标读者: string                      # 本次选题面向谁
候选题目:
  - 题目: string
    一句话判断: string                # 为什么这个题现在值得做
    原始信号:
      平台: string
      证据: string
    建议角度: string                  # 怎么讲，不复述原热点
    推荐钩子: string                  # 适合作为开头的冲突句
    综合评分: number                  # 0-16
    评分档位: 立刻做|补搜后做|观察|丢弃
    可延展形态:
      - string                       # 文章/口播/朋友圈/小红书
```

---

## content-brief.md（创作简报）

由 `content-brief-builder` 或 `interview-to-draft` 输出，被 `wechat-article-writer` 消费。

```yaml
选题: string                          # 有具体角度，不是"写关于XX"
来源: string                          # topic-pool 第几题 / 用户输入 / 访谈

# 方向锁定
目标读者: string                      # 具体到某一类人（不接受"所有人"）
读者痛点: string                      # 他们最关心/最困扰的一件事
核心判断: string                      # 你要传递的核心观点，必须有明确立场
写作目的: string                      # 希望读者看完做什么/想什么
切入角度: string                      # 不复述热点，而是"这对读者有什么用"

# 结构
推荐框架: 故事类|观点类|热点类|清单类|教学类
SCQA:
  情境(S): string                    # 大家熟悉的场景
  冲突(C): string                    # 场景中的矛盾
  问题(Q): string                    # 基于冲突的核心问题
  答案(A): string                    # 你的解决方案或观点

# 证据
素材清单:
  - 类型: 案例|数据|故事|金句|引用
    内容: string
    来源: string                      # 必须可追溯，至少 3 条

# 风险
风险提醒: string                      # 至少 1 个潜在翻车点
可延展形态:
  - string
```

**content-brief.md 不包含：** 标题方向、开头草稿、结尾草稿、包装建议。

---

## article-draft.md（公众号文章稿）

由 `wechat-article-writer` 输出。被 `content-polisher`、`adversarial-content-review`、`voice-script-writer` 消费。

```yaml
标题: string
副标题/摘要: string
正文: markdown                         # 完整正文
字数: number
brief来源: string                      # 指向 content-brief.md 的路径
```

---

## voice-script.md（口播逐字稿）

由 `voice-script-writer` 输出。只消费 `article-draft.md`，不直接消费 `content-brief.md`。

```yaml
主题: string
时长: string                          # 如"90秒"、"3分钟"
逐字稿: string
封面标题:
  - string                            # 3个候选
来源稿件: string                       # 指向 article-draft.md 路径
```

---

## review-report.md（审稿报告）

由 `adversarial-content-review` 输出。

```yaml
稿件来源: string                      # 指向被审稿件的路径
总分: number                          # 0-10
维度评分:
  标题吸引力: number
  结构稳定性: number
  数据强度: number
  读者价值: number
  篇幅比例: number
主要问题:
  - string
修改建议:
  - string
结论: 通过|需修改|需重写
```
