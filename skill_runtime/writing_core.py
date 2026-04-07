from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


STRUCTURE_TYPES = {
    "story": "故事型",
    "parallel": "平行式",
    "listicle": "清单式",
    "progressive": "递进式",
    "what_why_how": "What-Why-How",
}

OPENING_TYPES = {
    "relevance_utility": "与我有关/对我有用",
    "story": "讲故事",
    "direct_claim": "开门见山表明观点",
    "pain_point": "痛点切入",
    "news_event": "新闻事件切入",
    "quote": "金句切入",
    "suspense": "悬念切入",
    "summary": "精华摘要切入",
}

ENDING_TYPES = {
    "summary": "总结全文",
    "restate_claim": "强调观点",
    "quote_elevation": "金句升华",
    "cta": "互动引导",
    "signature": "惯用标语",
}

TITLE_PATTERNS = {
    "label": "关键词/人群标签式",
    "contrast": "冲突反差式",
    "question": "提问式",
    "suspense": "悬念式",
    "scene": "场景式",
    "experience": "经验分享式",
    "emotion": "情绪式",
    "emphasis": "强调式",
}

TITLE_DRIVERS = {
    "relevance": "与我有关",
    "utility": "对我有用",
    "curiosity": "引发好奇",
    "emotion": "挑动情绪",
    "voice_of_reader": "替我说话",
}

HUMAN_NATURE_TOKENS = [
    "赚钱",
    "成长",
    "焦虑",
    "安全",
    "关系",
    "爱",
    "归属",
    "尊重",
    "失业",
    "家庭",
    "婚姻",
    "身份",
    "自由",
    "机会",
    "翻身",
    "逆袭",
    "创业",
]

STORY_TOKENS = [
    "故事",
    "经历",
    "亲历",
    "失败",
    "低谷",
    "被裁",
    "辞职",
    "转型",
    "逆袭",
    "十年",
    "曾经",
    "后来",
]

TIMELY_TOKENS = [
    "最近",
    "今年",
    "这两年",
    "今天",
    "这周",
    "当下",
    "眼下",
    "最新",
    "热点",
]

PAIN_TOKENS = [
    "问题",
    "卡住",
    "焦虑",
    "不会",
    "失败",
    "风险",
    "困境",
    "难点",
    "麻烦",
    "吃亏",
    "亏钱",
]

AI_PHRASE_REPLACEMENTS = [
    (r"值得注意的是[，,]?", ""),
    (r"需要指出的是[，,]?", ""),
    (r"总的来说[，,]?", ""),
    (r"总而言之[，,]?", ""),
    (r"此外[，,]?", "还有，"),
    (r"与此同时[，,]?", "同时，"),
    (r"在[^，。]{0,12}背景下", "在这个语境里"),
    (r"不仅仅是", "不只是"),
    (r"不仅是", "不只是"),
    (r"从某种意义上说[，,]?", ""),
    (r"无缝、直观和强大", "更顺手"),
    (r"无缝、直观、强大", "更顺手"),
    (r"深入探讨", "分析"),
    (r"突出了", "写清了"),
    (r"关键作用", "作用"),
    (r"不断演变的", "变化中的"),
    (r"至关重要", "很关键"),
    (r"充满活力的", "有活力的"),
    (r"格局", "局面"),
    (r"证明", "体现"),
    (r"此外", "另外"),
]

AI_TRACE_RULES = [
    ("significance_inflation", "过度拔高意义", r"(划时代|革命性|颠覆性|标志着.*时代|证明了.*重要性)"),
    ("promotional_language", "宣传腔", r"(无缝|强大体验|极致体验|令人惊叹|风景如画|充满活力)"),
    ("vague_attribution", "模糊归因", r"(专家认为|业内人士认为|大家都知道|事实证明)"),
    ("formulaic_contrast", "套话反转", r"(不只是.+而是.+|不仅.+更.+)"),
    ("signposting", "提示性套话", r"(让我们来看看|下面我们将|你需要知道的是|先说结论)"),
    ("chatbot_artifact", "聊天机器人痕迹", r"(希望这能帮到你|如果你愿意我可以|让我知道你是否需要)"),
    ("filler_phrases", "填充短语", r"(由于这一事实|为了能够|从某种意义上说|需要指出的是|值得注意的是)"),
    ("generic_conclusion", "通用积极结尾", r"(未来可期|前景广阔|值得期待|一切才刚刚开始)"),
    ("em_dash_overuse", "破折号滥用", r"[—]{1,}"),
    ("excessive_hedging", "过度限定", r"(可能也许|或许可能|可以说是|某种程度上)"),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def dump_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def truncate_text(value: Any, limit: int) -> str:
    cleaned = clean_text(value)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(limit - 1, 0)].rstrip() + "…"


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", clean_text(text).lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "untitled"


