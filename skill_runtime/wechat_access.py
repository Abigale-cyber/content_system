from __future__ import annotations

import html
import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


WECHAT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def truncate_text(value: Any, limit: int = 180) -> str:
    cleaned = clean_text(value)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(limit - 1, 0)].rstrip() + "…"


def canonicalize_url(url: str) -> str:
    normalized = html.unescape(clean_text(url))
    if not normalized:
        return ""
    parsed = urllib.parse.urlparse(normalized)
    scheme = parsed.scheme or "https"
    query = parsed.query
    fragment = parsed.fragment
    if parsed.netloc.endswith("mp.weixin.qq.com") and parsed.path.startswith("/s") and not fragment:
        fragment = "rd"
    return urllib.parse.urlunparse((scheme, parsed.netloc, parsed.path, "", query, fragment))


def fetch_page(url: str, *, timeout: int = 30) -> dict[str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": WECHAT_USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        html_text = response.read().decode(charset, errors="ignore")
        final_url = response.geturl()
    return {"html": html_text, "final_url": canonicalize_url(final_url)}


def extract_target_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    target = clean_text((query.get("target_url") or [""])[0])
    if not target:
        return ""
    return canonicalize_url(urllib.parse.unquote(target))


def classify_page(*, source_url: str, html_text: str, final_url: str) -> dict[str, Any]:
    body = re.sub(r"\s+", " ", html_text or "")
    canonical_source = canonicalize_url(source_url)
    target_url = extract_target_url(final_url)
    canonical_url = target_url or canonical_source

    if (
        "wappoc_appmsgcaptcha" in final_url
        or ("环境异常" in body and "完成验证后即可继续访问" in body)
        or 'id="js_verify"' in html_text
    ):
        return {
            "status": "captcha_blocked",
            "canonical_url": canonical_url,
            "final_url": final_url,
            "note": "微信返回了环境异常/验证码页面，当前访问链路被人机校验拦截。",
            "page_excerpt": truncate_text(body, 220),
            "should_browser_retry": True,
        }

    if "参数错误" in body and "weui-msg__title" in body:
        return {
            "status": "param_error",
            "canonical_url": canonical_source,
            "final_url": final_url,
            "note": "微信返回了参数错误页；这类短链或分享链接当前不是可直接抓取的标准文章入口。",
            "page_excerpt": truncate_text(body, 220),
            "should_browser_retry": False,
        }

    expired_or_deleted_markers = [
        "链接已过期",
        "该内容已被发布者删除",
        "内容已被发布者删除",
        "此内容因违规无法查看",
        "被投诉且经审核涉嫌侵权，无法查看",
    ]
    if any(marker in body for marker in expired_or_deleted_markers):
        return {
            "status": "expired_or_deleted",
            "canonical_url": canonical_source,
            "final_url": final_url,
            "note": "微信返回了已过期、已删除或违规不可见页面。",
            "page_excerpt": truncate_text(body, 220),
            "should_browser_retry": False,
        }

    if 'id="js_content"' in html_text or 'id=\\"js_content\\"' in html_text or "cover_url" in html_text:
        return {
            "status": "article_page",
            "canonical_url": canonical_source,
            "final_url": final_url,
            "note": "当前页面已命中文章正文结构，可以直接进入正文解析。",
            "page_excerpt": "",
            "should_browser_retry": False,
        }

    return {
        "status": "unknown_extract_failure",
        "canonical_url": canonical_source,
        "final_url": final_url,
        "note": "当前页面未命中文章正文结构，也不属于已识别的验证码或参数错误页。",
        "page_excerpt": truncate_text(body, 220),
        "should_browser_retry": False,
    }


def maybe_json(stdout: str) -> Any:
    stripped = stdout.strip()
    if not stripped:
        return {}
    return json.loads(stripped)


def run_node_script(script_path: Path, *args: str, cwd: Path) -> Any:
    completed = subprocess.run(
        ["node", str(script_path), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(clean_text(completed.stderr) or clean_text(completed.stdout) or f"Helper script failed: {script_path.name}")
    return maybe_json(completed.stdout)


def browser_fetch_html(
    *,
    workspace_root: Path,
    source_url: str,
    profile_dir: Path,
    output_html_path: Path,
    headless: bool = False,
) -> dict[str, Any]:
    script_path = workspace_root / "skills" / "wechat-report" / "scripts" / "fetch_article_html.js"
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    profile_dir.mkdir(parents=True, exist_ok=True)
    return run_node_script(
        script_path,
        str(workspace_root),
        source_url,
        str(profile_dir),
        str(output_html_path),
        "1" if headless else "0",
        cwd=workspace_root,
    )
