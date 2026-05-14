from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skill_runtime.writing_core import clean_text, slugify, write_text  # noqa: E402


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def simple_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw_frontmatter = text[4:end]
    body = text[end + 5 :]
    return parse_yaml_like(raw_frontmatter), body


def parse_yaml_like(block: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z0-9_-]+:\s*$", line):
            current_list_key = line[:-1].strip()
            result[current_list_key] = []
            continue
        if line.startswith("  - ") and current_list_key:
            result[current_list_key].append(line[4:].strip().strip("'\""))
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = coerce_scalar(value.strip())
            current_list_key = None
    return result


def coerce_scalar(value: str) -> Any:
    stripped = value.strip("'\"")
    if stripped.lower() in {"true", "false"}:
        return stripped.lower() == "true"
    if stripped.isdigit():
        return int(stripped)
    return stripped


def parse_sections(body: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"root": []}
    current = "root"
    for line in body.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def bullet_values(lines: list[str]) -> list[str]:
    values: list[str] = []
    for line in lines:
        stripped = clean_text(line)
        m = re.match(r"^[-*]\s*(.+)$", stripped)
        if m:
            values.append(clean_text(m.group(1)))
    return values


def positioning_dir(workspace_root: Path) -> Path:
    return workspace_root / "content-production" / "positioning"


def report_path(workspace_root: Path, slug: str) -> Path:
    return positioning_dir(workspace_root) / f"{slug}-positioning-report.md"


def pack_path(workspace_root: Path, slug: str) -> Path:
    return positioning_dir(workspace_root) / f"{slug}-positioning-pack.json"


def synthesize(frontmatter: dict[str, Any], sections: dict[str, list[str]]) -> dict[str, Any]:
    audience = clean_text(frontmatter.get("target_audience", "")) or first_nonempty(
        bullet_values(sections.get("Target Audience", []))
    )
    creator_background = bullet_values(sections.get("Creator Background", []))
    user_pains = bullet_values(sections.get("Audience Pains", []))
    goals = bullet_values(sections.get("Audience Goals", []))
    proof_assets = bullet_values(sections.get("Proof Assets", []))
    monetization = bullet_values(sections.get("Business Goal", []))
    constraints = bullet_values(sections.get("Constraints", []))
    benchmark_notes = bullet_values(sections.get("Benchmark Notes", []))

    topic_domain = clean_text(frontmatter.get("topic_domain", "AI content and workflows"))
    account_name = clean_text(frontmatter.get("account_name", "")) or "Alex Positioning Draft"
    core_pain = first_nonempty(user_pains) or "知道 AI 很重要，但不知道如何稳定落地到自己的内容和工作流"
    core_goal = first_nonempty(goals) or "用更低试错成本把 AI 真正接进内容生产"
    strongest_proof = first_nonempty(proof_assets) or first_nonempty(creator_background) or "具备一线实操经验"

    positioning_statement = (
        f"为{audience or '想做 AI 内容的人'}提供围绕{topic_domain}的可执行判断和工作流，"
        f"帮助他们解决“{core_pain}”，最终实现“{core_goal}”。"
    )

    content_pillars = build_pillars(topic_domain, user_pains, goals)
    differentiation = build_differentiation(strongest_proof, benchmark_notes, constraints)
    conversion_path = build_conversion_path(monetization)

    return {
        "account_name": account_name,
        "target_audience": audience or "AI 内容创作者 / 想把 AI 用进内容和工作的人",
        "topic_domain": topic_domain,
        "core_pain": core_pain,
        "core_goal": core_goal,
        "strongest_proof": strongest_proof,
        "positioning_statement": positioning_statement,
        "content_pillars": content_pillars,
        "differentiation": differentiation,
        "conversion_path": conversion_path,
        "constraints": constraints,
        "benchmark_notes": benchmark_notes,
        "timeliness": {
            "labels": ["Evergreen", "Verify-Now", "Legacy-2024"]
        },
    }


def first_nonempty(items: list[str]) -> str:
    for item in items:
        if clean_text(item):
            return clean_text(item)
    return ""