def parse_markdown_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"root": []}
    current = "root"
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def markdown_title(text_or_path: str | Path) -> str:
    text = read_text(text_or_path) if isinstance(text_or_path, Path) else str(text_or_path)
    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return clean_text(match.group(1)) if match else ""


def markdown_h2_headings(text: str) -> list[str]:
    return [clean_text(item) for item in re.findall(r"^##\s+(.+)$", text, flags=re.MULTILINE)]


def split_paragraphs(text: str) -> list[str]:
    paragraphs = []
    for block in text.split("\n\n"):
        stripped = block.strip()
        if not stripped:
            continue
        paragraphs.append(stripped)
    return paragraphs


def markdown_body_paragraphs(text: str) -> list[str]:
    body: list[str] = []
    for block in split_paragraphs(text):
        stripped = block.strip()
        if not stripped:
            continue
        if stripped.startswith(("#", ">", "- ", "* ")):
            continue
        body.append(stripped)
    return body


def bullet_values(lines: list[str]) -> list[str]:
    values: list[str] = []
    for line in lines:
        stripped = line.strip()
        bullet = re.match(r"^[-*]\s*(.+)$", stripped)
        ordered = re.match(r"^\d+\.\s*(.+)$", stripped)
        if bullet and clean_text(bullet.group(1)):
            values.append(clean_text(bullet.group(1)))
        elif ordered and clean_text(ordered.group(1)):
            values.append(clean_text(ordered.group(1)))
    return values


def score_topic_material(
    *,
    topic: str,
    core_view: str = "",
    background: list[str] | None = None,
    arguments: list[str] | None = None,
    cases: list[str] | None = None,
    notes: list[str] | None = None,
    question: str = "",
) -> dict[str, Any]:
    background = background or []
    arguments = arguments or []
    cases = cases or []
    notes = notes or []
    merged_text = " ".join([topic, core_view, question, *background, *arguments, *cases, *notes])
    lowered = clean_text(merged_text)

    story_hits = sum(1 for token in STORY_TOKENS if token in lowered)
    long_term_hits = sum(1 for token in HUMAN_NATURE_TOKENS if token in lowered)
    timely_hits = sum(1 for token in TIMELY_TOKENS if token in lowered) + len(re.findall(r"20\d{2}", lowered))
    pain_hits = sum(1 for token in PAIN_TOKENS if token in lowered)
    evidence_hits = len(cases) * 2 + len(re.findall(r"\d+", lowered)) + len(re.findall(r"https?://", lowered))

    def clamp_score(value: int) -> int:
        return max(0, min(value, 100))

    story_potential = clamp_score(45 + story_hits * 11 + min(len(cases), 3) * 6)
    long_term_value = clamp_score(42 + long_term_hits * 8 + (8 if not timely_hits else 0))
    pain_point_strength = clamp_score(40 + pain_hits * 12 + (10 if len(arguments) == 1 else 0))
    timeliness = clamp_score(35 + timely_hits * 10 + (10 if "最近" in lowered or "当下" in lowered else 0))
    human_nature_fit = clamp_score(40 + long_term_hits * 10 + (8 if "读者" in lowered else 0))
    evidence_density = clamp_score(35 + evidence_hits * 4)

    total = round(
        (
            story_potential
            + long_term_value
            + pain_point_strength
            + timeliness
            + human_nature_fit
            + evidence_density
        )
        / 6
    )

    if total >= 75:
        recommendation = "recommended"
    elif total >= 60:
        recommendation = "revise_before_write"
    else:
        recommendation = "not_recommended"

    return {
        "story_potential": story_potential,
        "long_term_value": long_term_value,
        "pain_point_strength": pain_point_strength,
        "timeliness": timeliness,
        "human_nature_fit": human_nature_fit,
        "evidence_density": evidence_density,
        "total": total,
        "recommendation": recommendation,
    }


