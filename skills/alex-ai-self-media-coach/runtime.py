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


def route_dir(workspace_root: Path) -> Path:
    return workspace_root / "content-production" / "routes"


def report_path(workspace_root: Path, slug: str) -> Path:
    return route_dir(workspace_root) / f"{slug}-route-report.md"


def pack_path(workspace_root: Path, slug: str) -> Path:
    return route_dir(workspace_root) / f"{slug}-route-pack.json"


def choose_route(frontmatter: dict[str, Any], body: str) -> dict[str, Any]:
    text = clean_text(" ".join([json.dumps(frontmatter, ensure_ascii=False), body]))
    text_lower = text.lower()

    rules = [
        (
            "alex-account-positioning",
            "positioning",
            [
                r"账号定位", r"定位", r"人群", r"赛道", r"方向", r"差异化", r"我适合做什么", r"定位一下", r"做什么号", r"适合我",
                r"positioning", r"audience", r"differentiation",
            ],
            ["alex-benchmark-research", "alex-title-lab", "topic-radar"],
            "The request is missing or refining account-level strategy, so positioning should come first.",
        ),
        (
            "alex-benchmark-research",
            "benchmark",
            [
                r"对标", r"拆账号", r"拆一下", r"拆一下这个博主", r"拆博主", r"竞品", r"benchmark", r"栏目结构",
                r"叙事套路", r"选题密度", r"账号结构",
            ],
            ["alex-title-lab", "topic-radar", "content-brief-builder"],
            "The request is about learning from another account's structure and content patterns.",
        ),
        (
            "alex-title-lab",
            "title",
            [
                r"标题", r"headline", r"爆款标题", r"为什么能火", r"为什么能点开", r"a/b", r"ab 测试",
                r"包装一下标题", r"改标题",
            ],
            ["topic-radar", "content-brief-builder"],
            "The current blocker is packaging or analyzing headlines rather than writing the full piece.",
        ),
        (
            "topic-radar",
            "topic",
            [
                r"选题", r"热点", r"值不值得写", r"这个题怎么写", r"topic", r"hotspot", r"角度",
            ],
            ["content-brief-builder", "case-writer-hybrid"],
            "The request needs topic judgment or angle selection before brief creation.",
        ),
        (
            "content-brief-builder",
            "brief",
            [
                r"brief", r"整理 brief", r"先别写", r"先定方向再写", r"结构化一下", r"先整理",
            ],
            ["case-writer-hybrid", "adversarial-content-review"],
            "The user wants structure and direction locked before drafting.",
        ),
        (
            "case-writer-hybrid",
            "draft",
            [
                r"写成文章", r"写一篇", r"起草", r"正文", r"draft", r"文章初稿", r"写公众号",
            ],
            ["adversarial-content-review", "script-writer-short", "wechat-formatter"],
            "The user is ready for article drafting.",
        ),
        (
            "adversarial-content-review",
            "review",
            [
                r"审稿", r"review", r"把关", r"能不能发", r"发前看一下", r"质量",
            ],
            ["script-writer-short", "wechat-formatter", "wechat-draft-publisher"],
            "The draft exists and needs independent review before distribution.",
        ),
        (
            "script-writer-short",
            "repurpose",
            [
                r"口播", r"短视频", r"改成脚本", r"视频号", r"reels", r"短脚本",
            ],
            ["wechat-formatter", "wechat-draft-publisher"],
            "The user wants a short oral version of an existing idea or article.",
        ),
        (
            "wechat-formatter",
            "format",
            [
                r"排版", r"公众号 html", r"wechat html", r"格式化", r"html 预览",
            ],
            ["wechat-draft-publisher"],
            "The request is already at the formatting stage.",
        ),
        (
            "wechat-draft-publisher",
            "publish",
            [
                r"发草稿箱", r"推到公众号", r"发布", r"草稿箱", r"draft publisher",
            ],
            [],
            "The request is already at the publishing stage.",
        ),
    ]

    matches: list[dict[str, Any]] = []
    for skill_id, stage, patterns, downstream, reason in rules:
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                matches.append(
                    {
                        "primary_skill": skill_id,
                        "stage": stage,
                        "downstream_chain": downstream,
                        "reason": reason,
                        "timeliness": infer_timeliness(text_lower),
                    }
                )
                break

    if matches:
        stage_order = {
            "positioning": 0,
            "benchmark": 1,
            "title": 2,
            "topic": 3,
            "brief": 4,
            "draft": 5,
            "review": 6,
            "repurpose": 7,
            "format": 8,
            "publish": 9,
        }
        matches.sort(key=lambda item: stage_order.get(item["stage"], 99))
        return matches[0]

    return {
        "primary_skill": "alex-account-positioning",
        "stage": "positioning",
        "downstream_chain": ["alex-benchmark-research", "alex-title-lab", "topic-radar"],
        "reason": "The request is broad or ambiguous, so Alex should start by clarifying positioning before downstream execution.",
        "timeliness": infer_timeliness(text_lower),
    }


