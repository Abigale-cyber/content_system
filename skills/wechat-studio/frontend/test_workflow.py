import importlib.util
import shutil
import unittest
from unittest import mock
from pathlib import Path
from tempfile import TemporaryDirectory


SERVER_PATH = Path(__file__).with_name("server.py")
SPEC = importlib.util.spec_from_file_location("wechat_studio_server", SERVER_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(SERVER)


class WorkflowSnapshotTests(unittest.TestCase):
    def test_defaults_to_draft_when_content_is_not_ready(self):
        workflow = SERVER.build_workflow_snapshot(
            article={"title": "示例文章", "summary": ""},
            preview={"ready": False},
            editor_blocks=[],
            inline_slots=[],
            cover_candidate_path="",
            draft={},
        )

        self.assertEqual(workflow["currentStage"], "draft")
        self.assertEqual(workflow["stages"]["draft"]["statusText"], "未开始")
        self.assertEqual(workflow["stages"]["assets"]["statusText"], "未完成")
        self.assertEqual(workflow["stages"]["publish"]["statusText"], "待确认")
        self.assertFalse(workflow["publishChecks"][2]["ok"])
        self.assertFalse(workflow["publishChecks"][3]["ok"])

    def test_advances_to_publish_when_preview_and_assets_are_ready(self):
        workflow = SERVER.build_workflow_snapshot(
            article={"title": "示例文章", "summary": "这是摘要"},
            preview={"ready": True},
            editor_blocks=[{"id": "block-1", "kind": "paragraph"}],
            inline_slots=[
                {
                    "slotId": "slot-1",
                    "currentItem": {"localPath": "skills/wechat-studio/content/articles/demo/studio-assets/inline-1.png"},
                }
            ],
            cover_candidate_path="skills/wechat-studio/content/articles/demo/studio-assets/cover-1.png",
            draft={},
        )

        self.assertEqual(workflow["currentStage"], "publish")
        self.assertEqual(workflow["stages"]["draft"]["statusText"], "已完成")
        self.assertEqual(workflow["stages"]["assets"]["statusText"], "已完成")
        self.assertEqual(workflow["stages"]["publish"]["statusText"], "待发布")
        self.assertEqual(workflow["progress"]["completed"], 2)

    def test_keeps_assets_active_when_inline_slots_are_missing(self):
        workflow = SERVER.build_workflow_snapshot(
            article={"title": "示例文章", "summary": "这是摘要"},
            preview={"ready": True},
            editor_blocks=[{"id": "block-1", "kind": "paragraph"}],
            inline_slots=[
                {"slotId": "slot-1", "currentItem": {"localPath": "cover.png"}},
                {"slotId": "slot-2", "currentItem": None},
            ],
            cover_candidate_path="skills/wechat-studio/content/articles/demo/studio-assets/cover-1.png",
            draft={},
        )

        self.assertEqual(workflow["currentStage"], "assets")
        self.assertEqual(workflow["stages"]["assets"]["statusText"], "进行中")
        self.assertIn("插图位", " ".join(workflow["stages"]["assets"]["missing"]))
        self.assertFalse(workflow["publishChecks"][4]["ok"])


class UploadedImageAssetTests(unittest.TestCase):
    def setUp(self):
        self.article_dir = SERVER.CONTENT_DIR / "unit-upload-article"
        if self.article_dir.exists():
            shutil.rmtree(self.article_dir)
        self.article_dir.mkdir(parents=True)
        (self.article_dir / "doocs.md").write_text("# 测试文章\n\n正文\n\n[[IMAGE_SLOT:slot-1]]\n", encoding="utf-8")

    def tearDown(self):
        if self.article_dir.exists():
            shutil.rmtree(self.article_dir)

    def test_uploaded_cover_becomes_current_candidate_and_history_item(self):
        state = SERVER.load_studio_state(self.article_dir)

        record = SERVER.save_uploaded_cover_asset(
            self.article_dir,
            state,
            filename="hero cover.PNG",
            file_bytes=b"fake png bytes",
        )

        saved_state = SERVER.load_studio_state(self.article_dir)
        self.assertEqual(saved_state["cover"]["candidatePath"], record["localPath"])
        self.assertEqual(saved_state["cover"]["generated"]["localPath"], record["localPath"])
        self.assertEqual(saved_state["cover"]["history"][0]["localPath"], record["localPath"])
        self.assertEqual(saved_state["cover"]["history"][0]["source"], "upload")
        self.assertTrue((SERVER.ROOT / record["localPath"]).exists())

    def test_uploaded_inline_image_becomes_slot_current_item(self):
        state = SERVER.load_studio_state(self.article_dir)
        markdown = (self.article_dir / "doocs.md").read_text(encoding="utf-8")
        SERVER.ensure_inline_slot_state(self.article_dir, markdown, state)

        record = SERVER.save_uploaded_inline_asset(
            self.article_dir,
            state,
            slot_id="slot-1",
            filename="inline photo.jpg",
            file_bytes=b"fake jpg bytes",
        )

        saved_state = SERVER.load_studio_state(self.article_dir)
        slot = saved_state["inlineImages"]["slots"][0]
        self.assertEqual(slot["slotId"], "slot-1")
        self.assertEqual(slot["currentItem"]["localPath"], record["localPath"])
        self.assertEqual(slot["selectedLocalPath"], record["localPath"])
        self.assertEqual(slot["history"][0]["source"], "upload")
        self.assertTrue((SERVER.ROOT / record["localPath"]).exists())


class DraftPushErrorTests(unittest.TestCase):
    def setUp(self):
        self.article_dir = SERVER.CONTENT_DIR / "unit-draft-error"
        if self.article_dir.exists():
            shutil.rmtree(self.article_dir)
        self.article_dir.mkdir(parents=True)
        (self.article_dir / "doocs.md").write_text("# 测试文章\n\n正文\n", encoding="utf-8")
        (self.article_dir / "publish-pack.json").write_text(
            '{"title":"测试文章","summary":"摘要","author":"tester"}\n',
            encoding="utf-8",
        )
        state = SERVER.load_studio_state(self.article_dir)
        SERVER.save_uploaded_cover_asset(
            self.article_dir,
            state,
            filename="cover.png",
            file_bytes=b"fake png bytes",
        )

    def tearDown(self):
        if self.article_dir.exists():
            shutil.rmtree(self.article_dir)

    def test_system_exit_from_wechat_api_is_saved_as_draft_error(self):
        with mock.patch.object(SERVER, "get_access_token", side_effect=SystemExit("WeChat API error 40164: invalid ip")):
            with self.assertRaises(RuntimeError) as error:
                SERVER.push_article_draft(self.article_dir.name, {})

        self.assertIn("WeChat API error 40164", str(error.exception))
        saved_state = SERVER.load_studio_state(self.article_dir)
        self.assertIn("WeChat API error 40164", saved_state["draft"]["lastError"])


class WeChatPayloadSanitizerTests(unittest.TestCase):
    def test_forbidden_template_words_are_removed_from_draft_payload(self):
        article = SERVER.build_wechat_article_payload(
            {"title": "秀米模板测试", "summary": "OPC专属排版 xiumi-winter-ins", "author": "tester"},
            "# 标题\n\n正文",
            "media-id",
            "<section>正文里不要出现秀米模板、OPC专属排版、xiumi-winter-ins，也不要出现风格。</section>",
        )

        combined = "\n".join([article["title"], article["digest"], article["content"]])
        self.assertNotIn("秀米", combined)
        self.assertNotIn("模板", combined)
        self.assertNotIn("OPC专属", combined)
        self.assertNotIn("排版", combined)
        self.assertNotIn("xiumi", combined)
        self.assertNotIn("风格", combined)

    def test_draft_payload_preserves_code_block_line_breaks(self):
        html = "<pre><code>安全要求：\n1. 不要删除文件；\n2. 不要清空目录；\n3. 不要泄露 token。</code></pre>"

        article = SERVER.build_wechat_article_payload(
            {"title": "测试", "summary": "摘要", "author": "tester"},
            "# 标题\n\n正文",
            "media-id",
            html,
        )

        self.assertIn("安全要求：\n1. 不要删除文件；\n2. 不要清空目录；", article["content"])


class RichEditorBlockTests(unittest.TestCase):
    def test_extracts_code_quote_and_list_as_editable_blocks(self):
        markdown = "# 标题\n\n> 引用第一行\n> 引用第二行\n\n```latex\n安全要求：\n1. 不要删除文件；\n```\n\n1. 第一条\n2. 第二条\n"

        blocks = SERVER.extract_editor_blocks(markdown)
        kinds = [block["kind"] for block in blocks]

        self.assertIn("quote", kinds)
        self.assertIn("code", kinds)
        self.assertIn("list", kinds)
        code = next(block for block in blocks if block["kind"] == "code")
        self.assertEqual(code["language"], "latex")
        self.assertIn("安全要求：\n1. 不要删除文件；", code["text"])

    def test_updates_code_block_without_losing_line_breaks(self):
        markdown = "# 标题\n\n```latex\n旧内容\n1. 旧条目\n```\n"
        code_id = next(block["id"] for block in SERVER.extract_editor_blocks(markdown) if block["kind"] == "code")

        updated = SERVER.update_markdown_text_block(markdown, code_id, "新内容\n1. 新条目\n2. 第二条")

        self.assertIn("```latex\n新内容\n1. 新条目\n2. 第二条\n```", updated)

    def test_extracts_and_deletes_markdown_image_blocks(self):
        markdown = "# 标题\n\n正文前\n\n![封面](/api/assets?path=content/articles/demo/studio-assets/cover.png)\n\n正文后\n"
        image = next(block for block in SERVER.extract_editor_blocks(markdown) if block["kind"] == "image")

        updated = SERVER.delete_markdown_image_block(markdown, image["id"])

        self.assertEqual(image["alt"], "封面")
        self.assertIn("/api/assets?path=content/articles/demo/studio-assets/cover.png", image["url"])
        self.assertNotIn("![封面]", updated)
        self.assertIn("正文前", updated)
        self.assertIn("正文后", updated)


class CoverModuleBakeTests(unittest.TestCase):
    def test_generate_cover_module_asset_bakes_accent_block_into_image(self):
        from PIL import Image

        with TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            source = tmp_dir / "source.png"
            output = tmp_dir / "output.png"
            Image.new("RGB", (320, 180), "#eeeeee").save(source)

            SERVER.generate_cover_module_asset(
                source_path=source,
                output_path=output,
                style_id="collage-editorial",
                accent_color="#7987cd",
            )

            baked = Image.open(output).convert("RGB")
            self.assertGreater(baked.width, 320)
            self.assertGreater(baked.height, 180)
            self.assertEqual(baked.getpixel((4, baked.height - 4)), (121, 135, 205))
            self.assertEqual(baked.getpixel((baked.width - 2, 2)), (32, 34, 36))
            self.assertEqual(baked.getpixel((baked.width - 2, baked.height // 2)), (32, 34, 36))


if __name__ == "__main__":
    unittest.main()
