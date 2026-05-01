#!/usr/bin/env python3
"""Prepare a fused builders + latest-news digest for the ai-dalaba skill."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


SKILL_DIR = Path(__file__).resolve().parents[1]
BUILDERS_SCRIPT = SKILL_DIR / "runtime" / "builders" / "scripts" / "prepare-digest.js"
LATEST_SCRIPT = SKILL_DIR / "runtime" / "latest" / "scripts" / "fetch_news.py"
USER_DIR = Path.home() / ".ai-dalaba"
LEGACY_USER_DIR = Path.home() / ".follow-builders"
CONFIG_PATH = USER_DIR / "config.json"
LEGACY_CONFIG_PATH = LEGACY_USER_DIR / "config.json"
DEFAULT_LATEST_SOURCES = [
    "hackernews",
    "github",
    "producthunt",
    "huggingface",
    "ai_newsletters",
]
DEFAULT_CONFIG = {
    "platform": "openclaw",
    "language": "zh",
    "timezone": "Asia/Shanghai",
    "frequency": "daily",
    "deliveryTime": "09:30",
    "delivery": {"method": "stdout"},
    "onboardingComplete": True,
}
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "into",
    "over",
    "about",
    "your",
    "this",
    "that",
    "will",
    "just",
    "today",
    "latest",
    "news",
    "daily",
    "openai",
    "anthropic",
    "google",
    "github",
    "hacker",
    "product",
    "hunt",
    "paper",
    "agent",
    "agents",
    "model",
    "models",
    "build",
    "builder",
    "builders",
    "using",
    "launches",
}
SOURCE_PRIORITY = {
    "Hacker News": 120,
    "GitHub Trending": 115,
    "Product Hunt": 105,
    "Hugging Face Papers": 100,
    "Ben's Bites": 95,
    "Interconnects": 94,
    "One Useful Thing": 93,
    "ChinAI": 92,
    "Memia": 91,
    "AI to ROI": 90,
    "KDnuggets": 89,
}

# User interest keywords: heavy boost for topics the user cares about
USER_INTEREST_KEYWORDS = {
    # OPC / OpenClaw ecosystem (highest priority)
    "openclaw": 60, "opc": 60, "open claw": 60,
    # AI coding tools
    "claude code": 55, "codex": 50, "cursor": 50, "copilot": 45,
    "vibe coding": 55, "ai coding": 50, "code agent": 50,
    # AI Agent platforms
    "ai agent": 50, "agent framework": 45, "mcp": 45, "digital employee": 50,
    # AI self-media / content creation
    "ai自媒体": 55, "ai创作者": 55, "ai内容": 50, "ai写作": 50,
    "content creation": 45, "ai writing": 45, "自媒体": 45,
    # Key AI companies/products
    "anthropic": 45, "deepseek": 45, "openai": 35, "gemini": 35,
    "claude": 40, "gpt": 30, "llama": 30,
    # Feishu / Lark
    "feishu": 45, "飞书": 45, "lark": 40,
    # Hot AI topics
    "rag": 35, "sora": 35, "agent": 30, "llm": 25,
    "prompt": 25, "fine-tun": 25, "reasoning": 25,
}


def user_interest_boost(title: str, summary: str) -> float:
    """Calculate boost score based on user interest keywords."""
    text = (title + " " + (summary or "")).lower()
    boost = 0.0
    for keyword, weight in USER_INTEREST_KEYWORDS.items():
        if keyword in text:
            boost += weight
    return min(boost, 120)  # cap at 120 to avoid extreme distortion


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()
    return value


def truncate(value: str | None, limit: int) -> str:
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def safe_json_loads(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse JSON output: {exc}") from exc


def run_json_command(cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 180) -> tuple[Any, str]:
    completed = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    stderr = clean_text(completed.stderr)
    stdout = completed.stdout.strip()
    if completed.returncode != 0 and not stdout:
        raise RuntimeError(stderr or f"Command failed: {' '.join(cmd)}")
    if not stdout:
        raise RuntimeError(f"Command returned no stdout: {' '.join(cmd)}")
    return safe_json_loads(stdout), stderr


def ensure_config() -> tuple[dict[str, Any], dict[str, Any] | None]:
    USER_DIR.mkdir(parents=True, exist_ok=True)
    migrated = None
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    elif LEGACY_CONFIG_PATH.exists():
        legacy = json.loads(LEGACY_CONFIG_PATH.read_text(encoding="utf-8"))
        config = {**DEFAULT_CONFIG, **legacy}
        migrated = {"from": str(LEGACY_CONFIG_PATH), "to": str(CONFIG_PATH)}
        CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        config = dict(DEFAULT_CONFIG)
        CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return config, migrated


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = clean_text(value)
    if not text:
        return None

    if text in {"Today", "Real-time", "Recent", "Hot"}:
        return now_utc() - timedelta(hours=4)

    relative_match = re.search(r"(\d+)\s+(minute|minutes|hour|hours|day|days)", text, re.I)
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2).lower()
        if "minute" in unit:
            return now_utc() - timedelta(minutes=amount)
        if "hour" in unit:
            return now_utc() - timedelta(hours=amount)
        if "day" in unit:
            return now_utc() - timedelta(days=amount)

    normalized = text.replace("Z", "+00:00")
    for parser in (
        lambda s: datetime.fromisoformat(s),
        lambda s: datetime.strptime(s, "%Y-%m-%d"),
        lambda s: datetime.strptime(s, "%Y/%m/%d"),
    ):
        try:
            parsed = parser(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def recency_bonus(date_value: datetime | None) -> float:
    if not date_value:
        return 8.0
    age_hours = max((now_utc() - date_value).total_seconds() / 3600.0, 0.0)
    if age_hours <= 12:
        return 28.0
    if age_hours <= 24:
        return 22.0
    if age_hours <= 48:
        return 16.0
    if age_hours <= 96:
        return 10.0
    return 4.0


def parse_heat_value(value: str | int | float | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_text(str(value))
    if not text:
        return 0.0
    numbers = re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))
    if not numbers:
        return 0.0
    base = float(numbers[0])
    lower = text.lower()
    if "k" in lower:
        base *= 1000
    if "m" in lower:
        base *= 1_000_000
    if "万" in text:
        base *= 10_000
    return base


def canonical_url(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")
    if host == "twitter.com":
        host = "x.com"
    path = parsed.path.rstrip("/")
    query_pairs = []
    if host == "news.ycombinator.com":
        query_pairs = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k == "id"]
    return urlunparse((parsed.scheme or "https", host, path, "", urlencode(query_pairs), ""))


def normalize_title(value: str | None) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def key_terms(value: str | None) -> set[str]:
    text = normalize_title(value)
    return {token for token in text.split() if len(token) >= 3 and token not in STOPWORDS}


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def signature(item: dict[str, Any]) -> dict[str, Any]:
    urls = set()
    for candidate in (item.get("url"), item.get("discussionUrl"), item.get("hnUrl"), item.get("githubUrl")):
        canonical = canonical_url(candidate)
        if canonical:
            urls.add(canonical)
    title_norm = normalize_title(item.get("title"))
    return {
        "urls": urls,
        "title": title_norm,
        "terms": key_terms(item.get("title")),
    }


def is_duplicate(candidate: dict[str, Any], existing_items: list[dict[str, Any]]) -> bool:
    candidate_sig = signature(candidate)
    for item in existing_items:
        existing_sig = signature(item)
        if candidate_sig["urls"] & existing_sig["urls"]:
            return True
        if similarity(candidate_sig["title"], existing_sig["title"]) >= 0.88:
            return True
        overlap = candidate_sig["terms"] & existing_sig["terms"]
        union = candidate_sig["terms"] | existing_sig["terms"]
        if overlap and union and len(overlap) >= 3 and len(overlap) / len(union) >= 0.6:
            return True
    return False


def title_case_from_text(text: str, prefix: str) -> str:
    cleaned = truncate(text, 88)
    if not cleaned:
        return prefix
    return f"{prefix}{cleaned}"


def format_heat(*parts: str) -> str:
    values = [clean_text(part) for part in parts if clean_text(part)]
    return " | ".join(values)


def derive_builder_items(raw: dict[str, Any], max_items: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for builder in raw.get("x", []):
        name = clean_text(builder.get("name"))
        handle = clean_text(builder.get("handle"))
        bio = truncate(builder.get("bio"), 240)
        for tweet in builder.get("tweets", []):
            text = clean_text(tweet.get("text"))
            if not text:
                continue
            created_at = parse_datetime(tweet.get("createdAt"))
            likes = int(tweet.get("likes") or 0)
            retweets = int(tweet.get("retweets") or 0)
            replies = int(tweet.get("replies") or 0)
            engagement = likes + (retweets * 2) + (replies * 2.5)
            score = 58 + recency_bonus(created_at) + min(math.log10(engagement + 1) * 18, 24) + user_interest_boost(text, bio)
            if text.startswith("@"):
                score -= 12
            candidates.append(
                {
                    "kind": "builders",
                    "bucket": "x",
                    "source": "X",
                    "sourceName": name or handle or "Builder",
                    "actor": name or handle or "Builder",
                    "handle": handle,
                    "title": title_case_from_text(text, f"{name or handle}: "),
                    "summaryHint": truncate(text, 320),
                    "contextHint": bio,
                    "publishedAt": created_at.isoformat() if created_at else None,
                    "time": tweet.get("createdAt") or "Unknown Time",
                    "heat": format_heat(
                        f"{likes} likes" if likes else "",
                        f"{retweets} reposts" if retweets else "",
                        f"{replies} replies" if replies else "",
                    ),
                    "url": tweet.get("url"),
                    "score": round(score, 2),
                }
            )

    for blog in raw.get("blogs", []):
        published_at = parse_datetime(blog.get("publishedAt"))
        score = 82 + recency_bonus(published_at)
        candidates.append(
            {
                "kind": "builders",
                "bucket": "blog",
                "source": "Official Blog",
                "sourceName": clean_text(blog.get("name")) or "Official Blog",
                "actor": clean_text(blog.get("name")) or "Official Blog",
                "title": clean_text(blog.get("title")) or "Untitled blog update",
                "summaryHint": truncate(blog.get("description") or blog.get("content"), 360),
                "contextHint": truncate(blog.get("content"), 420),
                "publishedAt": published_at.isoformat() if published_at else None,
                "time": blog.get("publishedAt") or "Unknown Time",
                "heat": "",
                "url": blog.get("url"),
                "score": round(score, 2),
            }
        )

    for episode in raw.get("podcasts", []):
        published_at = parse_datetime(episode.get("publishedAt"))
        transcript = re.sub(r"Speaker\s+\d+\s+\|\s+\d+:\d+\s*-\s*\d+:\d+\s*", "", episode.get("transcript") or "")
        score = 78 + recency_bonus(published_at)
        candidates.append(
            {
                "kind": "builders",
                "bucket": "podcast",
                "source": "Podcast",
                "sourceName": clean_text(episode.get("name")) or "Podcast",
                "actor": clean_text(episode.get("name")) or "Podcast",
                "title": clean_text(episode.get("title")) or "Untitled episode",
                "summaryHint": truncate(transcript or episode.get("summary"), 360),
                "contextHint": truncate(transcript, 480),
                "publishedAt": published_at.isoformat() if published_at else None,
                "time": episode.get("publishedAt") or "Unknown Time",
                "heat": "",
                "url": episode.get("url"),
                "score": round(score, 2),
            }
        )

    buckets: dict[str, list[dict[str, Any]]] = {"blog": [], "podcast": [], "x": []}
    for item in candidates:
        buckets[item["bucket"]].append(item)
    for bucket_items in buckets.values():
        bucket_items.sort(key=lambda item: item["score"], reverse=True)

    selected: list[dict[str, Any]] = []
    used_titles: set[str] = set()
    for bucket_name in ("blog", "podcast", "x"):
        for item in buckets[bucket_name]:
            title_key = normalize_title(item.get("title"))
            if title_key and title_key in used_titles:
                continue
            selected.append(item)
            if title_key:
                used_titles.add(title_key)
            break

    remaining = sorted(candidates, key=lambda item: item["score"], reverse=True)
    for item in remaining:
        if len(selected) >= max_items:
            break
        if item in selected:
            continue
        if is_duplicate(item, selected):
            continue
        selected.append(item)

    return sorted(selected[:max_items], key=lambda item: item["score"], reverse=True)


def derive_latest_items(raw_items: list[dict[str, Any]], max_items: int, builders_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    candidates: list[dict[str, Any]] = []
    deduped = 0

    for item in raw_items:
        source = clean_text(item.get("source")) or "Latest News"
        title = clean_text(item.get("title"))
        if not title:
            continue
        if is_duplicate(item, builders_items) or is_duplicate(item, candidates):
            deduped += 1
            continue
        published_at = parse_datetime(item.get("time"))
        heat_value = parse_heat_value(item.get("heat"))
        score = SOURCE_PRIORITY.get(source, 88) + recency_bonus(published_at) + min(math.log10(heat_value + 1) * 16, 26) + user_interest_boost(title, item.get("summary") or "")
        candidates.append(
            {
                "kind": "latest",
                "source": source,
                "sourceName": source,
                "title": title,
                "summaryHint": truncate(item.get("summary") or item.get("content"), 320),
                "contextHint": truncate(item.get("content"), 420),
                "publishedAt": published_at.isoformat() if published_at else None,
                "time": item.get("time") or "Unknown Time",
                "heat": clean_text(str(item.get("heat") or "")),
                "url": item.get("url"),
                "discussionUrl": item.get("hn_url"),
                "githubUrl": item.get("github"),
                "score": round(score, 2),
            }
        )

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates[:max_items], deduped


def top_terms(items: list[dict[str, Any]], limit: int = 8) -> list[str]:
    counter: Counter[str] = Counter()
    for item in items:
        counter.update(key_terms(item.get("title")))
    return [term for term, _ in counter.most_common(limit)]


def load_builders() -> tuple[dict[str, Any], str]:
    env = os.environ.copy()
    env["AI_DALABA_USER_DIR"] = str(USER_DIR)
    env["AI_DALABA_CONFIG_PATH"] = str(CONFIG_PATH)
    return run_json_command(["node", str(BUILDERS_SCRIPT)], env=env, timeout=150)


def load_latest(per_source_limit: int, sources: list[str]) -> tuple[list[dict[str, Any]], str]:
    cmd = [
        sys.executable,
        str(LATEST_SCRIPT),
        "--source",
        ",".join(sources),
        "--limit",
        str(per_source_limit),
        "--no-save",
    ]
    return run_json_command(cmd, timeout=220)


def build_output(max_builders: int, max_latest: int, per_source_limit: int, sources: list[str]) -> dict[str, Any]:
    config, migrated = ensure_config()
    errors: list[str] = []
    builders_raw: dict[str, Any] = {}
    latest_raw: list[dict[str, Any]] = []
    builders_stderr = ""
    latest_stderr = ""

    try:
        builders_raw, builders_stderr = load_builders()
    except Exception as exc:
        errors.append(f"builders fetch failed: {exc}")

    try:
        latest_raw, latest_stderr = load_latest(per_source_limit, sources)
    except Exception as exc:
        errors.append(f"latest fetch failed: {exc}")

    builders_items = derive_builder_items(builders_raw, max_builders) if builders_raw else []
    latest_items, latest_deduped = derive_latest_items(latest_raw, max_latest, builders_items) if latest_raw else ([], 0)

    status = "ok"
    if errors:
        status = "partial" if (builders_items or latest_items) else "error"

    today = datetime.now().strftime("%Y-%m-%d")
    output = {
        "status": status,
        "generatedAt": now_utc().isoformat(),
        "title": f"📣 AI大喇叭 | 今日 AI 融合速报（{today}）",
        "config": {
            "language": config.get("language", "zh"),
            "timezone": config.get("timezone", "Asia/Shanghai"),
            "frequency": config.get("frequency", "daily"),
            "deliveryTime": config.get("deliveryTime", "09:30"),
            "delivery": config.get("delivery", {"method": "stdout"}),
        },
        "builders": builders_items,
        "latest": latest_items,
        "editorialSignals": {
            "focusTerms": top_terms(builders_items + latest_items),
            "buildersFirst": True,
            "latestSources": sources,
            "dedupeRule": "Builders section wins. Latest section only supplements non-overlapping items.",
        },
        "presentation": {
            "buildersExpandedCount": 5,
            "latestExpandedCount": 5,
            "expandedStyle": "Front 5 items in each section should be fully expanded.",
            "compactStyle": "Any remaining items after the first 5 in each section should be rendered as short briefs.",
        },
        "counts": {
            "buildersCandidates": len(builders_items),
            "latestCandidates": len(latest_items),
            "latestDeduped": latest_deduped,
        },
        "notes": {
            "migration": migrated,
            "buildersWarnings": builders_raw.get("errors") if isinstance(builders_raw, dict) else None,
            "buildersStderr": builders_stderr or None,
            "latestStderr": latest_stderr or None,
        },
        "errors": errors or None,
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare ai-dalaba fused digest JSON.")
    parser.add_argument("--max-builders", type=int, default=10)
    parser.add_argument("--max-latest", type=int, default=10)
    parser.add_argument("--limit-per-source", type=int, default=4)
    parser.add_argument("--latest-sources", default=",".join(DEFAULT_LATEST_SOURCES))
    args = parser.parse_args()

    sources = [source.strip() for source in args.latest_sources.split(",") if source.strip()]
    output = build_output(args.max_builders, args.max_latest, args.limit_per_source, sources)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
