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

from skill_runtime.writing_core import slugify, write_text


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
    frontmatter = parse_yaml_like(raw_frontmatter)
    return frontmatter, body


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
            value = line[4:].strip().strip("'\"")
            result[current_list_key].append(value)
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


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in reader]


def load_samples(request_path: Path, frontmatter: dict[str, Any], body: str) -> list[dict[str, str]]:
    sample_file = frontmatter.get("sample_file")
    if sample_file:
        sample_path = (request_path.parent / sample_file).resolve()
        if sample_path.suffix.lower() == ".csv":
            return load_csv(sample_path)
        if sample_path.suffix.lower() in {".md", ".markdown"}:
            return parse_markdown_table(read_text(sample_path))
        raise ValueError(f"Unsupported sample_file type: {sample_path.suffix}")
    return parse_markdown_table(body)


def parse_date(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def summarize(samples: list[dict[str, str]]) -> dict[str, Any]:
    topic_counter = Counter(item.get("topic_cluster", "unclassified") or "unclassified" for item in samples)
    format_counter = Counter(item.get("format_type", "unknown") or "unknown" for item in samples)
    hook_counter = Counter(item.get("hook_type", "unknown") or "unknown" for item in samples)
    narrative_counter = Counter(item.get("narrative_pattern", "unknown") or "unknown" for item in samples)

    publish_dates = [parsed for item in samples if (parsed := parse_date(item.get("publish_date", "")))]
    latest = max(publish_dates).date().isoformat() if publish_dates else ""
    earliest = min(publish_dates).date().isoformat() if publish_dates else ""

    return {
        "sample_count": len(samples),
        "topic_clusters": topic_counter.most_common(),
        "format_types": format_counter.most_common(),
        "hook_types": hook_counter.most_common(),
        "narrative_patterns": narrative_counter.most_common(),
        "date_range": {"earliest": earliest, "latest": latest},
    }


def benchmark_dir(workspace_root: Path) -> Path:
    return workspace_root / "content-production" / "benchmarks"


def report_path(workspace_root: Path, slug: str) -> Path:
    return benchmark_dir(workspace_root) / f"{slug}-benchmark-report.md"


def pack_path(workspace_root: Path, slug: str) -> Path:
    return benchmark_dir(workspace_root) / f"{slug}-benchmark-pack.json"


def build_report(frontmatter: dict[str, Any], summary: dict[str, Any]) -> str:
    focus = frontmatter.get("focus", [])
    if not isinstance(focus, list):
        focus = [str(focus)] if focus else []

    lines = [
        f"# Benchmark Report | {frontmatter.get('account_name', 'Unknown Account')}",
        "",
        "## 1. Snapshot",
        f"- Platform: {frontmatter.get('platform', 'unknown')}",
        f"- Account: {frontmatter.get('account_name', 'unknown')}",
        f"- Analysis window: {frontmatter.get('analysis_window_days', 90)} days",
        f"- Sample count: {summary['sample_count']}",
        f"- Focus: {', '.join(focus) if focus else 'account structure, columns, narrative, topic density'}",
        "",
        "## 2. Initial Read",
        "- Expand this starter report using references/report-template.md.",
        "- Tag concrete platform/tool/model claims as Verify-Now unless freshly confirmed.",
        "",
        "## 3. Sample Overview",
        f"- Earliest sample: {summary['date_range']['earliest'] or 'n/a'}",
        f"- Latest sample: {summary['date_range']['latest'] or 'n/a'}",
        "",
        "## 4. Topic Cluster Snapshot",
    ]

    for topic, count in summary["topic_clusters"][:10]:
        lines.append(f"- {topic}: {count}")

    lines.extend(["", "## 5. Format Snapshot"])
    for format_type, count in summary["format_types"][:10]:
        lines.append(f"- {format_type}: {count}")

    lines.extend(["", "## 6. Hook Snapshot"])
    for hook_type, count in summary["hook_types"][:10]:
        lines.append(f"- {hook_type}: {count}")

    lines.extend(["", "## 7. Narrative Snapshot"])
    for pattern, count in summary["narrative_patterns"][:10]:
        lines.append(f"- {pattern}: {count}")

    lines.extend(
        [
            "",
            "## 8. Next Step",
            "- Expand into full Alex benchmark output: positioning, pillars, columns, patterns, topic density, borrow/adapt/avoid.",
            "",
        ]
    )
    return "\n".join(lines)


def build_pack(frontmatter: dict[str, Any], samples: list[dict[str, str]], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill": "alex-benchmark-research",
        "request": frontmatter,
        "summary": summary,
        "timeliness": {
            "default_window_days": frontmatter.get("analysis_window_days", 90),
            "downrank_after_days": 180,
            "labels": ["Evergreen", "Verify-Now", "Legacy-2024"],
        },
        "samples": samples,
        "analysis": {
            "account_positioning": [],
            "content_pillars": [],
            "recurring_columns": [],
            "narrative_patterns": [],
            "topic_density": [],
            "borrow_adapt_avoid": {"borrow": [], "adapt": [], "avoid": []},
        },
    }


def run(input_path: str) -> dict[str, str]:
    request_path = Path(input_path).resolve()
    workspace_root = REPO_ROOT
    frontmatter, body = simple_frontmatter(read_text(request_path))
    slug = slugify(frontmatter.get("account_name") or request_path.stem)
    samples = load_samples(request_path, frontmatter, body)
    summary = summarize(samples)

    outdir = benchmark_dir(workspace_root)
    outdir.mkdir(parents=True, exist_ok=True)

    report = report_path(workspace_root, slug)
    pack = pack_path(workspace_root, slug)

    write_text(report, build_report(frontmatter, summary))
    write_text(pack, json.dumps(build_pack(frontmatter, samples, summary), ensure_ascii=False, indent=2))

    return {"report_path": str(report), "pack_path": str(pack)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Alex benchmark research scaffold")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.input), ensure_ascii=False))
