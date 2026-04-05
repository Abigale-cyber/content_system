from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any


SKILL_SCRIPTS = Path("/Users/Abigale/.codex/skills/wechat-article-workflow/scripts").resolve()
DEFAULT_THEME_NAME = "elegant-gold"
DEFAULT_TEMPLATE_NAME = "default"

if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from wechat_html_renderer import (  # noqa: E402
    apply_template,
    available_template_catalog,
    available_themes,
    load_theme,
    markdown_to_wechat_html,
    render_standalone_document,
    theme_to_dict,
)


def apply_html_typography_overrides(html: str, typography: dict[str, Any]) -> str:
    paragraph_gap = clamp_int(typography.get("paragraphGap"), 8, 32, 16)

    def replace_paragraph_margin(match: re.Match[str]) -> str:
        style = match.group(1)
        updated = re.sub(r"margin:0 0 \d+px;", f"margin:0 0 {paragraph_gap}px;", style, count=1)
        return f'<p style="{updated}">'

    return re.sub(r'<p style="([^"]*?)">', replace_paragraph_margin, html)


def clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def resolve_theme(theme_name: str | None = None, template_name: str | None = None) -> tuple[Any, str, str]:
    normalized_theme = str(theme_name or DEFAULT_THEME_NAME).strip() or DEFAULT_THEME_NAME
    if normalized_theme not in available_themes():
        normalized_theme = DEFAULT_THEME_NAME

    supported_templates = {item.get("id") for item in available_template_catalog()}
    normalized_template = str(template_name or DEFAULT_TEMPLATE_NAME).strip() or DEFAULT_TEMPLATE_NAME
    if normalized_template not in supported_templates:
        normalized_template = DEFAULT_TEMPLATE_NAME

    return apply_template(load_theme(normalized_theme), normalized_template), normalized_theme, normalized_template


def render_wechat_preview(
    markdown_text: str,
    *,
    theme: Any,
    typography: dict[str, Any] | None = None,
    metadata_overrides: dict[str, Any] | None = None,
    template_name: str | None = None,
    wechat_safe: bool = True,
) -> dict[str, Any]:
    typography = typography or {}
    metadata_overrides = metadata_overrides or {}

    body_html = apply_html_typography_overrides(
        markdown_to_wechat_html(
            markdown_text,
            theme=theme,
            template_name=template_name,
            metadata_overrides=metadata_overrides,
            wechat_safe=wechat_safe,
        ),
        typography,
    )
    standalone_html = apply_html_typography_overrides(
        render_standalone_document(
            markdown_text,
            theme=theme,
            template_name=template_name,
            metadata_overrides=metadata_overrides,
            wechat_safe=wechat_safe,
        ),
        typography,
    )
    return {
        "bodyHtml": body_html,
        "standaloneHtml": standalone_html,
        "sourceHtml": standalone_html,
        "wechatSafeBodyHtml": body_html,
        "wechatSafeStandaloneHtml": standalone_html,
        "wechatSafeSourceHtml": standalone_html,
        "theme": theme_to_dict(theme),
    }


def render_article_html(
    markdown_text: str,
    *,
    theme_name: str | None = None,
    template_name: str | None = None,
    typography: dict[str, Any] | None = None,
    metadata_overrides: dict[str, Any] | None = None,
    wechat_safe: bool = True,
) -> dict[str, Any]:
    theme, resolved_theme_name, resolved_template_name = resolve_theme(theme_name, template_name)
    rendered = render_wechat_preview(
        markdown_text,
        theme=theme,
        typography=typography,
        metadata_overrides=metadata_overrides,
        template_name=None,
        wechat_safe=wechat_safe,
    )
    rendered["themeName"] = resolved_theme_name
    rendered["templateName"] = resolved_template_name
    return rendered
