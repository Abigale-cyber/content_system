from __future__ import annotations

import html
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
WORKFLOWS_DIR = ROOT / "workflows"
_GENERATE_IMAGE_RUNTIME: Any | None = None
_WECHAT_FORMATTER_RUNTIME: Any | None = None
_WECHAT_COLLECT_RUNTIME: Any | None = None


@dataclass
class RunResult:
    skill_id: str
    output_path: str
    metadata: dict[str, Any]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def slug_from_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or datetime.now().strftime("%Y%m%d-%H%M%S")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def parse_markdown_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = "root"
    sections[current] = []
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            continue
        sections.setdefault(current, []).append(line)
    return sections


def parse_brief(path: Path) -> dict[str, Any]:
    text = read_text(path)
    sections = parse_markdown_sections(text)
    base = "\n".join(sections.get("基础信息", []))

    def field(name: str) -> str:
        match = re.search(rf"`?{re.escape(name)}`?\s*[：:]\s*(.+)", base)
        return match.group(1).strip() if match else ""

    def bullet_values(section_name: str) -> list[str]:
        values = []
        for line in sections.get(section_name, []):
            stripped = line.strip()
            match = re.match(r"^[-*]\s*(.+)$", stripped)
            if match and match.group(1).strip():
                values.append(match.group(1).strip())
            num_match = re.match(r"^\d+\.\s*(.+)$", stripped)
            if num_match and num_match.group(1).strip():
                values.append(num_match.group(1).strip())
        return values

    core_view = "\n".join(
        line.strip()
        for line in sections.get("核心观点", [])
        if line.strip() and not line.strip().startswith(">")
    ).strip()

    if not core_view:
        quoted = [
            line.strip("> ").strip()
            for line in sections.get("核心观点", [])
            if line.strip().startswith(">")
        ]
        core_view = "\n".join(quoted).strip()

    topic = field("topic") or path.stem
    slug = field("slug") or slug_from_text(topic)

    return {
        "topic": topic,
        "slug": slug,
        "date": field("date") or datetime.now().strftime("%Y%m%d"),
        "target_reader": field("target_reader"),
        "publish_goal": field("publish_goal"),
        "core_view": core_view,
        "background": bullet_values("背景与语境"),
        "arguments": bullet_values("论证方向"),
        "cases": bullet_values("可用案例 / 素材"),
        "avoid": bullet_values("明确不要写什么"),
        "style": bullet_values("风格要求"),
        "visual": bullet_values("配图方向"),
        "notes": bullet_values("备注"),
    }


def article_output_path(slug: str) -> Path:
    return ROOT / "content-production" / "drafts" / f"{slug}-article.md"


def image_output_path(slug: str) -> Path:
    return ROOT / "content-production" / "ready" / f"{slug}-img-1.png"


def html_output_path(slug: str) -> Path:
    return ROOT / "content-production" / "ready" / f"{slug}-wechat.html"


def markdown_title(path: Path) -> str:
    text = read_text(path)
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return title_match.group(1).strip() if title_match else path.stem