def choose_structure(
    *,
    topic: str,
    core_view: str,
    arguments: list[str],
    cases: list[str],
    background: list[str] | None = None,
) -> dict[str, str]:
    background = background or []
    joined = " ".join([topic, core_view, *arguments, *cases, *background])

    if any(token in joined for token in STORY_TOKENS) and cases:
        return {"type": "story", "reason": "题目和素材都带明显经历感，优先用故事结构承载观点。"}
    if re.search(r"\b(why|how|what)\b", joined, flags=re.I) or "为什么" in joined or "怎么" in joined:
        return {"type": "what_why_how", "reason": "命题自带解释和方法导向，适合 what-why-how。"}
    if len(arguments) >= 4:
        return {"type": "parallel", "reason": "存在多个并列论证点，适合总分结构展开。"}
    if len(arguments) == 1 and len(cases) >= 4:
        return {"type": "listicle", "reason": "信息点多且可拆条，适合清单式承载。"}
    if len(arguments) >= 2:
        return {"type": "progressive", "reason": "论证点可以逐层深入，适合递进式推进结论。"}
    return {"type": "parallel", "reason": "默认采用平行式，便于先稳定成稿再优化。"}


def sentence_fragments(text: str) -> list[str]:
    parts = re.split(r"[。！？!?]\s*", clean_text(text))
    return [part.strip("，,；; ") for part in parts if clean_text(part)]


def concise_claim(text: str) -> str:
    parts = sentence_fragments(text)
    return truncate_text(parts[0] if parts else clean_text(text), 44)


def build_opening_options(
    *,
    topic: str,
    reader_profile: str,
    pain_point: str,
    core_view: str,
    chosen_structure: str,
    cases: list[str],
) -> list[dict[str, str]]:
    core_claim = concise_claim(core_view or topic)
    case_line = truncate_text(cases[0], 56) if cases else ""
    reader_profile = reader_profile or "这类读者"
    pain_point = pain_point or "总觉得内容很重要，但写出来没人看"

    openings = [
        {
            "type": "relevance_utility",
            "label": OPENING_TYPES["relevance_utility"],
            "text": f"如果你是{reader_profile}，眼下最现实的问题往往不是不会努力，而是{pain_point}。这篇文章只回答一件事：{core_claim}。",
        },
        {
            "type": "direct_claim",
            "label": OPENING_TYPES["direct_claim"],
            "text": f"先把结论放在前面：{core_claim}。真正拉开差距的，从来不是表面动作，而是背后的结构。",
        },
        {
            "type": "pain_point",
            "label": OPENING_TYPES["pain_point"],
            "text": f"很多人已经很努力了，问题却还是没解。原因常常不在执行力，而在于{pain_point}。这也是为什么我想把{topic}说透。",
        },
        {
            "type": "summary",
            "label": OPENING_TYPES["summary"],
            "text": f"这篇文章会拆三件事：为什么{topic}现在值得写，问题到底卡在哪里，以及普通人能怎么把这套方法落地。",
        },
    ]

    if case_line:
        openings.append(
            {
                "type": "story",
                "label": OPENING_TYPES["story"],
                "text": f"先讲个片段：{case_line}。真正打动人的，不是这个故事本身，而是它把一个现实问题撕开给你看。",
            }
        )
    if chosen_structure in {"progressive", "what_why_how"}:
        openings.append(
            {
                "type": "suspense",
                "label": OPENING_TYPES["suspense"],
                "text": f"表面上看，{topic}像是在谈一个概念。可真正的问题是：为什么大家做了很多动作，结果还是没有起色？",
            }
        )

    return openings[:5]


def build_ending_options(
    *,
    topic: str,
    reader_profile: str,
    core_view: str,
) -> list[dict[str, str]]:
    claim = concise_claim(core_view or topic)
    reader_profile = reader_profile or "你"
    return [
        {
            "type": "summary",
            "label": ENDING_TYPES["summary"],
            "text": f"总结一下，{topic}真正重要的地方，不在表层技巧，而在你能不能把它变成稳定的判断、结构和动作。",
        },
        {
            "type": "restate_claim",
            "label": ENDING_TYPES["restate_claim"],
            "text": f"说到底，这篇文章只想留下一个判断：{claim}。",
        },
        {
            "type": "cta",
            "label": ENDING_TYPES["cta"],
            "text": f"如果你也是{reader_profile}，不妨回看一下自己的内容或项目：你现在卡住的，究竟是执行不够，还是结构没搭起来？",
        },
    ]


