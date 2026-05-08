from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skill_runtime.writing_core import critique_article, judge_article  # noqa: E402


class WritingCoreCritiqueTests(unittest.TestCase):
    def test_critique_article_penalizes_missing_story_and_resonance(self) -> None:
        article = (
            "# AI 内容系统为什么重要\n\n"
            "## 导语\n\n"
            "稳定内容产出靠系统，不靠灵感。\n\n"
            "## 问题提出\n\n"
            "内容生产需要选题、写作、审稿和发布形成闭环。\n\n"
            "## 核心判断\n\n"
            "真正决定结果的是流程稳定性。\n\n"
            "## 论证一\n\n"
            "流程可以降低随机性。流程可以提升复用性。流程可以减少临时决策。\n\n"
            "## 论证二\n\n"
            "结构可以帮助作者沉淀经验。结构可以减少重复劳动。结构可以提升发布效率。\n\n"
            "## 结论\n\n"
            "所以，内容系统是增长基础设施。\n"
        )

        critique = critique_article(article, chosen_structure="progressive")

        self.assertIn("story_resonance", critique["scores"])
        self.assertLess(critique["scores"]["story_resonance"], 7.0)
        self.assertTrue(critique["issues"]["story_resonance"])

    def test_critique_article_rewards_story_and_resonance_anchors(self) -> None:
        flat_article = (
            "# AI 内容系统为什么重要\n\n"
            "## 导语\n\n"
            "稳定内容产出靠系统，不靠灵感。\n\n"
            "## 问题提出\n\n"
            "内容生产需要选题、写作、审稿和发布形成闭环。\n\n"
            "## 核心判断\n\n"
            "真正决定结果的是流程稳定性。\n\n"
            "## 论证一\n\n"
            "流程可以降低随机性。流程可以提升复用性。流程可以减少临时决策。\n\n"
            "## 结论\n\n"
            "所以，内容系统是增长基础设施。\n"
        )
        resonant_article = (
            "# AI 内容系统为什么重要\n\n"
            "## 导语\n\n"
            "你有没有这种感觉：每天都在换 prompt，但文章还是忽好忽坏？\n\n"
            "## 问题提出\n\n"
            "有个创作者连续写废了 3 篇稿子。后来他没有继续换工具，而是先把 brief、审稿和发布节奏固定下来。\n\n"
            "## 核心判断\n\n"
            "说白了，真正决定结果的是流程稳定性。\n\n"
            "## 论证一\n\n"
            "这个故事的转折点不是工具变强了，而是每一篇稿子都有了同一套检查顺序。\n\n"
            "## 结论\n\n"
            "如果你也遇到过这个情况，先别急着换模型，先把流程搭起来。\n"
        )

        flat = critique_article(flat_article, chosen_structure="progressive")
        resonant = critique_article(resonant_article, chosen_structure="progressive")

        self.assertGreater(resonant["scores"]["story_resonance"], flat["scores"]["story_resonance"])
        self.assertFalse(resonant["issues"]["story_resonance"])

    def test_judge_article_can_focus_story_resonance(self) -> None:
        article = (
            "# AI 内容系统为什么重要\n\n"
            "## 导语\n\n"
            "稳定内容产出靠系统，不靠灵感。\n\n"
            "## 问题提出\n\n"
            "内容生产需要选题、写作、审稿和发布形成闭环。\n\n"
            "## 核心判断\n\n"
            "真正决定结果的是流程稳定性。\n\n"
            "## 论证一\n\n"
            "流程可以降低随机性。流程可以提升复用性。流程可以减少临时决策。\n\n"
            "## 结论\n\n"
            "所以，内容系统是增长基础设施。\n"
        )

        critique = critique_article(article, chosen_structure="progressive")
        judge = judge_article(article, critique=critique, humanizer_report={"ai_trace_risk": "low"})

        self.assertIn("story_resonance", judge["low_dimensions"])
        self.assertIn("story_resonance", judge["focus_areas"])

    def test_critique_article_penalizes_template_repetition(self) -> None:
        article = (
            "# AI 内容系统为什么重要\n\n"
            "## 导语\n\n"
            "你有没有这种感觉：文章明明写了很多，却还是像流程说明？\n\n"
            "## 问题提出\n\n"
            "有个创作者连续写废了 3 篇稿子。后来他发现，不是模型不够强，而是流程没有固定。\n\n"
            "## 核心判断\n\n"
            "说白了，稳定内容产出靠系统，不靠灵感。\n\n"
            "## 论证一\n\n"
            "这不是抽象判断。至少可以从三个层面去看：一是案例有没有重复出现，二是事实能不能验证，三是结论能不能支撑。\n\n"
            "## 论证二\n\n"
            "这不是抽象判断。至少可以从三个层面去看：一是案例有没有重复出现，二是事实能不能验证，三是结论能不能支撑。\n\n"
            "## 论证三\n\n"
            "这不是抽象判断。至少可以从三个层面去看：一是案例有没有重复出现，二是事实能不能验证，三是结论能不能支撑。\n\n"
            "## 结论\n\n"
            "如果你也遇到过这个情况，先把流程搭起来。\n"
        )

        critique = critique_article(article, chosen_structure="progressive")
        judge = judge_article(article, critique=critique, humanizer_report={"ai_trace_risk": "low"})

        self.assertIn("template_repetition", critique["scores"])
        self.assertLess(critique["scores"]["template_repetition"], 7.0)
        self.assertTrue(critique["issues"]["template_repetition"])
        self.assertIn("template_repetition", judge["low_dimensions"])


if __name__ == "__main__":
    unittest.main()