def load_generate_image_runtime() -> Any:
    global _GENERATE_IMAGE_RUNTIME
    if _GENERATE_IMAGE_RUNTIME is not None:
        return _GENERATE_IMAGE_RUNTIME

    runtime_path = SKILLS_DIR / "generate-image" / "runtime.py"
    if not runtime_path.exists():
        raise FileNotFoundError(f"generate-image runtime not found: {runtime_path}")

    spec = importlib.util.spec_from_file_location("generate_image_runtime", runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load generate-image runtime module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("generate_image_runtime", module)
    spec.loader.exec_module(module)
    _GENERATE_IMAGE_RUNTIME = module
    return module


def load_wechat_formatter_runtime() -> Any:
    global _WECHAT_FORMATTER_RUNTIME
    if _WECHAT_FORMATTER_RUNTIME is not None:
        return _WECHAT_FORMATTER_RUNTIME

    runtime_path = SKILLS_DIR / "wechat-formatter" / "runtime.py"
    if not runtime_path.exists():
        raise FileNotFoundError(f"wechat-formatter runtime not found: {runtime_path}")

    spec = importlib.util.spec_from_file_location("wechat_formatter_runtime", runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load wechat-formatter runtime module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("wechat_formatter_runtime", module)
    spec.loader.exec_module(module)
    _WECHAT_FORMATTER_RUNTIME = module
    return module


def load_wechat_collect_runtime() -> Any:
    global _WECHAT_COLLECT_RUNTIME
    if _WECHAT_COLLECT_RUNTIME is not None:
        return _WECHAT_COLLECT_RUNTIME

    runtime_path = SKILLS_DIR / "wechat-collect" / "runtime.py"
    if not runtime_path.exists():
        raise FileNotFoundError(f"wechat-collect runtime not found: {runtime_path}")

    spec = importlib.util.spec_from_file_location("wechat_collect_runtime", runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load wechat-collect runtime module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("wechat_collect_runtime", module)
    spec.loader.exec_module(module)
    _WECHAT_COLLECT_RUNTIME = module
    return module


def first_url_from_input(path: Path) -> str:
    text = read_text(path)
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.search(r"https?://\S+", stripped)
        if match:
            return match.group(0).rstrip(").,]")
    raise ValueError(f"No URL found in input file: {path}")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        ("/System/Library/Fonts/PingFang.ttc", 0 if not bold else 5),
        ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
        ("/System/Library/Fonts/STHeiti Light.ttc", 0),
    ]
    for path, index in candidates:
        try:
            return ImageFont.truetype(path, size=size, index=index)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = list(text)
    lines: list[str] = []
    current = ""
    for ch in words:
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def truncate_text(text: str, limit: int) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(limit - 1, 0)].rstrip() + "…"


def render_case_writer_hybrid(input_path: Path) -> RunResult:
    brief = parse_brief(input_path)
    topic = brief["topic"]
    slug = brief["slug"]
    arguments = brief["arguments"][:3] or ["为什么这个问题值得现在讨论", "为什么这不是单点执行问题", "为什么系统化才是长期解法"]
    cases = brief["cases"][:3]

    argument_blocks = []
    for index, argument in enumerate(arguments, start=1):
        normalized_argument = argument.rstrip("。！？!?. ")
        case_line = cases[index - 1] if index - 1 < len(cases) else "可补充一个与你业务场景接近的真实案例。"
        argument_blocks.append(
            "\n".join(
                [
                    f"## 论证 {index}：{normalized_argument}",
                    "",
                    f"{normalized_argument}。如果只靠临时输出，你会发现内容难以积累，认知难以形成，外部很难持续理解你到底在做什么。",
                    "",
                    f"可结合案例：{case_line}",
                    "",
                    "这部分要回到主观点：真正决定长期结果的，不是偶尔发出一篇内容，而是有没有一条能反复执行的生产与分发系统。",
                ]
            )
        )

    article = "\n".join(
        [
            f"# {topic}",
            "",
            f"> 目标读者：{brief['target_reader'] or '关注 AI 创业、个人品牌、独立产品的人'}",
            f"> 发布目标：{brief['publish_goal'] or '形成一篇可发布的公众号长文'}",
            "",
            "## 导语",
            "",
            brief["core_view"] or "这是一篇从观点 brief 扩展出的阶段 1 主稿，用于验证内容链路是否能稳定跑通。",
            "",
            "## 问题提出",
            "",
            "很多内容看起来没有产出，不是因为作者不努力，而是因为没有一条稳定的内容生产链。没有链，所有动作都只能临时发生，无法积累，也无法复盘。",
            "",
            "## 核心判断",
            "",
            "对一人公司、独立开发者、AI 创业者来说，内容系统不是宣传动作，而是增长基础设施。它决定你是否能被持续看见、被持续理解、被持续信任。",
            "",
            *argument_blocks,
            "",
            "## 结论",
            "",
            "真正值得搭的，不只是某个爆款选题能力，而是一条可重复的内容流水线：输入清晰、输出固定、节点可复用、结果可分发。只有这样，内容才会从消耗动作，变成增长资产。",
            "",
            "## 可传播总结",
            "",
            "- 没有内容系统，再好的产品也很难持续被理解。",
            "- 内容不是附属品，而是 AI 一人公司的增长基础设施。",
        ]
    )

    output = article_output_path(slug)
    write_text(output, article + "\n")
    return RunResult("case-writer-hybrid", str(output), {"slug": slug, "topic": topic})


def render_wechat_collect(input_path: Path) -> RunResult:
    collect_runtime = load_wechat_collect_runtime()
    source_url = first_url_from_input(input_path)
    inbox_dir = ROOT / "content-production" / "inbox"
    archive_dir = inbox_dir / "raw" / "wechat"
    collected = collect_runtime.collect_article_to_brief(source_url, inbox_dir=inbox_dir, archive_dir=archive_dir)
    return RunResult(
        "wechat-collect",
        str(collected["brief_path"]),
        {
            "slug": collected["slug"],
            "title": collected["title"],
            "author": collected["author"],
            "source_url": collected["source_url"],
            "archive_path": str(collected["archive_path"]),
        },
    )


def extract_article_summary(path: Path) -> dict[str, Any]:
    text = read_text(path)
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem
    headings = re.findall(r"^##\s+(.+)$", text, flags=re.MULTILINE)
    preferred = [item for item in headings if item.startswith("论证 ")]
    filtered = [item for item in headings if item not in {"导语", "问题提出", "核心判断", "结论", "可传播总结"}]
    paragraphs = []
    for block in text.split("\n\n"):
        stripped = block.strip()
        if not stripped:
            continue
        if stripped.startswith(("#", ">", "- ", "* ")):
            continue
        paragraphs.append(stripped)
    summary_source = paragraphs[0] if paragraphs else "这张图作为公众号配图，用于把文章主张和三个关键论点可视化。"
    summary = truncate_text(summary_source, 72)
    chosen_headings = (preferred or filtered or headings)[:3]
    return {"title": title, "headings": chosen_headings, "summary": summary}


def generate_image_style(summary: dict[str, Any]) -> str:
    key_points = " | ".join(str(item).strip() for item in summary.get("headings", []) if str(item).strip())
    base_style = (
        "wechat article companion image, editorial infographic, structured information design, "
        "clean hierarchy, concise typography, soft neutral background, minimal decorative noise"
    )
    if key_points:
        return f"{base_style}; emphasize key points: {key_points}"
    return base_style


def render_generate_image_local(input_path: Path) -> RunResult:
    summary = extract_article_summary(input_path)
    slug = re.sub(r"-article$", "", input_path.stem)
    output = image_output_path(slug)
    ensure_parent(output)

    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#f7f8fc")
    draw = ImageDraw.Draw(image)

    title_font = load_font(64, bold=True)
    subtitle_font = load_font(30)
    card_title_font = load_font(28, bold=True)
    card_body_font = load_font(22)
    footer_font = load_font(20)

    draw.rounded_rectangle((70, 60, width - 70, height - 60), radius=40, fill="#ffffff", outline="#e2e8f0", width=2)
    draw.rounded_rectangle((110, 110, width - 110, 270), radius=28, fill="#eef4ff")
    draw.text((150, 140), "内容系统信息图", fill="#2563eb", font=subtitle_font)

    title_lines = wrap_text(draw, summary["title"], title_font, 1200)
    y = 182
    for line in title_lines[:2]:
        draw.text((150, y), line, fill="#0f172a", font=title_font)
        y += 76

    cards = summary["headings"] or ["为什么内容系统重要", "为什么临时写作不可持续", "为什么系统化是增长基础设施"]
    card_w = 400
    gap = 30
    start_x = 110
    top = 360
    for idx in range(3):
        x1 = start_x + idx * (card_w + gap)
        x2 = x1 + card_w
        draw.rounded_rectangle((x1, top, x2, 730), radius=26, fill="#f8fafc", outline="#dbeafe", width=2)
        draw.text((x1 + 26, top + 26), f"论点 {idx + 1}", fill="#2563eb", font=card_title_font)
        card_text = cards[idx] if idx < len(cards) else "围绕文章的关键判断补充一个核心论点。"
        wrapped = wrap_text(draw, card_text, card_body_font, card_w - 52)
        text_y = top + 86
        for line in wrapped[:5]:
            draw.text((x1 + 26, text_y), line, fill="#334155", font=card_body_font)
            text_y += 34

    draw.rounded_rectangle((110, 756, width - 110, 824), radius=18, fill="#f8fafc")
    summary_lines = wrap_text(draw, summary["summary"] or "这张图作为公众号配图，用于把文章主张和三个关键论点可视化。", footer_font, 1220)
    footer_y = 776
    visible_summary_lines = summary_lines[:2]
    if len(summary_lines) > 2:
        visible_summary_lines[-1] = truncate_text(visible_summary_lines[-1], max(len(visible_summary_lines[-1]) - 1, 1))
    for line in visible_summary_lines:
        draw.text((150, footer_y), line, fill="#475569", font=footer_font)
        footer_y += 26

    draw.text((150, 844), f"slug: {slug}", fill="#94a3b8", font=footer_font)
    image.save(output)
    return RunResult("generate-image", str(output), {"slug": slug, "source_article": str(input_path), "provider": "local"})


def render_generate_image(input_path: Path) -> RunResult:
    try:
        image_runtime = load_generate_image_runtime()
        summary = extract_article_summary(input_path)
        slug = re.sub(r"-article$", "", input_path.stem)
        output = image_output_path(slug)
        ensure_parent(output)
        generated = image_runtime.generate_image_asset(
            title=summary["title"],
            summary=summary["summary"] or "公众号文章配图",
            article_path=input_path,
            preset="infographic-bento",
            style=generate_image_style(summary),
            workspace_root=ROOT,
        )
        image_runtime.download_binary(generated["previewUrl"], output)
        return RunResult(
            "generate-image",
            str(output),
            {
                "slug": slug,
                "source_article": str(input_path),
                "provider": "generate-image-skill",
                "preset": "infographic-bento",
                "style": generate_image_style(summary),
                "prompt": generated["prompt"],
                "media_id": generated["mediaId"],
                "width": generated["width"],
                "height": generated["height"],
            },
        )
    except Exception as error:  # noqa: BLE001
        fallback = render_generate_image_local(input_path)
        fallback.metadata["fallback_reason"] = str(error)
        return fallback


def markdown_to_html(text: str, title: str) -> str:
    lines = text.splitlines()
    blocks: list[str] = []
    in_list = False
    paragraph_parts: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_parts
        if paragraph_parts:
            blocks.append(f"<p>{format_inline(' '.join(paragraph_parts))}</p>")
            paragraph_parts = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            blocks.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            close_list()
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            close_list()
            blocks.append(f"<h1>{format_inline(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            flush_paragraph()
            close_list()
            blocks.append(f"<h2>{format_inline(stripped[3:])}</h2>")
        elif stripped.startswith("> "):
            flush_paragraph()
            close_list()
            blocks.append(f"<blockquote>{format_inline(stripped[2:])}</blockquote>")
        elif re.match(r"^[-*]\s+.+", stripped):
            flush_paragraph()
            if not in_list:
                blocks.append("<ul>")
                in_list = True
            item_text = stripped[2:].strip()
            blocks.append(f"<li>{format_inline(item_text)}</li>")
        else:
            paragraph_parts.append(stripped)

    flush_paragraph()
    close_list()

    body = "\n".join(blocks)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)}</title>