def detect_title_drivers(title: str) -> list[str]:
    drivers: list[str] = []
    if re.search(r"(你|普通人|中产|创始人|年轻人|创业者|一人公司|新手|读者)", title):
        drivers.append("relevance")
    if re.search(r"(如何|怎么|方法|清单|经验|指南|避免|搞懂|提升|增长)", title):
        drivers.append("utility")
    if re.search(r"(为什么|？|\?|居然|其实|真相|分水岭|突然|到底)", title):
        drivers.append("curiosity")
    if re.search(r"(焦虑|危险|致命|翻身|崩了|痛|失控|反而|别再)", title):
        drivers.append("emotion")
    if re.search(r"(不是.+而是|别再|其实|你以为|都在)", title):
        drivers.append("voice_of_reader")
    return drivers


def title_pattern_for(title: str) -> str:
    if re.search(r"(为什么|如何|怎么|？|\?)", title):
        return "question"
    if re.search(r"(不是.+而是|反而|分水岭|vs|和.+的区别)", title):
        return "contrast"
    if re.search(r"(别再|必须|一定|重磅|注意)", title):
        return "emphasis"
    if re.search(r"(故事|经历|十年|被裁|辞职|转型)", title):
        return "experience"
    if re.search(r"(今天|当下|场景|一次|那天|如果)", title):
        return "scene"
    if re.search(r"(真相|到底|居然|突然|你以为)", title):
        return "suspense"
    if re.search(r"(焦虑|翻身|致命|危险|愤怒)", title):
        return "emotion"
    return "label"


def score_title(title: str) -> float:
    score = 5.4
    drivers = detect_title_drivers(title)
    score += min(len(drivers), 4) * 0.65
    title_len = len(title)
    if title_len <= 20:
        score += 0.7
    elif title_len <= 26:
        score += 0.2
    else:
        score -= 0.5
    if re.search(r"(分析|研究报告|综合观察|方法论)", title):
        score -= 0.6
    if re.search(r"(为什么|如何|不是.+而是|分水岭|别再)", title):
        score += 0.5
    return round(max(0.0, min(score, 10.0)), 1)


def generate_title_options(
    *,
    topic: str,
    core_view: str,
    reader_profile: str,
    pain_point: str,
) -> list[dict[str, Any]]:
    reader = reader_profile or "普通人"
    pain = pain_point or "做了很多事却没结果"
    claim = concise_claim(core_view or topic)
    raw_titles = [
        f"{topic}：为什么{reader}最后还是得回到结构思维",
        f"你以为问题在执行，其实卡在{topic}",
        f"{reader}最容易忽略的，不是努力，而是{topic}",
        f"{topic}：真正的分水岭，不是会不会做，而是能不能稳",
        f"为什么很多人已经很努力了，还是会被{pain}卡住？",
        f"别再把{topic}写成空话了",
        f"{topic}不是技巧清单，而是一套结果系统",
        f"看懂{topic}，你才知道问题到底卡在哪",
        f"{reader}要补的，不只是动作，更是{topic}",
        f"{topic}这件事，为什么现在必须讲清楚",
        f"{topic}：把问题说透，比堆方法更重要",
        f"{reader}做不好这件事，不是因为不努力",
    ]
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for title in raw_titles:
        normalized = clean_text(title)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        pattern = title_pattern_for(normalized)
        drivers = detect_title_drivers(normalized)
        deduped.append(
            {
                "title": normalized,
                "pattern": pattern,
                "pattern_label": TITLE_PATTERNS[pattern],
                "drivers": drivers,
                "driver_labels": [TITLE_DRIVERS[item] for item in drivers],
                "length": len(normalized),
                "score": score_title(normalized),
            }
        )
    deduped.sort(key=lambda item: item["score"], reverse=True)
    return deduped[:10]


def build_share_copy_options(
    *,
    topic: str,
    core_view: str,
    reader_profile: str,
) -> list[str]:
    claim = concise_claim(core_view or topic)
    reader = reader_profile or "普通人"
    return [
        f"这篇把{topic}讲得很透，尤其适合{reader}回看。最认同的一句是：{claim}。",
        f"很多时候我们不是不努力，而是没把结构搭起来。这篇对{topic}的判断值得收藏。",
        f"看完会更清楚：真正决定结果的，不是表面动作，而是背后的系统。分享给也在卡这件事的人。",
    ]


