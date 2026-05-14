#!/usr/bin/env python3
"""One-click daily push: fetch top sources, format Top5, push to Feishu."""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "oc_5957da1b76ad64aa9b037eebb2899999")

SOURCES = "hackernews,github,36kr,wallstreetcn,producthunt"
FETCH_LIMIT = 10

# Weight per source: normalize so no single source dominates ranking
SOURCE_WEIGHT = {
    "Hacker News": 100, "GitHub": 100, "36氪": 100,
    "华尔街见闻": 100, "Product Hunt": 100, "微博热搜": 10,
    "腾讯新闻": 80, "V2EX": 80, "Hugging Face": 120,
}

AI_KEYWORDS = [
    "ai", "llm", "gpt", "claude", "agent", "openai", "anthropic",
    "deepseek", "model", "llama", "gemini", "copilot", "cursor",
    "claude code", "openclaw", "codex", "rag", "sora", "midjourney",
    "transformer", "diffusion", "mcp", "vibe coding",
]

# High-priority keywords: OPC/AI creator/OpenClaw ecosystem topics get extra boost
PRIORITY_KEYWORDS = [
    "opc", "openclaw", "claude code", "ai自媒体", "ai创作者", "ai内容",
    "ai写作", "内容创作", "digital employee", "数字员工", "agent平台",
    "ai coding", "ai工具", "ai agent", "lark", "feishu", "飞书",
    "workspace", "skill", "hermes", "codex", "prompt",
]

TECH_KEYWORDS = [
    "github", "open source", "release", "launch", "startup",
    "programming", "developer", "rust", "python", "typescript",
    "framework", "api", "cloud", "deploy", "docker",
]


def normalize_heat(heat_str: str, source: str) -> float:
    """Normalize heat value to 0-100 scale per source."""
    if not heat_str:
        return 30  # default for items without heat
    m = re.search(r"[\d.]+", str(heat_str))
    if not m:
        return 30
    val = float(m.group())
    if "万" in str(heat_str):
        val *= 10000
    # Normalize by source
    src = source or ""
    if "微博" in src:
        return min(100, val / 50000)  # 50万→100
    elif src == "Hacker News":
        return min(100, val / 5)      # 500 points→100
    elif src == "GitHub":
        return min(100, val / 50)     # 5000 stars→100
    elif "华尔街" in src:
        return min(100, val / 100)
    else:
        return min(100, val / 10)


def compute_score(item: dict) -> float:
    """Compute overall relevance score for an item."""
    source = item.get("source", "")
    heat = item.get("heat", "")
    title = (item.get("title") or "").lower()
    summary = (item.get("summary") or "").lower()
    text = title + " " + summary

    base = normalize_heat(heat, source)

    # AI boost
    ai_hits = sum(1 for kw in AI_KEYWORDS if kw in text)
    ai_boost = ai_hits * 25

    # Priority topic boost (OPC/AI creator/OpenClaw ecosystem)
    priority_hits = sum(1 for kw in PRIORITY_KEYWORDS if kw in text)
    priority_boost = priority_hits * 40  # higher weight than general AI

    # Tech boost
    tech_hits = sum(1 for kw in TECH_KEYWORDS if kw in text)
    tech_boost = tech_hits * 10

    return base + ai_boost + priority_boost + tech_boost


def fetch_news() -> list:
    """Run fetch_news.py and return parsed JSON."""
    cmd = [
        sys.executable, str(SCRIPT_DIR / "fetch_news.py"),
        "--source", SOURCES,
        "--limit", str(FETCH_LIMIT),
        "--no-save",
    ]
    print(f"Fetching from: {SOURCES}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"Fetch error: {result.stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Failed to parse fetch output", file=sys.stderr)
        return []


def format_top5(items: list) -> str:
    """Select top 5 items and format as Feishu-ready Markdown."""
    scored = [(compute_score(item), item) for item in items]
    scored.sort(key=lambda x: x[0], reverse=True)

    top5 = scored[:5]
    total = len(items)
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [f"**每日热点 Top5 | {today}**", ""]

    source_names = {
        "Hacker News": "HN", "GitHub": "GitHub", "36氪": "36氪",
        "华尔街见闻": "华尔街见闻", "微博热搜": "微博", "Product Hunt": "PH",
        "腾讯新闻": "腾讯", "V2EX": "V2EX", "Hugging Face": "HF",
    }

    max_score = top5[0][0] if top5 else 1
    for i, (sc, item) in enumerate(top5, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        source = source_names.get(item.get("source", ""), item.get("source", ""))
        heat = item.get("heat", "")
        summary = item.get("summary", "")

        rank_score = min(10, max(1, round(sc / max(max_score, 1) * 10)))

        title_md = f"[{title}]({url})" if url else title
        lines.append(f"**{i}. [{rank_score}分] {title_md}**")
        lines.append(f"{source} | {heat}")
        if summary:
            lines.append(f"> {summary[:80]}")
        lines.append("")

    lines.append(f"📊 今日收录 {total} 条")
    return "\n".join(lines)


def push_to_feishu(content: str, dry_run: bool = False) -> bool:
    """Push formatted content to Feishu via lark-cli."""
    if dry_run:
        print(f"[DRY RUN] Would send {len(content)} chars to chat {CHAT_ID}")
        print(f"--- Preview ---\n{content}")
        return True

    cmd = [
        "npx", "@larksuite/cli", "im", "+messages-send",
        "--chat-id", CHAT_ID,
        "--as", "bot",
        "--markdown", content,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"Pushed to Feishu chat {CHAT_ID}", file=sys.stderr)
            return True
        else:
            print(f"Push failed: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Push error: {e}", file=sys.stderr)
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Daily AI news Top5 push to Feishu")
    parser.add_argument("--dry-run", action="store_true", help="Preview without pushing")
    parser.add_argument("--save", action="store_true", help="Save report locally")
    args = parser.parse_args()

    items = fetch_news()
    if not items:
        print("No items fetched, aborting", file=sys.stderr)
        sys.exit(1)

    content = format_top5(items)

    if args.save:
        today = datetime.now().strftime("%Y-%m-%d")
        report_dir = SKILL_DIR / "reports" / today
        report_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%H%M")
        report_file = report_dir / f"feishu_top5_{ts}.md"
        report_file.write_text(content, encoding="utf-8")
        print(f"Saved to {report_file}", file=sys.stderr)

    success = push_to_feishu(content, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
