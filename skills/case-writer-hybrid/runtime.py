from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from skill_runtime.writing_core import (
    STRUCTURE_TYPES,
    TITLE_DRIVERS,
    TITLE_PATTERNS,
    build_ending_cta,
    build_ending_options,
    build_opening_options,
    build_quality_gate_notice,
    build_share_copy_options,
    build_summary_points,
    bullet_values,
    choose_structure,
    clean_text,
    critique_article,
    derive_primary_pain_point,
    derive_reader_profile,
    dump_json,
    extract_highlight_quotes,
    generate_title_options,
    humanize_markdown,
    judge_article,
    parse_markdown_sections,
    quality_gate_path,
    read_text,
    score_topic_material,
    score_title,
    slugify,
    title_pattern_for,
    truncate_text,
    write_text,
    detect_title_drivers,
)


EXTERNAL_FRAMEWORK_MAP = {
    "对比式": "parallel",
    "对比结构": "parallel",
    "问答式": "what_why_how",
    "教学类": "what_why_how",
    "序列步骤结构": "what_why_how",
    "故事类": "story",
    "故事叙述结构": "story",
    "清单类": "listicle",
    "金字塔结构": "progressive",
    "观点类": "progressive",
    "热点类": "progressive",
    "环形首尾呼应结构": "progressive",
}


def parse_brief(path: Path) -> dict[str, Any]:
    text = read_text(path)
    sections = parse_markdown_sections(text)
    base = "\n".join(sections.get("基础信息", []))

    def field(name: str) -> str:
        match = re.search(rf"`?{re.escape(name)}`?\s*[：:]\s*(.+)", base)
        return match.group(1).strip() if match else ""

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
    slug = field("slug") or slugify(topic)
    date = field("date") or datetime.now().strftime("%Y%m%d")
    notes = bullet_values(sections.get("备注", []))

    def note_field(name: str) -> str:
        prefix = f"{name}："
        alt_prefix = f"{name}:"
        for item in notes:
            if item.startswith(prefix):
                return clean_text(item[len(prefix) :])
            if item.startswith(alt_prefix):
                return clean_text(item[len(alt_prefix) :])
        return ""

    def note_fields(name: str) -> list[str]:
        values: list[str] = []
        prefix = f"{name}："
        alt_prefix = f"{name}:"
        for item in notes:
            if item.startswith(prefix):
                values.append(clean_text(item[len(prefix) :]))
            elif item.startswith(alt_prefix):
                values.append(clean_text(item[len(alt_prefix) :]))
        return values

    def section_field(section_name: str, labels: list[str]) -> str:
        lines = bullet_values(sections.get(section_name, []))
        for label in labels:
            prefixes = [f"{label}：", f"{label}:"]
            for item in lines:
                for prefix in prefixes:
                    if item.startswith(prefix):
                        return clean_text(item[len(prefix) :])
        return ""

    def material_confidence_values() -> list[dict[str, str]]:
        values: list[dict[str, str]] = []
        for item in bullet_values(sections.get("素材来源可信度", [])):
            match = re.match(r"^(?P<case>案例\s*\d+)\s*可信度\s*[：:]\s*(?P<level>高|中|低)", item)
            if not match:
                continue
            values.append(
                {
                    "case": clean_text(match.group("case")),
                    "level": clean_text(match.group("level")),
                }
            )
        return values

    return {
        "topic": topic,
        "slug": slug,
        "date": date,
        "target_reader": field("target_reader"),
        "publish_goal": field("publish_goal"),
        "core_view": core_view,
        "background": bullet_values(sections.get("背景与语境", [])),
        "arguments": bullet_values(sections.get("论证方向", [])),
        "cases": bullet_values(sections.get("可用案例 / 素材", [])),
        "avoid": bullet_values(sections.get("明确不要写什么", [])),
        "style": bullet_values(sections.get("风格要求", [])),
        "visual": bullet_values(sections.get("配图方向", [])),
        "notes": notes,
        "recommended_framework": note_field("推荐框架"),
        "source_type": note_field("上游来源类型"),
        "selected_angle": note_field("采用切口"),
        "recommended_opening_type": note_field("上游建议开头"),
        "title_directions": note_fields("上游标题方向"),
        "scqa": {
            "situation": section_field("SCQA 结构", ["情境(S)", "情境", "S"]),
            "complication": section_field("SCQA 结构", ["冲突(C)", "冲突", "C"]),
            "question": section_field("SCQA 结构", ["问题(Q)", "问题", "Q"]),
            "answer": section_field("SCQA 结构", ["答案(A)", "答案", "A"]),
        },
        "risk_reminders": bullet_values(sections.get("风险提醒", [])),
        "material_confidence": material_confidence_values(),
        "source_path": str(path),
    }