def extract_highlight_quotes(
    *,
    topic: str,
    core_view: str,
    arguments: list[str],
) -> list[str]:
    quotes = []
    if core_view:
        quotes.append(concise_claim(core_view))
    for argument in arguments[:3]:
        normalized = argument.rstrip("。！？!?. ")
        quotes.append(f"{normalized}。")
    if not quotes:
        quotes.append(f"{topic}这件事，真正该补的不是表面动作，而是底层结构。")
    deduped: list[str] = []
    seen: set[str] = set()
    for item in quotes:
        normalized = clean_text(item)
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped[:4]


def derive_reader_profile(brief: dict[str, Any]) -> str:
    return clean_text(brief.get("target_reader") or brief.get("reader_profile") or "")


def derive_primary_pain_point(brief: dict[str, Any]) -> str:
    joined = " ".join([brief.get("core_view", ""), *brief.get("background", []), *brief.get("arguments", [])])
    sentences = sentence_fragments(joined)
    for sentence in sentences:
        if any(token in sentence for token in PAIN_TOKENS):
            return truncate_text(sentence, 60)
    return "已经投入很多精力，但结果始终不稳定"


def detect_ai_trace_patterns(text: str) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for key, label, pattern in AI_TRACE_RULES:
        matches = re.findall(pattern, text, flags=re.I)
        if matches:
            hits.append(
                {
                    "key": key,
                    "label": label,
                    "count": len(matches),
                    "samples": [truncate_text(match, 48) for match in matches[:3]],
                }
            )
    total_hits = sum(item["count"] for item in hits)
    if total_hits >= 9:
        risk = "high"
    elif total_hits >= 4:
        risk = "medium"
    else:
        risk = "low"
    return {"risk": risk, "total_hits": total_hits, "patterns": hits}


def _humanize_line(line: str) -> tuple[str, int]:
    changed = 0
    updated = line.replace("——", "，").replace("—", "，")
    if updated != line:
        changed += 1
    for pattern, replacement in AI_PHRASE_REPLACEMENTS:
        next_value = re.sub(pattern, replacement, updated)
        if next_value != updated:
            updated = next_value
            changed += 1
    updated = re.sub(r"(，\s*){2,}", "，", updated)
    updated = re.sub(r"\s{2,}", " ", updated)
    updated = re.sub(r"^，", "", updated)
    if updated != line and not updated.strip():
        updated = line
        changed = 0
    return updated, changed


def humanize_markdown(text: str, *, mode: str = "surgical") -> dict[str, Any]:
    lines = text.splitlines()
    output: list[str] = []
    changed_line_count = 0
    change_samples: list[dict[str, str]] = []

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith(("#", ">", "- ", "* ", "|")):
            output.append(raw)
            continue
        updated, changed = _humanize_line(raw)
        output.append(updated)
        if changed:
            changed_line_count += 1
            if len(change_samples) < 8:
                change_samples.append({"before": truncate_text(raw, 80), "after": truncate_text(updated, 80)})

    humanized = "\n".join(output).rstrip() + "\n"
    trace = detect_ai_trace_patterns(humanized)
    return {
        "text": humanized,
        "mode": mode,
        "changed_line_count": changed_line_count,
        "changes": change_samples,
        "ai_trace_risk": trace["risk"],
        "pattern_hits": trace["patterns"],
        "pattern_hit_count": trace["total_hits"],
    }


def evaluate_headline(title: str) -> tuple[float, list[str]]:
    issues: list[str] = []
    score = score_title(title)
    if len(title) > 22:
        issues.append("标题偏长，微信场景下前半句卖点不够集中。")
    drivers = detect_title_drivers(title)
    if "utility" not in drivers and "curiosity" not in drivers:
        issues.append("标题缺少明确收益或好奇钩子。")
    if re.search(r"(分析|研究报告|综合分析)", title):
        issues.append("标题偏像报告名，不像用户会点开的标题。")
        score = max(0.0, score - 0.8)
    return score, issues


