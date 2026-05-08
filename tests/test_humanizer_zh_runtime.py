from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skill_runtime.engine import run_skill  # noqa: E402
from skill_runtime.writing_core import humanize_markdown  # noqa: E402


class HumanizerZhRuntimeTests(unittest.TestCase):
    def test_humanize_markdown_reports_sentence_metrics_and_reduces_ai_phrases(self) -> None:
        text = (
            "# 测试文章\n\n"
            "在当今数字化时代，很多创作者不仅需要持续输出内容而且需要不断优化流程更需要建立完整系统，"
            "否则他们会陷入每天换工具换模型换提示词但依然没有稳定结果的困境。\n\n"
            "首先，我们要看到问题不只是效率。其次，我们要看到流程缺失。最后，我们要回到内容系统。\n"
        )

        result = humanize_markdown(text, mode="surgical")

        self.assertIn("sentence_metrics", result)
        self.assertGreaterEqual(result["sentence_metrics"]["long_sentence_count"], 1)
        self.assertGreaterEqual(result["sentence_metrics"]["mechanical_connector_count"], 3)
        self.assertNotIn("在当今数字化时代", result["text"])
        self.assertNotIn("首先，", result["text"])
        self.assertNotIn("其次，", result["text"])
        self.assertNotIn("最后，", result["text"])
        self.assertTrue(
            any(item["key"] == "long_sentence" for item in result["pattern_hits"]),
            result["pattern_hits"],
        )
        self.assertTrue(
            any(item["key"] == "mechanical_connectors" for item in result["pattern_hits"]),
            result["pattern_hits"],
        )

    def test_run_skill_writes_sentence_metrics_to_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "sample-article.md"
            input_path.write_text(
                "# 测试文章\n\n"
                "在当今数字化时代，很多创作者不仅需要持续输出内容而且需要不断优化流程更需要建立完整系统，"
                "否则他们会陷入每天换工具换模型换提示词但依然没有稳定结果的困境。\n\n"
                "首先，我们要看到问题不只是效率。其次，我们要看到流程缺失。最后，我们要回到内容系统。\n",
                encoding="utf-8",
            )

            result = run_skill("humanizer-zh", str(input_path))
            output_path = Path(result.output_path)
            report_path = Path(result.metadata["report_path"])
            self.addCleanup(lambda: output_path.exists() and output_path.unlink())
            self.addCleanup(lambda: report_path.exists() and report_path.unlink())

            report = json.loads(report_path.read_text(encoding="utf-8"))

            self.assertIn("sentence_metrics", report)
            self.assertGreaterEqual(report["sentence_metrics"]["long_sentence_count"], 1)
            self.assertGreaterEqual(report["sentence_metrics"]["mechanical_connector_count"], 3)
            self.assertIn("sentence_metrics", result.metadata)

    def test_humanize_markdown_only_replaces_mechanical_final_connector(self) -> None:
        text = "这不是抽象判断。关键是这些事实能不能支撑你最后那个结论。\n\n最后，我们再回到行动。\n"

        result = humanize_markdown(text, mode="surgical")

        self.assertIn("最后那个结论", result["text"])
        self.assertNotIn("收尾时，那个结论", result["text"])
        self.assertIn("收尾时，我们再回到行动", result["text"])


if __name__ == "__main__":
    unittest.main()
