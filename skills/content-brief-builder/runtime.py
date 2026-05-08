from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from skill_runtime.writing_core import clean_text, slugify, truncate_text, write_text


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_explicit_field(text: str, names: list[str]) -> str:
    for name in names:
        pattern = rf"(?:^|\n)\s*{re.escape(name)}\s*[：:]\s*(?P<value>[^\n]+)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean_text(match.group("value"))
    return ""


def markdown_title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    if match:
        return clean_text(match.group(1))
    for line in text.splitlines():
        cleaned = clean_text(line)
        if cleaned:
            return cleaned
    return fallback


def extract_section(text: str, heading: str) -> str:
    pattern = rf"(?ms)^##\s+{re.escape(heading)}\s*\n(?P<body>.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, text)
    if not match:
        return ""
    return match.group("body").strip()


def first_subsection(section_text: str) -> str:
    match = re.search(r"(?ms)^###\s+.+?\n(?P<body>.*?)(?=^###\s+|\Z)", section_text)
    if match:
        return match.group("body").strip()
    return section_text.strip()


def parse_section_field(section_text: str, names: list[str]) -> str:
    for name in names:
        patterns = [
            rf"(?:^|\n)\s*-\s*`?{re.escape(name)}`?\s*[：:]\s*(?P<value>[^\n]+)",
            rf"(?:^|\n)\s*{re.escape(name)}\s*[：:]\s*(?P<value>[^\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, section_text, flags=re.IGNORECASE)
            if match:
                return clean_text(match.group("value"))
    return ""


def extract_numbered_titles(section_text: str) -> list[str]:
    titles: list[str] = []
    for line in section_text.splitlines():
        cleaned = clean_text(line)
        link_match = re.match(r"^\d+\.\s+\[(?P<title>[^\]]+)\]\([^)]+\)$", cleaned)
        if link_match:
            titles.append(clean_text(link_match.group("title")))
            continue
        plain_match = re.match(r"^\d+\.\s+(?P<title>.+)$", cleaned)
        if plain_match:
            titles.append(clean_text(plain_match.group("title")))
    return titles


def extract_bullet_values(section_text: str, label: str) -> list[str]:
    values: list[str] = []
    pattern = rf"^\s*-\s*`?{re.escape(label)}`?\s*[：:]\s*(?P<value>.+)$"
    for line in section_text.splitlines():
        match = re.match(pattern, line.strip(), flags=re.IGNORECASE)
        if match:
            values.append(clean_text(match.group("value")))
    return values


def extract_section_bullets(section_text: str) -> list[str]:
    values: list[str] = []
    for line in section_text.splitlines():
        stripped = clean_text(line)
        match = re.match(r"^[-*]\s*(?P<value>.+)$", stripped)
        if match:
            values.append(clean_text(match.group("value")))
    return values


def strip_markdown_prefix(value: str) -> str:
    return re.sub(r"^#+\s*", "", clean_text(value))


def detect_source_type(text: str) -> str:
    first_heading = markdown_title(text, "")
    if first_heading.startswith("资讯扫描报告："):
        return "news-report"
    if first_heading.startswith("深度研究报告："):
        return "research-report"
    return "generic-note"


def finalize_arguments(candidates: list[str], topic: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned = clean_text(candidate)
        if not cleaned or cleaned in seen:
            continue
        values.append(cleaned)
        seen.add(cleaned)
        if len(values) >= 3:
            return values
    for fallback in infer_arguments(topic):
        if fallback in seen:
            continue
        values.append(fallback)
        seen.add(fallback)
        if len(values) >= 3:
            break
    return values[:3]


def parse_news_report_context(text: str, fallback_topic: str, source_path: Path) -> dict[str, Any]:
    summary_section = extract_section(text, "扫描摘要")
    candidate_section = extract_section(text, "候选条目")
    recommendation_section = extract_section(text, "推荐选题")
    writeworthiness_section = first_subsection(extract_section(text, "写作价值判断"))
    cut_section = first_subsection(extract_section(text, "推荐切口"))
    framework_section = first_subsection(extract_section(text, "推荐框架与开头"))
    title_section = extract_section(text, "标题方向")

    topic = extract_numbered_titles(recommendation_section)[:1]
    selected_topic = topic[0] if topic else fallback_topic
    target_reader = parse_section_field(writeworthiness_section, ["primary_reader"])
    pain_point = parse_section_field(writeworthiness_section, ["primary_pain_point"])
    recommendation_reason = parse_section_field(recommendation_section, ["推荐理由"])
    selected_angle = parse_section_field(cut_section, ["推荐切口"]) or parse_section_field(recommendation_section, ["写作角度"])
    recommended_structure = parse_section_field(framework_section, ["recommended_structure"])
    recommended_opening_type = parse_section_field(framework_section, ["recommended_opening_type"])
    title_directions = extract_section_bullets(title_section)

    candidate_titles = extract_numbered_titles(candidate_section)
    candidate_summaries = extract_bullet_values(candidate_section, "摘要")
    summary_lines = [
        clean_text(line).removeprefix("- ").strip()
        for line in summary_section.splitlines()
        if clean_text(line).startswith("- ")
    ]

    core_parts = [selected_angle, recommendation_reason]
    if pain_point:
        core_parts.append(f"这篇文章最该回应的读者卡点是：{pain_point}。")
    core_view = "\n".join(part for part in core_parts if part) or infer_core_view(selected_topic, candidate_summaries)

    background = [
        summary_lines[0] if summary_lines else (recommendation_reason or f"“{selected_topic}”来自上游资讯扫描的推荐选题。"),
        f"当前最具体的读者痛点是：{pain_point}" if pain_point else "当前最容易被忽略的，是读者并不缺信息，而是缺判断和落地路径。",
        "现在写这个题最合适，因为热点讨论已经出现，但多数内容还停留在表层复述。",
    ]

    arguments = finalize_arguments(
        [
            selected_angle,
            f"先把读者真正卡住的地方讲透：{pain_point}" if pain_point else "",
            f"把 {candidate_titles[0]} 等一手来源转成可验证的论据。" if candidate_titles else "",
        ],
        selected_topic,
    )

    materials = [f"来源笔记：{source_path.name}"]
    materials.extend(candidate_titles[:2])
    materials.extend(candidate_summaries[:2])
    while len(materials) < 4:
        materials.append(f"待补一条和“{selected_topic}”直接相关的一手案例或数据。")
    materials = materials[:4]

    merged_source = " ".join([selected_topic, selected_angle, recommendation_reason, pain_point, *candidate_summaries])
    fit_scores = score_topic_fit(selected_topic, merged_source, candidate_summaries)

    publish_goal = (
        f"帮助{target_reader}先看清“{pain_point}”，再决定该怎么把这个热点写成有判断的公众号文章。"
        if target_reader and pain_point
        else infer_publish_goal(merged_source, candidate_summaries)
    )

    return {
        "source_type": "news-report",
        "topic": selected_topic,
        "target_reader": target_reader,
        "publish_goal": publish_goal,
        "core_view": core_view,
        "background": background,
        "arguments": arguments,
        "materials": materials,
        "timely_topic": True,
        "recommended_framework": recommended_structure or choose_framework(selected_topic, merged_source, candidate_summaries),
        "recommended_opening_type": recommended_opening_type,
        "recommended_formula": choose_angle_formula(selected_topic, merged_source, candidate_summaries),
        "fit_scores": fit_scores,
        "selected_angle": selected_angle,
        "title_directions": title_directions[:3],
        "risk_line": infer_risk(selected_topic, True),
    }


def parse_research_report_context(text: str, fallback_topic: str, source_path: Path) -> dict[str, Any]:
    question_section = extract_section(text, "研究问题")
    conclusion_section = extract_section(text, "核心结论")
    evidence_section = extract_section(text, "关键证据")
    angle_section = extract_section(text, "候选写作角度")
    reader_section = extract_section(text, "推荐读者与主痛点")
    framework_section = extract_section(text, "推荐框架与论证顺序")
    title_section = extract_section(text, "标题方向")

    target_reader = parse_section_field(reader_section, ["reader_profile"])
    pain_point = parse_section_field(reader_section, ["pain_point"])
    recommended_structure = parse_section_field(framework_section, ["recommended_structure"])
    recommended_opening_type = parse_section_field(framework_section, ["recommended_opening_type"])
    title_directions = extract_section_bullets(title_section)

    conclusion_lines = [
        strip_markdown_prefix(clean_text(line).removeprefix("- ").strip())
        for line in conclusion_section.splitlines()
        if clean_text(line).startswith("- ")
    ]
    evidence_titles = extract_numbered_titles(evidence_section)
    angle_titles = extract_numbered_titles(angle_section)
    selected_angle = angle_titles[0] if angle_titles else ""
    selected_topic = fallback_topic

    core_view = "\n".join(
        part for part in [conclusion_lines[0] if conclusion_lines else "", f"这篇文章最该回应的读者卡点是：{pain_point}。" if pain_point else ""] if part
    ) or infer_core_view(selected_topic, conclusion_lines)

    background = [
        truncate_text(question_section or f"这份研究围绕“{selected_topic}”展开。", 100),
        f"当前最常见的卡点是：{pain_point}" if pain_point else "当前最大问题不是有没有观点，而是有没有足够扎实的证据链。",
        "现在写这个题合适，因为研究已经把核心来源和主要分歧收拢成了可直接进入写作的结构。",
    ]

    arguments = finalize_arguments(
        [
            selected_angle,
            conclusion_lines[0] if conclusion_lines else "",
            f"把 {evidence_titles[0]} 等关键证据转成论据链。" if evidence_titles else "",
        ],
        selected_topic,
    )

    materials = [f"来源笔记：{source_path.name}"]
    materials.extend(evidence_titles[:3])
    while len(materials) < 4:
        materials.append(f"待补一条和“{selected_topic}”相关的补充来源或案例。")
    materials = materials[:4]

    merged_source = " ".join([selected_topic, question_section, *conclusion_lines, selected_angle, pain_point, *evidence_titles])
    fit_scores = score_topic_fit(selected_topic, merged_source, conclusion_lines + evidence_titles)

    publish_goal = (
        f"帮助{target_reader}围绕“{pain_point}”形成清楚判断，并把研究结果转成能发布的公众号观点稿。"
        if target_reader and pain_point
        else infer_publish_goal(merged_source, conclusion_lines)
    )

    return {
        "source_type": "research-report",
        "topic": selected_topic,
        "target_reader": target_reader,
        "publish_goal": publish_goal,
        "core_view": core_view,
        "background": background,
        "arguments": arguments,
        "materials": materials,
        "timely_topic": is_timely_topic(selected_topic, merged_source),
        "recommended_framework": recommended_structure or choose_framework(selected_topic, merged_source, conclusion_lines),
        "recommended_opening_type": recommended_opening_type,
        "recommended_formula": choose_angle_formula(selected_topic, merged_source, conclusion_lines),
        "fit_scores": fit_scores,
        "selected_angle": selected_angle,
        "title_directions": title_directions[:3],
        "risk_line": infer_risk(selected_topic, is_timely_topic(selected_topic, merged_source)),
    }


def body_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    for block in text.split("\n\n"):
        cleaned = clean_text(block)
        if not cleaned or cleaned.startswith("#"):
            continue
        if re.match(r"^(目标读者|写作目的|publish_goal|target_reader)\s*[：:]", cleaned, flags=re.IGNORECASE):
            continue
        paragraphs.append(cleaned)
    return paragraphs


def infer_target_reader(text: str, paragraphs: list[str]) -> str:
    explicit = parse_explicit_field(text, ["目标读者", "target_reader"])
    if explicit:
        return explicit
    patterns = [
        r"写给(?P<value>[^。！\n]+)",
        r"适合(?P<value>[^。！\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return clean_text(match.group("value")).removesuffix("的人").removesuffix("的人看").strip()
    for paragraph in paragraphs:
        if "读者" in paragraph or "公众号" in paragraph:
            return truncate_text(paragraph, 42)
    return "正在尝试用 AI 提升内容产出，但流程还不稳定的内容创作者"


def infer_publish_goal(text: str, paragraphs: list[str]) -> str:
    explicit = parse_explicit_field(text, ["写作目的", "publish_goal"])
    if explicit:
        return explicit
    patterns = [
        r"希望读者看完(?P<value>[^。！\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = clean_text(match.group("value"))
            if value.startswith("后"):
                value = value[1:].strip()
            return "希望读者看完后" + value
    if paragraphs:
        return f"希望读者看完后，能基于“{truncate_text(paragraphs[0], 20)}”形成明确判断，并知道下一步怎么做。"
    return "希望读者看完后，能形成明确判断，并知道下一步怎么做。"


def infer_core_view(topic: str, paragraphs: list[str]) -> str:
    if paragraphs:
        return "\n".join(paragraphs[:2])
    return (
        f"{topic}不是一个只靠工具就能解决的表面问题。\n"
        "真正决定结果的，是有没有一套可复用的判断、结构和执行流程。"
    )


def is_timely_topic(topic: str, text: str) -> bool:
    merged = clean_text(f"{topic} {text}").lower()
    timely_tokens = ["热点", "更新", "发布", "热搜", "刚刚", "最近", "本周", "今天", "deepseek", "chatgpt"]
    return any(token in merged for token in timely_tokens)


def choose_framework(topic: str, text: str, paragraphs: list[str]) -> str:
    merged = clean_text(" ".join([topic, text, *paragraphs])).lower()
    if any(token in merged for token in ["经历", "故事", "朋友", "被裁", "后来"]):
        return "故事类"
    if any(token in merged for token in ["热点", "热搜", "更新", "发布", "事件"]):
        return "热点类"
    if any(token in merged for token in ["如何", "怎么", "步骤", "教程", "方法"]):
        return "教学类"
    if any(token in merged for token in ["清单", "个方法", "个技巧", "列表"]):
        return "清单类"
    return "观点类"


def choose_angle_formula(topic: str, text: str, paragraphs: list[str]) -> str:
    merged = clean_text(" ".join([topic, text, *paragraphs]))
    lowered = merged.lower()
    if "别再" in merged or "替代" in merged or "效率" in merged or "效果" in merged:
        return "低效动作 + AI 替代 + 效果对比"
    if "你以为" in merged or "误区" in merged or "其实" in merged or "不是" in merged:
        return "误区 + 反转 + 方法"
    if "痛点" in merged or "省" in merged or "收益" in merged or "花你" in merged:
        return "痛点 + 工具 + 收益"
    if "deepseek" in lowered or "chatgpt" in lowered:
        return "低效动作 + AI 替代 + 效果对比"
    return "误区 + 反转 + 方法"


def score_dimension(source: str, keywords: list[str], *, base: int = 3, cap: int = 5) -> int:
    score = base
    lowered = source.lower()
    for keyword in keywords:
        if keyword.lower() in lowered:
            score += 1
    return min(score, cap)


def score_topic_fit(topic: str, text: str, paragraphs: list[str]) -> dict[str, int]:
    merged = clean_text(" ".join([topic, text, *paragraphs]))
    return {
        "热爱程度": score_dimension(merged, ["我想", "想写", "长期", "一直", "最想"]),
        "专业能力": score_dimension(merged, ["案例", "经验", "流程", "方法", "判断"]),
        "市场需求": score_dimension(merged, ["读者", "痛点", "热点", "更新", "不会", "卡住"]),
        "资源积累": score_dimension(merged, ["案例", "数据", "经历", "来源", "素材"]),
    }


def infer_risk(topic: str, timely: bool) -> str:
    if timely:
        return f"至少 1 个潜在翻车点：如果只复述“{topic}”本身，而没有转成对目标读者有用的判断，这篇文章会失去时效价值。"
    return "至少 1 个潜在翻车点：如果没有案例或数据支撑，文章很容易变成只有立场没有说服力的判断文。"


def infer_material_confidence(materials: list[str]) -> list[str]:
    levels: list[str] = []
    for item in materials[:3]:
        cleaned = clean_text(item)
        if "来源笔记" in cleaned or "http" in cleaned:
            levels.append("高")
        elif "待补" in cleaned or "待验证" in cleaned:
            levels.append("低")
        else:
            levels.append("中")
    while len(levels) < 3:
        levels.append("低")
    return levels[:3]


def infer_background(topic: str, paragraphs: list[str]) -> list[str]:
    if paragraphs:
        values = [truncate_text(item, 90) for item in paragraphs[:3]]
        while len(values) < 3:
            values.append(f"围绕“{topic}”的讨论正在增多，但观点质量参差不齐。")
        return values[:3]
    return [
        f"“{topic}”之所以被反复提起，通常不是因为信息不够，而是因为执行路径不清楚。",
        "很多相关内容停留在工具介绍和表面技巧，没有回答读者真正卡住的地方。",
        "现在写这个题，价值在于把零散经验整理成稳定可复用的方法。",
    ]


def infer_arguments(topic: str) -> list[str]:
    return [
        f"{topic}真正卡住的点，到底是工具问题、流程问题，还是判断问题",
        "为什么只更换工具，往往解决不了产出不稳定这件事",
        "如果要做出可复用结果，应该先搭哪一层结构，再补哪一层动作",
    ]


def infer_materials(paragraphs: list[str], topic: str, source_path: Path) -> list[str]:
    materials = [f"来源笔记：{source_path.name}"]
    for paragraph in paragraphs[:3]:
        materials.append(truncate_text(paragraph, 90))
    while len(materials) < 4:
        materials.append(f"待补一条和“{topic}”直接相关的案例、数据或人物经历。")
    return materials[:4]


def build_brief_markdown(
    *,
    date: str,
    slug: str,
    topic: str,
    target_reader: str,
    publish_goal: str,
    core_view: str,
    background: list[str],
    arguments: list[str],
    materials: list[str],
    source_path: Path,
    recommended_framework: str,
    recommended_formula: str,
    timely_topic: bool,
    fit_scores: dict[str, int],
    risk_line: str,
    confidence_levels: list[str],
    source_type: str = "",
    selected_angle: str = "",
    recommended_opening_type: str = "",
    title_directions: list[str] | None = None,
) -> str:
    title_directions = title_directions or []
    lines = [
        "# 阶段 1 观点 Brief",
        "",
        "## 基础信息",
        "",
        f"- `date`：{date}",
        f"- `slug`：{slug}",
        f"- `topic`：{topic}",
        f"- `target_reader`：{target_reader}",
        f"- `publish_goal`：{publish_goal}",
        "",
        "## 核心观点",
        "",
        core_view,
        "",
        "## 背景与语境",
        "",
        f"- 这件事是因为什么事件/现象引发的：{background[0]}",
        f"- 当前讨论环境里最常见的误区：{background[1]}",
        f"- 为什么现在写最合适：{background[2]}",
        "",
        "## 论证方向",
        "",
        *[f"{index}. {value}" for index, value in enumerate(arguments, start=1)],
        "",
        "## 可用案例 / 素材",
        "",
        *[f"- {value}" for value in materials],
        "",
        "## 明确不要写什么",
        "",
        "- 不要写成纯工具说明书或泛泛而谈的趋势综述。",
        "- 不要使用空泛、拔高、明显 AI 腔的表达。",
        "- 不要把没有验证的判断直接写成确定结论。",
        "",
        "## 风格要求",
        "",
        "- 风格关键词：清楚、克制、有判断。",
        "- 希望偏理性 / 偏锋利 / 偏故事化：偏理性，必要时补故事感。",
        "- 是否允许强观点：允许，但要有依据。",
        "- 是否需要金句或标题党：需要 1-2 句可传播的判断，但不过度标题党。",
        "",
        "## 配图方向",
        "",
        "- 希望图片类型：信息图 / 封面感视觉。",
        f"- 希望表达的核心视觉：围绕“{topic}”的结构、流程或判断。",
        "- 禁止出现的元素：无关炫技感、无关人物肖像、低信息密度装饰。",
        "",
        "## 备注",
        "",
        f"- 推荐框架：{recommended_framework}",
        f"- 推荐选题公式：{recommended_formula}",
        f"- 热点判断：{'是，适合按“热点七步法”处理' if timely_topic else '否，优先按常规观点/方法稿处理'}",
        f"- 选题四维打分：热爱程度 {fit_scores['热爱程度']}/5，专业能力 {fit_scores['专业能力']}/5，市场需求 {fit_scores['市场需求']}/5，资源积累 {fit_scores['资源积累']}/5",
        *( [f"- 上游来源类型：{source_type}"] if source_type else [] ),
        *( [f"- 采用切口：{selected_angle}"] if selected_angle else [] ),
        *( [f"- 上游建议开头：{recommended_opening_type}"] if recommended_opening_type else [] ),
        *([f"- 上游标题方向：{title}" for title in title_directions[:3]]),
        f"- 来源文件：{source_path}",
        "",
        "## SCQA 结构",
        "",
        f"- 情境(S)：{background[0]}",
        f"- 冲突(C)：{background[1]}",
        "- 问题(Q)：面对这个局面，读者到底该先改判断、改流程，还是改工具？",
        f"- 答案(A)：{truncate_text(core_view.splitlines()[0], 80)}",
        "",
        "## 风险提醒",
        "",
        f"- {risk_line}",
        "",
        "## 素材来源可信度",
        "",
        f"- 案例 1 可信度：{confidence_levels[0]}",
        f"- 案例 2 可信度：{confidence_levels[1]}",
        f"- 案例 3 可信度：{confidence_levels[2]}",
        "",
    ]
    return "\n".join(lines)


def build_content_brief(input_path: Path, *, workspace_root: Path) -> dict[str, Any]:
    text = read_text(input_path)
    date = datetime.now().strftime("%Y%m%d")
    paragraphs = body_paragraphs(text)
    source_type = detect_source_type(text)

    structured_context: dict[str, Any] = {}
    fallback_topic = markdown_title(text, input_path.stem)
    if source_type == "news-report":
        structured_context = parse_news_report_context(text, fallback_topic, input_path)
    elif source_type == "research-report":
        structured_context = parse_research_report_context(text, fallback_topic, input_path)

    topic = structured_context.get("topic") or fallback_topic
    slug = slugify(topic)
    target_reader = structured_context.get("target_reader") or infer_target_reader(text, paragraphs)
    publish_goal = structured_context.get("publish_goal") or infer_publish_goal(text, paragraphs)
    core_view = structured_context.get("core_view") or infer_core_view(topic, paragraphs)
    background = structured_context.get("background") or infer_background(topic, paragraphs)
    arguments = structured_context.get("arguments") or infer_arguments(topic)
    materials = structured_context.get("materials") or infer_materials(paragraphs, topic, input_path)
    timely_topic = structured_context.get("timely_topic")
    if timely_topic is None:
        timely_topic = is_timely_topic(topic, text)
    recommended_framework = structured_context.get("recommended_framework") or choose_framework(topic, text, paragraphs)
    recommended_formula = structured_context.get("recommended_formula") or choose_angle_formula(topic, text, paragraphs)
    fit_scores = structured_context.get("fit_scores") or score_topic_fit(topic, text, paragraphs)
    risk_line = structured_context.get("risk_line") or infer_risk(topic, timely_topic)
    confidence_levels = infer_material_confidence(materials)
    selected_angle = structured_context.get("selected_angle", "")
    recommended_opening_type = structured_context.get("recommended_opening_type", "")
    title_directions = structured_context.get("title_directions") or []

    output_path = workspace_root / "content-production" / "inbox" / f"{date}-{slug}-gzh-brief.md"
    markdown = build_brief_markdown(
        date=date,
        slug=slug,
        topic=topic,
        target_reader=target_reader,
        publish_goal=publish_goal,
        core_view=core_view,
        background=background,
        arguments=arguments,
        materials=materials,
        source_path=input_path,
        recommended_framework=recommended_framework,
        recommended_formula=recommended_formula,
        timely_topic=timely_topic,
        fit_scores=fit_scores,
        risk_line=risk_line,
        confidence_levels=confidence_levels,
        source_type=source_type if source_type != "generic-note" else "",
        selected_angle=selected_angle,
        recommended_opening_type=recommended_opening_type,
        title_directions=title_directions,
    )
    write_text(output_path, markdown)

    return {
        "brief_path": output_path,
        "slug": slug,
        "topic": topic,
        "target_reader": target_reader,
        "publish_goal": publish_goal,
        "source_path": str(input_path),
        "recommended_framework": recommended_framework,
        "recommended_formula": recommended_formula,
        "timely_topic": timely_topic,
        "source_type": source_type,
        "selected_angle": selected_angle,
        "title_directions": title_directions,
    }