</head>
<body style="margin:0;background:#f6f8fc;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;color:#0f172a;">
  <main style="max-width:760px;margin:0 auto;padding:40px 24px 72px;">
    <article style="background:#ffffff;border:1px solid #e2e8f0;border-radius:24px;padding:40px 32px;box-shadow:0 18px 48px rgba(15,23,42,.06);line-height:1.9;">
      {body}
    </article>
  </main>
</body>
</html>
"""


def format_inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    return escaped


def render_wechat_formatter_local(input_path: Path) -> RunResult:
    text = read_text(input_path)
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else input_path.stem
    slug = re.sub(r"-article$", "", input_path.stem)
    output = html_output_path(slug)
    write_text(output, markdown_to_html(text, title))
    return RunResult("wechat-formatter", str(output), {"slug": slug, "source_markdown": str(input_path), "provider": "local"})


def render_wechat_formatter(input_path: Path) -> RunResult:
    try:
        formatter_runtime = load_wechat_formatter_runtime()
        markdown = read_text(input_path)
        slug = re.sub(r"-article$", "", input_path.stem)
        title = markdown_title(input_path)
        preview = formatter_runtime.render_article_html(
            markdown,
            theme_name=formatter_runtime.DEFAULT_THEME_NAME,
            template_name=formatter_runtime.DEFAULT_TEMPLATE_NAME,
            typography={},
            metadata_overrides={"title": title},
            wechat_safe=True,
        )
        html_text = str(preview.get("wechatSafeSourceHtml") or preview.get("sourceHtml") or preview.get("standaloneHtml") or "").strip()
        if not html_text:
            raise RuntimeError("wechat-formatter executor returned empty HTML.")
        output = html_output_path(slug)
        write_text(output, html_text)
        return RunResult(
            "wechat-formatter",
            str(output),
            {
                "slug": slug,
                "source_markdown": str(input_path),
                "provider": "wechat-formatter-skill",
                "theme": str(preview.get("themeName") or formatter_runtime.DEFAULT_THEME_NAME),
                "template": str(preview.get("templateName") or formatter_runtime.DEFAULT_TEMPLATE_NAME),
                "title": title,
            },
        )
    except Exception as error:  # noqa: BLE001
        fallback = render_wechat_formatter_local(input_path)
        fallback.metadata["fallback_reason"] = str(error)
        return fallback


EXECUTORS = {
    "wechat_collect_v1": render_wechat_collect,
    "case_writer_hybrid_v1": render_case_writer_hybrid,
    "generate_image_card_v1": render_generate_image,
    "wechat_formatter_v1": render_wechat_formatter,
}


def load_skill(skill_id: str) -> dict[str, Any]:
    path = SKILLS_DIR / skill_id / "skill.json"
    if not path.exists():
        raise FileNotFoundError(f"Skill not found: {skill_id}")
    return load_json(path)


def run_skill(skill_id: str, input_path: str) -> RunResult:
    skill = load_skill(skill_id)
    executor_id = skill["executor"]
    if executor_id not in EXECUTORS:
        raise ValueError(f"Unknown executor: {executor_id}")
    return EXECUTORS[executor_id](ROOT / input_path if not Path(input_path).is_absolute() else Path(input_path))


def load_workflow(workflow_id: str) -> dict[str, Any]:
    path = WORKFLOWS_DIR / f"{workflow_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Workflow not found: {workflow_id}")
    return load_json(path)


def resolve_input(reference: str, workflow_input: str, results: dict[str, RunResult], previous: RunResult | None) -> str:
    if reference == "workflow_input":
        return workflow_input
    if reference == "previous_output":
        if previous is None:
            raise ValueError("previous_output referenced before any step ran")
        return previous.output_path
    if reference.startswith("step:"):
        step_id = reference.split(":", 1)[1]
        if step_id not in results:
            raise ValueError(f"Workflow step output not found: {step_id}")
        return results[step_id].output_path
    raise ValueError(f"Unknown input reference: {reference}")


def run_workflow(workflow_id: str, workflow_input: str) -> dict[str, Any]:
    workflow = load_workflow(workflow_id)
    results: dict[str, RunResult] = {}
    previous: RunResult | None = None

    for step in workflow["steps"]:
        skill_id = step["skill"]
        source = step["input"]
        resolved_input = resolve_input(source, workflow_input, results, previous)
        result = run_skill(skill_id, resolved_input)
        results[skill_id] = result
        previous = result

    manifest = {
        "workflow_id": workflow_id,
        "workflow_input": workflow_input,
        "ran_at": datetime.now().isoformat(timespec="seconds"),
        "results": {
            skill_id: {
                "output_path": result.output_path,
                "metadata": result.metadata,
            }
            for skill_id, result in results.items()
        },
    }
    manifest_path = ROOT / "content-production" / "published" / f"{workflow_id}-last-run.json"
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def list_skills() -> list[dict[str, Any]]:
    items = []
    for path in sorted(SKILLS_DIR.glob("*/skill.json")):
        items.append(load_json(path))
    return items


def list_workflows() -> list[dict[str, Any]]:
    return [load_json(path) for path in sorted(WORKFLOWS_DIR.glob("*.json"))]
