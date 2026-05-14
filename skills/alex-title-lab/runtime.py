from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skill_runtime.writing_core import (  # noqa: E402
    clean_text,
    detect_title_drivers,
    generate_title_options,
    infer_reader_value_type,
    score_title,
    slugify,
    title_pattern_for,
    write_text,
)


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


def parse_markdown_table(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []
    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows


def parse_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in reader]


def load_title_samples(request_path: Path, frontmatter: dict[str, Any], body: str) -> list[dict[str, str]]:
    sample_file = frontmatter.get("sample_file")
    if sample_file:
        sample_path = (request_path.parent / sample_file).resolve()
        if sample_path.suffix.lower() == ".csv":
            return parse_csv(sample_path)
        if sample_path.suffix.lower() in {".md", ".markdown"}:
            return parse_markdown_table(read_text(sample_path))
        raise ValueError(f"Unsupported sample_file type: {sample_path.suffix}")
    return parse_markdown_table(body)


def analyze_titles(samples: list[dict[str, str]]) -> dict[str, Any]:
    analyzed: list[dict[str, Any]] = []
    pattern_counter: Counter[str] = Counter()
    driver_counter: Counter[str] = Counter()
    reader_value_counter: Counter[str] = Counter()
    hook_counter: Counter[str] = Counter()

    for row in samples:
        title = clean_text(row.get("title", ""))
        if not title:
            continue
        pattern = title_pattern_for(title)
        drivers = detect_title_drivers(title)
        value_type = infer_reader_value_type(title, row.get("summary", ""))
        score = score_title(title)
        hook_family = infer_hook_family(title)

        analyzed.append(
            {
                **row,
                "title": title,
                "pattern": pattern,
                "drivers": drivers,
                "reader_value_type": value_type,
                "hook_family": hook_family,
                "title_score": round(score, 1),
            }
        )
        pattern_counter[pattern] += 1
        reader_value_counter[value_type] += 1
        hook_counter[hook_family] += 1
        for driver in drivers:
            driver_counter[driver] += 1

    top_titles = sorted(analyzed, key=lambda item: item["title_score"], reverse=True)
    return {
        "sample_count": len(analyzed),
        "pattern_counts": pattern_counter.most_common(),
        "driver_counts": driver_counter.most_common(),
        "reader_value_counts": reader_value_counter.most_common(),
        "hook_counts": hook_counter.most_common(),
        "top_titles": top_titles[:10],
        "all_titles": analyzed,
    }


def infer_hook_family(title: str) -> str:
    text = clean_text(title)
    if re.search(r"(为什么|如何|怎么|到底)", text):
        return "question"
    if re.search(r"(不是.+而是|反而|居然|分水岭)", text):
        return "contrast"
    if re.search(r"(\d+个|\d+条|\d+种)", text):
        return "numbered"
    if re.search(r"(焦虑|翻身|致命|危险|崩溃)", text):
        return "emotion"
    if re.search(r"(普通人|创业者|打工人|博主|一人公司)", text):
        return "identity"
    return "direct"


def generate_variants(frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    topic = clean_text(frontmatter.get("topic", ""))
    core_view = clean_text(frontmatter.get("core_view", "")) or topic
    reader_profile = clean_text(frontmatter.get("reader_profile", ""))
    pain_point = clean_text(frontmatter.get("pain_point", "")) or "内容有价值，但标题还不够让人点开"
    if not topic:
        topic = core_view or "Alex 标题实验"
    return generate_title_options(
        topic=topic,
        core_view=core_view,
        reader_profile=reader_profile,
        pain_point=pain_point,
    )


def titles_dir(workspace_root: Path) -> Path:
    return workspace_root / "content-production" / "titles"


def report_path(workspace_root: Path, slug: str) -> Path:
    return titles_dir(workspace_root) / f"{slug}-title-report.md"


def pack_path(workspace_root: Path, slug: str) -> Path:
    return titles_dir(workspace_root) / f"{slug}-title-pack.json"


def build_report(frontmatter: dict[str, Any], analysis: dict[str, Any], variants: list[dict[str, Any]]) -> str:
    lines = [
        f"# Title Report | {frontmatter.get('topic') or frontmatter.get('account_name') or 'Untitled'}",
        "",
        "## 1. Snapshot",
        f"- Topic: {frontmatter.get('topic', 'unknown')}",
        f"- Reader profile: {frontmatter.get('reader_profile', 'unknown')}",
        f"- Sample count: {analysis['sample_count']}",
        "",
        "## 2. Dominant Title Patterns",
    ]

    for name, count in analysis["pattern_counts"][:8]:
        lines.append(f"- {name}: {count}")

    lines.extend(["", "## 3. Dominant Drivers"])
    for name, count in analysis["driver_counts"][:8]:
        lines.append(f"- {name}: {count}")

    lines.extend(["", "## 4. Hook Families"])
    for name, count in analysis["hook_counts"][:8]:
        lines.append(f"- {name}: {count}")

    lines.extend(["", "## 5. Top Sample Titles"])
    for item in analysis["top_titles"][:5]:
        lines.append(f"- {item['title']} | score={item['title_score']} | pattern={item['pattern']}")

    lines.extend(["", "## 6. Alex Candidate Variants"])
    for item in variants[:8]:
        lines.append(f"- {item['title']}")

    lines.extend(
        [
            "",
            "## 7. Alex Guidance",
            "- Borrow the strongest click triggers, but translate them into Alex's positioning rather than copying surface wording.",
            "- Treat trend-heavy and time-bound wording as Verify-Now.",
            "- Use the strongest two or three variants as inputs for brief writing or headline A/B testing.",
            "",
        ]
    )
    return "\n".join(lines)


def build_pack(frontmatter: dict[str, Any], analysis: dict[str, Any], variants: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill": "alex-title-lab",
        "request": frontmatter,
        "analysis": analysis,
        "generated_variants": variants,
        "timeliness": {
            "labels": ["Evergreen", "Verify-Now", "Legacy-2024"]
        },
    }


def run(input_path: str) -> dict[str, str]:
    request_path = Path(input_path).resolve()
    workspace_root = REPO_ROOT
    frontmatter, body = simple_frontmatter(read_text(request_path))
    slug = slugify(frontmatter.get("topic") or frontmatter.get("account_name") or request_path.stem)
    samples = load_title_samples(request_path, frontmatter, body)
    analysis = analyze_titles(samples)
    variants = generate_variants(frontmatter)

    outdir = titles_dir(workspace_root)
    outdir.mkdir(parents=True, exist_ok=True)
    report = report_path(workspace_root, slug)
    pack = pack_path(workspace_root, slug)

    write_text(report, build_report(frontmatter, analysis, variants))
    write_text(pack, json.dumps(build_pack(frontmatter, analysis, variants), ensure_ascii=False, indent=2))
    return {"report_path": str(report), "pack_path": str(pack)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Alex title analysis and generation scaffold")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.input), ensure_ascii=False))