def critique_article(markdown_text: str, *, chosen_structure: str) -> dict[str, Any]:
    title = markdown_title(markdown_text)
    headings = markdown_h2_headings(markdown_text)
    body_paragraphs = markdown_body_paragraphs(markdown_text)
    full_text = clean_text(markdown_text)
    title_score, title_issues = evaluate_headline(title)

    structure_score = 6.2 + min(len(headings), 6) * 0.45
    structure_issues: list[str] = []
    if "结论" not in headings:
        structure_score -= 1.2
        structure_issues.append("正文缺少明确结论，读者读完不容易留下一个判断。")
    if len(headings) < 4:
        structure_score -= 0.8
        structure_issues.append("章节数量偏少，论证推进还可以更清楚。")
    if chosen_structure == "parallel" and len(headings) < 5:
        structure_score -= 0.6
        structure_issues.append("平行结构下支撑段还不够完整。")

    evidence_signals = len(re.findall(r"\d{2,4}", full_text)) + len(re.findall(r"(案例|例如|比如|来自|根据)", full_text))
    evidence_score = 5.8 + min(evidence_signals, 8) * 0.5
    evidence_issues: list[str] = []
    if evidence_signals < 3:
        evidence_score -= 1.5
        evidence_issues.append("论证硬度偏弱，案例、数字或来源信号不够。")

    reader_value_signals = len(re.findall(r"(你|如果你|读者|怎么做|意味着|建议|提醒)", full_text))
    reader_value_score = 6.0 + min(reader_value_signals, 8) * 0.45
    reader_issues: list[str] = []
    if reader_value_signals < 3:
        reader_value_score -= 1.0
        reader_issues.append("读者收益还不够前置，容易写成作者自我表达。")

    avg_para_len = 0.0
    if body_paragraphs:
        avg_para_len = sum(len(item) for item in body_paragraphs) / len(body_paragraphs)
    pacing_score = 6.2
    pacing_issues: list[str] = []
    if avg_para_len > 180:
        pacing_score -= 1.0
        pacing_issues.append("段落偏长，阅读节奏容易拖慢。")
    if len(full_text) < 1400:
        pacing_score -= 0.8
        pacing_issues.append("篇幅偏短，展开还不够。")
    if len(full_text) > 5200:
        pacing_score -= 0.6
        pacing_issues.append("篇幅偏长，建议压缩重复表达。")
    pacing_score += 0.4 if 70 <= avg_para_len <= 150 else 0.0

    scores = {
        "headline_hook": round(max(0.0, min(title_score, 10.0)), 1),
        "structure_logic": round(max(0.0, min(structure_score, 10.0)), 1),
        "evidence_substance": round(max(0.0, min(evidence_score, 10.0)), 1),
        "reader_value": round(max(0.0, min(reader_value_score, 10.0)), 1),
        "pacing_length": round(max(0.0, min(pacing_score, 10.0)), 1),
    }
    issues = {
        "headline_hook": title_issues,
        "structure_logic": structure_issues,
        "evidence_substance": evidence_issues,
        "reader_value": reader_issues,
        "pacing_length": pacing_issues,
    }
    return {"scores": scores, "issues": issues}


def judge_article(
    markdown_text: str,
    *,
    critique: dict[str, Any],
    humanizer_report: dict[str, Any],
) -> dict[str, Any]:
    scores = critique["scores"]
    total = round(sum(scores.values()) / len(scores), 1)
    ai_trace_risk = humanizer_report.get("ai_trace_risk", "low")

    if ai_trace_risk == "high":
        total = round(max(0.0, total - 0.5), 1)
    elif ai_trace_risk == "low":
        total = round(min(10.0, total + 0.1), 1)

    ordered = sorted(scores.items(), key=lambda item: item[1])
    low_dimensions = [item[0] for item in ordered[:3]]
    unresolved = []
    for key in low_dimensions:
        unresolved.extend(critique["issues"].get(key, []))
    if ai_trace_risk == "high":
        unresolved.append("AI 痕迹仍然偏重，语言还不够像真实作者写的。")

    pass_gate = total >= 8.0 and ai_trace_risk != "high"
    return {
        "score": total,
        "scores": scores,
        "ai_trace_risk": ai_trace_risk,
        "pass": pass_gate,
        "low_dimensions": low_dimensions,
        "focus_areas": low_dimensions[:2],
        "unresolved_issues": unresolved[:6],
    }


def build_summary_points(arguments: list[str], core_view: str) -> list[str]:
    points = [concise_claim(core_view)] if core_view else []
    points.extend(truncate_text(item.rstrip("。！？!?. "), 38) for item in arguments[:3])
    deduped: list[str] = []
    seen: set[str] = set()
    for item in points:
        normalized = clean_text(item)
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped[:4]


def build_ending_cta(reader_profile: str, topic: str) -> str:
    reader = reader_profile or "你"
    return f"如果你也是{reader}，欢迎把这篇转给同样卡在 {topic} 上的人，顺手想一想：你现在最该补的是动作，还是结构？"


