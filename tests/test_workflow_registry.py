from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skill_runtime.engine import list_workflows  # noqa: E402


class WorkflowRegistryTests(unittest.TestCase):
    def test_topic_to_wechat_workflow_is_registered(self) -> None:
        workflows = list_workflows()
        workflow = next((item for item in workflows if item["id"] == "topic-to-wechat-pipeline"), None)

        self.assertIsNotNone(workflow)
        self.assertEqual(workflow["steps"][0]["skill"], "content-brief-builder")
        self.assertEqual(workflow["steps"][1]["skill"], "case-writer-hybrid")
        self.assertEqual(workflow["steps"][2]["skill"], "adversarial-content-review")
        self.assertEqual(workflow["steps"][3]["skill"], "generate-image")
        self.assertEqual(workflow["steps"][4]["skill"], "wechat-formatter")

    def test_topic_radar_to_brief_workflow_is_registered(self) -> None:
        workflows = list_workflows()
        workflow = next((item for item in workflows if item["id"] == "topic-radar-to-brief-pipeline"), None)

        self.assertIsNotNone(workflow)
        self.assertEqual(workflow["steps"][0]["skill"], "topic-radar")
        self.assertEqual(workflow["steps"][1]["skill"], "content-brief-builder")

    def test_article_to_short_script_workflow_is_registered(self) -> None:
        workflows = list_workflows()
        workflow = next((item for item in workflows if item["id"] == "article-to-short-script-pipeline"), None)

        self.assertIsNotNone(workflow)
        self.assertEqual(workflow["steps"][0]["skill"], "script-writer-short")


if __name__ == "__main__":
    unittest.main()
