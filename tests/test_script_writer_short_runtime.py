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


class ScriptWriterShortRuntimeTests(unittest.TestCase):
    def test_skill_is_registered(self) -> None:
        skill_ids = {item["id"] for item in list_skills()}

        self.assertIn("script-writer-short", skill_ids)

    def test_run_skill_generates_short_video_script_and_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "ai-content-system-article.md"
            input_path.write_text(
                "# AI 内容系统为什么总写不出稳定文章\n\n"
                "## 导语\n\n"
                "你有没有这种感觉：每天都在换 prompt，但文章还是忽好忽坏？\n\n"
                "## 核心判断\n\n"
                "稳定内容产出靠系统，不靠灵感。\n\n"
                "## 论证 1\n\n"
                "一个创作者连续换了 5 套 prompt，质量仍然不稳定。后来他把选题、brief、审稿和发布节奏固定下来，文章才开始稳定。\n\n"
                "## 论证 2\n\n"
                "真正有用的流程不是多加工具，而是让每篇文章都经过同一套判断顺序。\n\n"
                "## 结论\n\n"
                "如果你也遇到过这个情况，先别急着换模型，先把流程搭起来。\n",
                encoding="utf-8",
            )

            result = run_skill("script-writer-short", str(input_path))
            script_path = Path(result.output_path)
            json_path = Path(result.metadata["script_json_path"])
            self.addCleanup(lambda: script_path.exists() and script_path.unlink())
            self.addCleanup(lambda: json_path.exists() and json_path.unlink())

            script = script_path.read_text(encoding="utf-8")
            sidecar = json.loads(json_path.read_text(encoding="utf-8"))

            self.assertEqual(result.skill_id, "script-writer-short")
            self.assertEqual(result.run_status, "completed")
            self.assertIn("# 短视频口播脚本", script)
            self.assertIn("## Hook", script)
            self.assertIn("## Introduction", script)
            self.assertIn("## Body", script)
            self.assertIn("## Summary", script)
            self.assertIn("## 拍摄提示", script)
            self.assertIn("你有没有这种感觉", script)
            self.assertEqual(sidecar["duration_seconds"], 90)
            self.assertIn("hook", sidecar["script"])
            self.assertIn("body_points", sidecar["script"])
            self.assertGreaterEqual(len(sidecar["script"]["body_points"]), 2)
            self.assertLessEqual(sidecar["estimated_cn_chars"], 420)


if __name__ == "__main__":
    unittest.main()