def infer_timeliness(text_lower: str) -> dict[str, list[str]]:
    verify_signals = []
    legacy_signals = []
    if any(token in text_lower for token in ["2024", "旧版", "老教程", "gpt-3.5", "旧模型", "plus", "插件", "coze", "bot"]):
        verify_signals.append("The request references time-sensitive tools, models, pricing, or platform workflows.")
    if any(token in text_lower for token in ["2024", "旧版", "老教程", "gpt-3.5", "chatgpt-on-wechat"]):
        legacy_signals.append("Some source material appears tied to the 2024 ecosystem and should be treated as historical context.")
    return {
        "evergreen": ["Strategy, audience, positioning, benchmark logic, and title psychology are usually durable."],
        "verify_now": verify_signals,
        "legacy_2024": legacy_signals,
    }


def build_report(frontmatter: dict[str, Any], route: dict[str, Any]) -> str:
    lines = [
        "# Alex Route Report",
        "",
        "## 1. Next Skill",
        f"- Primary skill: {route['primary_skill']}",
        f"- Stage: {route['stage']}",
        "",
        "## 2. Why This Route",
        f"- {route['reason']}",
        "",
        "## 3. Recommended Chain",
    ]
    if route["downstream_chain"]:
        for item in route["downstream_chain"]:
            lines.append(f"- {item}")
    else:
        lines.append("- No mandatory downstream step. This may already be the last stage.")

    lines.extend(["", "## 4. Timeliness"])
    lines.append("### Evergreen")
    for item in route["timeliness"]["evergreen"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### Verify-Now")
    if route["timeliness"]["verify_now"]:
        for item in route["timeliness"]["verify_now"]:
            lines.append(f"- {item}")
    else:
        lines.append("- No immediate time-sensitive warning detected.")
    lines.append("")
    lines.append("### Legacy-2024")
    if route["timeliness"]["legacy_2024"]:
        for item in route["timeliness"]["legacy_2024"]:
            lines.append(f"- {item}")
    else:
        lines.append("- No explicit legacy-2024 signal detected.")

    lines.extend(
        [
            "",
            "## 5. Alex Coach Note",
            "- Prefer fixing the earliest missing step in the workflow rather than polishing downstream assets too early.",
            "",
        ]
    )
    return "\n".join(lines)


def build_pack(frontmatter: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill": "alex-ai-self-media-coach",
        "request": frontmatter,
        "route": route,
    }


def run(input_path: str) -> dict[str, str]:
    request_path = Path(input_path).resolve()
    frontmatter, body = simple_frontmatter(read_text(request_path))
    route = choose_route(frontmatter, body)
    slug = slugify(frontmatter.get("topic") or frontmatter.get("account_name") or request_path.stem)

    outdir = route_dir(REPO_ROOT)
    outdir.mkdir(parents=True, exist_ok=True)
    report = report_path(REPO_ROOT, slug)
    pack = pack_path(REPO_ROOT, slug)
    write_text(report, build_report(frontmatter, route))
    write_text(pack, json.dumps(build_pack(frontmatter, route), ensure_ascii=False, indent=2))
    return {"report_path": str(report), "pack_path": str(pack)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Alex self-media coach router")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.input), ensure_ascii=False))
