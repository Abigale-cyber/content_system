from __future__ import annotations

import re
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from lxml import html


def fetch_html(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="ignore")


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or datetime.now().strftime("%Y%m%d-%H%M%S")


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def truncate_text(value: str, limit: int) -> str:
    cleaned = clean_text(value)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(limit - 1, 0)].rstrip() + "…"


def is_noise_line(text: str) -> bool:
    cleaned = clean_text(text)
    if not cleaned:
        return True
    if len(cleaned) < 8:
        return True
    noise_patterns = [
        r"^撰文[｜|]",
        r"^编辑[｜|]",
        r"^图源[:：；]",
        r"^图源",
        r"^官方公众号[:：]",
        r"^官方视频号[:：]",
        r"^官方小红书[:：]",
        r"^官方网站[:：]",
        r"^官方邮箱[:：]",
        r"^咨询信息[:：]",
        r"^联络方式[:：]?",
        r"^图\d*$",
        r"^微信扫一扫",
    ]
    return any(re.search(pattern, cleaned) for pattern in noise_patterns)


def first_non_empty(values: list[str]) -> str:
    for value in values:
        cleaned = clean_text(value)
        if cleaned:
            return cleaned
    return ""


def extract_meta_text(tree: html.HtmlElement, *xpaths: str) -> str:
    for xpath in xpaths:
        values = tree.xpath(xpath)
        if not values:
            continue
        if isinstance(values[0], str):
            return first_non_empty([str(item) for item in values])
        return first_non_empty([item.text_content() for item in values])
    return ""


def extract_publish_date(raw_html: str) -> str:
    ct_match = re.search(r'\bct\s*=\s*"?(?P<ts>\d{10})"?', raw_html)
    if ct_match:
        return datetime.fromtimestamp(int(ct_match.group("ts"))).strftime("%Y%m%d")
    date_match = re.search(r"(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})", raw_html)
    if date_match:
        year, month, day = date_match.groups()
        return f"{year}{int(month):02d}{int(day):02d}"
    return datetime.now().strftime("%Y%m%d")


def extract_article(raw_html: str, source_url: str) -> dict[str, Any]:
    if "The content has been deleted by the author." in raw_html:
        raise RuntimeError("公众号原文已被作者删除，无法采集。")
    if "内容已被发布者删除" in raw_html:
        raise RuntimeError("公众号原文已被发布者删除，无法采集。")

    tree = html.fromstring(raw_html)
    title = extract_meta_text(
        tree,
        '//meta[@property="og:title"]/@content',
        '//meta[@name="twitter:title"]/@content',
        '//h1[@id="activity-name"]',
        "//title/text()",
    )
    author = extract_meta_text(
        tree,
        '//meta[@name="author"]/@content',
        '//*[@id="js_name"]/text()',
        '//*[contains(@class,"account_nickname")]/text()',
    )

    paragraphs: list[str] = []
    nodes = tree.xpath(
        '//*[@id="js_content"]//*[self::p or self::blockquote or self::h2 or self::h3 or self::li]'
        '[not(descendant::*[self::p or self::blockquote or self::h2 or self::h3 or self::li])]'
    )
    if not nodes:
        nodes = tree.xpath(
            "//article//*[self::p or self::blockquote or self::h2 or self::h3 or self::li]"
            "[not(descendant::*[self::p or self::blockquote or self::h2 or self::h3 or self::li])]"
        )
    for node in nodes:
        text = clean_text(node.text_content())
        if is_noise_line(text):
            continue
        if text in paragraphs:
            continue
        paragraphs.append(text)

    headings = [item for item in paragraphs if 8 <= len(item) <= 36][:5]
    body_paragraphs = [item for item in paragraphs if item not in headings and len(item) >= 28]
    summary_paragraphs = body_paragraphs[:4] or paragraphs[:4]
    publish_date = extract_publish_date(raw_html)
    topic = title or f"公众号文章采集-{publish_date}"
    slug = slugify(topic)
    if not title and not summary_paragraphs:
        raise RuntimeError("未识别到公众号正文，可能是反爬页或非文章详情页。")
    return {
        "title": topic,
        "slug": slug,
        "author": author,
        "publish_date": publish_date,
        "headings": headings[:3],
        "paragraphs": summary_paragraphs,
        "source_url": source_url,
    }