def article_sidecar_paths(workspace_root: Path, slug: str) -> dict[str, Path]:
    drafts_dir = workspace_root / "content-production" / "drafts"
    published_dir = workspace_root / "content-production" / "published"
    today = re.sub(r"[^\d]", "", clean_text(slug))  # unused fallback, overwritten by caller if needed
    return {
        "article": drafts_dir / f"{slug}-article.md",
        "writing_pack_md": drafts_dir / f"{slug}-writing-pack.md",
        "writing_pack_json": drafts_dir / f"{slug}-writing-pack.json",
        "review_trace": drafts_dir / f"{slug}-review-trace.json",
        "humanized": drafts_dir / f"{slug}-humanized.md",
        "humanizer_report": drafts_dir / f"{slug}-humanizer-report.json",
        "quality_gate": published_dir / f"{today or slug}-{slug}-quality-gate.md",
    }


def quality_gate_path(workspace_root: Path, *, date: str, slug: str) -> Path:
    return workspace_root / "content-production" / "published" / f"{date}-{slug}-quality-gate.md"


def build_quality_gate_notice(
    *,
    date: str,
    slug: str,
    topic: str,
    judge: dict[str, Any],
    article_path: Path,
    writing_pack_path: Path,
    review_trace_path: Path,
) -> str:
    issue_lines = judge.get("unresolved_issues") or ["当前版本仍需人工复核后再发。"]
    lines = [
        f"# 质量门控中断通知：{topic}",
        "",
        "## 结果",
        "",
        "- `run_status`：quality_gate_failed",
        "- `next_action`：user_review_required",
        f"- `score`：{judge['score']}",
        f"- `ai_trace_risk`：{judge['ai_trace_risk']}",
        "",
        "## 分项分数",
        "",
    ]
    for key, value in judge["scores"].items():
        lines.append(f"- `{key}`：{value}")
    lines.extend(
        [
            "",
            "## 当前最需要修的点",
            "",
            *[f"- {item}" for item in issue_lines[:3]],
            "",
            "## 相关文件",
            "",
            f"- 正文：{article_path}",
            f"- 写作包：{writing_pack_path}",
            f"- 审稿轨迹：{review_trace_path}",
            "",
            "## 说明",
            "",
            "- 已达到三轮上限，因此自动停止，不再继续跑配图和排版。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def load_writing_pack_json(article_path: Path) -> dict[str, Any]:
    slug = re.sub(r"-article$", "", article_path.stem)
    path = article_path.parent / f"{slug}-writing-pack.json"
    if not path.exists():
        return {}
    try:
        payload = load_json(path)
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def augment_markdown_with_writing_pack(markdown: str, writing_pack: dict[str, Any]) -> str:
    if not writing_pack:
        return markdown

    summary_points = [clean_text(item) for item in writing_pack.get("summary_points") or [] if clean_text(item)]
    highlight_quotes = [clean_text(item) for item in writing_pack.get("highlight_quotes") or [] if clean_text(item)]
    share_copy = [clean_text(item) for item in writing_pack.get("share_copy_options") or [] if clean_text(item)]
    ending_cta = clean_text(writing_pack.get("ending_cta"))

    sections: list[str] = []
    if summary_points:
        sections.extend(["## 阅读提要", "", *[f"- {item}" for item in summary_points], ""])
    if highlight_quotes:
        sections.extend(["## 金句高亮", "", *[f"> {item}" for item in highlight_quotes[:3]], ""])
    if share_copy:
        sections.extend(["## 转发配文", "", *[f"- {item}" for item in share_copy[:2]], ""])
    if ending_cta:
        sections.extend(["## 互动引导", "", ending_cta, ""])

    if not sections:
        return markdown
    return markdown.rstrip() + "\n\n" + "\n".join(sections).rstrip() + "\n"


def classify_opening_type(title: str, preview_text: str) -> str:
    text = clean_text(f"{title} {preview_text}")
    if re.search(r"(最近|热搜|又火了|刚刚|这两天)", text):
        return "news_event"
    if re.search(r"(为什么|先说结论|结论是|我认为)", text):
        return "direct_claim"
    if re.search(r"(故事|那一年|有个朋友|我曾经|后来)", text):
        return "story"
    if re.search(r"(焦虑|卡住|失败|怎么办|痛苦|困住)", text):
        return "pain_point"
    if re.search(r"(到底|居然|为什么会这样|你以为)", text):
        return "suspense"
    return "summary"


def classify_structure_type(title: str, headings: list[str], plain_text_length: int) -> str:
    joined = " ".join(headings)
    if re.search(r"(为什么|怎样|怎么|What|Why|How)", joined, flags=re.I):
        return "what_why_how"
    if len(headings) >= 4:
        return "parallel"
    if plain_text_length > 3200 and len(headings) <= 2:
        return "progressive"
    if re.search(r"(\d+个|\d+条|\d+种)", title):
        return "listicle"
    return "story" if re.search(r"(故事|经历|十年|后来)", title) else "unknown"


def classify_ending_type(title: str, summary: str) -> str:
    text = clean_text(f"{title} {summary}")
    if re.search(r"(你怎么看|欢迎留言|大家觉得呢)", text):
        return "cta"
    if re.search(r"(总结|最后|说到底)", text):
        return "summary"
    if re.search(r"(金句|一句话|别忘了)", text):
        return "quote_elevation"
    return "unknown"


def infer_reader_value_type(title: str, summary: str) -> str:
    text = clean_text(f"{title} {summary}")
    if re.search(r"(如何|方法|经验|清单|建议|步骤)", text):
        return "实用"
    if re.search(r"(焦虑|情绪|爱|关系|情感)", text):
        return "情绪"
    if re.search(r"(普通人|中产|创业者|年轻人|女性|男人)", text):
        return "身份表达"
    return "认知升级"


def infer_evidence_style(summary: str, plain_text_length: int) -> str:
    if re.search(r"\d", summary):
        return "数据/案例结合"
    if plain_text_length >= 3500:
        return "长论证"
    return "观点型"


def extract_share_hooks(title: str, summary: str) -> list[str]:
    hooks: list[str] = []
    if re.search(r"(为什么|如何|怎么)", title):
        hooks.append("问题钩子")
    if re.search(r"(不是.+而是|反而|分水岭)", title):
        hooks.append("反差钩子")
    if re.search(r"(普通人|中产|创业者|一人公司)", title):
        hooks.append("身份代入")
    if re.search(r"(焦虑|翻身|危险|致命)", title):
        hooks.append("情绪触发")
    if not hooks and summary:
        hooks.append("观点摘录")
    return hooks[:3]


def build_angle_pack(
    *,
    topic: str,
    summary: str,
    reader_hint: str = "",
    source_hint: str = "",
    evidence_gap: str = "",
) -> dict[str, Any]:
    score_payload = score_topic_material(topic=topic, core_view=summary, arguments=[summary], background=[source_hint])
    structure = choose_structure(topic=topic, core_view=summary, arguments=[summary], cases=[], background=[source_hint])
    pain_point = truncate_text(summary or "信息有了，但读者不知道为什么和自己有关", 50)
    openings = build_opening_options(
        topic=topic,
        reader_profile=reader_hint,
        pain_point=pain_point,
        core_view=summary,
        chosen_structure=structure["type"],
        cases=[],
    )
    titles = generate_title_options(
        topic=topic,
        core_view=summary,
        reader_profile=reader_hint,
        pain_point=pain_point,
    )
    primary_reader = clean_text(reader_hint) or "关注该议题但需要明确切口的公众号读者"
    evidence_gap_text = clean_text(evidence_gap) or "仍需补足更多数据、案例或来源来提高说服力。"
    title_angles = [item["title"] for item in titles[:3]]
    return {
        "writeworthiness_score": score_payload["total"],
        "topic_score": score_payload,
        "primary_reader": primary_reader,
        "reader_profile": primary_reader,
        "primary_pain_point": pain_point,
        "pain_point": pain_point,
        "recommended_structure": structure["type"],
        "recommended_structure_label": STRUCTURE_TYPES[structure["type"]],
        "recommended_opening_type": openings[0]["type"] if openings else "summary",
        "recommended_opening_label": OPENING_TYPES[openings[0]["type"]] if openings else OPENING_TYPES["summary"],
        "opening_options": openings,
        "title_angles": title_angles,
        "title_options": title_angles,
        "shareability_note": "优先把读者收益和身份代入写在标题前半句。",
        "evidence_gap": evidence_gap_text,
        "evidence_risks": [evidence_gap_text],
        "risk_note": "避免写成纯信息搬运或空泛趋势文。",
    }
