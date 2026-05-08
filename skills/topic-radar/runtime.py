from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from skill_runtime.writing_core import clean_text, slugify, truncate_text


FORMULAS = [
    "痛点 + 工具 + 具体结果",
    "误解 + 反转 + 证明",
    "低效动作 + AI 替代 + 效果对比",
]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def markdown_title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    if match:
        return clean_text(match.group(1))
    for line in text.splitlines():
        cleaned = clean_text(line)
        if cleaned:
            return cleaned
    return fallback


def topic_radar_md_path(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "content-production" / "topics" / f"{slug}-topic-radar.md"


def topic_radar_json_path(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "content-production" / "topics" / f"{slug}-topic-radar.json"


def score_dimension(source: str, keywords: list[str], *, base: int = 3) -> int:
    score = base
    lowered = source.lower()
    for keyword in keywords:
        if keyword.lower() in lowered:
            score += 1
    return max(1, min(5, score))


def four_dimension_scores(topic: str, text: str, angle: str) -> dict[str, int]:
    merged = clean_text(" ".join([topic, text, angle]))
    return {
        "热爱程度": score_dimension(merged, ["我想", "想写", "长期", "持续", "创作者", "个人"]),
        "专业能力": score_dimension(merged, ["案例", "经验", "流程", "方法", "判断", "系统"]),
        "市场需求": score_dimension(merged, ["读者", "痛点", "热点", "不会", "卡住", "效率", "团队"]),
        "资源积累": score_dimension(merged, ["案例", "数据", "来源", "素材", "notion", "asana", "rakuten", "飞书"]),
    }


def choose_formula(text: str, index: int) -> str:
    merged = clean_text(text).lower()
    if any(token in merged for token in ["误解", "不是", "其实", "噱头", "以为"]):
        preferred = "误解 + 反转 + 证明"
    elif any(token in merged for token in ["效率", "替代", "自动", "agent", "ai"]):
        preferred = "低效动作 + AI 替代 + 效果对比"
    elif any(token in merged for token in ["痛点", "卡住", "怎么", "如何"]):
        preferred = "痛点 + 工具 + 具体结果"
    else:
        preferred = FORMULAS[index % len(FORMULAS)]
    ordered = [preferred, *[item for item in FORMULAS if item != preferred]]
    return ordered[index % len(ordered)]


def choose_structure(topic: str, text: str, formula: str) -> str:
    merged = clean_text(" ".join([topic, text]))
    if "对比" in merged or "不是" in merged or "误解" in formula:
        return "对比式"
    if "怎么" in merged or "如何" in merged or "具体结果" in formula:
        return "教学类"
    if "案例" in merged or "故事" in merged:
        return "故事类"
    if any(token in merged for token in ["热点", "发布", "进入", "趋势"]):
        return "热点类"
    return "观点类"


def infer_timeliness(text: str) -> str:
    if re.search(r"(今天|昨天|刚刚|发布|进入|热搜|热点|更新)", text):
        return "48h 内"
    if re.search(r"(趋势|正在|开始|越来越)", text):
        return "7 天内"
    return "常青"


def extract_materials(text: str) -> list[str]:
    materials: list[str] = []
    material_match = re.search(r"(?:可用素材|素材|案例)[：:]\s*(?P<body>.+)", text)
    if material_match:
        parts = re.split(r"[、,，；;。]", material_match.group("body"))
        materials.extend(clean_text(part) for part in parts if clean_text(part))
    for line in text.splitlines():
        cleaned = clean_text(line).removeprefix("- ").strip()
        if any(token in cleaned for token in ["案例", "来源", "Notion", "Asana", "飞书", "数据"]):
            materials.append(cleaned)
    deduped: list[str] = []
    for item in materials:
        if item and item not in deduped:
            deduped.append(item)
    return deduped[:5]


def build_angle(topic: str, text: str, index: int) -> dict[str, Any]:
    formulas = {
        0: f"别只复述“{topic}”，真正值得写的是它解决了谁的什么卡点",
        1: f"很多人以为“{topic}”只是新工具发布，其实它在改变团队协作的责任边界",
        2: f"把“{topic}”写成普通团队的判断清单：什么时候该追，什么时候该观望",
    }
    angle = formulas.get(index, f"从目标读者的实际决策场景重写“{topic}”")
    formula = choose_formula(" ".join([text, angle]), index)
    structure = choose_structure(topic, text, formula)
    fit_scores = four_dimension_scores(topic, text, angle)
    total = sum(fit_scores.values())
    title_directions = [
        truncate_text(angle.replace("“", "").replace("”", ""), 28),
        f"{topic}，普通人真正该看的不是热闹",
        f"别把{topic}只写成一条新闻",
    ]
    materials = extract_materials(text)
    evidence_gap = "素材基础够用，写作前仍建议补一条可验证数据。"
    if len(materials) < 2:
        evidence_gap = "素材偏少，至少再补 2 条案例、数据或一手来源。"
    return {
        "angle": angle,
        "formula": formula,
        "recommended_structure": structure,
        "timeliness": infer_timeliness(" ".join([topic, text])),
        "fit_scores": fit_scores,
        "total_score": total,
        "title_directions": title_directions,
        "materials": materials,
        "evidence_gap": evidence_gap,
    }


def build_report(*, topic: str, slug: str, source_path: Path, angles: list[dict[str, Any]], recommended: dict[str, Any]) -> str:
    lines = [
        f"# 选题雷达：{topic}",
        "",
        f"- `slug`：{slug}",
        f"- `source`：{source_path}",
        f"- `recommended_angle`：{recommended['angle']}",
        f"- `recommended_score`：{recommended['total_score']}",
        "",
        "## 候选切口",
        "",
    ]
    for index, item in enumerate(angles, start=1):
        scores = "，".join(f"{key} {value}/5" for key, value in item["fit_scores"].items())
        lines.extend(
            [
                f"### {index}. {item['angle']}",
                "",
                f"- `formula`：{item['formula']}",
                f"- `recommended_structure`：{item['recommended_structure']}",
                f"- `timeliness`：{item['timeliness']}",
                f"- `fit_scores`：{scores}",
                f"- `evidence_gap`：{item['evidence_gap']}",
                "- `title_directions`：",
                *[f"  - {title}" for title in item["title_directions"]],
                "",
            ]
        )
    lines.extend(["## 下一步", "", "- 选择推荐切口后，把本报告或单个切口交给 `content-brief-builder` 生成 brief。"])
    return "\n".join(lines).rstrip() + "\n"


def run_topic_radar(input_path: Path, *, workspace_root: Path) -> dict[str, Any]:
    text = input_path.read_text(encoding="utf-8")
    topic = markdown_title(text, input_path.stem)
    slug = slugify(topic)
    angles = [build_angle(topic, text, index) for index in range(3)]
    angles.sort(key=lambda item: item["total_score"], reverse=True)
    recommended = angles[0]
    report_path = topic_radar_md_path(workspace_root, slug)
    json_path = topic_radar_json_path(workspace_root, slug)
    payload = {
        "slug": slug,
        "topic": topic,
        "source_path": str(input_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "recommended_angle": recommended,
        "angles": angles,
    }
    write_text(report_path, build_report(topic=topic, slug=slug, source_path=input_path, angles=angles, recommended=recommended))
    write_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2))
    return {
        "slug": slug,
        "topic": topic,
        "report_path": report_path,
        "radar_json_path": json_path,
        "recommended_angle": recommended,
        "angle_count": len(angles),
        "run_status": "completed",
    }
