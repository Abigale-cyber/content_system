from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skill_runtime.engine import load_case_writer_runtime  # noqa: E402


class CaseWriterHybridRuntimeTests(unittest.TestCase):
    def test_parse_brief_extracts_upstream_guidance(self) -> None:
        runtime = load_case_writer_runtime()
        with tempfile.TemporaryDirectory() as tmp_dir:
            brief_path = Path(tmp_dir) / "brief.md"
            brief_path.write_text(
                "# 阶段 1 观点 Brief\n\n"
                "## 基础信息\n\n"
                "- `date`：20260505\n"
                "- `slug`：ai-runtime-gap\n"
                "- `topic`：别把 AI 编程当提示词比赛，真正拉开差距的是运行时\n"
                "- `target_reader`：已经在团队里试用 AI 编程，但产出不稳定的工程负责人\n"
                "- `publish_goal`：帮助读者先判断值不值得追这个题，再决定怎么写\n\n"
                "## 核心观点\n\n"
                "真正拉开差距的不是 prompt，而是运行时、验证和回滚。\n\n"
                "## 背景与语境\n\n"
                "- 这类讨论最近明显增多。\n"
                "- 很多人还在把 AI 编程理解成 prompt 技巧比赛。\n"
                "- 现在最适合把热点转成工程判断。\n\n"
                "## 论证方向\n\n"
                "1. 为什么会写 demo 不等于能交付\n"
                "2. 运行时约束、验证和回滚为什么是商业化交付的分水岭\n"
                "3. 工程负责人现在该先补哪层能力\n\n"
                "## 可用案例 / 素材\n\n"
                "- Harness engineering for coding agent users - Martin Fowler\n"
                "- Effective harnesses for long-running agents - Anthropic\n\n"
                "## 备注\n\n"
                "- 推荐框架：对比式\n"
                "- 上游来源类型：news-report\n"
                "- 采用切口：先解释为什么“会写 demo”不等于“能交付”，再拆运行时、验证和回滚。\n"
                "- 上游建议开头：反常识开头\n",
                encoding="utf-8",
            )

            brief = runtime.parse_brief(brief_path)

            self.assertEqual(brief["recommended_framework"], "对比式")
            self.assertEqual(brief["source_type"], "news-report")
            self.assertIn("会写 demo", brief["selected_angle"])
            self.assertEqual(brief["recommended_opening_type"], "反常识开头")

    def test_parse_brief_extracts_scqa_risk_and_material_confidence(self) -> None:
        runtime = load_case_writer_runtime()
        with tempfile.TemporaryDirectory() as tmp_dir:
            brief_path = Path(tmp_dir) / "brief.md"
            brief_path.write_text(
                "# 阶段 1 观点 Brief\n\n"
                "## 基础信息\n\n"
                "- `date`：20260506\n"
                "- `slug`：ai-content-system\n"
                "- `topic`：AI 内容系统为什么总写不出稳定文章\n"
                "- `target_reader`：已经开始用 AI 写公众号，但产出忽高忽低的内容创作者\n"
                "- `publish_goal`：帮助他们看清问题不只是 prompt，而是缺少稳定流程\n\n"
                "## 核心观点\n\n"
                "稳定内容产出靠系统，不靠灵感。\n\n"
                "## 背景与语境\n\n"
                "- 很多人每天都在换模型、换工具、换提示词。\n"
                "- 文章质量仍然忽高忽低。\n"
                "- 现在适合把工具讨论转成流程判断。\n\n"
                "## 论证方向\n\n"
                "1. 为什么换 prompt 解决不了稳定产出\n"
                "2. 为什么 brief、审稿和发布节奏才是关键\n"
                "3. 普通创作者应该先补哪一层流程\n\n"
                "## 可用案例 / 素材\n\n"
                "- 来源笔记：interactive-topic.md\n"
                "- 一个创作者连续换了 5 套 prompt，文章质量仍然不稳定\n"
                "- 待补一条真实案例\n\n"
                "## SCQA 结构\n\n"
                "- 情境(S)：很多创作者已经开始用 AI 写公众号。\n"
                "- 冲突(C)：工具越来越多，文章质量却仍然不稳定。\n"
                "- 问题(Q)：到底应该先改 prompt、改流程，还是改选题判断？\n"
                "- 答案(A)：先搭从选题到审稿的内容系统，再优化工具。\n\n"
                "## 风险提醒\n\n"
                "- 至少 1 个潜在翻车点：如果没有真实案例，文章会变成流程口号。\n\n"
                "## 素材来源可信度\n\n"
                "- 案例 1 可信度：高\n"
                "- 案例 2 可信度：中\n"
                "- 案例 3 可信度：低\n",
                encoding="utf-8",
            )

            brief = runtime.parse_brief(brief_path)

            self.assertEqual(brief["scqa"]["situation"], "很多创作者已经开始用 AI 写公众号。")
            self.assertEqual(brief["scqa"]["complication"], "工具越来越多，文章质量却仍然不稳定。")
            self.assertEqual(brief["scqa"]["question"], "到底应该先改 prompt、改流程，还是改选题判断？")
            self.assertEqual(brief["scqa"]["answer"], "先搭从选题到审稿的内容系统，再优化工具。")
            self.assertIn("没有真实案例", brief["risk_reminders"][0])
            self.assertEqual(
                brief["material_confidence"],
                [
                    {"case": "案例 1", "level": "高"},
                    {"case": "案例 2", "level": "中"},
                    {"case": "案例 3", "level": "低"},
                ],
            )

    def test_run_case_writer_hybrid_uses_upstream_guidance(self) -> None:
        runtime = load_case_writer_runtime()
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir)
            brief_path = workspace_root / "brief.md"
            brief_path.write_text(
                "# 阶段 1 观点 Brief\n\n"
                "## 基础信息\n\n"
                "- `date`：20260505\n"
                "- `slug`：ai-runtime-gap\n"
                "- `topic`：别把 AI 编程当提示词比赛，真正拉开差距的是运行时\n"
                "- `target_reader`：已经在团队里试用 AI 编程，但产出不稳定的工程负责人\n"
                "- `publish_goal`：帮助他们先看清为什么这不是 prompt 问题，而是交付问题\n\n"
                "## 核心观点\n\n"
                "真正拉开差距的不是 prompt，而是运行时、验证和回滚。\n\n"
                "## 背景与语境\n\n"
                "- 这类讨论最近明显增多。\n"
                "- 很多人还在把 AI 编程理解成 prompt 技巧比赛。\n"
                "- 现在最适合把热点转成工程判断。\n\n"
                "## 论证方向\n\n"
                "1. 为什么会写 demo 不等于能交付\n"
                "2. 运行时约束、验证和回滚为什么是商业化交付的分水岭\n"
                "3. 工程负责人现在该先补哪层能力\n\n"
                "## 可用案例 / 素材\n\n"
                "- Harness engineering for coding agent users - Martin Fowler\n"
                "- Effective harnesses for long-running agents - Anthropic\n\n"
                "## 备注\n\n"
                "- 推荐框架：对比式\n"
                "- 上游来源类型：news-report\n"
                "- 采用切口：先解释为什么“会写 demo”不等于“能交付”，再拆运行时、验证和回滚。\n"
                "- 上游建议开头：反常识开头\n",
                encoding="utf-8",
            )

            result = runtime.run_case_writer_hybrid(brief_path, workspace_root=workspace_root)

            package = json.loads(Path(result["writing_pack_json_path"]).read_text(encoding="utf-8"))
            article = Path(result["article_path"]).read_text(encoding="utf-8")

            self.assertEqual(result["chosen_structure"]["type"], "parallel")
            self.assertEqual(result["upstream_guidance"]["source_type"], "news-report")
            self.assertEqual(package["chosen_structure"]["type"], "parallel")
            self.assertEqual(package["upstream_guidance"]["source_type"], "news-report")
            self.assertEqual(package["upstream_guidance"]["recommended_framework"], "对比式")
            self.assertEqual(package["opening_options"][0]["source"], "upstream-guidance")
            self.assertIn("会写 demo", package["opening_options"][0]["text"])
            self.assertIn("这篇文章会沿着这样一个切口展开", article)
            self.assertIn("会写 demo", article)

    def test_run_case_writer_hybrid_prefers_upstream_titles_and_evidence_lines(self) -> None:
        runtime = load_case_writer_runtime()
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir)
            brief_path = workspace_root / "brief.md"
            brief_path.write_text(
                "# 阶段 1 观点 Brief\n\n"
                "## 基础信息\n\n"
                "- `date`：20260505\n"
                "- `slug`：harness-research\n"
                "- `topic`：Harness Engineering 与 AI 编程交付\n"
                "- `target_reader`：关注 AI 编程落地、想把研究结果转成公众号文章的内容负责人\n"
                "- `publish_goal`：帮助他们把研究结论转成一篇能发的判断文\n\n"
                "## 核心观点\n\n"
                "Harness Engineering 不是提示词技巧，而是把模型输出纳入可重复、可观测、可审计交付流程的运行时系统。\n\n"
                "## 背景与语境\n\n"
                "- 海外工程文章和中文内容圈都在讨论这个概念。\n"
                "- 很多人知道它重要，但还说不清为什么比 prompt 更接近真实交付。\n"
                "- 现在最适合把研究结论转成判断文。\n\n"
                "## 论证方向\n\n"
                "1. 为什么 AI 编程一旦进入商业化交付，就必须回到工程思维\n"
                "2. vibe coding 与 harness engineering 的适用边界分别在哪里\n"
                "3. 内容负责人现在应该如何把这个概念讲清楚\n\n"
                "## 可用案例 / 素材\n\n"
                "- Harness engineering for coding agent users - Martin Fowler\n"
                "- Effective harnesses for long-running agents - Anthropic\n"
                "- What Is an Agent Harness? - Firecrawl\n\n"
                "## 备注\n\n"
                "- 推荐框架：问答式\n"
                "- 上游来源类型：research-report\n"
                "- 采用切口：直接回答“为什么 AI 编程一旦进入商业化交付，就必须回到工程思维”。\n"
                "- 上游建议开头：提问式开头\n"
                "- 上游标题方向：AI 编程真正的分水岭，不是 prompt，而是运行时\n"
                "- 上游标题方向：为什么商业化交付一定会把 AI 编程拉回工程世界\n",
                encoding="utf-8",
            )

            result = runtime.run_case_writer_hybrid(brief_path, workspace_root=workspace_root)

            package = json.loads(Path(result["writing_pack_json_path"]).read_text(encoding="utf-8"))
            article = Path(result["article_path"]).read_text(encoding="utf-8")

            self.assertEqual(result["chosen_structure"]["type"], "what_why_how")
            self.assertEqual(package["title_options"][0]["source"], "upstream-guidance")
            self.assertEqual(
                package["title_options"][0]["title"],
                "AI 编程真正的分水岭，不是 prompt，而是运行时",
            )
            self.assertIn("Martin Fowler", article)
            self.assertIn("Anthropic", article)
            self.assertIn("这不是抽象判断", article)

    def test_run_case_writer_hybrid_carries_scqa_risk_and_confidence_into_outputs(self) -> None:
        runtime = load_case_writer_runtime()
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir)
            brief_path = workspace_root / "brief.md"
            brief_path.write_text(
                "# 阶段 1 观点 Brief\n\n"
                "## 基础信息\n\n"
                "- `date`：20260506\n"
                "- `slug`：ai-content-system\n"
                "- `topic`：AI 内容系统为什么总写不出稳定文章\n"
                "- `target_reader`：已经开始用 AI 写公众号，但产出忽高忽低的内容创作者\n"
                "- `publish_goal`：帮助他们看清问题不只是 prompt，而是缺少稳定流程\n\n"
                "## 核心观点\n\n"
                "稳定内容产出靠系统，不靠灵感。\n\n"
                "## 背景与语境\n\n"
                "- 很多人每天都在换模型、换工具、换提示词。\n"
                "- 文章质量仍然忽高忽低。\n"
                "- 现在适合把工具讨论转成流程判断。\n\n"
                "## 论证方向\n\n"
                "1. 为什么换 prompt 解决不了稳定产出\n"
                "2. 为什么 brief、审稿和发布节奏才是关键\n"
                "3. 普通创作者应该先补哪一层流程\n\n"
                "## 可用案例 / 素材\n\n"
                "- 来源笔记：interactive-topic.md\n"
                "- 一个创作者连续换了 5 套 prompt，文章质量仍然不稳定\n"
                "- 待补一条真实案例\n\n"
                "## SCQA 结构\n\n"
                "- 情境(S)：很多创作者已经开始用 AI 写公众号。\n"
                "- 冲突(C)：工具越来越多，文章质量却仍然不稳定。\n"
                "- 问题(Q)：到底应该先改 prompt、改流程，还是改选题判断？\n"
                "- 答案(A)：先搭从选题到审稿的内容系统，再优化工具。\n\n"
                "## 风险提醒\n\n"
                "- 至少 1 个潜在翻车点：如果没有真实案例，文章会变成流程口号。\n\n"
                "## 素材来源可信度\n\n"
                "- 案例 1 可信度：高\n"
                "- 案例 2 可信度：中\n"
                "- 案例 3 可信度：低\n",
                encoding="utf-8",
            )

            result = runtime.run_case_writer_hybrid(brief_path, workspace_root=workspace_root)

            package = json.loads(Path(result["writing_pack_json_path"]).read_text(encoding="utf-8"))
            article = Path(result["article_path"]).read_text(encoding="utf-8")

            self.assertEqual(package["scqa"]["question"], "到底应该先改 prompt、改流程，还是改选题判断？")
            self.assertIn("没有真实案例", package["risk_reminders"][0])
            self.assertEqual(package["material_confidence"][2]["level"], "低")
            self.assertIn("到底应该先改 prompt、改流程，还是改选题判断？", article)
            self.assertIn("低可信素材只作为待验证线索", article)
            self.assertLessEqual(article.count("如果只把这个问题看成一个表面动作"), 1)
            self.assertNotIn("最能说明这一点的案例是：待补一条真实案例", article)
            self.assertIn("待补一条真实案例", article)
            self.assertIn("只能作为待验证线索", article)

    def test_run_case_writer_hybrid_normalizes_punctuation_artifacts(self) -> None:
        runtime = load_case_writer_runtime()
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir)
            brief_path = workspace_root / "brief.md"
            brief_path.write_text(
                "# 阶段 1 观点 Brief\n\n"
                "## 基础信息\n\n"
                "- `date`：20260506\n"
                "- `slug`：punctuation-cleanup\n"
                "- `topic`：AI 编程交付为什么不能只看 prompt\n"
                "- `target_reader`：正在把 AI 编程用于真实项目的工程负责人\n"
                "- `publish_goal`：帮他们看清 prompt 和交付系统的区别\n\n"
                "## 核心观点\n\n"
                "真正决定交付质量的不是 prompt，而是验证、回滚和运行时约束。\n\n"
                "## 背景与语境\n\n"
                "- 很多人已经能用 AI 写出 demo。\n"
                "- 一进入真实项目，质量、回归和责任边界就会冒出来。\n"
                "- 现在适合把话题从工具技巧拉回工程交付。\n\n"
                "## 论证方向\n\n"
                "1. 为什么 demo 能跑不代表能交付\n"
                "2. 为什么验证和回滚才是分水岭\n"
                "3. 工程负责人该先补哪层能力\n\n"
                "## 可用案例 / 素材\n\n"
                "- Martin Fowler 的 harness engineering 文章\n"
                "- Anthropic long-running agents 工程文章\n"
                "- OpenAI Codex 运行时实践\n\n"
                "## 备注\n\n"
                "- 推荐框架：问答式\n"
                "- 上游建议开头：提问式开头\n"
                "- 采用切口：直接回答“为什么 AI 编程一旦进入商业化交付，就必须回到工程思维”。\n",
                encoding="utf-8",
            )

            result = runtime.run_case_writer_hybrid(brief_path, workspace_root=workspace_root)

            article = Path(result["article_path"]).read_text(encoding="utf-8")

            self.assertNotIn("。；", article)
            self.assertNotIn("。？", article)
            self.assertNotIn("？。", article)

    def test_compose_article_adds_story_anchor_when_story_resonance_is_focus(self) -> None:
        runtime = load_case_writer_runtime()
        brief = {
            "topic": "AI 内容系统为什么总写不出稳定文章",
            "target_reader": "已经开始用 AI 写公众号，但产出忽高忽低的内容创作者",
            "publish_goal": "帮助他们看清问题不只是 prompt，而是缺少稳定流程",
            "core_view": "稳定内容产出靠系统，不靠灵感。",
            "background": ["很多人每天都在换模型、换工具、换提示词。"],
            "arguments": ["为什么换 prompt 解决不了稳定产出"],
            "cases": ["一个创作者连续换了 5 套 prompt，文章质量仍然不稳定"],
            "source_type": "",
            "selected_angle": "",
            "scqa": {},
            "material_confidence": [{"case": "案例 1", "level": "中"}],
        }
        package = {
            "title_options": [{"title": "AI 内容系统真正该补的不是 prompt"}],
            "opening_options": [{"text": "稳定内容产出靠系统，不靠灵感。"}],
            "ending_options": [{"text": "先把流程搭起来，再谈工具优化。"}],
            "chosen_structure": {"type": "progressive"},
            "highlight_quotes": ["稳定内容产出靠系统，不靠灵感。"],
        }

        article = runtime.compose_article(
            brief=brief,
            package=package,
            round_index=2,
            focus_areas=["story_resonance"],
        )

        self.assertIn("你有没有这种感觉", article)
        self.assertIn("有个", article)
        self.assertIn("后来", article)
        self.assertIn("说白了", article)

    def test_compose_article_varies_argument_templates_when_repetition_is_focus(self) -> None:
        runtime = load_case_writer_runtime()
        brief = {
            "topic": "AI 编程交付为什么不能只看 prompt",
            "target_reader": "正在把 AI 编程用于真实项目的工程负责人",
            "publish_goal": "帮他们看清 prompt 和交付系统的区别",
            "core_view": "真正决定交付质量的不是 prompt，而是验证、回滚和运行时约束。",
            "background": ["很多团队已经能用 AI 写出 demo。"],
            "arguments": [
                "为什么 demo 能跑不代表能交付",
                "为什么验证和回滚才是分水岭",
                "工程负责人该先补哪层能力",
            ],
            "cases": [
                "Martin Fowler 的 harness engineering 文章",
                "Anthropic long-running agents 工程文章",
                "OpenAI Codex 运行时实践",
            ],
            "source_type": "research-report",
            "selected_angle": "",
            "scqa": {},
            "material_confidence": [
                {"case": "案例 1", "level": "高"},
                {"case": "案例 2", "level": "高"},
                {"case": "案例 3", "level": "高"},
            ],
        }
        package = {
            "title_options": [{"title": "AI 编程交付真正该补的不是 prompt"}],
            "opening_options": [{"text": "很多人以为 AI 编程拼的是 prompt，其实拼的是交付系统。"}],
            "ending_options": [{"text": "先把验证和回滚搭起来，再谈 prompt 技巧。"}],
            "chosen_structure": {"type": "progressive"},
            "highlight_quotes": ["真正决定交付质量的不是 prompt，而是验证、回滚和运行时约束。"],
        }

        article = runtime.compose_article(
            brief=brief,
            package=package,
            round_index=2,
            focus_areas=["template_repetition"],
        )

        self.assertLessEqual(article.count("这不是抽象判断"), 1)
        self.assertLessEqual(article.count("至少可以从三个层面去看"), 1)
        self.assertIn("换个角度看", article)
        self.assertIn("如果把它放进真实项目", article)


if __name__ == "__main__":
    unittest.main()
