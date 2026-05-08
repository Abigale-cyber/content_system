from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from skill_runtime.writing_core import clean_text, markdown_h2_headings, markdown_title, slugify, truncate_text


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def script_md_path(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "content-production" / "drafts" / f"{slug}-script.md"


def script_json_path(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "content-production" / "drafts" / f"{slug}-script.json"


def body_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    for block in text.split("\n\n"):
        stripped = clean_text(block)
        if not stripped or stripped.startswith(("#", ">", "- ", "* ")):
            continue
        paragraphs.append(stripped)
    return paragraphs


def first_resonance_line(text: str, title: str) -> str:
    patterns = [
        r"(你有没有这种感觉[：:].*?[。！？!?])",
        r"(很多人.*?卡.*?[。！？!?])",
        r"(如果你也.*?[。！？!?])",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return truncate_text(clean_text(match.group(1)), 34)
    return truncate_text(f"你有没有这种感觉：{title}明明很重要，但总是做不稳？", 34)


def core_claim(text: str, title: str) -> str:
    claim_patterns = [
        r"(稳定.*?不靠.*?[。！？!?])",
        r"(真正.*?不是.*?而是.*?[。！？!?])",
        r"(说白了.*?[。！？!?])",
    ]
    for pattern in claim_patterns:
        match = re.search(pattern, text)
        if match:
            return truncate_text(clean_text(match.group(1)), 52)
    paragraphs = body_paragraphs(text)
    return truncate_text(paragraphs[0] if paragraphs else title, 52)


def extract_story(text: str) -> str:
    story_patterns = [
        r"((?:有个|一个|有位).{8,90}?(?:后来|结果|最后).{6,90}?[。！？!?])",
        r"((?:如果你也|你有没有).{8,90}?[。！？!?])",
    ]
    for pattern in story_patterns:
        match = re.search(pattern, text)
        if match:
            return truncate_text(clean_text(match.group(1)), 76)
    return ""


def point_from_heading(heading: str, fallback: str) -> str:
    cleaned = clean_text(heading)
    cleaned = re.sub(r"^(论证|清单)\s*\d*[：:]?\s*", "", cleaned)
    return truncate_text(cleaned or fallback, 46)


def build_body_points(text: str, headings: list[str], claim: str) -> list[str]:
    usable_headings = [
        item
        for item in headings
        if item not in {"导语", "问题提出", "核心判断", "结论", "可传播总结", "拍摄提示"}
    ]
    points = [point_from_heading(item, claim) for item in usable_headings[:3]]
    if not points:
        paragraphs = body_paragraphs(text)
        points = [truncate_text(item, 46) for item in paragraphs[:3]]
    while len(points) < 2:
        points.append("先把最容易失控的一步固定下来，再谈效率。")
    return points[:3]


def build_script_payload(text: str, title: str, *, duration_seconds: int = 90) -> dict[str, Any]:
    headings = markdown_h2_headings(text)
    hook = first_resonance_line(text, title)
    claim = core_claim(text, title)
    story = extract_story(text)
    body_points = build_body_points(text, headings, claim)
    intro = truncate_text(f"今天这条视频，想用一个很简单的判断讲清楚：{claim}", 66)
    body_lines: list[str] = []
    for index, point in enumerate(body_points, start=1):
        if index == 1 and story:
            body_lines.append(truncate_text(f"第一，{point}。{story}", 92))
        else:
            body_lines.append(truncate_text(f"第{index}，{point}。重点不是多加动作，而是让这一步可以重复。", 86))
    summary = truncate_text(f"所以，别急着换工具。先把流程跑稳，再谈技巧。你最卡的是哪一步？评论区告诉我。", 72)
    shooting_tips = [
        "镜头：半身口播，前 3 秒直接看镜头抛问题。",
        "字幕：Hook 用大字，Body 每点只保留一句关键词。",
        "节奏：每 12-15 秒换一次气口，结尾留互动问题。",
    ]
    script_text = "\n".join([hook, intro, *body_lines, summary])
    estimated_chars = len(re.sub(r"\s+", "", script_text))
    return {
        "duration_seconds": duration_seconds,
        "script": {
            "hook": hook,
            "introduction": intro,
            "body_points": body_lines,
            "summary": summary,
            "shooting_tips": shooting_tips,
        },
        "estimated_cn_chars": estimated_chars,
    }


def build_markdown(title: str, slug: str, source_path: Path, payload: dict[str, Any]) -> str:
    script = payload["script"]
    lines = [
        f"# 短视频口播脚本：{title}",
        "",
        f"- `slug`：{slug}",
        f"- `source`：{source_path}",
        f"- `duration_seconds`：{payload['duration_seconds']}",
        f"- `estimated_cn_chars`：{payload['estimated_cn_chars']}",
        "",
        "## Hook",
        "",
        script["hook"],
        "",
        "## Introduction",
        "",
        script["introduction"],
        "",
        "## Body",
        "",
    ]
    for item in script["body_points"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Summary", "", script["summary"], "", "## 拍摄提示", ""])
    lines.extend(f"- {item}" for item in script["shooting_tips"])
    return "\n".join(lines).rstrip() + "\n"


def run_script_writer_short(input_path: Path, *, workspace_root: Path) -> dict[str, Any]:
    text = input_path.read_text(encoding="utf-8")
    title = markdown_title(text) or input_path.stem
    slug = re.sub(r"-article$", "", input_path.stem)
    if not slug or slug == input_path.stem:
        slug = slugify(title)
    payload = build_script_payload(text, title, duration_seconds=90)
    md_path = script_md_path(workspace_root, slug)
    json_path = script_json_path(workspace_root, slug)
    full_payload = {
        "slug": slug,
        "title": clean_text(title),
        "source_path": str(input_path),
        **payload,
    }
    write_text(md_path, build_markdown(clean_text(title), slug, input_path, full_payload))
    write_text(json_path, json.dumps(full_payload, ensure_ascii=False, indent=2))
    return {
        "slug": slug,
        "title": clean_text(title),
        "script_path": md_path,
        "script_json_path": json_path,
        "duration_seconds": payload["duration_seconds"],
        "estimated_cn_chars": payload["estimated_cn_chars"],
        "run_status": "completed",
    }
