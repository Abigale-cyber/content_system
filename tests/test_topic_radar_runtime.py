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


class TopicRadarRuntimeTests(unittest.TestCase):
    def test_skill_is_registered(self) -> None:
        skill_ids = {item["id"] for item in list_skills()}

        self.assertIn("topic-radar", skill_ids)

    def test_run_skill_generates_angles_with_four_dimension_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "hot-topic.md"
            input_path.write_text(
                "# AI Agent 进入企业协作工具\n\n"
                "飞书、Notion、Asana 都在把 AI Agent 接进团队协作。很多内容创作者只会复述发布信息，"
                "但读者真正关心的是：普通团队怎么判断这是不是又一个效率噱头。\n\n"
                "可用素材：Notion Custom Agents、Asana AI Teammates、Rakuten 企业 Agent 案例。\n",
                encoding="utf-8",
            )

            result = run_skill("topic-radar", str(input_path))
            report_path = Path(result.output_path)
            json_path = Path(result.metadata["radar_json_path"])
            self.addCleanup(lambda: report_path.exists() and report_path.unlink())
            self.addCleanup(lambda: json_path.exists() and json_path.unlink())

            report = report_path.read_text(encoding="utf-8")
            payload = json.loads(json_path.read_text(encoding="utf-8"))

            self.assertEqual(result.skill_id, "topic-radar")
            self.assertEqual(result.run_status, "completed")
            self.assertIn("# 选题雷达", report)
            self.assertIn("## 候选切口", report)
            self.assertGreaterEqual(len(payload["angles"]), 3)
            first = payload["angles"][0]
            self.assertIn(first["formula"], {"痛点 + 工具 + 具体结果", "误解 + 反转 + 证明", "低效动作 + AI 替代 + 效果对比"})
            self.assertIn("recommended_structure", first)
            self.assertIn("title_directions", first)
            self.assertEqual(set(first["fit_scores"]), {"热爱程度", "专业能力", "市场需求", "资源积累"})
            self.assertTrue(all(1 <= score <= 5 for score in first["fit_scores"].values()))
            self.assertIn(payload["recommended_angle"]["angle"], [item["angle"] for item in payload["angles"]])


if __name__ == "__main__":
    unittest.main()
