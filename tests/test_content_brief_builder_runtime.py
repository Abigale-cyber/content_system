from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skill_runtime.engine import run_skill  # noqa: E402


class ContentBriefBuilderRuntimeTests(unittest.TestCase):
    def test_run_skill_outputs_stage1_compatible_brief(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "topic.md"
            input_path.write_text(
                "# AI 内容系统为什么总写不出稳定文章\n\n"
                "我想写给已经开始用 AI 写公众号，但产出不稳定的人看。\n"
                "希望读者看完知道问题不只是工具，而是缺一套流程。\n",
                encoding="utf-8",
            )

            result = run_skill("content-brief-builder", str(input_path))

            output_path = Path(result.output_path)
            self.addCleanup(lambda: output_path.exists() and output_path.unlink())

            text = output_path.read_text(encoding="utf-8")

            self.assertEqual(result.skill_id, "content-brief-builder")
            self.assertEqual(result.run_status, "completed")
            self.assertFalse(result.blocking)
            self.assertIn("## 基础信息", text)
            self.assertIn("## 核心观点", text)
            self.assertIn("## 背景与语境", text)
            self.assertIn("## 论证方向", text)
            self.assertIn("## 可用案例 / 素材", text)
            self.assertIn("## SCQA 结构", text)
            self.assertIn("## 风险提醒", text)
            self.assertIn("## 素材来源可信度", text)
            self.assertIn("`publish_goal`", text)

    def test_run_skill_preserves_explicit_fields_and_adds_recommendations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "hot-topic.md"
            input_path.write_text(
                "# DeepSeek 更新后，公众号作者最该先补的不是 prompt，而是选题判断\n\n"
                "目标读者：已经稳定发公众号、但不知道怎么追热点的 AI 创作者\n"
                "写作目的：帮助他们在热点来的时候，先判断值不值得写，再决定怎么写\n\n"
                "这是一个热点话题，重点不是复述更新，而是告诉读者这对公众号作者有什么用。\n"
                "别再只盯着 prompt 模板了，用这次更新做一次选题判断，效果会比继续堆工具更直接。\n",
                encoding="utf-8",
            )

            result = run_skill("content-brief-builder", str(input_path))

            output_path = Path(result.output_path)
            self.addCleanup(lambda: output_path.exists() and output_path.unlink())

            text = output_path.read_text(encoding="utf-8")

            self.assertIn("`target_reader`：已经稳定发公众号、但不知道怎么追热点的 AI 创作者", text)
            self.assertIn("`publish_goal`：帮助他们在热点来的时候，先判断值不值得写，再决定怎么写", text)
            self.assertIn("- 推荐框架：热点类", text)
            self.assertIn("- 推荐选题公式：低效动作 + AI 替代 + 效果对比", text)
            self.assertIn("- 热点判断：是，适合按“热点七步法”处理", text)
            self.assertIn("- 选题四维打分：", text)

    def test_run_skill_understands_news_report_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "ai-coding-news-report.md"
            input_path.write_text(
                "# 资讯扫描报告：AI 编程周报\n\n"
                "## 扫描摘要\n\n"
                "- 共抓取 8 条候选信息，覆盖 3 个来源：Hacker News（3）、GitHub（3）、博客（2）\n"
                "- 扫描 profile：`global_ai`；实际来源：hackernews, github, ai_newsletters\n\n"
                "## 候选条目\n\n"
                "1. [Harness engineering for coding agent users - Martin Fowler](https://martinfowler.com/articles/harness-engineering.html)\n"
                "- 来源：Hacker News | 时间：2026-05-01 | 热度：高\n"
                "- 摘要：把 AI 编程从会写 demo 带入稳定交付，关键不是 prompt，而是 harness、反馈回路与验证。\n\n"
                "2. [Effective harnesses for long-running agents - Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)\n"
                "- 来源：博客 | 时间：2026-05-02 | 热度：高\n"
                "- 摘要：长任务代理需要检查点、回滚和人工接管机制。\n\n"
                "## 推荐选题\n\n"
                "1. 别把 AI 编程当提示词比赛，真正拉开差距的是运行时\n"
                "- 推荐理由：来源 Hacker News，热度信号 高。\n"
                "- 写作角度：适合写成“从工具炫技转向工程交付”的判断文。\n"
                "- 值得写评分：82\n\n"
                "## 写作价值判断\n\n"
                "### 1. 别把 AI 编程当提示词比赛，真正拉开差距的是运行时\n\n"
                "- `writeworthiness_score`：82\n"
                "- `primary_reader`：已经在团队里试用 AI 编程，但产出不稳定的工程负责人\n"
                "- `primary_pain_point`：大家会写 demo，却很难把结果接进真实交付流程\n"
                "- `shareability_note`：这类反常识判断很容易引发转发讨论\n\n"
                "## 推荐切口\n\n"
                "### 1. 别把 AI 编程当提示词比赛，真正拉开差距的是运行时\n\n"
                "- 推荐切口：先解释为什么“会写 demo”不等于“能交付”，再拆运行时、验证和回滚。\n"
                "- 更适合先打的痛点：大家会写 demo，却很难把结果接进真实交付流程\n\n"
                "## 推荐框架与开头\n\n"
                "### 1. 别把 AI 编程当提示词比赛，真正拉开差距的是运行时\n\n"
                "- `recommended_structure`：对比式\n"
                "- `recommended_opening_type`：反常识开头\n",
                encoding="utf-8",
            )

            result = run_skill("content-brief-builder", str(input_path))

            output_path = Path(result.output_path)
            self.addCleanup(lambda: output_path.exists() and output_path.unlink())

            text = output_path.read_text(encoding="utf-8")

            self.assertEqual(result.metadata["source_type"], "news-report")
            self.assertIn("`topic`：别把 AI 编程当提示词比赛，真正拉开差距的是运行时", text)
            self.assertIn("`target_reader`：已经在团队里试用 AI 编程，但产出不稳定的工程负责人", text)
            self.assertIn("大家会写 demo，却很难把结果接进真实交付流程", text)
            self.assertIn("- 推荐框架：对比式", text)
            self.assertIn("- 上游来源类型：news-report", text)
            self.assertIn("- 采用切口：先解释为什么“会写 demo”不等于“能交付”", text)
            self.assertIn("Martin Fowler", text)

    def test_run_skill_understands_research_report_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "ai-coding-research.md"
            input_path.write_text(
                "# 深度研究报告：Harness Engineering 与 AI 编程交付\n\n"
                "## 研究问题\n\n"
                "为什么 AI 编程一旦进入商业化交付，就必须回到工程思维、运行时约束与可验证性？\n\n"
                "## 核心结论\n\n"
                "- Harness Engineering 不是提示词技巧，而是把模型输出纳入可重复、可观测、可审计交付流程的运行时系统。\n\n"
                "## 关键证据\n\n"
                "1. [Harness engineering for coding agent users - Martin Fowler](https://martinfowler.com/articles/harness-engineering.html)\n"
                "2. [Effective harnesses for long-running agents - Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)\n\n"
                "## 候选写作角度\n\n"
                "1. 直接回答“为什么 AI 编程一旦进入商业化交付，就必须回到工程思维”，拆成现状、分歧、机会与风险四段。\n"
                "2. 对比 vibe coding 与 harness engineering 的适用边界。\n\n"
                "## 推荐读者与主痛点\n\n"
                "- `reader_profile`：关注 AI 编程落地、想把研究结果转成公众号文章的内容负责人\n"
                "- `pain_point`：知道这个概念重要，但还说不清为什么它比 prompt 更接近真实交付\n\n"
                "## 推荐框架与论证顺序\n\n"
                "- `recommended_structure`：问答式\n"
                "- `recommended_opening_type`：提问式开头\n\n"
                "## 标题方向\n\n"
                "- AI 编程真正的分水岭，不是 prompt，而是运行时\n",
                encoding="utf-8",
            )

            result = run_skill("content-brief-builder", str(input_path))

            output_path = Path(result.output_path)
            self.addCleanup(lambda: output_path.exists() and output_path.unlink())

            text = output_path.read_text(encoding="utf-8")

            self.assertEqual(result.metadata["source_type"], "research-report")
            self.assertIn("`target_reader`：关注 AI 编程落地、想把研究结果转成公众号文章的内容负责人", text)
            self.assertIn("Harness Engineering 不是提示词技巧", text)
            self.assertIn("知道这个概念重要，但还说不清为什么它比 prompt 更接近真实交付", text)
            self.assertIn("- 推荐框架：问答式", text)
            self.assertIn("- 上游来源类型：research-report", text)
            self.assertIn("- 采用切口：直接回答“为什么 AI 编程一旦进入商业化交付，就必须回到工程思维”", text)
            self.assertIn("- 上游标题方向：AI 编程真正的分水岭，不是 prompt，而是运行时", text)
            self.assertIn("Anthropic", text)


if __name__ == "__main__":
    unittest.main()
