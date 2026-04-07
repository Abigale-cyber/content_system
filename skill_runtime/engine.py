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

from skill_runtime.writing_core import augment_markdown_with_writing_pack, load_writing_pack_json


ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
WORKFLOWS_DIR = ROOT / "workflows"
_CASE_WRITER_RUNTIME: Any | None = None
_GENERATE_IMAGE_RUNTIME: Any | None = None
_WECHAT_FORMATTER_RUNTIME: Any | None = None
_WECHAT_COLLECT_RUNTIME: Any | None = None
_NEWS_COLLECT_RUNTIME: Any | None = None
_TOPIC_RESEARCH_RUNTIME: Any | None = None
_WECHAT_REPORT_RUNTIME: Any | None = None
_FEISHU_BITABLE_SYNC_RUNTIME: Any | None = None
_FEISHU_USER_AUTH_RUNTIME: Any | None = None
_HUMANIZER_ZH_RUNTIME: Any | None = None


@dataclass
class RunResult:
    skill_id: str
    output_path: str
    metadata: dict[str, Any]
    run_status: str = "completed"
    blocking: bool = False
    message: str = ""
    next_action: str = ""


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


def load_pillow() -> tuple[Any, Any, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ModuleNotFoundError as error:  # pragma: no cover - import path depends on runtime env
        raise RuntimeError(
            "Pillow is required for the local generate-image fallback. Install it in the active Python environment."
        ) from error
    return Image, ImageDraw, ImageFont


def load_runtime_module(module_name: str, runtime_path: Path) -> Any:
    if not runtime_path.exists():
        raise FileNotFoundError(f"runtime not found: {runtime_path}")

    spec = importlib.util.spec_from_file_location(module_name, runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load runtime module: {module_name}")

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(module_name, module)
    spec.loader.exec_module(module)
    return module


def load_generate_image_runtime() -> Any:
    global _GENERATE_IMAGE_RUNTIME
    if _GENERATE_IMAGE_RUNTIME is not None:
        return _GENERATE_IMAGE_RUNTIME

    runtime_path = SKILLS_DIR / "generate-image" / "runtime.py"
    _GENERATE_IMAGE_RUNTIME = load_runtime_module("generate_image_runtime", runtime_path)
    return _GENERATE_IMAGE_RUNTIME


def load_case_writer_runtime() -> Any:
    global _CASE_WRITER_RUNTIME
    if _CASE_WRITER_RUNTIME is not None:
        return _CASE_WRITER_RUNTIME

    runtime_path = SKILLS_DIR / "case-writer-hybrid" / "runtime.py"
    _CASE_WRITER_RUNTIME = load_runtime_module("case_writer_hybrid_runtime", runtime_path)
    return _CASE_WRITER_RUNTIME


def load_wechat_formatter_runtime() -> Any:
    global _WECHAT_FORMATTER_RUNTIME
    if _WECHAT_FORMATTER_RUNTIME is not None:
        return _WECHAT_FORMATTER_RUNTIME

    runtime_path = SKILLS_DIR / "wechat-formatter" / "runtime.py"
    _WECHAT_FORMATTER_RUNTIME = load_runtime_module("wechat_formatter_runtime", runtime_path)
    return _WECHAT_FORMATTER_RUNTIME


def load_wechat_collect_runtime() -> Any:
    global _WECHAT_COLLECT_RUNTIME
    if _WECHAT_COLLECT_RUNTIME is not None:
        return _WECHAT_COLLECT_RUNTIME

    runtime_path = SKILLS_DIR / "wechat-collect" / "runtime.py"
    _WECHAT_COLLECT_RUNTIME = load_runtime_module("wechat_collect_runtime", runtime_path)
    return _WECHAT_COLLECT_RUNTIME


def load_news_collect_runtime() -> Any:
    global _NEWS_COLLECT_RUNTIME
    if _NEWS_COLLECT_RUNTIME is not None:
        return _NEWS_COLLECT_RUNTIME

    runtime_path = SKILLS_DIR / "news-collect" / "runtime.py"
    _NEWS_COLLECT_RUNTIME = load_runtime_module("news_collect_runtime", runtime_path)
    return _NEWS_COLLECT_RUNTIME


def load_topic_research_runtime() -> Any:
    global _TOPIC_RESEARCH_RUNTIME
    if _TOPIC_RESEARCH_RUNTIME is not None:
        return _TOPIC_RESEARCH_RUNTIME

    runtime_path = SKILLS_DIR / "topic-research" / "runtime.py"
    _TOPIC_RESEARCH_RUNTIME = load_runtime_module("topic_research_runtime", runtime_path)
    return _TOPIC_RESEARCH_RUNTIME


def load_wechat_report_runtime() -> Any:
    global _WECHAT_REPORT_RUNTIME
    if _WECHAT_REPORT_RUNTIME is not None:
        return _WECHAT_REPORT_RUNTIME

    runtime_path = SKILLS_DIR / "wechat-report" / "runtime.py"
    _WECHAT_REPORT_RUNTIME = load_runtime_module("wechat_report_runtime", runtime_path)
    return _WECHAT_REPORT_RUNTIME


def load_feishu_bitable_sync_runtime() -> Any:
    global _FEISHU_BITABLE_SYNC_RUNTIME
    if _FEISHU_BITABLE_SYNC_RUNTIME is not None:
        return _FEISHU_BITABLE_SYNC_RUNTIME

    runtime_path = SKILLS_DIR / "feishu-bitable-sync" / "runtime.py"
    _FEISHU_BITABLE_SYNC_RUNTIME = load_runtime_module("feishu_bitable_sync_runtime", runtime_path)
    return _FEISHU_BITABLE_SYNC_RUNTIME


def load_feishu_user_auth_runtime() -> Any:
    global _FEISHU_USER_AUTH_RUNTIME
    if _FEISHU_USER_AUTH_RUNTIME is not None:
        return _FEISHU_USER_AUTH_RUNTIME

    runtime_path = SKILLS_DIR / "feishu-user-auth" / "runtime.py"
    _FEISHU_USER_AUTH_RUNTIME = load_runtime_module("feishu_user_auth_runtime", runtime_path)
    return _FEISHU_USER_AUTH_RUNTIME


def load_humanizer_zh_runtime() -> Any:
    global _HUMANIZER_ZH_RUNTIME
    if _HUMANIZER_ZH_RUNTIME is not None:
        return _HUMANIZER_ZH_RUNTIME

    runtime_path = SKILLS_DIR / "humanizer-zh" / "runtime.py"
    _HUMANIZER_ZH_RUNTIME = load_runtime_module("humanizer_zh_runtime", runtime_path)
    return _HUMANIZER_ZH_RUNTIME


def resolve_repo_skill_dependency(skill_name: str) -> Path:
    allowed = {
        "news-aggregator-skill": SKILLS_DIR / "news-aggregator-skill",
        "tavily-research": SKILLS_DIR / "tavily-research",
        "wechat-article-extractor-skill": SKILLS_DIR / "wechat-article-extractor-skill",
    }
    if skill_name not in allowed:
        raise ValueError(f"Unsupported repo-local skill dependency: {skill_name}")

    path = allowed[skill_name]
    if not path.exists():
        raise FileNotFoundError(f"Repo-local skill dependency not found: {path}")
    return path


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


def load_font(size: int, bold: bool = False, *, image_font_module: Any | None = None) -> Any:
    if image_font_module is None:
        _, _, image_font_module = load_pillow()
    candidates = [
        ("/System/Library/Fonts/PingFang.ttc", 0 if not bold else 5),
        ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
        ("/System/Library/Fonts/STHeiti Light.ttc", 0),
    ]
    for path, index in candidates:
        try:
            return image_font_module.truetype(path, size=size, index=index)
        except OSError:
            continue
    return image_font_module.load_default()


def wrap_text(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
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
    case_runtime = load_case_writer_runtime()
    drafted = case_runtime.run_case_writer_hybrid(input_path, workspace_root=ROOT)
    return RunResult(
        "case-writer-hybrid",
        str(drafted["article_path"]),
        {
            "slug": drafted["slug"],
            "topic": drafted["topic"],
            "writing_pack_md_path": str(drafted["writing_pack_md_path"]),
            "writing_pack_json_path": str(drafted["writing_pack_json_path"]),
            "review_trace_path": str(drafted["review_trace_path"]),
            "quality_gate_notice_path": str(drafted["quality_gate_notice_path"]) if drafted["quality_gate_notice_path"] else "",
            "publish_ready": drafted["publish_ready"],
            "score": drafted["score"],
            "scores": drafted["scores"],
            "ai_trace_risk": drafted["ai_trace_risk"],
        },
        run_status=drafted["run_status"],
        blocking=bool(drafted["blocking"]),
        message=str(drafted["message"]),
        next_action=str(drafted["next_action"]),
    )


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


def render_news_collect(input_path: Path) -> RunResult:
    collect_runtime = load_news_collect_runtime()
    dependency_path = resolve_repo_skill_dependency("news-aggregator-skill")
    collected = collect_runtime.run_news_collect(
        input_path,
        workspace_root=ROOT,
        vendor_root=dependency_path,
    )
    return RunResult(
        "news-collect",
        str(collected["report_path"]),
        {
            "slug": collected["slug"],
            "title": collected["title"],
            "profile": collected["profile"],
            "sources": collected["sources"],
            "item_count": collected["item_count"],
            "recommended_count": collected.get("recommended_count", 0),
            "raw_path": str(collected["raw_path"]),
        },
    )


def render_topic_research(input_path: Path) -> RunResult:
    research_runtime = load_topic_research_runtime()
    dependency_path = resolve_repo_skill_dependency("tavily-research")
    researched = research_runtime.run_topic_research(
        input_path,
        workspace_root=ROOT,
        vendor_root=dependency_path,
    )
    return RunResult(
        "topic-research",
        str(researched["report_path"]),
        {
            "slug": researched["slug"],
            "topic": researched["topic"],
            "model": researched["model"],
            "writeworthiness_score": researched.get("writeworthiness_score", 0),
            "raw_path": str(researched["raw_path"]),
            "source_count": researched["source_count"],
        },
    )


def render_wechat_report(input_path: Path) -> RunResult:
    report_runtime = load_wechat_report_runtime()
    dependency_path = resolve_repo_skill_dependency("wechat-article-extractor-skill")
    reported = report_runtime.run_wechat_report(
        input_path,
        workspace_root=ROOT,
        vendor_root=dependency_path,
    )
    return RunResult(
        "wechat-report",
        str(reported["report_path"]),
        {
            "slug": reported["slug"],
            "topic": reported["topic"],
            "article_count": reported["article_count"],
            "candidate_count": reported["candidate_count"],
            "raw_path": str(reported["raw_path"]),
        },
    )


def render_feishu_bitable_sync(input_path: Path) -> RunResult:
    sync_runtime = load_feishu_bitable_sync_runtime()
    synced = sync_runtime.run_feishu_bitable_sync(input_path, workspace_root=ROOT)
    return RunResult(
        "feishu-bitable-sync",
        str(synced["manifest_path"]),
        {
            "slug": synced["slug"],
            "topic": synced["topic"],
            "status": synced.get("status", "synced"),
            "created_count": synced["created_count"],
            "updated_count": synced["updated_count"],
            "raw_path": str(synced["raw_path"]),
        },
    )


def render_feishu_user_auth(input_path: Path) -> RunResult:
    auth_runtime = load_feishu_user_auth_runtime()
    authorized = auth_runtime.run_feishu_user_auth(input_path, workspace_root=ROOT)
    return RunResult(
        "feishu-user-auth",
        str(authorized["manifest_path"]),
        {
            "status": authorized["status"],
            "cache_path": authorized["cache_path"],
            "redirect_uri": authorized["redirect_uri"],
            "expires_at": authorized["expires_at"],
            "open_id": authorized["open_id"],
        },
    )


def render_humanizer_zh(input_path: Path) -> RunResult:
    humanizer_runtime = load_humanizer_zh_runtime()
    humanized = humanizer_runtime.run_humanizer_zh(input_path, workspace_root=ROOT)
    return RunResult(
        "humanizer-zh",
        str(humanized["output_path"]),
        {
            "slug": humanized["slug"],
            "report_path": str(humanized["report_path"]),
            "ai_trace_risk": humanized["ai_trace_risk"],
            "changed_line_count": humanized["changed_line_count"],
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
    Image, ImageDraw, ImageFont = load_pillow()
    summary = extract_article_summary(input_path)
    slug = re.sub(r"-article$", "", input_path.stem)
    output = image_output_path(slug)
    ensure_parent(output)

    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#f7f8fc")
    draw = ImageDraw.Draw(image)

    title_font = load_font(64, bold=True, image_font_module=ImageFont)
    subtitle_font = load_font(30, image_font_module=ImageFont)
    card_title_font = load_font(28, bold=True, image_font_module=ImageFont)
    card_body_font = load_font(22, image_font_module=ImageFont)
    footer_font = load_font(20, image_font_module=ImageFont)

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
    writing_pack = load_writing_pack_json(input_path)
    if writing_pack:
        text = augment_markdown_with_writing_pack(text, writing_pack)
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else input_path.stem
    slug = re.sub(r"-article$", "", input_path.stem)
    output = html_output_path(slug)
    write_text(output, markdown_to_html(text, title))
    return RunResult(
        "wechat-formatter",
        str(output),
        {
            "slug": slug,
            "source_markdown": str(input_path),
            "provider": "local",
            "writing_pack_used": bool(writing_pack),
        },
    )


def render_wechat_formatter(input_path: Path) -> RunResult:
    try:
        formatter_runtime = load_wechat_formatter_runtime()
        markdown = read_text(input_path)
        writing_pack = load_writing_pack_json(input_path)
        if writing_pack:
            markdown = augment_markdown_with_writing_pack(markdown, writing_pack)
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
                "writing_pack_used": bool(writing_pack),
            },
        )
    except Exception as error:  # noqa: BLE001
        fallback = render_wechat_formatter_local(input_path)
        fallback.metadata["fallback_reason"] = str(error)
        return fallback


EXECUTORS = {
    "wechat_collect_v1": render_wechat_collect,
    "news_collect_v1": render_news_collect,
    "topic_research_v1": render_topic_research,
    "wechat_report_v1": render_wechat_report,
    "feishu_user_auth_v1": render_feishu_user_auth,
    "feishu_bitable_sync_v1": render_feishu_bitable_sync,
    "case_writer_hybrid_v1": render_case_writer_hybrid,
    "humanizer_zh_v1": render_humanizer_zh,
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
    workflow_status = "completed"
    interrupted_by = ""

    for step in workflow["steps"]:
        skill_id = step["skill"]
        source = step["input"]
        resolved_input = resolve_input(source, workflow_input, results, previous)
        result = run_skill(skill_id, resolved_input)
        results[skill_id] = result
        previous = result
        if result.blocking or result.run_status in {"quality_gate_failed", "awaiting_user_review"}:
            workflow_status = "interrupted_for_review"
            interrupted_by = skill_id
            break

    manifest = {
        "workflow_id": workflow_id,
        "workflow_input": workflow_input,
        "ran_at": datetime.now().isoformat(timespec="seconds"),
        "workflow_status": workflow_status,
        "interrupted_by": interrupted_by,
        "results": {
            skill_id: {
                "output_path": result.output_path,
                "metadata": result.metadata,
                "run_status": result.run_status,
                "blocking": result.blocking,
                "message": result.message,
                "next_action": result.next_action,
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