def build_pillars(topic_domain: str, pains: list[str], goals: list[str]) -> list[dict[str, str]]:
    defaults = [
        ("定位与策略", "帮读者先判断该做什么，不先掉进工具细节"),
        ("工作流与方法", "把 AI 变成可复用流程，而不是一次性灵感"),
        ("案例与复盘", "用真实样本证明为什么这样做有效"),
        ("工具与取舍", "讲清楚该用什么、为什么、什么时候不要用"),
    ]
    if "视频" in topic_domain or "口播" in topic_domain:
        defaults.append(("内容复用", "把长内容拆成短视频、口播和多平台版本"))
    if pains or goals:
        defaults.append(("读者痛点回应", f"持续围绕“{first_nonempty(pains) or first_nonempty(goals)}”给出解决路径"))
    return [{"pillar": name, "description": desc} for name, desc in defaults[:5]]


def build_differentiation(strongest_proof: str, benchmark_notes: list[str], constraints: list[str]) -> list[str]:
    items = [
        f"用“{strongest_proof}”而不是泛泛搬运，建立可信度。",
        "优先讲可执行判断和取舍，而不是百科式堆砌。",
        "把复杂 AI 主题翻译成普通创作者能直接照着做的路径。",
    ]
    if benchmark_notes:
        items.append(f"结合 benchmark 观察：{benchmark_notes[0]}")
    if constraints:
        items.append(f"明确边界，避免超出当前资源条件：{constraints[0]}")
    return items[:5]


def build_conversion_path(monetization: list[str]) -> list[str]:
    if not monetization:
        return [
            "内容建立信任",
            "引导进入更深的私域或持续关注",
            "逐步承接咨询、课程、社群或工具服务",
        ]
    return [
        "内容建立信任",
        f"围绕业务目标承接转化：{monetization[0]}",
        "根据反馈迭代定位和内容支柱",
    ]


def build_report(payload: dict[str, Any]) -> str:
    lines = [
        f"# Positioning Report | {payload['account_name']}",
        "",
        "## 1. One-Line Positioning",
        f"- {payload['positioning_statement']}",
        "",
        "## 2. Audience",
        f"- Target audience: {payload['target_audience']}",
        f"- Core pain: {payload['core_pain']}",
        f"- Desired outcome: {payload['core_goal']}",
        "",
        "## 3. Content Pillars",
    ]
    for item in payload["content_pillars"]:
        lines.append(f"- {item['pillar']}: {item['description']}")

    lines.extend(["", "## 4. Differentiation"])
    for item in payload["differentiation"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 5. Conversion Path"])
    for item in payload["conversion_path"]:
        lines.append(f"- {item}")

    if payload["constraints"]:
        lines.extend(["", "## 6. Constraints"])
        for item in payload["constraints"]:
            lines.append(f"- {item}")

    if payload["benchmark_notes"]:
        lines.extend(["", "## 7. Benchmark Notes"])
        for item in payload["benchmark_notes"][:5]:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 8. Alex Next Step",
            "- Use this positioning output to choose benchmark accounts and reject misaligned topics early.",
            "- Feed the account promise and pillars into topic-radar and content-brief-builder.",
            "",
        ]
    )
    return "\n".join(lines)


def build_pack(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill": "alex-account-positioning",
        "positioning": payload,
    }


def run(input_path: str) -> dict[str, str]:
    request_path = Path(input_path).resolve()
    frontmatter, body = simple_frontmatter(read_text(request_path))
    sections = parse_sections(body)
    synthesized = synthesize(frontmatter, sections)
    slug = slugify(frontmatter.get("account_name") or request_path.stem)

    outdir = positioning_dir(REPO_ROOT)
    outdir.mkdir(parents=True, exist_ok=True)
    report = report_path(REPO_ROOT, slug)
    pack = pack_path(REPO_ROOT, slug)
    write_text(report, build_report(synthesized))
    write_text(pack, json.dumps(build_pack(synthesized), ensure_ascii=False, indent=2))
    return {"report_path": str(report), "pack_path": str(pack)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Alex account positioning scaffold")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.input), ensure_ascii=False))
