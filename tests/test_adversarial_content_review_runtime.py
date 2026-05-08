from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skill_runtime.engine import list_skills, run_skill  # noqa: E402


class AdversarialContentReviewRuntimeTests(unittest.TestCase):
    def test_skill_is_registered(self) -> None:
        skill_ids = {item["id"] for item in list_skills()}

        self.assertIn("adversarial-content-review", skill_ids)

    def test_run_skill_writes_structured_review_report_and_json_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "weak-article.md"
            input_path.write_text(
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
                "所以，内容系统是增长基础设施。\n",
                encoding="utf-8",
            )

            result = run_skill("adversarial-content-review", str(input_path))
            report_path = Path(result.output_path)
            json_path = Path(result.metadata["review_json_path"])
            self.addCleanup(lambda: report_path.exists() and report_path.unlink())
            self.addCleanup(lambda: json_path.exists() and json_path.unlink())

            report = report_path.read_text(encoding="utf-8")
            sidecar = json.loads(json_path.read_text(encoding="utf-8"))

            self.assertEqual(result.skill_id, "adversarial-content-review")
            self.assertIn("# 对抗式审稿报告", report)
            self.assertIn("## 第 1 轮：笔杆子审", report)
            self.assertIn("## 第 2 轮：参谋审", report)
            self.assertIn("## 第 3 轮：裁判裁定", report)
            self.assertIn("## 五维度评分", report)
            self.assertIn("## 具体修改建议", report)
            self.assertIn(sidecar["verdict"], {"需修改", "需重写"})
            self.assertTrue(result.blocking)
            self.assertEqual(result.run_status, "awaiting_revision")
            self.assertLess(sidecar["total_score"], 8)
            self.assertIn("dimension_scores", sidecar)
            self.assertIn("story_resonance", sidecar["dimension_scores"])


if __name__ == "__main__":
    unittest.main()
