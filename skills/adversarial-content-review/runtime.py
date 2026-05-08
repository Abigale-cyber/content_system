from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from skill_runtime.writing_core import (
    clean_text,
    critique_article,
    detect_ai_trace_patterns,
    markdown_h2_headings,
    markdown_title,
    truncate_text,
)


def review_report_path(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "content-production" / "reviews" / f"{slug}-review-report.md"


def review_json_path(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "content-production" / "reviews" / f"{slug}-review-report.json"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def slug_for_article(path: Path, title: str) -> str:
    stem = re.sub(r"-article$", "", path.stem)
    if stem and stem != "article":
        return stem
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", title.strip().lower())
    return re.sub(r"-{2,}", "-", cleaned).strip("-") or "article"


def score_to_two(score: float) -> float:
    return round(max(0.0, min(2.0, score / 5.0)), 1)


def verdict_for(total_score: float) -> str:
    if total_score >= 8:
        return "通过"
    if total_score >= 5:
        return "需修改"
    return "需重写"


def dimension_scores(critique: dict[str, Any], ai_trace_risk: str) -> dict[str, float]:
    scores = critique["scores"]
    language_base = (scores["pacing_length"] + scores.get("template_repetition", 8.0)) / 2
    if ai_trace_risk == "high":
        language_base -= 1.5
    elif ai_trace_risk == "medium":
        language_base -= 0.6
    return {
        "structure_logic": score_to_two((scores["headline_hook"] + scores["structure_logic"]) / 2),
        "evidence_substance": score_to_two(scores["evidence_substance"]),
        "reader_value": score_to_two(scores["reader_value"]),
        "story_resonance": score_to_two(scores["story_resonance"]),
        "language_delivery": score_to_two(language_base),
    }


def collect_top_issues(critique: dict[str, Any], *, limit: int = 6) -> list[str]:
    issues: list[str] = []
    for key in (
        "headline_hook",
        "structure_logic",
        "evidence_substance",
        "reader_value",
        "story_resonance",
        "template_repetition",
        "pacing_length",
    ):
        for item in critique["issues"].get(key, []):
            if item not in issues:
                issues.append(item)
    return issues[:limit]


def writer_pass(critique: dict[str, Any], headings: list[str]) -> list[str]:
    notes = []
    if critique["scores"]["structure_logic"] < 8:
        notes.append("结构推进还不够稳，需要让每一节都承担明确任务。")
    if critique["scores"]["evidence_substance"] < 8:
        notes.append("论据硬度不足，建议补案例、数字、来源或可验证细节。")
    if len(headings) < 5:
        notes.append("章节数量偏少，容易显得像观点提纲而不是完整文章。")
    if not notes:
        notes.append("主线基本成立，下一步重点是压实细节和表达节奏。")
    return notes


def reader_pass(critique: dict[str, Any], ai_trace_risk: str) -> list[str]:
    notes = []
    if critique["scores"]["reader_value"] < 8:
        notes.append("读者读完后还不够清楚自己下一步该做什么。")
    if critique["scores"]["story_resonance"] < 8:
        notes.append("共鸣和画面感偏弱，需要补人物、冲突或真实场景。")
    if ai_trace_risk != "low":
        notes.append("语言仍有 AI 痕迹，部分表达像报告而不是作者在说话。")
    if not notes:
        notes.append("读者能抓到核心收益，但仍可以继续强化转发点。")
    return notes


def revision_suggestions(critique: dict[str, Any]) -> list[str]:
    suggestions = []
    issue_map = {
        "headline_hook": "标题：把读者收益或反常识冲突前置，避免报告化命名。",
        "structure_logic": "结构：补齐问题、论证、行动建议和结论的承接关系。",
        "evidence_substance": "证据：每个关键论点至少补一个案例、数据或来源线索。",
        "reader_value": "读者收益：在关键段落后补一句“对读者意味着什么”。",
        "story_resonance": "故事共鸣：补一个人物、冲突、转折都清楚的短故事。",
        "template_repetition": "模板味：替换重复的固定解释句，改用场景、问题或案例切入。",
        "pacing_length": "节奏：拆短长段落，给读者更多停顿和气口。",
    }
    for key, message in issue_map.items():
        if critique["issues"].get(key):
            suggestions.append(message)
    return suggestions[:6] or ["保留当前主线，优先补强标题钩子、证据细节和结尾行动感。"]


def build_markdown_report(
    *,
    title: str,
    slug: str,
    article_path: Path,
    critique: dict[str, Any],
    ai_trace_risk: str,
    dimensions: dict[str, float],
    total_score: float,
    verdict: str,
    writer_notes: list[str],
    reader_notes: list[str],
    suggestions: list[str],
) -> str:
    lines = [
        f"# 对抗式审稿报告：{title}",
        "",
        f"- `slug`：{slug}",
        f"- `source`：{article_path}",
        f"- `ai_trace_risk`：{ai_trace_risk}",
        f"- `total_score`：{total_score}",
        f"- `verdict`：{verdict}",
        "",
        "## 第 1 轮：笔杆子审",
        "",
    ]
    lines.extend(f"- {item}" for item in writer_notes)
    lines.extend(["", "## 第 2 轮：参谋审", ""])
    lines.extend(f"- {item}" for item in reader_notes)
    lines.extend(["", "## 第 3 轮：裁判裁定", "", f"结论：**{verdict}**。"])
    lines.extend(["", "## 五维度评分", ""])
    labels = {
        "structure_logic": "结构与标题",
        "evidence_substance": "论据硬度",
        "reader_value": "读者收益",
        "story_resonance": "故事共鸣",
        "language_delivery": "语言节奏",
    }
    for key, label in labels.items():
        lines.append(f"- `{key}` {label}：{dimensions[key]} / 2")
    lines.extend(["", "## 主要问题", ""])
    top_issues = collect_top_issues(critique)
    lines.extend(f"- {item}" for item in top_issues)
    lines.extend(["", "## 具体修改建议", ""])
    lines.extend(f"- {item}" for item in suggestions)
    return "\n".join(lines).rstrip() + "\n"


def run_adversarial_content_review(input_path: Path, *, workspace_root: Path) -> dict[str, Any]:
    text = input_path.read_text(encoding="utf-8")
    title = markdown_title(text) or input_path.stem
    slug = slug_for_article(input_path, title)
    headings = markdown_h2_headings(text)
    critique = critique_article(text, chosen_structure="progressive")
    trace = detect_ai_trace_patterns(text)
    dimensions = dimension_scores(critique, trace["risk"])
    total_score = round(sum(dimensions.values()), 1)
    verdict = verdict_for(total_score)
    writer_notes = writer_pass(critique, headings)
    reader_notes = reader_pass(critique, trace["risk"])
    suggestions = revision_suggestions(critique)

    report_path = review_report_path(workspace_root, slug)
    json_path = review_json_path(workspace_root, slug)
    payload = {
        "slug": slug,
        "title": clean_text(title),
        "source_path": str(input_path),
        "ai_trace_risk": trace["risk"],
        "total_score": total_score,
        "verdict": verdict,
        "dimension_scores": dimensions,
        "critique_scores": critique["scores"],
        "critic_issues": critique["issues"],
        "suggestions": suggestions,
        "article_excerpt": truncate_text(text, 260),
    }
    write_text(
        report_path,
        build_markdown_report(
            title=clean_text(title),
            slug=slug,
            article_path=input_path,
            critique=critique,
            ai_trace_risk=trace["risk"],
            dimensions=dimensions,
            total_score=total_score,
            verdict=verdict,
            writer_notes=writer_notes,
            reader_notes=reader_notes,
            suggestions=suggestions,
        ),
    )
    dump_json(json_path, payload)

    return {
        "slug": slug,
        "title": clean_text(title),
        "report_path": report_path,
        "review_json_path": json_path,
        "total_score": total_score,
        "verdict": verdict,
        "dimension_scores": dimensions,
        "blocking": verdict != "通过",
        "run_status": "completed" if verdict == "通过" else "awaiting_revision",
        "next_action": "" if verdict == "通过" else "Revise the article, then run adversarial-content-review again.",
    }