def article_output_path(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "content-production" / "drafts" / f"{slug}-article.md"


def writing_pack_md_path(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "content-production" / "drafts" / f"{slug}-writing-pack.md"


def writing_pack_json_path(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "content-production" / "drafts" / f"{slug}-writing-pack.json"


def review_trace_path(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "content-production" / "drafts" / f"{slug}-review-trace.json"


def _argument_label(index: int, total: int, structure_type: str) -> str:
    if structure_type == "what_why_how":
        return ["What：问题到底是什么", "Why：为什么现在必须重视", "How：普通人怎么落地"][min(index - 1, 2)]
    if structure_type == "story":
        return ["故事先讲到这里", "问题真正卡在哪里", "这件事最后怎么落地"][min(index - 1, 2)]
    if structure_type == "listicle":
        return f"清单 {index}"
    return f"论证 {index}"


def guided_structure(brief: dict[str, Any]) -> dict[str, str] | None:
    recommended = clean_text(brief.get("recommended_framework"))
    if not recommended:
        return None
    mapped = EXTERNAL_FRAMEWORK_MAP.get(recommended)
    if not mapped:
        return None
    return {
        "type": mapped,
        "reason": f"沿用 brief 备注里的推荐框架“{recommended}”，让上游选题判断继续传递到正文结构。",
    }


def guided_opening_option(brief: dict[str, Any], *, reader_profile: str, pain_point: str) -> dict[str, str] | None:
    angle = clean_text(brief.get("selected_angle"))
    opening_hint = clean_text(brief.get("recommended_opening_type"))
    if not angle and not opening_hint:
        return None

    reader = reader_profile or "这类读者"
    pain = pain_point or "已经做了很多动作，但结果还是不稳定"
    topic = brief["topic"]
    claim = truncate_text(angle or brief.get("core_view") or topic, 56).rstrip("。！？!?. ")
    case_line = truncate_text(brief["cases"][0], 56) if brief.get("cases") else ""

    if "故事" in opening_hint and case_line:
        opening_type = "story"
        label = opening_hint or "故事开头"
        text = f"先讲个片段：{case_line}。表面上这是一个案例，实际上它刚好说明了这篇文章要拆开的切口：{claim}"
    elif "提问" in opening_hint:
        opening_type = "suspense"
        label = opening_hint or "提问式开头"
        text = f"{claim}？如果你是{reader}，真正该追问的不是工具够不够新，而是这件事能不能进入稳定交付。"
    elif "痛点" in opening_hint:
        opening_type = "pain_point"
        label = opening_hint or "痛点开头"
        text = f"如果你也是{reader}，现在最容易卡住的往往不是不努力，而是{pain}。这篇文章就从这个切口往下拆：{claim}"
    else:
        opening_type = "direct_claim"
        label = opening_hint or "上游建议开头"
        text = f"很多人以为{topic}拼的是 prompt 和动作，但真正拉开差距的，往往是{claim}"

    return {
        "type": opening_type,
        "label": label,
        "text": text,
        "source": "upstream-guidance",
    }


def join_sentence_hints(items: list[str], *, limit: int = 2) -> str:
    cleaned = [clean_text(item).rstrip("。！？!?；;，, ") for item in items[:limit] if clean_text(item)]
    return "；".join(cleaned)


def guided_title_options(brief: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for title in brief.get("title_directions") or []:
        normalized = clean_text(title)
        if not normalized:
            continue
        pattern = title_pattern_for(normalized)
        drivers = detect_title_drivers(normalized)
        items.append(
            {
                "title": normalized,
                "pattern": pattern,
                "pattern_label": TITLE_PATTERNS[pattern],
                "drivers": drivers,
                "driver_labels": [TITLE_DRIVERS[item] for item in drivers],
                "length": len(normalized),
                "score": score_title(normalized),
                "source": "upstream-guidance",
            }
        )
    return items


def merge_title_options(upstream: list[dict[str, Any]], generated: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in upstream + generated:
        normalized = clean_text(item["title"])
        if not normalized or normalized in seen:
            continue
        enriched = {"source": item.get("source", "generated"), **item}
        merged.append(enriched)
        seen.add(normalized)
    return merged[:10]


def material_confidence_level(brief: dict[str, Any], case_index: int) -> str:
    confidence = brief.get("material_confidence") or []
    if case_index - 1 < len(confidence):
        return clean_text(confidence[case_index - 1].get("level"))
    for item in confidence:
        case_label = clean_text(item.get("case"))
        match = re.search(r"\d+", case_label)
        if match and int(match.group(0)) == case_index:
            return clean_text(item.get("level"))
    return "中"


def argument_lead_paragraph(
    *,
    normalized_argument: str,
    argument_index: int,
    brief: dict[str, Any],
) -> str:
    reader = brief.get("target_reader") or "读者"
    leads = [
        f"{normalized_argument}。先把这个判断放回读者现场：{reader}通常不是少一个工具，而是少一个能反复执行的顺序。",
        f"{normalized_argument}。这一段要拆的是中间那层误会：看起来是在比工具，实际是在比谁能把输入、判断和反馈串起来。",
        f"{normalized_argument}。落到行动上，重点不是再多加一个动作，而是先判断哪一步最容易失控。",
    ]
    return leads[min(argument_index - 1, len(leads) - 1)]


def case_paragraph(case_line: str, *, confidence_level: str) -> str:
    if not case_line:
        return ""
    if confidence_level == "低":
        return f"这里有一条待验证线索：{case_line}。在补到来源或细节之前，它只能作为待验证线索，不能当作确定事实。"
    if confidence_level == "高":
        return f"比较扎实的证据是：{case_line}。它的价值在于把判断落到具体来源上，而不是停在口号里。"
    return f"可以先参考的案例是：{case_line}。它能提供一个观察入口，但写作时还需要补时间、来源或具体细节。"


def story_resonance_paragraph(
    *,
    case_line: str,
    confidence_level: str,
    brief: dict[str, Any],
) -> str:
    reader = brief.get("target_reader") or "读者"
    pain = derive_primary_pain_point(brief) or "明明很努力，结果还是不稳定"
    if case_line and confidence_level != "低":
        return (
            f"你有没有这种感觉：{pain}？有个{reader}就遇到过这个情况：{case_line}。"
            "后来他没有继续换工具，而是先把选题、brief、审稿顺序固定下来。"
            "说白了，故事的转折不在工具变多，而在流程终于能重复。"
        )
    return (
        f"你有没有这种感觉：{pain}？有个{reader}一开始也以为答案是再换一套工具。"
        "后来他把每次卡住的地方记下来，才发现真正反复出问题的不是工具，而是选题、素材和审稿顺序没有固定。"
        "说白了，这个故事要提醒的是，先把流程跑稳，再谈技巧优化。"
    )


def evidence_bridge_paragraph(
    *,
    argument_index: int,
    brief: dict[str, Any],
    varied: bool,
) -> str:
    reader = brief.get("target_reader") or "读者"
    if not varied:
        return "这不是抽象判断。至少可以从三个层面去看：一是实际案例有没有重复出现，二是论证里有没有可验证的事实，三是这些事实能不能支撑你最后那个结论。"
    variants = [
        "这不是抽象判断。至少可以从三个层面去看：一是实际案例有没有重复出现，二是论证里有没有可验证的事实，三是这些事实能不能支撑你最后那个结论。",
        f"换个角度看，真正要比较的不是说法漂不漂亮，而是证据能不能互相咬合。对{reader}来说，一条孤立案例只能提供线索，多条来源指向同一个问题，判断才站得住。",
        "如果把它放进真实项目，判断标准会更直接：出了问题能不能定位，改完以后能不能验证，下一次遇到类似情况能不能复用同一套处理顺序。",
    ]
    return variants[min(argument_index - 1, len(variants) - 1)]


def reader_value_paragraph(
    *,
    argument_index: int,
    brief: dict[str, Any],
    varied: bool,
) -> str:
    reader = brief["target_reader"] or "读者"
    if not varied:
        return f"对{reader}来说，真正有用的地方不只是听懂一个观点，而是知道自己接下来应该往哪一步补。"
    variants = [
        f"对{reader}来说，这里的价值不在于多记一个概念，而在于能立刻判断：下一步到底该补流程、补素材，还是补验证。",
        "落到行动上，可以先问一个更小的问题：如果明天就要复用这套方法，哪一步最容易失控？那一步就是优先级。",
        "所以别急着把所有动作都加上。先挑一个最常翻车的环节，把输入、检查和反馈固定下来，效果会更容易看见。",
    ]
    return variants[min(argument_index - 1, len(variants) - 1)]


def _argument_paragraphs(
    *,
    argument: str,
    argument_index: int,
    case_line: str,
    brief: dict[str, Any],
    focus_areas: list[str],
    round_index: int,
) -> list[str]:
    normalized_argument = argument.rstrip("。！？!?. ")
    paragraphs = [
        argument_lead_paragraph(
            normalized_argument=normalized_argument,
            argument_index=argument_index,
            brief=brief,
        ),
    ]
    case_text = case_paragraph(
        case_line,
        confidence_level=material_confidence_level(brief, argument_index),
    )
    if case_text:
        paragraphs.append(case_text)
    confidence_level = material_confidence_level(brief, argument_index)
    if "story_resonance" in focus_areas and argument_index == 1:
        paragraphs.append(
            story_resonance_paragraph(
                case_line=case_line,
                confidence_level=confidence_level,
                brief=brief,
            )
        )
    evidence_needed = (
        "evidence_substance" in focus_areas
        or round_index >= 2
        or brief.get("source_type") in {"news-report", "research-report"}
    )
    if evidence_needed:
        additional_cases = [
            clean_text(item)
            for case_offset, item in enumerate(brief.get("cases", [])[1:3], start=2)
            if clean_text(item)
            and clean_text(item) != clean_text(case_line)
            and material_confidence_level(brief, case_offset) != "低"
        ]
        if additional_cases:
            evidence_text = "；".join(additional_cases)
            paragraphs.append(f"继续往下看，关键证据并不只一条。像 {evidence_text} 这些线索，能把同一个判断从不同来源上钉得更牢。")
        paragraphs.append(
            evidence_bridge_paragraph(
                argument_index=argument_index,
                brief=brief,
                varied="template_repetition" in focus_areas,
            )
        )
    if "reader_value" in focus_areas or round_index >= 2:
        paragraphs.append(
            reader_value_paragraph(
                argument_index=argument_index,
                brief=brief,
                varied="template_repetition" in focus_areas,
            )
        )
    if "pacing_length" in focus_areas and round_index >= 2:
        paragraphs.append("换句话说，别急着加动作，先把结构补齐。")
    return paragraphs


def compose_article(
    *,
    brief: dict[str, Any],
    package: dict[str, Any],
    round_index: int,
    focus_areas: list[str],
) -> str:
    arguments = brief["arguments"][:3] or [
        "为什么这个问题值得现在讨论",
        "为什么它不是一个单点动作问题",
        "为什么最后还是要回到系统和结构",
    ]
    cases = brief["cases"][:3]
    title_candidates = package["title_options"]
    title = brief["topic"] if round_index == 1 else title_candidates[min(round_index - 2, len(title_candidates) - 1)]["title"]
    if "headline_hook" in focus_areas and title_candidates:
        title = title_candidates[0]["title"]

    opening_options = package["opening_options"]
    ending_options = package["ending_options"]
    opening_text = opening_options[min(round_index - 1, len(opening_options) - 1)]["text"]
    ending_text = ending_options[0]["text"] if "reader_value" not in focus_areas else ending_options[min(1, len(ending_options) - 1)]["text"]
    topic = brief["topic"]
    core_view = clean_text(brief["core_view"]) or f"{topic}不是表面技巧，而是一套能复用的结构。"
    structure_label = STRUCTURE_TYPES[package["chosen_structure"]["type"]]

    argument_blocks: list[str] = []
    for index, argument in enumerate(arguments, start=1):
        case_line = cases[index - 1] if index - 1 < len(cases) else ""
        section_title = _argument_label(index, len(arguments), package["chosen_structure"]["type"])
        if not section_title.startswith(("论证", "What", "Why", "How", "故事", "清单")):
            section_title = f"论证 {index}"
        paragraphs = _argument_paragraphs(
            argument=argument,
            argument_index=index,
            case_line=case_line,
            brief=brief,
            focus_areas=focus_areas,
            round_index=round_index,
        )
        argument_blocks.extend([f"## {section_title}", "", *paragraphs, ""])

    action_lines = [
        "先明确这篇内容到底要替谁解决什么问题，别上来就堆信息。",
        f"优先采用 `{structure_label}`，先把结构搭好，再补素材和标题。",
        "发布前至少再过一遍标题、开头、证据和结尾互动，不要只改错别字。",
    ]

    spread_lines = [f"- {item}" for item in package["highlight_quotes"][:3]]
    background_hint = truncate_text(join_sentence_hints(brief["background"]), 140)
    selected_angle = clean_text(brief.get("selected_angle"))
    scqa = brief.get("scqa") or {}
    scqa_question = clean_text(scqa.get("question"))
    scqa_answer = clean_text(scqa.get("answer"))
    low_confidence_items = [
        item
        for item in brief.get("material_confidence", [])
        if clean_text(item.get("level")) == "低"
    ]
    evidence_note = (
        "低可信素材只作为待验证线索，不能直接写成确定事实。"
        if low_confidence_items
        else ""
    )

    article = [
        f"# {title}",
        "",
        f"> 目标读者：{brief['target_reader'] or '关注该议题的公众号读者'}",
        f"> 发布目标：{brief['publish_goal'] or '形成一篇可发布的公众号长文'}",
        "",
        "## 导语",
        "",
        opening_text,
        "",
        "## 问题提出",
        "",
        background_hint or "很多内容之所以没有结果，不是因为作者不努力，而是因为题目、结构、包装和质量门控并没有形成闭环。",
        *(["", f"用 SCQA 来看，这篇文章真正要回答的问题是：{scqa_question}"] if scqa_question else []),
        *(["", f"这篇文章会沿着这样一个切口展开：{selected_angle}"] if selected_angle else []),
        "",
        "## 核心判断",
        "",
        f"{core_view} {scqa_answer or '这也是为什么这篇文章不打算只停留在现象判断，而是要把背后的结构说清楚。'}",
        "",
        *argument_blocks,
        "## 你现在可以怎么做",
        "",
        *[f"- {item}" for item in action_lines],
        *(["", f"- {evidence_note}"] if evidence_note else []),
        "",
        "## 结论",
        "",
        ending_text,
        "",
        "## 可传播总结",
        "",
        *spread_lines,
        "",
    ]
    return "\n".join(article).rstrip() + "\n"


def build_writing_pack_markdown(package: dict[str, Any], judge: dict[str, Any]) -> str:
    lines = [
        f"# 写作包：{package['topic']}",
        "",
        "## 写作定位",
        "",
        f"- `topic_score`：{package['topic_score']['total']}",
        f"- `reader_profile`：{package['reader_profile']}",
        f"- `primary_pain_point`：{package['primary_pain_point']}",
        "",
    ]
    upstream = package.get("upstream_guidance") or {}
    if any(clean_text(value) for value in upstream.values()):
        lines.extend(
            [
                "## 上游指导",
                "",
                f"- `source_type`：{upstream.get('source_type', '') or 'unknown'}",
                f"- `recommended_framework`：{upstream.get('recommended_framework', '') or '未提供'}",
                f"- `selected_angle`：{upstream.get('selected_angle', '') or '未提供'}",
                f"- `recommended_opening_type`：{upstream.get('recommended_opening_type', '') or '未提供'}",
                *( [f"- `title_direction`：{item}" for item in (upstream.get("title_directions") or [])[:3]] ),
                "",
            ]
        )

    scqa = package.get("scqa") or {}
    if any(clean_text(value) for value in scqa.values()):
        lines.extend(
            [
                "## SCQA",
                "",
                f"- `situation`：{scqa.get('situation', '') or '未提供'}",
                f"- `complication`：{scqa.get('complication', '') or '未提供'}",
                f"- `question`：{scqa.get('question', '') or '未提供'}",
                f"- `answer`：{scqa.get('answer', '') or '未提供'}",
                "",
            ]
        )

    if package.get("risk_reminders") or package.get("material_confidence"):
        lines.extend(["## 风险与素材可信度", ""])
        for item in package.get("risk_reminders") or []:
            lines.append(f"- `risk`：{item}")
        for item in package.get("material_confidence") or []:
            lines.append(f"- `{item['case']}`：{item['level']}")
        lines.append("")

    lines.extend(
        [
        "## 选用结构",
        "",
        f"- `type`：{package['chosen_structure']['type']}",
        f"- `label`：{STRUCTURE_TYPES[package['chosen_structure']['type']]}",
        f"- `reason`：{package['chosen_structure']['reason']}",
        "",
        "## 开头备选",
        "",
        ]
    )
    for item in package["opening_options"]:
        lines.extend([f"### {item['label']}", "", item["text"], ""])

    lines.extend(["## 结尾备选", ""])
    for item in package["ending_options"]:
        lines.extend([f"### {item['label']}", "", item["text"], ""])

    lines.extend(["## 标题候选", ""])
    for item in package["title_options"]:
        driver_text = " / ".join(item["driver_labels"]) or "无"
        lines.append(f"- {item['title']} | {item['pattern_label']} | 驱动：{driver_text} | 分数：{item['score']}")

    lines.extend(["", "## 转发语候选", ""])
    for item in package["share_copy_options"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 金句候选", ""])
    for item in package["highlight_quotes"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 裁判结论",
            "",
            f"- `score`：{judge['score']}",
            f"- `ai_trace_risk`：{judge['ai_trace_risk']}",
            f"- `pass`：{'true' if judge['pass'] else 'false'}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_case_writer_hybrid(input_path: Path, *, workspace_root: Path) -> dict[str, Any]:
    brief = parse_brief(input_path)
    topic_score = score_topic_material(
        topic=brief["topic"],
        core_view=brief["core_view"],
        background=brief["background"],
        arguments=brief["arguments"],
        cases=brief["cases"],
        notes=brief["notes"],
    )
    chosen_structure = guided_structure(brief) or choose_structure(
        topic=brief["topic"],
        core_view=brief["core_view"],
        arguments=brief["arguments"],
        cases=brief["cases"],
        background=brief["background"],
    )
    reader_profile = derive_reader_profile(brief)
    primary_pain_point = derive_primary_pain_point(brief)
    opening_options = build_opening_options(
        topic=brief["topic"],
        reader_profile=reader_profile,
        pain_point=primary_pain_point,
        core_view=brief["core_view"],
        chosen_structure=chosen_structure["type"],
        cases=brief["cases"],
    )
    guided_opening = guided_opening_option(
        brief,
        reader_profile=reader_profile,
        pain_point=primary_pain_point,
    )
    if guided_opening is not None:
        deduped_openings = [guided_opening]
        seen_opening_texts = {clean_text(guided_opening["text"])}
        for item in opening_options:
            normalized = clean_text(item["text"])
            enriched = {"source": item.get("source", "generated"), **item}
            if normalized in seen_opening_texts:
                continue
            deduped_openings.append(enriched)
            seen_opening_texts.add(normalized)
        opening_options = deduped_openings[:5]
    else:
        opening_options = [{"source": item.get("source", "generated"), **item} for item in opening_options]
    ending_options = build_ending_options(
        topic=brief["topic"],
        reader_profile=reader_profile,
        core_view=brief["core_view"],
    )
    title_options = generate_title_options(
        topic=brief["topic"],
        core_view=brief["core_view"],
        reader_profile=reader_profile,
        pain_point=primary_pain_point,
    )
    title_options = merge_title_options(guided_title_options(brief), title_options)
    share_copy_options = build_share_copy_options(
        topic=brief["topic"],
        core_view=brief["core_view"],
        reader_profile=reader_profile,
    )
    highlight_quotes = extract_highlight_quotes(
        topic=brief["topic"],
        core_view=brief["core_view"],
        arguments=brief["arguments"],
    )
    summary_points = build_summary_points(brief["arguments"], brief["core_view"])
    ending_cta = build_ending_cta(reader_profile, brief["topic"])

    package = {
        "topic": brief["topic"],
        "slug": brief["slug"],
        "topic_score": topic_score,
        "reader_profile": reader_profile or "关注该议题的公众号读者",
        "primary_pain_point": primary_pain_point,
        "chosen_structure": chosen_structure,
        "opening_options": opening_options,
        "ending_options": ending_options,
        "title_options": title_options,
        "share_copy_options": share_copy_options,
        "highlight_quotes": highlight_quotes,
        "summary_points": summary_points,
        "ending_cta": ending_cta,
        "upstream_guidance": {
            "source_type": brief.get("source_type", ""),
            "recommended_framework": brief.get("recommended_framework", ""),
            "selected_angle": brief.get("selected_angle", ""),
            "recommended_opening_type": brief.get("recommended_opening_type", ""),
            "title_directions": brief.get("title_directions", []),
        },
        "scqa": brief.get("scqa", {}),
        "risk_reminders": brief.get("risk_reminders", []),
        "material_confidence": brief.get("material_confidence", []),
    }

    best_article = ""
    best_judge: dict[str, Any] | None = None
    best_score = -1.0
    focus_areas: list[str] = []
    rounds: list[dict[str, Any]] = []

    for round_index in range(1, 4):
        draft = compose_article(
            brief=brief,
            package=package,
            round_index=round_index,
            focus_areas=focus_areas,
        )
        humanized = humanize_markdown(draft, mode="surgical")
        critique = critique_article(humanized["text"], chosen_structure=chosen_structure["type"])
        judge = judge_article(humanized["text"], critique=critique, humanizer_report=humanized)

        rounds.append(
            {
                "round": round_index,
                "title": clean_text(re.search(r"^#\s+(.+)$", humanized["text"], flags=re.MULTILINE).group(1)) if re.search(r"^#\s+(.+)$", humanized["text"], flags=re.MULTILINE) else brief["topic"],
                "score": judge["score"],
                "scores": judge["scores"],
                "ai_trace_risk": judge["ai_trace_risk"],
                "critic_issues": critique["issues"],
                "focus_areas": judge["focus_areas"],
                "humanizer": {
                    "changed_line_count": humanized["changed_line_count"],
                    "pattern_hit_count": humanized["pattern_hit_count"],
                    "changes": humanized["changes"],
                },
                "article_excerpt": truncate_text(humanized["text"], 260),
            }
        )

        if judge["score"] > best_score:
            best_score = judge["score"]
            best_article = humanized["text"]
            best_judge = judge

        if judge["pass"]:
            break
        focus_areas = judge["focus_areas"]

    assert best_judge is not None

    article_path = article_output_path(workspace_root, brief["slug"])
    pack_md_path = writing_pack_md_path(workspace_root, brief["slug"])
    pack_json_path = writing_pack_json_path(workspace_root, brief["slug"])
    trace_path = review_trace_path(workspace_root, brief["slug"])
    notice_path = quality_gate_path(workspace_root, date=brief["date"], slug=brief["slug"])

    publish_ready = bool(best_judge["pass"])
    run_status = "completed" if publish_ready else "quality_gate_failed"
    next_action = "" if publish_ready else "user_review_required"

    package["judge_summary"] = {
        "score": best_judge["score"],
        "scores": best_judge["scores"],
        "ai_trace_risk": best_judge["ai_trace_risk"],
        "pass": publish_ready,
    }
    package["publish_ready"] = publish_ready
    package["run_status"] = run_status
    package["next_action"] = next_action

    write_text(article_path, best_article)
    write_text(pack_md_path, build_writing_pack_markdown(package, best_judge))
    dump_json(pack_json_path, package)
    dump_json(
        trace_path,
        {
            "slug": brief["slug"],
            "topic": brief["topic"],
            "source_path": brief["source_path"],
            "publish_ready": publish_ready,
            "run_status": run_status,
            "next_action": next_action,
            "final_round": rounds[-1]["round"],
            "selected_round": max(rounds, key=lambda item: item["score"])["round"],
            "rounds": rounds,
            "latest_score": best_judge["score"],
            "latest_scores": best_judge["scores"],
            "ai_trace_risk": best_judge["ai_trace_risk"],
            "unresolved_issues": best_judge["unresolved_issues"],
        },
    )

    if not publish_ready:
        write_text(
            notice_path,
            build_quality_gate_notice(
                date=brief["date"],
                slug=brief["slug"],
                topic=brief["topic"],
                judge=best_judge,
                article_path=article_path,
                writing_pack_path=pack_md_path,
                review_trace_path=trace_path,
            ),
        )

    return {
        "slug": brief["slug"],
        "topic": brief["topic"],
        "article_path": article_path,
        "writing_pack_md_path": pack_md_path,
        "writing_pack_json_path": pack_json_path,
        "review_trace_path": trace_path,
        "quality_gate_notice_path": notice_path if not publish_ready else "",
        "chosen_structure": chosen_structure,
        "upstream_guidance": package["upstream_guidance"],
        "publish_ready": publish_ready,
        "run_status": run_status,
        "blocking": not publish_ready,
        "next_action": next_action,
        "score": best_judge["score"],
        "scores": best_judge["scores"],
        "ai_trace_risk": best_judge["ai_trace_risk"],
        "message": "文章已通过质量门控。" if publish_ready else "文章连续三轮未达标，已中断并等待人工处理。",
    }