def infer_arguments(article: dict[str, Any]) -> list[str]:
    headings = [clean_text(item) for item in article.get("headings", []) if clean_text(item)]
    if headings:
        return headings[:3]
    paragraphs = [clean_text(item) for item in article.get("paragraphs", []) if clean_text(item)]
    fallback = [truncate_text(item, 34) for item in paragraphs[:3]]
    if fallback:
        return fallback
    return [
        "这篇公众号文章在讨论什么问题",
        "作者给出的核心判断是什么",
        "哪些案例或论据值得再创作复用",
    ]


def build_brief_markdown(article: dict[str, Any]) -> str:
    paragraphs = [clean_text(item) for item in article.get("paragraphs", []) if clean_text(item)]
    core_view = "\n".join(paragraphs[:2]) if paragraphs else "这是一篇从公众号文章采集后生成的再创作 brief。"
    background = [truncate_text(item, 80) for item in paragraphs[1:4]] or [truncate_text(core_view, 80)]
    arguments = infer_arguments(article)
    materials = [
        f"来源链接：{article['source_url']}",
        f"来源公众号/作者：{article.get('author') or '未识别'}",
    ]
    materials.extend(truncate_text(item, 90) for item in paragraphs[:3])

    lines = [
        f"# 阶段 2 采集 Brief：{article['title']}",
        "",
        "## 基础信息",
        "",
        f"- `date`：{article['publish_date']}",
        f"- `slug`：{article['slug']}",
        f"- `topic`：{article['title']}",
        "- `target_reader`：关注原文主题、希望将公众号素材加工为可发布观点文章的读者",
        f"- `publish_goal`：基于公众号素材再创作一篇适合公众号发布的观点型长文，保留原文有价值的信息点，但不直接照抄原文",
        "",
        "## 核心观点",
        "",
        core_view,
        "",
        "## 背景与语境",
        "",
        *[f"- {item}" for item in background[:4]],
        "",
        "## 论证方向",
        "",
        *[f"{index}. {item}" for index, item in enumerate(arguments[:3], start=1)],
        "",
        "## 可用案例 / 素材",
        "",
        *[f"- {item}" for item in materials[:5]],
        "",
        "## 明确不要写什么",
        "",
        "- 不要直接复刻原公众号原文结构或句子。",
        "- 不要保留明显的公众号套话、标题党和营销腔。",
        "- 不要把未核实的事实当作确定结论输出。",
        "",
        "## 风格要求",
        "",
        "- 提炼观点，重组结构，保留信息密度。",
        "- 语言清晰，适合后续进入公众号再创作链。",
        "- 重点突出原文中最值得复用的判断、案例和线索。",
        "",
        "## 配图方向",
        "",
        f"- 围绕主题“{article['title']}”生成概念图或信息图。",
        "- 优先做公众号头图或关键信息提炼图。",
        "",
    ]
    return "\n".join(lines)


def collect_article_to_brief(url: str, *, inbox_dir: Path, archive_dir: Path) -> dict[str, Any]:
    raw_html = fetch_html(url)
    article = extract_article(raw_html, url)

    inbox_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    brief_path = inbox_dir / f"{article['publish_date']}-{article['slug']}-gzh-brief.md"
    archive_path = archive_dir / f"{article['publish_date']}-{article['slug']}.html"

    brief_path.write_text(build_brief_markdown(article) + "\n", encoding="utf-8")
    archive_path.write_text(raw_html, encoding="utf-8")

    return {
        "brief_path": brief_path,
        "archive_path": archive_path,
        "slug": article["slug"],
        "title": article["title"],
        "author": article.get("author", ""),
        "source_url": url,
        "publish_date": article["publish_date"],
    }
