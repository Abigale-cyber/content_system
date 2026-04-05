#!/usr/bin/env python3
"""Local API server for the wechat-studio subsystem."""

from __future__ import annotations

import colorsys
import copy
import importlib.util
import json
import mimetypes
import re
import subprocess
import sys
import urllib.error
import urllib.request
import yaml
from email.parser import BytesParser
from email.policy import default as email_policy_default
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
CONTENT_DIR = ROOT / "content" / "articles"
THEME_OUTPUT_DIR = ROOT / "AI" / "themes"
REFERENCE_SHOTS_DIR = ROOT / "AI" / "reference-shots"
DEFAULT_THEME = "elegant-gold"
DEFAULT_COVER_RELATIVE = "AI/covers/2026-03-28-ai-art-cover.png"
DEFAULT_COVER_PATH = (ROOT / DEFAULT_COVER_RELATIVE).resolve()
STUDIO_STATE_FILENAME = "studio-state.json"
STUDIO_ASSET_DIRNAME = "studio-assets"
SKILL_SCRIPTS = Path("/Users/Abigale/.codex/skills/wechat-article-workflow/scripts").resolve()
IMAGE_VENV_PYTHON = ROOT / ".venv-image" / "bin" / "python"
COLLAGE_SCRIPT = FRONTEND_DIR / "generate_cover_collage_module.py"
_GENERATE_IMAGE_RUNTIME: Any | None = None
_WECHAT_FORMATTER_RUNTIME: Any | None = None

if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from push_wechat_draft_api import (  # noqa: E402
    create_draft,
    get_access_token,
    load_config,
    load_publish_inputs,
    upload_article_image,
    upload_cover_image,
)
from reference_theme_extractor import extract_reference_theme  # noqa: E402
from wechat_html_renderer import (  # noqa: E402
    Theme,
    apply_template,
    available_theme_catalog,
    available_template_catalog,
    available_themes,
    extract_markdown_images,
    load_theme,
    markdown_to_wechat_html,
    render_standalone_document,
    save_theme,
    split_frontmatter,
    theme_from_mapping,
    theme_to_dict,
)


ARTICLE_DETAIL_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)$")
LAYOUT_PREVIEW_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/layout/preview$")
IMAGE_COVER_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/images/cover$")
IMAGE_COVER_SELECT_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/images/cover/select$")
IMAGE_COVER_DELETE_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/images/cover/delete$")
IMAGE_COVER_MODULE_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/images/cover-module$")
IMAGE_COVER_MODULE_SELECT_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/images/cover-module/select$")
IMAGE_SECTION_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/images/section$")
IMAGE_SECTION_SELECT_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/images/section/select$")
IMAGE_INLINE_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/images/inline$")
IMAGE_INLINE_SELECT_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/images/inline/select$")
IMAGE_INLINE_DELETE_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/images/inline/delete$")
TEXT_BLOCK_UPDATE_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/text-block$")
DRAFT_IMPORT_RE = re.compile(r"^/api/articles/import$")
DRAFT_PUSH_RE = re.compile(r"^/api/articles/(?P<slug>[^/]+)/draft$")


def load_generate_image_runtime() -> Any:
    global _GENERATE_IMAGE_RUNTIME
    if _GENERATE_IMAGE_RUNTIME is not None:
        return _GENERATE_IMAGE_RUNTIME

    runtime_path = ROOT.parent / "generate-image" / "runtime.py"
    if not runtime_path.exists():
        raise FileNotFoundError(f"generate-image runtime not found: {runtime_path}")

    spec = importlib.util.spec_from_file_location("generate_image_runtime", runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load generate-image runtime module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("generate_image_runtime", module)
    spec.loader.exec_module(module)
    _GENERATE_IMAGE_RUNTIME = module
    return module


def load_wechat_formatter_runtime() -> Any:
    global _WECHAT_FORMATTER_RUNTIME
    if _WECHAT_FORMATTER_RUNTIME is not None:
        return _WECHAT_FORMATTER_RUNTIME

    runtime_path = ROOT.parent / "wechat-formatter" / "runtime.py"
    if not runtime_path.exists():
        raise FileNotFoundError(f"wechat-formatter runtime not found: {runtime_path}")

    spec = importlib.util.spec_from_file_location("wechat_formatter_runtime", runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load wechat-formatter runtime module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("wechat_formatter_runtime", module)
    spec.loader.exec_module(module)
    _WECHAT_FORMATTER_RUNTIME = module
    return module

REMOTE_ASSET_RE = re.compile(r"^(?:https?:)?//", re.I)
COVER_STYLE_CHOICES: list[dict[str, str]] = [
    {
        "id": "magazine",
        "label": "杂志感",
        "style": "magazine editorial cover, clean layout, strong title-safe area, refined visual hierarchy, no person, no product mockup",
    },
    {
        "id": "offset-collage",
        "label": "错位拼贴",
        "style": "offset collage cover, layered paper frames, editorial overlap, angled blocks, tactile paper texture, no person, no product mockup",
    },
    {
        "id": "sticker-note",
        "label": "贴纸感",
        "style": "sticker note cover, memo paper labels, taped elements, playful editorial composition, clean color blocks, no person, no product mockup",
    },
    {
        "id": "quiet-poster",
        "label": "留白海报",
        "style": "minimal poster cover, large white space, restrained modern composition, calm art direction, no person, no product mockup",
    },
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def relative_to_root(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def file_exists_relative(relative_path: str) -> bool:
    if not relative_path:
        return False
    try:
        path = resolve_workspace_path(relative_path)
    except FileNotFoundError:
        return False
    return path.exists()


def ensure_relative_path(value: str) -> str:
    path = Path(value).expanduser()
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(ROOT))
        except ValueError as error:
            raise FileNotFoundError("Only paths inside the workspace are allowed.") from error
    return str(path)


def resolve_workspace_path(value: str) -> Path:
    relative = ensure_relative_path(value)
    path = (ROOT / relative).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {relative}")
    return path


def absolute_theme_file(theme_file: str | None) -> str | None:
    if not theme_file:
        return None
    return str(resolve_workspace_path(theme_file))


def resolve_article_dir(slug: str) -> Path:
    decoded = unquote(slug).strip()
    if not decoded:
        raise FileNotFoundError("Article id is required.")
    path = (CONTENT_DIR / decoded).resolve()
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Article directory not found: {decoded}")
    return path


def article_state_path(article_dir: Path) -> Path:
    return article_dir / STUDIO_STATE_FILENAME


def article_asset_dir(article_dir: Path) -> Path:
    return article_dir / STUDIO_ASSET_DIRNAME


def default_studio_state() -> dict[str, Any]:
    return {
        "source": {
            "originalName": "",
            "markdownPath": "",
            "uploadedAt": "",
            "warnings": [],
        },
        "layout": {
            "theme": DEFAULT_THEME,
            "template": "default",
            "themeFile": "",
            "referenceUrl": "",
            "warning": "",
            "extractionMeta": {},
            "updatedAt": "",
        },
        "tone": {
            "theme": DEFAULT_THEME,
            "primaryColor": "#b3832f",
            "saturation": 100,
            "opacity": 88,
            "updatedAt": "",
        },
        "typography": {
            "template": "default",
            "titleStyle": "standard",
            "bodySize": 16,
            "lineHeight": 1.9,
            "paragraphGap": 16,
            "sectionStyle": "editorial",
            "imageRadius": 24,
            "imageSpacing": 22,
            "updatedAt": "",
        },
        "cover": {
            "candidatePath": "",
            "generated": None,
            "history": [],
            "customPrompt": "",
            "updatedAt": "",
        },
        "coverModules": {
            "current": None,
            "history": [],
            "style": "collage-editorial",
            "updatedAt": "",
        },
        "inlineImages": {
            "items": [],
            "history": [],
            "positions": {},
            "customPrompt": "",
            "updatedAt": "",
        },
        "sectionModules": {
            "items": [],
            "history": [],
            "customPrompt": "",
            "updatedAt": "",
        },
        "draft": {
            "mediaId": "",
            "title": "",
            "pushedAt": "",
            "lastError": "",
            "theme": "",
            "themeFile": "",
            "template": "",
        },
        "preview": {
            "initialized": False,
            "updatedAt": "",
        },
    }


def merge_state(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge_state(base[key], value)
        else:
            base[key] = value
    return base


def load_studio_state(article_dir: Path) -> dict[str, Any]:
    state = default_studio_state()
    path = article_state_path(article_dir)
    if not path.exists():
        normalize_state_inplace(state)
        return state
    payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    if not isinstance(payload, dict):
        normalize_state_inplace(state)
        return state
    merged = merge_state(state, payload)
    cover_generated = merged.get("cover", {}).get("generated")
    cover_history = merged.get("cover", {}).get("history", [])
    if isinstance(cover_generated, dict) and isinstance(cover_history, list) and not cover_history:
        merged["cover"]["history"] = [copy.deepcopy(cover_generated)]

    cover_module_current = merged.get("coverModules", {}).get("current")
    cover_module_history = merged.get("coverModules", {}).get("history", [])
    if isinstance(cover_module_current, dict) and isinstance(cover_module_history, list) and not cover_module_history:
        merged["coverModules"]["history"] = [copy.deepcopy(cover_module_current)]

    inline_items = merged.get("inlineImages", {}).get("items", [])
    inline_history = merged.get("inlineImages", {}).get("history", [])
    if isinstance(inline_items, list) and isinstance(inline_history, list) and not inline_history and inline_items:
        merged["inlineImages"]["history"] = copy.deepcopy([item for item in inline_items if isinstance(item, dict)])
    normalize_state_inplace(merged)
    return merged


def save_studio_state(article_dir: Path, state: dict[str, Any]) -> None:
    normalize_state_inplace(state)
    path = article_state_path(article_dir)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def clamp_float(value: Any, minimum: float, maximum: float, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def normalize_hex_color(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", text):
        return text.lower()
    if re.fullmatch(r"[0-9a-fA-F]{6}", text):
        return f"#{text.lower()}"
    return fallback.lower()


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    color = normalize_hex_color(value, "#000000")[1:]
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def rgb_to_hex(red: int, green: int, blue: int) -> str:
    return f"#{red:02x}{green:02x}{blue:02x}"


def rgba_string(value: str, alpha: float) -> str:
    red, green, blue = hex_to_rgb(value)
    return f"rgba({red}, {green}, {blue}, {max(0.0, min(1.0, alpha)):.3f})"


def mix_hex(value: str, other: str, ratio: float) -> str:
    ratio = max(0.0, min(1.0, ratio))
    red_a, green_a, blue_a = hex_to_rgb(value)
    red_b, green_b, blue_b = hex_to_rgb(other)
    red = round(red_a * (1 - ratio) + red_b * ratio)
    green = round(green_a * (1 - ratio) + green_b * ratio)
    blue = round(blue_a * (1 - ratio) + blue_b * ratio)
    return rgb_to_hex(red, green, blue)


def adjust_hex_saturation(value: str, percent: int) -> str:
    ratio = clamp_int(percent, 40, 160, 100) / 100
    red, green, blue = hex_to_rgb(value)
    hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
    saturation = max(0.0, min(1.0, saturation * ratio))
    next_red, next_green, next_blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return rgb_to_hex(round(next_red * 255), round(next_green * 255), round(next_blue * 255))


def effective_theme_name(state: dict[str, Any]) -> str:
    tone = state.get("tone", {}) if isinstance(state.get("tone", {}), dict) else {}
    layout = state.get("layout", {}) if isinstance(state.get("layout", {}), dict) else {}
    theme_name = str(tone.get("theme") or layout.get("theme") or DEFAULT_THEME).strip() or DEFAULT_THEME
    return theme_name if theme_name in available_themes() else DEFAULT_THEME


def effective_template_name(state: dict[str, Any]) -> str:
    typography = state.get("typography", {}) if isinstance(state.get("typography", {}), dict) else {}
    layout = state.get("layout", {}) if isinstance(state.get("layout", {}), dict) else {}
    template_name = str(typography.get("template") or layout.get("template") or "default").strip() or "default"
    supported = {item.get("id") for item in available_template_catalog()}
    return template_name if template_name in supported else "default"


def default_primary_for_theme(theme_name: str) -> str:
    try:
        return normalize_hex_color(load_theme(theme_name).primary, "#b3832f")
    except Exception:
        return "#b3832f"


def normalize_tone_state_inplace(state: dict[str, Any]) -> dict[str, Any]:
    layout = state.setdefault("layout", {})
    if not isinstance(layout, dict):
        layout = {}
        state["layout"] = layout
    tone = state.setdefault("tone", {})
    if not isinstance(tone, dict):
        tone = {}
        state["tone"] = tone
    theme_name = effective_theme_name(state)
    fallback_primary = default_primary_for_theme(theme_name)
    tone["theme"] = theme_name
    tone["primaryColor"] = normalize_hex_color(tone.get("primaryColor"), fallback_primary)
    tone["saturation"] = clamp_int(tone.get("saturation"), 40, 160, 100)
    tone["opacity"] = clamp_int(tone.get("opacity"), 35, 100, 88)
    tone["updatedAt"] = str(tone.get("updatedAt", "")).strip()
    layout["theme"] = theme_name
    return tone


def normalize_typography_state_inplace(state: dict[str, Any]) -> dict[str, Any]:
    layout = state.setdefault("layout", {})
    if not isinstance(layout, dict):
        layout = {}
        state["layout"] = layout
    typography = state.setdefault("typography", {})
    if not isinstance(typography, dict):
        typography = {}
        state["typography"] = typography
    typography["template"] = effective_template_name(state)
    typography["titleStyle"] = str(typography.get("titleStyle") or "standard").strip() or "standard"
    if typography["titleStyle"] not in {"standard", "centered", "editorial"}:
        typography["titleStyle"] = "standard"
    typography["bodySize"] = clamp_int(typography.get("bodySize"), 14, 22, 16)
    typography["lineHeight"] = round(clamp_float(typography.get("lineHeight"), 1.5, 2.4, 1.9), 2)
    typography["paragraphGap"] = clamp_int(typography.get("paragraphGap"), 8, 32, 16)
    typography["sectionStyle"] = str(typography.get("sectionStyle") or "editorial").strip() or "editorial"
    if typography["sectionStyle"] not in {"editorial", "editorial-card", "bento", "winter-tag", "spring"}:
        typography["sectionStyle"] = "editorial"
    typography["imageRadius"] = clamp_int(typography.get("imageRadius"), 0, 32, 24)
    typography["imageSpacing"] = clamp_int(typography.get("imageSpacing"), 12, 40, 22)
    typography["updatedAt"] = str(typography.get("updatedAt", "")).strip()
    layout["template"] = typography["template"]
    return typography


def normalize_source_state_inplace(state: dict[str, Any]) -> dict[str, Any]:
    source = state.setdefault("source", {})
    if not isinstance(source, dict):
        source = {}
        state["source"] = source
    warnings = source.get("warnings", [])
    if not isinstance(warnings, list):
        warnings = []
    source["warnings"] = [str(item).strip() for item in warnings if str(item).strip()]
    source["originalName"] = str(source.get("originalName", "")).strip()
    source["markdownPath"] = str(source.get("markdownPath", "")).strip()
    source["uploadedAt"] = str(source.get("uploadedAt", "")).strip()
    return source


def normalize_inline_state_inplace(state: dict[str, Any]) -> dict[str, Any]:
    inline = state.setdefault("inlineImages", {})
    if not isinstance(inline, dict):
        inline = {}
        state["inlineImages"] = inline
    items = inline.get("items", [])
    history = inline.get("history", [])
    positions = inline.get("positions", {})
    inline["items"] = [copy.deepcopy(item) for item in items if isinstance(item, dict)]
    inline["history"] = [copy.deepcopy(item) for item in history if isinstance(item, dict)]
    if not isinstance(positions, dict):
        positions = {}
    normalized_positions: dict[str, str] = {}
    for slot in (1, 2):
        value = str(positions.get(str(slot), positions.get(slot, "")) or "").strip()
        if value:
            normalized_positions[str(slot)] = value
    inline["positions"] = normalized_positions
    inline["customPrompt"] = str(inline.get("customPrompt", "")).strip()
    inline["updatedAt"] = str(inline.get("updatedAt", "")).strip()
    return inline


def normalize_preview_state_inplace(state: dict[str, Any]) -> dict[str, Any]:
    preview = state.setdefault("preview", {})
    if not isinstance(preview, dict):
        preview = {}
        state["preview"] = preview
    preview["initialized"] = bool(preview.get("initialized"))
    preview["updatedAt"] = str(preview.get("updatedAt", "")).strip()
    return preview


def normalize_state_inplace(state: dict[str, Any]) -> dict[str, Any]:
    normalize_source_state_inplace(state)
    normalize_tone_state_inplace(state)
    normalize_typography_state_inplace(state)
    normalize_inline_state_inplace(state)
    normalize_preview_state_inplace(state)
    return state


def preview_initialized(state: dict[str, Any]) -> bool:
    preview = state.get("preview", {})
    return isinstance(preview, dict) and bool(preview.get("initialized"))


def safe_load_config() -> dict[str, Any]:
    try:
        return load_config()
    except BaseException:
        return {}


def update_editor_state_from_payload(state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    normalize_state_inplace(state)
    tone_payload = payload.get("tone", payload)
    typography_payload = payload.get("typography", payload)
    tone = state["tone"]
    typography = state["typography"]
    layout = state["layout"]
    inline_images = state["inlineImages"]

    if isinstance(tone_payload, dict):
        if "theme" in tone_payload:
            tone["theme"] = str(tone_payload.get("theme") or DEFAULT_THEME).strip() or DEFAULT_THEME
        if "primaryColor" in tone_payload:
            tone["primaryColor"] = normalize_hex_color(tone_payload.get("primaryColor"), tone["primaryColor"])
        if "saturation" in tone_payload:
            tone["saturation"] = clamp_int(tone_payload.get("saturation"), 40, 160, tone["saturation"])
        if "opacity" in tone_payload:
            tone["opacity"] = clamp_int(tone_payload.get("opacity"), 35, 100, tone["opacity"])

    if isinstance(typography_payload, dict):
        if "template" in typography_payload:
            typography["template"] = str(typography_payload.get("template") or "default").strip() or "default"
        if "titleStyle" in typography_payload:
            typography["titleStyle"] = str(typography_payload.get("titleStyle") or "standard").strip() or "standard"
        if "bodySize" in typography_payload:
            typography["bodySize"] = clamp_int(typography_payload.get("bodySize"), 14, 22, typography["bodySize"])
        if "lineHeight" in typography_payload:
            typography["lineHeight"] = round(
                clamp_float(typography_payload.get("lineHeight"), 1.5, 2.4, typography["lineHeight"]),
                2,
            )
        if "paragraphGap" in typography_payload:
            typography["paragraphGap"] = clamp_int(
                typography_payload.get("paragraphGap"),
                8,
                32,
                typography["paragraphGap"],
            )
        if "sectionStyle" in typography_payload:
            typography["sectionStyle"] = str(typography_payload.get("sectionStyle") or "editorial").strip() or "editorial"
        if "imageRadius" in typography_payload:
            typography["imageRadius"] = clamp_int(
                typography_payload.get("imageRadius"),
                0,
                32,
                typography["imageRadius"],
            )
        if "imageSpacing" in typography_payload:
            typography["imageSpacing"] = clamp_int(
                typography_payload.get("imageSpacing"),
                12,
                40,
                typography["imageSpacing"],
            )

    if "themeFile" in payload:
        layout["themeFile"] = str(payload.get("themeFile") or "").strip()
    if "referenceUrl" in payload:
        layout["referenceUrl"] = str(payload.get("referenceUrl") or "").strip()
    inline_positions_payload = payload.get("inlinePositions")
    if isinstance(inline_positions_payload, dict):
        positions: dict[str, str] = {}
        for slot in (1, 2):
            value = str(inline_positions_payload.get(str(slot), inline_positions_payload.get(slot, "")) or "").strip()
            if value:
                positions[str(slot)] = value
        inline_images["positions"] = positions
        inline_images["updatedAt"] = now_text()

    tone["updatedAt"] = now_text()
    typography["updatedAt"] = now_text()
    normalize_state_inplace(state)
    return state


def theme_with_overrides(theme: Theme, **overrides: Any) -> Theme:
    payload = theme_to_dict(theme)
    for key, value in overrides.items():
        if value in (None, ""):
            continue
        payload[key] = value
    return Theme(**payload)


def resolve_render_theme(state: dict[str, Any]) -> tuple[Theme, str, str, str | None]:
    normalize_state_inplace(state)
    theme_name = effective_theme_name(state)
    template_name = effective_template_name(state)
    theme_file = absolute_theme_file(str(state.get("layout", {}).get("themeFile", "")).strip() or None)
    base_theme = apply_template(load_theme(theme_name, theme_file), template_name)
    tone = state["tone"]
    typography = state["typography"]

    primary = adjust_hex_saturation(
        normalize_hex_color(tone.get("primaryColor"), default_primary_for_theme(theme_name)),
        int(tone.get("saturation", 100) or 100),
    )
    opacity_ratio = clamp_int(tone.get("opacity"), 35, 100, 88) / 100
    secondary = mix_hex(primary, "#ffffff", 0.82)
    card_border = mix_hex(primary, "#f4ede2", 0.72)
    quote_border = mix_hex(primary, "#ffffff", 0.38)
    divider = mix_hex(primary, "#ffffff", 0.76)
    card_bg = rgba_string("#ffffff", 0.82 + opacity_ratio * 0.16)
    quote_bg = rgba_string(primary, 0.08 + opacity_ratio * 0.08)
    hero_panel_bg = f"linear-gradient(180deg,{rgba_string(primary, 0.08 + opacity_ratio * 0.08)},rgba(255,255,255,0.94))"
    hero_panel_border = rgba_string(primary, 0.16 + opacity_ratio * 0.12)

    resolved = theme_with_overrides(
        base_theme,
        primary=primary,
        secondary=secondary,
        card_border=card_border,
        divider=divider,
        quote_border=quote_border,
        card_bg=card_bg,
        quote_bg=quote_bg,
        hero_accent=primary,
        hero_panel_bg=hero_panel_bg,
        hero_panel_border=hero_panel_border,
        paragraph_size=clamp_int(typography.get("bodySize"), 14, 22, base_theme.paragraph_size),
        paragraph_line_height=round(
            clamp_float(typography.get("lineHeight"), 1.5, 2.4, base_theme.paragraph_line_height),
            2,
        ),
        paragraph_gap=clamp_int(typography.get("paragraphGap"), 8, 32, base_theme.paragraph_gap),
        h2_variant=str(typography.get("sectionStyle") or base_theme.h2_variant).strip() or base_theme.h2_variant,
        card_radius=clamp_int(typography.get("imageRadius"), 0, 32, base_theme.card_radius),
    )

    title_style = str(typography.get("titleStyle") or "standard").strip() or "standard"
    if title_style == "centered":
        resolved = theme_with_overrides(resolved, hero_align="center", h1_size=max(resolved.h1_size, 34))
    elif title_style == "editorial":
        resolved = theme_with_overrides(
            resolved,
            hero_align="left",
            h1_size=max(resolved.h1_size, 36),
            hero_eyebrow="FEATURE",
        )

    return resolved, theme_name, template_name, theme_file


def apply_html_typography_overrides(html: str, typography: dict[str, Any]) -> str:
    return load_wechat_formatter_runtime().apply_html_typography_overrides(html, typography)


def current_cover_candidate(state: dict[str, Any]) -> str:
    candidate = str(state.get("cover", {}).get("candidatePath", "")).strip()
    if candidate and file_exists_relative(candidate):
        return candidate
    return ""


def article_date_label(article_dir: Path) -> str:
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", article_dir.name)
    if match:
        return match.group(1)
    return datetime.now().strftime("%Y-%m-%d")


def first_heading(markdown_text: str) -> str:
    _metadata, body = split_frontmatter(markdown_text)
    for line in body.splitlines():
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match:
            return clean_label(match.group(1), limit=60)
    return ""


def build_publish_pack_payload(title: str, summary: str, author: str) -> dict[str, Any]:
    payload: dict[str, Any] = {"title": title, "summary": summary}
    if author:
        payload["author"] = author
    return payload


def build_normalized_markdown(metadata: dict[str, Any], body: str, *, title: str, summary: str, author: str) -> str:
    normalized = dict(metadata)
    normalized["title"] = title
    normalized["digest"] = summary
    if author:
        normalized["author"] = author
    elif "author" in normalized and not str(normalized.get("author") or "").strip():
        normalized.pop("author", None)
    frontmatter = yaml.safe_dump(normalized, allow_unicode=True, sort_keys=False).strip()
    cleaned_body = body.strip("\n")
    if cleaned_body:
        cleaned_body += "\n"
    return f"---\n{frontmatter}\n---\n\n{cleaned_body}"


def import_warnings_from_markdown(markdown_text: str) -> list[str]:
    warnings: list[str] = []
    local_refs: list[str] = []
    for _alt_text, image_ref in extract_markdown_images(markdown_text):
        if REMOTE_ASSET_RE.match(image_ref):
            continue
        if image_ref.startswith("data:"):
            continue
        local_refs.append(image_ref)
    if local_refs:
        preview_refs = "、".join(local_refs[:3])
        if len(local_refs) > 3:
            preview_refs += " 等"
        warnings.append(f"检测到本地图片引用：{preview_refs}。单文件导入不会自动带入这些素材，请后续手动替换。")
    return warnings


def parse_markdown_upload(body: bytes, content_type_header: str) -> tuple[str, bytes]:
    if "multipart/form-data" not in content_type_header:
        raise RuntimeError("上传请求必须使用 multipart/form-data。")
    message = BytesParser(policy=email_policy_default).parsebytes(
        f"Content-Type: {content_type_header}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    if not message.is_multipart():
        raise RuntimeError("上传内容解析失败。")
    for part in message.iter_parts():
        filename = part.get_filename() or ""
        field_name = part.get_param("name", header="content-disposition") or ""
        if field_name != "file":
            continue
        payload = part.get_payload(decode=True) or b""
        if not filename:
            raise RuntimeError("上传文件缺少文件名。")
        return filename, payload
    raise RuntimeError("没有收到 Markdown 文件。")


def unique_article_directory(name_hint: str) -> Path:
    base = sanitize_filename(name_hint) or "article"
    dated = f"{datetime.now().strftime('%Y-%m-%d')}-{base}"
    article_dir = CONTENT_DIR / dated
    index = 2
    while article_dir.exists():
        article_dir = CONTENT_DIR / f"{dated}-{index}"
        index += 1
    return article_dir


def infer_article_archetype(title: str, summary: str, markdown_text: str) -> str:
    sample = f"{title}\n{summary}\n{markdown_text[:2500]}".lower()
    if any(keyword in sample for keyword in ["时间线", "里程碑", "发展历程", "路线图", "版本", "timeline"]):
        return "timeline"
    if any(keyword in sample for keyword in ["教程", "步骤", "指南", "清单", "怎么做", "手把手", "workflow", "process"]):
        return "tutorial"
    if any(keyword in sample for keyword in ["趋势", "分析", "报告", "数据", "对比", "复盘", "洞察", "strategy", "analysis"]):
        return "analysis"
    return "opinion"


def cover_preset_for_archetype(archetype: str) -> str:
    mapping = {
        "analysis": "cover-data-visual",
        "tutorial": "cover-minimal",
        "timeline": "cover-editorial",
        "opinion": "cover-editorial",
    }
    return mapping.get(archetype, "cover-editorial")


def inline_preset_for_archetype(archetype: str) -> str:
    mapping = {
        "analysis": "infographic-bento",
        "tutorial": "infographic-process",
        "timeline": "infographic-timeline",
        "opinion": "infographic-handdrawn-sketchnote",
    }
    return mapping.get(archetype, "infographic-bento")


def tone_prompt_context(state: dict[str, Any]) -> str:
    tone = state.get("tone", {}) if isinstance(state.get("tone", {}), dict) else {}
    typography = state.get("typography", {}) if isinstance(state.get("typography", {}), dict) else {}
    return (
        f"theme style {effective_theme_name(state)}, "
        f"primary color {normalize_hex_color(tone.get('primaryColor'), default_primary_for_theme(effective_theme_name(state)))}, "
        f"saturation {clamp_int(tone.get('saturation'), 40, 160, 100)} percent, "
        f"opacity {clamp_int(tone.get('opacity'), 35, 100, 88)} percent, "
        f"title style {str(typography.get('titleStyle') or 'standard').strip() or 'standard'}, "
        f"section heading style {str(typography.get('sectionStyle') or 'editorial').strip() or 'editorial'}"
    )


def build_render_metadata(
    article_dir: Path,
    state: dict[str, Any],
    *,
    mode: str,
    wechat_safe: bool = False,
    access_token: str | None = None,
) -> dict[str, Any]:
    candidate = current_cover_candidate(state)
    preview_url = asset_preview_url(candidate) if candidate and file_exists_relative(candidate) else ""
    draft_url = ""
    layout = state.get("layout", {}) if isinstance(state.get("layout", {}), dict) else {}
    template_name = str(layout.get("template", "default")).strip() or "default"
    cover_state = state.get("cover", {}) if isinstance(state.get("cover", {}), dict) else {}
    records: list[dict[str, Any]] = []
    generated = cover_state.get("generated")
    if isinstance(generated, dict):
        records.append(generated)
    history = cover_state.get("history", [])
    if isinstance(history, list):
        records.extend([item for item in history if isinstance(item, dict)])
    for item in records:
        if str(item.get("localPath", "")).strip() == candidate:
            draft_url = str(item.get("draftUrl") or item.get("previewUrl") or "").strip()
            if not preview_url:
                preview_url = str(item.get("previewUrl") or item.get("draftUrl") or "").strip()
            break
    if mode == "draft" and not draft_url and candidate and access_token and file_exists_relative(candidate):
        draft_url = upload_article_image(access_token, resolve_workspace_path(candidate))
    hero_url = preview_url if mode == "preview" else (draft_url or preview_url)
    cover_module_state = state.get("coverModules", {}) if isinstance(state.get("coverModules", {}), dict) else {}
    current_cover_module = cover_module_state.get("current") if isinstance(cover_module_state.get("current"), dict) else None
    cover_module_url = ""
    if current_cover_module:
        module_local_path = str(current_cover_module.get("localPath", "")).strip()
        module_preview_url = asset_preview_url(module_local_path) if module_local_path and file_exists_relative(module_local_path) else ""
        module_draft_url = str(current_cover_module.get("draftUrl", "")).strip()
        if mode == "draft" and not module_draft_url and module_local_path and access_token and file_exists_relative(module_local_path):
            module_draft_url = upload_article_image(access_token, resolve_workspace_path(module_local_path))
        cover_module_url = module_preview_url if mode == "preview" else (module_draft_url or module_preview_url)
    section_state = state.get("sectionModules", {}) if isinstance(state.get("sectionModules", {}), dict) else {}
    section_items = section_state.get("items", []) if isinstance(section_state.get("items", []), list) else []
    section_modules: list[dict[str, Any]] = []
    for item in section_items:
        if not isinstance(item, dict):
            continue
        local_path = str(item.get("localPath", "")).strip()
        local_preview = asset_preview_url(local_path) if local_path and file_exists_relative(local_path) else ""
        preview_value = local_preview or str(item.get("previewUrl", "")).strip() or str(item.get("draftUrl", "")).strip()
        draft_value = str(item.get("draftUrl", "")).strip()
        if mode == "draft" and not draft_value and local_path and access_token and file_exists_relative(local_path):
            draft_value = upload_article_image(access_token, resolve_workspace_path(local_path))
        url = preview_value if mode == "preview" else (draft_value or preview_value)
        if not url:
            continue
        section_modules.append(
            {
                "slot": int(item.get("slot") or 0),
                "label": str(item.get("label", "")).strip(),
                "url": url,
            }
        )
    return {
        "hero_image": hero_url,
        "cover_module_image": cover_module_url or hero_url,
        "cover_date": article_date_label(article_dir),
        "cover_left_label": "春日",
        "cover_right_label": "踏青",
        "cover_year": f"（ {article_date_label(article_dir)[:4]} ）",
        "section_modules": section_modules,
    }


def list_theme_files() -> list[str]:
    if not THEME_OUTPUT_DIR.exists():
        return []
    items: list[str] = []
    for path in sorted(THEME_OUTPUT_DIR.glob("*")):
        if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            continue
        items.append(relative_to_root(path))
    return items


def sanitize_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-").lower() or "asset"


def mask_secret(value: str) -> str:
    text = str(value or "").strip()
    if len(text) <= 8:
        return "已配置" if text else "未配置"
    return f"{text[:4]}...{text[-4:]}"


def asset_preview_url(relative_path: str) -> str:
    relative = ensure_relative_path(relative_path)
    return f"/api/assets?path={quote(relative)}"


def enrich_asset_record(record: Any) -> dict[str, Any] | None:
    if not isinstance(record, dict):
        return None
    enriched = copy.deepcopy(record)
    local_path = str(enriched.get("localPath", "")).strip()
    local_exists = bool(local_path and file_exists_relative(local_path))
    enriched["localExists"] = local_exists
    enriched["localPreviewUrl"] = asset_preview_url(local_path) if local_exists else ""
    return enriched


def merge_asset_history(existing: list[Any], new_items: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in [*new_items, *existing]:
        if not isinstance(item, dict):
            continue
        key = str(item.get("localPath") or item.get("previewUrl") or item.get("draftUrl") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(copy.deepcopy(item))
        if len(merged) >= limit:
            break
    return merged


def scan_local_asset_history(article_dir: Path, kind: str) -> list[dict[str, Any]]:
    asset_dir = article_asset_dir(article_dir)
    if not asset_dir.exists():
        return []
    results: list[dict[str, Any]] = []
    if kind == "cover":
        pattern = "cover-*.png"
    elif kind == "cover-module":
        pattern = "cover-module-*.png"
    elif kind == "section":
        pattern = "section-*.png"
    else:
        pattern = "inline-*.png"
    for path in sorted(asset_dir.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True):
        record: dict[str, Any] = {
            "localPath": relative_to_root(path),
            "createdAt": format_mtime(path),
        }
        if kind == "cover":
            record["preset"] = "local-cover"
        elif kind == "cover-module":
            record["preset"] = "cover-module"
            record["style"] = "collage-editorial"
        elif kind == "section":
            match = re.match(r"section-(\d+)-", path.name)
            slot = int(match.group(1)) if match else 0
            record.update(
                {
                    "slot": slot,
                    "label": f"分节 {slot}" if slot else "分节模块",
                    "preset": "local-section",
                }
            )
        else:
            match = re.match(r"inline-(\d+)-", path.name)
            slot = int(match.group(1)) if match else 0
            record.update(
                {
                    "slot": slot,
                    "label": f"插图 {slot}" if slot else "正文插图",
                    "preset": "local-inline",
                }
            )
        results.append(record)
    return results


def run_json_command(args: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    result = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )
    payload_text = (result.stdout or "").strip() or (result.stderr or "").strip()
    if not payload_text:
        raise RuntimeError("Command returned no output.")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as error:
        raise RuntimeError(payload_text) from error
    if result.returncode != 0 or payload.get("success") is False:
        raise RuntimeError(str(payload.get("error") or payload.get("message") or "Command failed."))
    return payload


def list_image_presets() -> list[dict[str, str]]:
    try:
        payload = run_json_command(["md2wechat", "prompts", "list", "--kind", "image", "--json"])
        prompts = payload.get("data", {}).get("prompts", [])
    except Exception:
        prompts = []
    if not isinstance(prompts, list):
        prompts = []
    preferred = {
        "cover-illustrated",
        "cover-editorial",
        "cover-minimal",
        "infographic-bento",
        "infographic-handdrawn-sketchnote",
        "infographic-default",
    }
    items: list[dict[str, str]] = []
    for prompt in prompts:
        if not isinstance(prompt, dict):
            continue
        prompt_id = str(prompt.get("name", "")).strip()
        if not prompt_id or prompt_id not in preferred:
            continue
        items.append(
            {
                "id": prompt_id,
                "label": prompt_id,
                "description": str(prompt.get("description", "")).strip(),
                "archetype": str(prompt.get("archetype", "")).strip(),
            }
        )
    if items:
        return items
    return [
        {"id": "cover-editorial", "label": "cover-editorial", "description": "评论 / 观点封面", "archetype": "cover"},
        {"id": "cover-data-visual", "label": "cover-data-visual", "description": "分析 / 数据封面", "archetype": "cover"},
        {"id": "cover-minimal", "label": "cover-minimal", "description": "极简封面", "archetype": "cover"},
        {"id": "infographic-bento", "label": "infographic-bento", "description": "信息卡正文图", "archetype": "infographic"},
        {"id": "infographic-process", "label": "infographic-process", "description": "流程型正文图", "archetype": "infographic"},
        {"id": "infographic-timeline", "label": "infographic-timeline", "description": "时间线正文图", "archetype": "infographic"},
        {"id": "infographic-handdrawn-sketchnote", "label": "infographic-handdrawn-sketchnote", "description": "手绘总结正文图", "archetype": "infographic"},
    ]


def cover_module_styles() -> list[dict[str, str]]:
    return [
        {
            "id": "collage-editorial",
            "label": "拼贴封面",
            "description": "大图 + 左下小图 + 白框偏移，适合杂志感正文头图。",
        },
        {
            "id": "poster-quiet",
            "label": "留白海报",
            "description": "更克制的单图海报感，适合散文和轻生活方式排版。",
        },
    ]


def simplified_cover_styles() -> list[dict[str, str]]:
    return [
        {"id": item["id"], "label": item["label"], "description": item["style"]}
        for item in COVER_STYLE_CHOICES
    ]


def title_style_options() -> list[dict[str, str]]:
    return [
        {"id": "standard", "label": "标准标题", "description": "保持当前主题的默认标题气质。"},
        {"id": "centered", "label": "居中大标题", "description": "标题居中，适合观点和专题封面。"},
        {"id": "editorial", "label": "专题标题", "description": "更强调刊物感与视觉冲击。"},
    ]


def section_style_options() -> list[dict[str, str]]:
    return [
        {"id": "editorial", "label": "标准分节", "description": "干净稳妥，适合大多数文章。"},
        {"id": "editorial-card", "label": "卡片分节", "description": "更像专题卡片标题。"},
        {"id": "bento", "label": "信息卡分节", "description": "层级更强，适合知识拆解。"},
        {"id": "winter-tag", "label": "标签分节", "description": "更像标签和刊物小标题。"},
        {"id": "spring", "label": "柔和分节", "description": "更适合生活方式和轻表达。"},
    ]


def settings_status() -> dict[str, Any]:
    config = safe_load_config()
    wechat = config.get("wechat", {})
    api = config.get("api", {})
    if not isinstance(wechat, dict):
        wechat = {}
    if not isinstance(api, dict):
        api = {}
    image_key = str(api.get("image_key", "")).strip()
    appid = str(wechat.get("appid", "")).strip()
    secret = str(wechat.get("secret", "")).strip()
    default_cover = DEFAULT_COVER_RELATIVE if DEFAULT_COVER_PATH.exists() else ""
    return {
        "workspace": str(ROOT),
        "defaultTheme": DEFAULT_THEME,
        "defaultTemplate": "default",
        "defaultCover": default_cover,
        "themes": available_theme_catalog(),
        "templates": available_template_catalog(),
        "themeFiles": list_theme_files(),
        "imagePresets": list_image_presets(),
        "coverStyles": simplified_cover_styles(),
        "titleStyles": title_style_options(),
        "sectionStyles": section_style_options(),
        "coverModuleStyles": cover_module_styles(),
        "wechat": {
            "configured": bool(appid and secret),
            "appid": mask_secret(appid),
            "mode": "单公众号账号",
        },
        "image": {
            "configured": bool(image_key),
            "provider": str(api.get("image_provider", "openai") or "openai"),
            "model": str(api.get("image_model", "")).strip() or "未设置",
            "size": str(api.get("image_size", "")).strip() or "默认",
        },
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def split_frontmatter_text(markdown_text: str) -> tuple[str, str]:
    text = markdown_text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text
    return text[: end + 5], text[end + 5 :]


def clean_label(text: str, *, limit: int = 26) -> str:
    stripped = re.sub(r"[#>*`*_!-]", " ", text)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    if len(stripped) <= limit:
        return stripped or "正文插图"
    return stripped[:limit].rstrip() + "…"


def editable_text_block_id(kind: str, line_index: int) -> str:
    return f"{str(kind or 'paragraph').strip()}:{max(0, int(line_index))}"


def normalize_editable_text(text: str) -> str:
    value = str(text or "")
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"[`*_~#>]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def is_non_editable_markdown_line(stripped: str) -> bool:
    if not stripped:
        return True
    if stripped.startswith(">"):
        return True
    if stripped in {"---", "***"}:
        return True
    if re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped):
        return True
    if stripped.startswith("|") and stripped.endswith("|") and "|" in stripped[1:-1]:
        return True
    if re.match(r"^[-*+]\s+.+$", stripped):
        return True
    if re.match(r"^\d+\.\s+.+$", stripped):
        return True
    return False


def extract_editable_text_blocks(markdown_text: str) -> list[dict[str, Any]]:
    _, body = split_frontmatter_text(markdown_text)
    lines = body.splitlines()
    blocks: list[dict[str, Any]] = []
    paragraph_start: int | None = None
    paragraph_buffer: list[str] = []
    in_code = False

    def flush_paragraph(line_end: int) -> None:
        nonlocal paragraph_start, paragraph_buffer
        if paragraph_start is None:
            return
        raw_text = " ".join(part.strip() for part in paragraph_buffer if part.strip())
        text = normalize_editable_text(raw_text)
        if text:
            blocks.append(
                {
                    "id": editable_text_block_id("paragraph", paragraph_start),
                    "kind": "paragraph",
                    "text": text,
                    "lineStart": paragraph_start,
                    "lineEnd": max(paragraph_start, line_end - 1),
                }
            )
        paragraph_start = None
        paragraph_buffer = []

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph(index)
            in_code = not in_code
            continue
        if in_code:
            continue
        heading = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        if heading:
            flush_paragraph(index)
            text = normalize_editable_text(heading.group(2))
            if text:
                blocks.append(
                    {
                        "id": editable_text_block_id("heading", index),
                        "kind": "heading",
                        "level": len(heading.group(1)),
                        "text": text,
                        "lineStart": index,
                        "lineEnd": index,
                    }
                )
            continue
        if is_non_editable_markdown_line(stripped):
            flush_paragraph(index)
            continue
        if paragraph_start is None:
            paragraph_start = index
        paragraph_buffer.append(line)

    flush_paragraph(len(lines))
    return blocks


def update_markdown_text_block(markdown_text: str, block_id: str, new_text: str) -> str:
    frontmatter, body = split_frontmatter_text(markdown_text)
    body_lines = body.splitlines()
    blocks = extract_editable_text_blocks(markdown_text)
    block = next((item for item in blocks if str(item.get("id", "")).strip() == block_id), None)
    if not block:
        raise RuntimeError("找不到对应的正文块。")

    clean_text = re.sub(r"\s+", " ", str(new_text or "").strip())
    if not clean_text:
        raise RuntimeError("文本内容不能为空。")

    line_start = int(block.get("lineStart") or 0)
    line_end = int(block.get("lineEnd") or line_start)
    if str(block.get("kind", "")).strip() == "heading":
        level = max(2, min(4, int(block.get("level") or 2)))
        body_lines[line_start] = f"{'#' * level} {clean_text}"
    else:
        body_lines[line_start : line_end + 1] = [clean_text]

    rebuilt_body = "\n".join(body_lines).strip("\n")
    if rebuilt_body:
        rebuilt_body += "\n"
    return frontmatter + rebuilt_body


def paragraph_targets(markdown_text: str, count: int) -> list[dict[str, Any]]:
    _, body = split_frontmatter_text(markdown_text)
    lines = body.splitlines()
    blocks: list[dict[str, Any]] = []
    start_index: int | None = None
    buffer: list[str] = []
    for index, line in enumerate(lines + [""]):
        if line.strip():
            if start_index is None:
                start_index = index
            buffer.append(line.strip())
            continue
        if start_index is not None:
            label = clean_label(" ".join(buffer))
            first_line = buffer[0].strip() if buffer else ""
            blocks.append(
                {
                    "lineIndex": start_index,
                    "label": label,
                    "kind": "paragraph",
                    "isHeading": first_line.startswith("#"),
                }
            )
            start_index = None
            buffer = []
    candidates = [block for block in blocks if not bool(block.get("isHeading"))] or blocks
    if not candidates:
        return [{"lineIndex": 0, "label": "正文开头", "kind": "paragraph"}] * count

    ratios = [0.35, 0.7] if count >= 2 else [0.35]
    chosen: list[dict[str, Any]] = []
    used: set[int] = set()
    for ratio in ratios[:count]:
        if len(candidates) == 1:
            position = 0
        else:
            position = int(round((len(candidates) - 1) * ratio))
        position = max(0, min(position, len(candidates) - 1))
        while position in used and position + 1 < len(candidates):
            position += 1
        while position in used and position - 1 >= 0:
            position -= 1
        used.add(position)
        chosen.append(candidates[position])
    return chosen


def inline_target_id(kind: str, line_index: int) -> str:
    return f"{str(kind or 'paragraph').strip()}:{max(0, int(line_index))}"


def inline_target_catalog(markdown_text: str) -> list[dict[str, Any]]:
    _, body = split_frontmatter_text(markdown_text)
    options: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, line in enumerate(body.splitlines()):
        match = re.match(r"^##\s+(.+)$", line.strip())
        if not match:
            continue
        label = clean_label(match.group(1), limit=40)
        target_id = inline_target_id("h2", index)
        if target_id in seen:
            continue
        seen.add(target_id)
        options.append(
            {
                "id": target_id,
                "kind": "h2",
                "lineIndex": index,
                "label": label,
                "description": f"H2 · {label}",
            }
        )

    fallback_paragraphs = paragraph_targets(markdown_text, 2)
    for index, target in enumerate(fallback_paragraphs, start=1):
        line_index = int(target.get("lineIndex") or 0)
        target_id = inline_target_id("paragraph", line_index)
        if target_id in seen:
            continue
        seen.add(target_id)
        label = clean_label(str(target.get("label", "")).strip() or f"正文段落 {index}", limit=40)
        options.append(
            {
                "id": target_id,
                "kind": "paragraph",
                "lineIndex": line_index,
                "label": label,
                "description": f"段落参考 {index} · {label}",
            }
        )

    if not options:
        options.append(
            {
                "id": inline_target_id("paragraph", 0),
                "kind": "paragraph",
                "lineIndex": 0,
                "label": "正文开头",
                "description": "段落参考 · 正文开头",
            }
        )
    return options


def resolve_inline_target_state(markdown_text: str, state: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, dict[str, Any]]]:
    inline_state = state.get("inlineImages", {})
    if not isinstance(inline_state, dict):
        inline_state = {}
        state["inlineImages"] = inline_state
    options = inline_target_catalog(markdown_text)
    option_map = {str(option.get("id", "")).strip(): option for option in options}
    defaults = compute_inline_targets(markdown_text, 2)
    default_positions: dict[str, str] = {}
    for index, target in enumerate(defaults, start=1):
        target_id = inline_target_id(str(target.get("kind", "paragraph")).strip() or "paragraph", int(target.get("lineIndex") or 0))
        if target_id in option_map:
            default_positions[str(index)] = target_id
    if options and "1" not in default_positions:
        default_positions["1"] = str(options[0].get("id", "")).strip()
    if options and "2" not in default_positions:
        fallback_index = 1 if len(options) > 1 else 0
        default_positions["2"] = str(options[fallback_index].get("id", "")).strip()

    current_positions = inline_state.get("positions", {})
    if not isinstance(current_positions, dict):
        current_positions = {}
    resolved_positions: dict[str, str] = {}
    for slot in (1, 2):
        key = str(slot)
        target_id = str(current_positions.get(key, current_positions.get(slot, "")) or "").strip()
        if target_id not in option_map:
            target_id = default_positions.get(key, "")
        if target_id in option_map:
            resolved_positions[key] = target_id
    inline_state["positions"] = resolved_positions

    items = inline_state.get("items", [])
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            slot = clamp_int(item.get("slot"), 1, 2, 1)
            target_id = resolved_positions.get(str(slot), "")
            target = option_map.get(target_id)
            if not target:
                continue
            item["targetId"] = target["id"]
            item["targetKind"] = target["kind"]
            item["targetLineIndex"] = int(target["lineIndex"])
            item["targetLabel"] = target["label"]
    return options, resolved_positions, option_map


def compute_inline_targets(markdown_text: str, count: int) -> list[dict[str, Any]]:
    _, body = split_frontmatter_text(markdown_text)
    lines = body.splitlines()
    h2_targets: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^##\s+(.+)$", line.strip())
        if match:
            h2_targets.append({"lineIndex": index, "label": clean_label(match.group(1)), "kind": "h2"})

    if count <= 0:
        return []
    if count == 1:
        if h2_targets:
            return [h2_targets[0]]
        return paragraph_targets(markdown_text, 1)
    if len(h2_targets) >= count:
        return h2_targets[:count]
    return paragraph_targets(markdown_text, count)


def compute_section_targets(markdown_text: str, limit: int = 6) -> list[dict[str, Any]]:
    _, body = split_frontmatter_text(markdown_text)
    targets: list[dict[str, Any]] = []
    for index, line in enumerate(body.splitlines()):
        match = re.match(r"^##\s+(.+)$", line.strip())
        if not match:
            continue
        targets.append(
            {
                "lineIndex": index,
                "label": clean_label(match.group(1), limit=40),
                "kind": "h2",
            }
        )
        if len(targets) >= limit:
            break
    return targets


def inject_inline_images(markdown_text: str, inline_items: list[dict[str, Any]], *, mode: str) -> str:
    if not inline_items:
        return markdown_text
    frontmatter, body = split_frontmatter_text(markdown_text)
    body_lines = body.splitlines()
    usable_items: list[dict[str, Any]] = []
    for item in inline_items:
        if not isinstance(item, dict):
            continue
        local_path = str(item.get("localPath", "")).strip()
        preview_url = asset_preview_url(local_path) if mode == "preview" and local_path and file_exists_relative(local_path) else ""
        resolved_url = preview_url or str(item.get("previewUrl" if mode == "preview" else "draftUrl", "")).strip()
        if not resolved_url:
            continue
        enriched = copy.deepcopy(item)
        enriched["_renderUrl"] = resolved_url
        usable_items.append(enriched)
    if not usable_items:
        return markdown_text

    usable_items.sort(key=lambda item: clamp_int(item.get("slot"), 1, 2, 1))
    fallback_targets = compute_inline_targets(markdown_text, min(2, len(usable_items)))
    fallback_by_slot = {str(index): target for index, target in enumerate(fallback_targets, start=1)}
    insertions: list[tuple[int, list[str]]] = []
    for index, item in enumerate(usable_items, start=1):
        url = str(item.get("_renderUrl", "")).strip()
        if not url:
            continue
        slot = str(clamp_int(item.get("slot"), 1, 2, index))
        target_kind = str(item.get("targetKind", "")).strip()
        target_line_index = item.get("targetLineIndex")
        target_label = str(item.get("targetLabel", "")).strip()
        if target_kind not in {"h2", "paragraph"}:
            fallback_target = fallback_by_slot.get(slot, {})
            target_kind = str(fallback_target.get("kind", "paragraph")).strip() or "paragraph"
            target_line_index = int(fallback_target.get("lineIndex") or 0)
            target_label = str(fallback_target.get("label", "")).strip()
        insertion_index = clamp_int(target_line_index, 0, max(len(body_lines), 0), 0)
        alt = clean_label(str(item.get("label", "")).strip() or target_label or "正文插图")
        if target_kind == "h2":
            insertion_index += 1
        insertions.append((insertion_index, ["", f"![{alt}]({url})", ""]))

    for line_index, block_lines in sorted(insertions, key=lambda pair: pair[0], reverse=True):
        body_lines[line_index:line_index] = block_lines

    rebuilt = "\n".join(body_lines).strip("\n")
    if rebuilt:
        rebuilt += "\n"
    return frontmatter + rebuilt


def extract_live_reference_theme(reference_url: str, theme_name: str, base_theme: str) -> tuple[Any, dict[str, Any]]:
    script = FRONTEND_DIR / "extract_live_reference.js"
    if not script.exists():
        raise FileNotFoundError(f"Live extractor not found: {script}")
    result = subprocess.run(
        ["node", str(script), reference_url, str(REFERENCE_SHOTS_DIR)],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(FRONTEND_DIR),
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise ValueError("Live extractor returned invalid JSON.")
    theme_payload = payload.get("theme", {})
    if not isinstance(theme_payload, dict):
        raise ValueError("Live extractor returned invalid theme mapping.")
    meta = payload.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}
    meta["base_theme"] = base_theme
    meta["source"] = reference_url
    return theme_from_mapping(theme_payload, name=theme_name, base_theme=base_theme), meta


def warning_from_meta(meta: dict[str, Any]) -> str:
    if meta.get("weak_extraction"):
        warning = str(meta.get("warning", "")).strip()
        if meta.get("is_wechat_article"):
            hint = str(meta.get("hint", "")).strip()
            return f"{warning} {hint}".strip()
        return warning or "参考样式抽取较弱，建议作为基础主题微调使用。"
    if meta.get("imageDriven"):
        return (
            "这篇参考页以图片模块驱动视觉效果。当前只会跟随字体、宽度、间距和基础颜色，"
            "不会复刻首图、章节横幅或图形模块。"
        )
    return ""


def apply_layout_selection(
    article_dir: Path,
    state: dict[str, Any],
    *,
    theme: str,
    template: str,
    theme_file: str,
    reference_url: str,
) -> tuple[dict[str, Any], str]:
    layout = state["layout"]
    warning = ""
    extraction_meta: dict[str, Any] = {}
    selected_theme_file = theme_file
    clean_reference = reference_url.strip()

    if clean_reference:
        theme_name_for_file = f"{article_dir.name}-reference"
        try:
            theme_obj, extraction_meta = extract_live_reference_theme(clean_reference, theme_name_for_file, theme)
        except Exception:
            theme_obj, extraction_meta = extract_reference_theme(clean_reference, theme_name=theme_name_for_file, base_theme=theme)
        THEME_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output = THEME_OUTPUT_DIR / f"{theme_name_for_file}.json"
        save_theme(theme_obj, output, meta=extraction_meta)
        selected_theme_file = relative_to_root(output)
        warning = warning_from_meta(extraction_meta)

    layout.update(
        {
            "theme": theme,
            "template": template,
            "themeFile": selected_theme_file,
            "referenceUrl": clean_reference,
            "warning": warning,
            "extractionMeta": extraction_meta,
            "updatedAt": now_text(),
        }
    )
    state.setdefault("tone", {})["theme"] = theme
    state.setdefault("typography", {})["template"] = template
    state.get("tone", {})["updatedAt"] = now_text()
    state.get("typography", {})["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    return state, warning


def article_updated_at(article_dir: Path) -> str:
    candidates = [article_dir / "publish-pack.json", article_dir / "doocs.md", article_state_path(article_dir)]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return ""
    latest = max(existing, key=lambda path: path.stat().st_mtime)
    return format_mtime(latest)


def first_paragraph(markdown_text: str) -> str:
    _, body = split_frontmatter(markdown_text)
    for block in re.split(r"\n\s*\n", body):
        stripped = block.strip()
        if stripped and not stripped.startswith("#"):
            return clean_label(stripped, limit=80)
    return ""


def article_summary(article_dir: Path) -> dict[str, Any]:
    slug = article_dir.name
    pack, markdown = load_publish_inputs(article_dir)
    state = load_studio_state(article_dir)
    title = str(pack.get("title", slug)).strip() or slug
    summary = str(pack.get("summary", "")).strip() or first_paragraph(markdown)
    author = str(pack.get("author", "")).strip()
    cover_candidate = current_cover_candidate(state)
    return {
        "id": slug,
        "title": title,
        "summary": summary,
        "author": author,
        "charCount": len(markdown),
        "updatedAt": article_updated_at(article_dir),
        "path": relative_to_root(article_dir),
        "status": {
            "hasTheme": bool(state.get("layout", {}).get("themeFile") or state.get("layout", {}).get("referenceUrl")),
            "hasCover": bool(cover_candidate),
            "hasDraft": bool(state.get("draft", {}).get("mediaId")),
            "inlineCount": len(state.get("inlineImages", {}).get("items", [])),
        },
    }


def build_articles_list() -> list[dict[str, Any]]:
    if not CONTENT_DIR.exists():
        return []
    items: list[dict[str, Any]] = []
    for article_dir in sorted(CONTENT_DIR.iterdir()):
        if not article_dir.is_dir():
            continue
        if not (article_dir / "publish-pack.json").exists() or not (article_dir / "doocs.md").exists():
            continue
        items.append(article_summary(article_dir))
    return items


def render_preview_for_article(article_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    formatter_runtime = load_wechat_formatter_runtime()
    pack, markdown = load_publish_inputs(article_dir)
    layout = state.get("layout", {})
    typography = state.get("typography", {}) if isinstance(state.get("typography", {}), dict) else {}
    resolve_inline_target_state(markdown, state)
    resolved_theme, theme_name, template_name, _theme_file = resolve_render_theme(state)
    preview_markdown = inject_inline_images(markdown, state.get("inlineImages", {}).get("items", []), mode="preview")
    wechat_safe_metadata_overrides = build_render_metadata(article_dir, state, mode="preview", wechat_safe=True)
    rendered = formatter_runtime.render_wechat_preview(
        preview_markdown,
        theme=resolved_theme,
        typography=typography,
        metadata_overrides=wechat_safe_metadata_overrides,
        template_name=None,
        wechat_safe=True,
    )
    return {
        "title": str(pack.get("title", article_dir.name)).strip() or article_dir.name,
        "summary": str(pack.get("summary", "")).strip(),
        "charCount": len(preview_markdown),
        "bodyHtml": rendered["bodyHtml"],
        "standaloneHtml": rendered["standaloneHtml"],
        "sourceHtml": rendered["sourceHtml"],
        "wechatSafeBodyHtml": rendered["wechatSafeBodyHtml"],
        "wechatSafeStandaloneHtml": rendered["wechatSafeStandaloneHtml"],
        "wechatSafeSourceHtml": rendered["wechatSafeSourceHtml"],
        "theme": rendered["theme"],
        "template": template_name,
        "themeFile": str(layout.get("themeFile", "")).strip(),
        "warning": str(layout.get("warning", "")).strip(),
        "extractionMeta": layout.get("extractionMeta", {}),
        "pushMode": "wechat-safe",
        "ready": True,
        "tone": state.get("tone", {}),
        "typography": state.get("typography", {}),
        "themeName": theme_name,
        "editableBlocks": extract_editable_text_blocks(markdown),
    }


def article_detail(slug: str) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    pack, markdown = load_publish_inputs(article_dir)
    state = load_studio_state(article_dir)
    inline_target_options, inline_positions, _inline_option_map = resolve_inline_target_state(markdown, state)
    cover_candidate = current_cover_candidate(state)
    layout = state.get("layout", {})
    source_files = {
        "source": {
            "name": "source.md",
            "path": relative_to_root(article_dir / "source.md"),
            "exists": (article_dir / "source.md").exists(),
        },
        "doocs": {
            "name": "doocs.md",
            "path": relative_to_root(article_dir / "doocs.md"),
            "exists": True,
        },
        "publishPack": {
            "name": "publish-pack.json",
            "path": relative_to_root(article_dir / "publish-pack.json"),
            "exists": True,
        },
    }
    generated_cover = state.get("cover", {}).get("generated")
    if not isinstance(generated_cover, dict):
        generated_cover = None
    generated_cover = enrich_asset_record(generated_cover) if generated_cover else None
    cover_history_records = merge_asset_history(
        state.get("cover", {}).get("history", []) if isinstance(state.get("cover", {}).get("history", []), list) else [],
        scan_local_asset_history(article_dir, "cover"),
        limit=24,
    )
    cover_history = [item for item in (enrich_asset_record(entry) for entry in cover_history_records) if item]
    cover_module = next((item for item in cover_history if str(item.get("localPath", "")).strip() == cover_candidate), None)
    if not cover_module and cover_candidate and file_exists_relative(cover_candidate):
        cover_module = {
            "localPath": cover_candidate,
            "localExists": True,
            "localPreviewUrl": asset_preview_url(cover_candidate),
            "previewUrl": "",
            "draftUrl": "",
            "preset": "selected-cover",
        }
    cover_module_current_state = state.get("coverModules", {}).get("current")
    cover_module_current = enrich_asset_record(cover_module_current_state) if isinstance(cover_module_current_state, dict) else None
    cover_module_history_records = merge_asset_history(
        state.get("coverModules", {}).get("history", []) if isinstance(state.get("coverModules", {}).get("history", []), list) else [],
        scan_local_asset_history(article_dir, "cover-module"),
        limit=24,
    )
    cover_module_history = [item for item in (enrich_asset_record(entry) for entry in cover_module_history_records) if item]
    inline_items = [
        item
        for item in (enrich_asset_record(entry) for entry in state.get("inlineImages", {}).get("items", []))
        if item
    ]
    inline_history_records = merge_asset_history(
        state.get("inlineImages", {}).get("history", []) if isinstance(state.get("inlineImages", {}).get("history", []), list) else [],
        scan_local_asset_history(article_dir, "inline"),
        limit=48,
    )
    inline_history = [item for item in (enrich_asset_record(entry) for entry in inline_history_records) if item]
    section_items = [
        item
        for item in (enrich_asset_record(entry) for entry in state.get("sectionModules", {}).get("items", []))
        if item
    ]
    section_history_records = merge_asset_history(
        state.get("sectionModules", {}).get("history", []) if isinstance(state.get("sectionModules", {}).get("history", []), list) else [],
        scan_local_asset_history(article_dir, "section"),
        limit=48,
    )
    section_history = [item for item in (enrich_asset_record(entry) for entry in section_history_records) if item]
    preview: dict[str, Any]
    if preview_initialized(state):
        try:
            preview = render_preview_for_article(article_dir, state)
        except Exception as error:  # noqa: BLE001
            preview = {
                "title": str(pack.get("title", article_dir.name)).strip() or article_dir.name,
                "summary": str(pack.get("summary", "")).strip(),
                "charCount": len(markdown),
                "bodyHtml": "",
                "standaloneHtml": "",
                "sourceHtml": "",
                "wechatSafeBodyHtml": "",
                "wechatSafeStandaloneHtml": "",
                "wechatSafeSourceHtml": "",
                "theme": {},
                "themeFile": str(layout.get("themeFile", "")).strip(),
                "warning": str(error),
                "extractionMeta": {},
                "error": str(error),
                "pushMode": "wechat-safe",
                "ready": False,
                "statusText": "预览生成失败，请调整设置后重试。",
            }
    else:
        preview = {
            "title": str(pack.get("title", article_dir.name)).strip() or article_dir.name,
            "summary": str(pack.get("summary", "")).strip(),
            "charCount": len(markdown),
            "bodyHtml": "",
            "standaloneHtml": "",
            "sourceHtml": "",
            "wechatSafeBodyHtml": "",
            "wechatSafeStandaloneHtml": "",
            "wechatSafeSourceHtml": "",
            "theme": {},
            "themeFile": str(layout.get("themeFile", "")).strip(),
            "warning": "",
            "extractionMeta": {},
            "pushMode": "wechat-safe",
            "ready": False,
            "statusText": "上传后默认不自动生成预览。先选风格和配色，再点“立即刷新预览”。",
        }

    return {
        "article": {
            "id": article_dir.name,
            "title": str(pack.get("title", article_dir.name)).strip() or article_dir.name,
            "summary": str(pack.get("summary", "")).strip() or first_paragraph(markdown),
            "author": str(pack.get("author", "")).strip(),
            "charCount": len(markdown),
            "updatedAt": article_updated_at(article_dir),
            "path": relative_to_root(article_dir),
            "sourceFiles": source_files,
        },
        "source": state.get("source", {}),
        "layout": {
            "theme": str(layout.get("theme", DEFAULT_THEME)).strip() or DEFAULT_THEME,
            "template": str(layout.get("template", "default")).strip() or "default",
            "themeFile": str(layout.get("themeFile", "")).strip(),
            "referenceUrl": str(layout.get("referenceUrl", "")).strip(),
            "warning": str(layout.get("warning", "")).strip(),
            "extractionMeta": layout.get("extractionMeta", {}),
            "updatedAt": str(layout.get("updatedAt", "")).strip(),
        },
        "tone": state.get("tone", {}),
        "typography": state.get("typography", {}),
        "images": {
            "coverCandidatePath": cover_candidate,
            "coverCandidateExists": bool(cover_candidate and file_exists_relative(cover_candidate)),
            "coverGenerated": generated_cover,
            "coverHistory": cover_history,
            "coverModule": cover_module,
            "coverModuleCurrent": cover_module_current,
            "coverModuleHistory": cover_module_history,
            "coverModuleStyle": str(state.get("coverModules", {}).get("style", "collage-editorial")).strip() or "collage-editorial",
            "coverPrompt": str(state.get("cover", {}).get("customPrompt", "")).strip(),
            "coverCandidatePreviewUrl": asset_preview_url(cover_candidate) if cover_candidate and file_exists_relative(cover_candidate) else "",
            "inlineItems": inline_items,
            "inlineHistory": inline_history,
            "inlineTargetOptions": inline_target_options,
            "inlinePositions": inline_positions,
            "inlinePrompt": str(state.get("inlineImages", {}).get("customPrompt", "")).strip(),
            "inlineUpdatedAt": str(state.get("inlineImages", {}).get("updatedAt", "")).strip(),
            "sectionModules": section_items,
            "sectionHistory": section_history,
            "sectionPrompt": str(state.get("sectionModules", {}).get("customPrompt", "")).strip(),
            "sectionUpdatedAt": str(state.get("sectionModules", {}).get("updatedAt", "")).strip(),
        },
        "draft": state.get("draft", {}),
        "preview": preview,
    }


def action_response(slug: str, message: str) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "detail": article_detail(slug),
    }


def download_binary(url: str, output_path: Path) -> None:
    load_generate_image_runtime().download_binary(url, output_path)


def usable_generated_asset_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        return raw
    if raw.startswith("//"):
        return raw

    local_value = unquote(parsed.path) if parsed.scheme == "file" else raw
    local_path = Path(local_value).expanduser()
    if local_path.exists() and local_path.is_file():
        return str(local_path)
    return ""


def generate_image_asset(
    *,
    title: str,
    summary: str,
    article_path: Path,
    preset: str,
    style: str,
) -> dict[str, Any]:
    return load_generate_image_runtime().generate_image_asset(
        title=title,
        summary=summary,
        article_path=article_path,
        preset=preset,
        style=style,
        workspace_root=ROOT.parent,
    )


def generate_cover_module_asset(*, source_path: Path, output_path: Path, style_id: str) -> None:
    if not IMAGE_VENV_PYTHON.exists():
        raise RuntimeError(f"封面模块图环境未就绪：{IMAGE_VENV_PYTHON}")
    if not COLLAGE_SCRIPT.exists():
        raise RuntimeError(f"封面模块图脚本不存在：{COLLAGE_SCRIPT}")
    result = subprocess.run(
        [
            str(IMAGE_VENV_PYTHON),
            str(COLLAGE_SCRIPT),
            str(source_path),
            str(output_path),
            "--style",
            style_id,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "封面模块图生成失败").strip())
    if not output_path.exists():
        raise RuntimeError("封面模块图生成失败：未找到输出文件。")


def compose_image_style(base_style: str, custom_prompt: str) -> str:
    return load_generate_image_runtime().compose_image_style(base_style, custom_prompt)


def section_word(slot: int) -> str:
    mapping = {
        1: "ONE",
        2: "TWO",
        3: "THREE",
        4: "FOUR",
        5: "FIVE",
        6: "SIX",
    }
    return mapping.get(slot, "SECTION")


def cover_style_for_layout(template: str, theme: str, base_style: str) -> str:
    if template == "xiumi-spring-letter":
        return (
            "wechat cover module, spring postcard collage, blurred spring foliage background, "
            "layered paper sheets, white photo frame, soft olive and cream palette, "
            "editorial chinese typography, clean composition, no person, no product mockup, "
            "magazine-like xiumi cover module, gentle spring outing mood"
        )
    if template == "xiumi-winter-ins":
        return (
            "winter editorial cover module, blue gray seasonal magazine, minimal ins layout, "
            "cold daylight, clean title area, numbered section feeling, no person, no product mockup"
        )
    if theme == "spring-whisper":
        return (
            "spring editorial cover, soft cream background, olive green accents, "
            "gentle magazine layout, clean chinese typography, no person, no product mockup"
        )
    return base_style


def section_style_for_layout(template: str, theme: str, slot: int, label: str, base_style: str) -> str:
    if template == "xiumi-spring-letter":
        return (
            f"wechat section banner module, xiumi spring style, centered large {section_word(slot)} word above ribbon, "
            f"olive green paper ribbon title strip, lime accent block on left edge, soft offset shadow block behind, "
            f"clean chinese title text '{label}', cream paper texture background, gentle spring palette, "
            "flat editorial graphic, no photography, no person, no product, single module image"
        )
    if template == "xiumi-winter-ins":
        return (
            f"wechat section banner module, winter ins editorial style, centered blue rounded number badge {slot:02d}, "
            f"clean chinese subtitle '{label}', cool blue gray seasonal palette, minimal magazine layout, "
            "flat editorial graphic, no photography, no person, no product, single module image"
        )
    if theme == "spring-whisper":
        return (
            f"soft spring section ribbon, clean chinese title '{label}', olive green title strip, "
            "paper cut collage feeling, gentle cream background, flat editorial module, no photography"
        )
    return f"{base_style}; section focus: {label}; layout: section ribbon banner"


def cover_style_config(style_id: str) -> dict[str, str]:
    for item in COVER_STYLE_CHOICES:
        if item["id"] == style_id:
            return item
    return COVER_STYLE_CHOICES[0]


def generate_cover_candidate_record(
    article_dir: Path,
    state: dict[str, Any],
    *,
    pack: dict[str, Any],
    markdown_text: str,
    custom_prompt: str,
    style_id: str,
) -> dict[str, Any]:
    layout = state.get("layout", {}) if isinstance(state.get("layout", {}), dict) else {}
    template = str(layout.get("template", "default")).strip() or "default"
    theme = effective_theme_name(state)
    title = str(pack.get("title", article_dir.name)).strip() or article_dir.name
    summary = str(pack.get("summary", "")).strip() or "微信公众号文章封面"
    archetype = infer_article_archetype(title, summary, markdown_text)
    style_config = cover_style_config(style_id)
    preset = cover_preset_for_archetype(archetype)
    base_style = (
        f"{style_config['style']}; {tone_prompt_context(state)}; article archetype {archetype}; "
        f"{cover_style_for_layout(template, theme, style_config['style'])}"
    )
    style = compose_image_style(base_style, custom_prompt)
    generated = generate_image_asset(
        title=title,
        summary=summary,
        article_path=article_dir / "doocs.md",
        preset=preset,
        style=style,
    )
    filename = f"cover-{style_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    local_path = article_asset_dir(article_dir) / filename
    download_binary(generated["previewUrl"], local_path)
    generated.update(
        {
            "preset": preset,
            "styleId": style_id,
            "styleLabel": style_config["label"],
            "customPrompt": custom_prompt,
            "style": style,
            "localPath": relative_to_root(local_path),
            "createdAt": now_text(),
        }
    )
    return generated


def generate_cover(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    pack, markdown_text = load_publish_inputs(article_dir)
    custom_prompt = str(payload.get("prompt") or state.get("cover", {}).get("customPrompt", "")).strip()
    requested_style_id = str(payload.get("styleId") or "").strip()
    style_ids = [requested_style_id] if requested_style_id else [item["id"] for item in COVER_STYLE_CHOICES]
    generated_items = [
        generate_cover_candidate_record(
            article_dir,
            state,
            pack=pack,
            markdown_text=markdown_text,
            custom_prompt=custom_prompt,
            style_id=style_id,
        )
        for style_id in style_ids
    ]
    if not generated_items:
        raise RuntimeError("未生成任何封面候选。")
    state["cover"]["generated"] = generated_items[-1]
    state["cover"]["customPrompt"] = custom_prompt
    existing_history = state.get("cover", {}).get("history", [])
    state["cover"]["history"] = merge_asset_history(
        existing_history if isinstance(existing_history, list) else [],
        generated_items,
        limit=24,
    )
    if not str(state.get("cover", {}).get("candidatePath", "")).strip():
        state["cover"]["candidatePath"] = str(generated_items[0].get("localPath", "")).strip()
    state["cover"]["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    message = "封面候选已生成，可以切换当前封面。"
    if requested_style_id:
        message = "封面已重新生成。"
    return action_response(slug, message)


def generate_cover_module(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    source_relative = current_cover_candidate(state)
    if not source_relative:
        raise RuntimeError("请先选择一张封面图，再处理封面风格。")
    source_path = resolve_workspace_path(source_relative)
    style_id = str(payload.get("style") or state.get("coverModules", {}).get("style") or "collage-editorial").strip() or "collage-editorial"
    filename = f"cover-module-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    local_path = article_asset_dir(article_dir) / filename
    generate_cover_module_asset(source_path=source_path, output_path=local_path, style_id=style_id)
    item = {
        "style": style_id,
        "localPath": relative_to_root(local_path),
        "createdAt": now_text(),
    }
    state["coverModules"]["current"] = item
    state["coverModules"]["style"] = style_id
    existing_history = state.get("coverModules", {}).get("history", [])
    state["coverModules"]["history"] = merge_asset_history(existing_history if isinstance(existing_history, list) else [], [item], limit=24)
    state["coverModules"]["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    return action_response(slug, "封面风格处理已完成，可用于正文顶部视觉模块。")


def select_cover_module(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    relative_path = str(payload.get("path", "")).strip()
    if not relative_path:
        raise RuntimeError("需要提供封面模块素材路径。")
    resolved = resolve_workspace_path(relative_path)
    history = state.get("coverModules", {}).get("history", [])
    if not isinstance(history, list):
        history = []
    match_item = None
    for item in history:
        if not isinstance(item, dict):
            continue
        if str(item.get("localPath", "")).strip() == relative_to_root(resolved):
            match_item = copy.deepcopy(item)
            break
    if not match_item:
        match_item = {
            "style": "collage-editorial",
            "localPath": relative_to_root(resolved),
            "createdAt": now_text(),
        }
    state["coverModules"]["current"] = match_item
    state["coverModules"]["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    return action_response(slug, "当前封面模块已更新。")


def select_cover_candidate(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    relative_path = str(payload.get("path", "")).strip()
    if not relative_path:
        generated = state.get("cover", {}).get("generated") or {}
        relative_path = str(generated.get("localPath", "")).strip()
    if not relative_path:
        raise RuntimeError("当前没有可选中的封面素材。")
    resolved = resolve_workspace_path(relative_path)
    state["cover"]["candidatePath"] = relative_to_root(resolved)
    state["cover"]["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    return action_response(slug, "当前封面候选已更新。")


def resolve_article_asset_path(article_dir: Path, relative_path: str) -> tuple[Path, str]:
    clean_relative = ensure_relative_path(relative_path)
    asset_path = (ROOT / clean_relative).resolve()
    asset_dir = article_asset_dir(article_dir).resolve()
    try:
        asset_path.relative_to(asset_dir)
    except ValueError as error:
        raise RuntimeError("只能删除当前文章生成的本地图片。") from error
    return asset_path, relative_to_root(asset_path)


def latest_existing_asset_record(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in reversed(items):
        if not isinstance(item, dict):
            continue
        local_path = str(item.get("localPath", "")).strip()
        if local_path and file_exists_relative(local_path):
            return copy.deepcopy(item)
    return None


def delete_cover_asset(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    relative_path = str(payload.get("path", "")).strip()
    if not relative_path:
        raise RuntimeError("需要提供要删除的封面路径。")
    asset_path, normalized_path = resolve_article_asset_path(article_dir, relative_path)
    if asset_path.exists() and asset_path.is_file():
        asset_path.unlink()

    cover_state = state.get("cover", {})
    if not isinstance(cover_state, dict):
        cover_state = {}
        state["cover"] = cover_state

    generated = cover_state.get("generated")
    if isinstance(generated, dict) and str(generated.get("localPath", "")).strip() == normalized_path:
        cover_state["generated"] = None

    history = cover_state.get("history", [])
    if not isinstance(history, list):
        history = []
    history = [
        item
        for item in history
        if not (isinstance(item, dict) and str(item.get("localPath", "")).strip() == normalized_path)
    ]
    cover_state["history"] = history

    if str(cover_state.get("candidatePath", "")).strip() == normalized_path:
        fallback = next(
            (
                str(item.get("localPath", "")).strip()
                for item in reversed(history)
                if isinstance(item, dict) and file_exists_relative(str(item.get("localPath", "")).strip())
            ),
            "",
        )
        cover_state["candidatePath"] = fallback

    if not isinstance(cover_state.get("generated"), dict):
        cover_state["generated"] = latest_existing_asset_record(history)

    cover_state["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    return action_response(slug, "封面图片已删除。")


def generate_inline_item(
    article_dir: Path,
    *,
    pack: dict[str, Any],
    preset: str,
    custom_prompt: str,
    target: dict[str, Any],
    slot: int,
    state: dict[str, Any],
) -> dict[str, Any]:
    title = str(pack.get("title", article_dir.name)).strip() or article_dir.name
    label = str(target.get("label", "")).strip() or f"正文段落 {slot}"
    style = compose_image_style(
        f"{tone_prompt_context(state)}; article companion image; section focus: {label}",
        custom_prompt,
    )
    generated = generate_image_asset(
        title=title,
        summary=label,
        article_path=article_dir / "doocs.md",
        preset=preset,
        style=style,
    )
    filename = f"inline-{slot}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    local_path = article_asset_dir(article_dir) / filename
    download_binary(generated["previewUrl"], local_path)
    return {
        "slot": slot,
        "label": label,
        "targetId": str(target.get("id", "")).strip(),
        "targetKind": str(target.get("kind", "paragraph")).strip() or "paragraph",
        "targetLineIndex": int(target.get("lineIndex") or 0),
        "targetLabel": label,
        "preset": preset,
        "customPrompt": custom_prompt,
        "style": style,
        "prompt": generated["prompt"],
        "previewUrl": generated["previewUrl"],
        "draftUrl": generated["draftUrl"],
        "mediaId": generated["mediaId"],
        "width": generated["width"],
        "height": generated["height"],
        "localPath": relative_to_root(local_path),
        "createdAt": now_text(),
    }


def generate_inline_images(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    pack, markdown = load_publish_inputs(article_dir)
    archetype = infer_article_archetype(
        str(pack.get("title", article_dir.name)).strip() or article_dir.name,
        str(pack.get("summary", "")).strip(),
        markdown,
    )
    preset = str(payload.get("preset") or inline_preset_for_archetype(archetype)).strip()
    custom_prompt = str(payload.get("prompt") or state.get("inlineImages", {}).get("customPrompt", "")).strip()
    requested_slot = clamp_int(payload.get("slot"), 0, 2, 0)
    if isinstance(payload.get("inlinePositions"), dict):
        update_editor_state_from_payload(state, {"inlinePositions": payload.get("inlinePositions", {})})
    _inline_target_options, inline_positions, inline_option_map = resolve_inline_target_state(markdown, state)
    targets = []
    for slot in (1, 2):
        target = inline_option_map.get(inline_positions.get(str(slot), ""))
        if target:
            targets.append(copy.deepcopy(target))
    if requested_slot:
        targets = [target for index, target in enumerate(targets, start=1) if index == requested_slot]
        if not targets:
            raise RuntimeError("当前文章没有可替换的插图位置。")
    items: list[dict[str, Any]] = []
    batch_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    for index, target in enumerate(targets, start=1):
        slot = requested_slot or index
        item = generate_inline_item(
            article_dir,
            pack=pack,
            preset=preset,
            custom_prompt=custom_prompt,
            target=target,
            slot=slot,
            state=state,
        )
        item["batchId"] = batch_id
        items.append(item)

    if requested_slot and isinstance(state.get("inlineImages", {}).get("items", []), list):
        next_items: list[dict[str, Any]] = []
        replaced = False
        for existing in state.get("inlineImages", {}).get("items", []):
            if not isinstance(existing, dict):
                continue
            if int(existing.get("slot") or 0) == requested_slot:
                next_items.extend(items)
                replaced = True
            else:
                next_items.append(existing)
        if not replaced:
            next_items.extend(items)
        next_items.sort(key=lambda item: int(item.get("slot") or 0))
        state["inlineImages"]["items"] = next_items
    else:
        state["inlineImages"]["items"] = items
    state["inlineImages"]["customPrompt"] = custom_prompt
    existing_history = state.get("inlineImages", {}).get("history", [])
    state["inlineImages"]["history"] = merge_asset_history(
        existing_history if isinstance(existing_history, list) else [],
        items,
        limit=48,
    )
    state["inlineImages"]["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    return action_response(slug, "正文插图已生成。")


def select_inline_image(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    _pack, markdown = load_publish_inputs(article_dir)
    slot = clamp_int(payload.get("slot"), 1, 2, 1)
    relative_path = str(payload.get("path", "")).strip()
    if not relative_path:
        raise RuntimeError("需要提供要替换的正文插图路径。")
    resolved = resolve_workspace_path(relative_path)
    history = state.get("inlineImages", {}).get("history", [])
    if not isinstance(history, list):
        history = []
    match_item = None
    for item in history:
        if not isinstance(item, dict):
            continue
        if int(item.get("slot") or 0) == slot and str(item.get("localPath", "")).strip() == relative_to_root(resolved):
            match_item = copy.deepcopy(item)
            break
    if not match_item:
        raise RuntimeError("找不到对应的正文插图历史记录。")
    current_items = state.get("inlineImages", {}).get("items", [])
    if not isinstance(current_items, list):
        current_items = []
    replaced = False
    next_items: list[dict[str, Any]] = []
    for item in current_items:
        if isinstance(item, dict) and int(item.get("slot") or 0) == slot:
            next_items.append(match_item)
            replaced = True
        elif isinstance(item, dict):
            next_items.append(item)
    if not replaced:
        next_items.append(match_item)
    next_items.sort(key=lambda item: int(item.get("slot") or 0))
    state["inlineImages"]["items"] = next_items
    resolve_inline_target_state(markdown, state)
    state["inlineImages"]["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    return action_response(slug, "正文插图已切换。")


def delete_inline_asset(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    relative_path = str(payload.get("path", "")).strip()
    if not relative_path:
        raise RuntimeError("需要提供要删除的正文配图路径。")
    asset_path, normalized_path = resolve_article_asset_path(article_dir, relative_path)
    if asset_path.exists() and asset_path.is_file():
        asset_path.unlink()

    inline_state = state.get("inlineImages", {})
    if not isinstance(inline_state, dict):
        inline_state = {}
        state["inlineImages"] = inline_state

    items = inline_state.get("items", [])
    if not isinstance(items, list):
        items = []
    inline_state["items"] = [
        item
        for item in items
        if not (isinstance(item, dict) and str(item.get("localPath", "")).strip() == normalized_path)
    ]

    history = inline_state.get("history", [])
    if not isinstance(history, list):
        history = []
    inline_state["history"] = [
        item
        for item in history
        if not (isinstance(item, dict) and str(item.get("localPath", "")).strip() == normalized_path)
    ]
    inline_state["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    return action_response(slug, "正文配图已删除。")


def update_article_text_block(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    markdown_path = article_dir / "doocs.md"
    if not markdown_path.exists():
        raise RuntimeError("当前文章缺少 doocs.md，暂时无法编辑正文。")

    block_id = str(payload.get("blockId", "")).strip()
    if not block_id:
        raise RuntimeError("需要提供要编辑的正文块。")

    markdown_text = markdown_path.read_text(encoding="utf-8")
    updated_markdown = update_markdown_text_block(markdown_text, block_id, str(payload.get("text", "")))
    markdown_path.write_text(updated_markdown, encoding="utf-8")
    return action_response(slug, "正文已更新。")


def generate_section_modules(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    pack, markdown = load_publish_inputs(article_dir)
    preset = str(payload.get("preset") or "cover-minimal").strip()
    default_style = str(
        payload.get("style") or "spring section banner, soft postcard composition, clean title strip, wechat-safe header module"
    ).strip()
    custom_prompt = str(payload.get("prompt") or state.get("sectionModules", {}).get("customPrompt", "")).strip()
    title = str(pack.get("title", article_dir.name)).strip() or article_dir.name
    layout = state.get("layout", {}) if isinstance(state.get("layout", {}), dict) else {}
    template = str(layout.get("template", "default")).strip() or "default"
    theme = str(layout.get("theme", DEFAULT_THEME)).strip() or DEFAULT_THEME
    targets = compute_section_targets(markdown, limit=6)
    if not targets:
        raise RuntimeError("当前文章还没有可生成分节图的 H2 小节。")
    items: list[dict[str, Any]] = []
    batch_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    for index, target in enumerate(targets, start=1):
        label = str(target.get("label", "")).strip() or f"分节 {index}"
        style = compose_image_style(section_style_for_layout(template, theme, index, label, default_style), custom_prompt)
        generated = generate_image_asset(
            title=title,
            summary=f"{section_word(index)} · {label}",
            article_path=article_dir / "doocs.md",
            preset=preset,
            style=style,
        )
        filename = f"section-{index}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
        local_path = article_asset_dir(article_dir) / filename
        download_binary(generated["previewUrl"], local_path)
        items.append(
            {
                "batchId": batch_id,
                "slot": index,
                "label": label,
                "preset": preset,
                "customPrompt": custom_prompt,
                "style": style,
                "prompt": generated["prompt"],
                "previewUrl": generated["previewUrl"],
                "draftUrl": generated["draftUrl"],
                "mediaId": generated["mediaId"],
                "width": generated["width"],
                "height": generated["height"],
                "localPath": relative_to_root(local_path),
                "createdAt": now_text(),
            }
        )
    state["sectionModules"]["items"] = items
    state["sectionModules"]["customPrompt"] = custom_prompt
    existing_history = state.get("sectionModules", {}).get("history", [])
    state["sectionModules"]["history"] = merge_asset_history(existing_history if isinstance(existing_history, list) else [], items, limit=48)
    state["sectionModules"]["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    return action_response(slug, "分节条图已生成，并用于当前模板预览。")


def select_section_module(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    slot = int(payload.get("slot") or 0)
    relative_path = str(payload.get("path", "")).strip()
    if slot <= 0 or not relative_path:
        raise RuntimeError("需要提供分节槽位和素材路径。")
    resolved = resolve_workspace_path(relative_path)
    history = state.get("sectionModules", {}).get("history", [])
    if not isinstance(history, list):
        history = []
    match_item = None
    for item in history:
        if not isinstance(item, dict):
            continue
        if int(item.get("slot") or 0) == slot and str(item.get("localPath", "")).strip() == relative_to_root(resolved):
            match_item = copy.deepcopy(item)
            break
    if not match_item:
        raise RuntimeError("找不到对应的分节模块历史记录。")
    current_items = state.get("sectionModules", {}).get("items", [])
    if not isinstance(current_items, list):
        current_items = []
    replaced = False
    next_items: list[dict[str, Any]] = []
    for item in current_items:
        if isinstance(item, dict) and int(item.get("slot") or 0) == slot:
            next_items.append(match_item)
            replaced = True
        elif isinstance(item, dict):
            next_items.append(item)
    if not replaced:
        next_items.append(match_item)
    next_items.sort(key=lambda item: int(item.get("slot") or 0))
    state["sectionModules"]["items"] = next_items
    state["sectionModules"]["updatedAt"] = now_text()
    save_studio_state(article_dir, state)
    return action_response(slug, "当前分节条模块已更新。")


def ensure_text_limit(text: str, limit: int) -> str:
    clean = str(text or "").strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def build_wechat_article_payload(
    pack: dict[str, Any],
    markdown_text: str,
    thumb_media_id: str,
    html: str,
) -> dict[str, Any]:
    title = ensure_text_limit(str(pack.get("title", "")).strip(), 32)
    digest = ensure_text_limit(str(pack.get("summary", "")).strip() or first_paragraph(markdown_text), 128)
    author = ensure_text_limit(str(pack.get("author", "")).strip(), 16)
    return {
        "title": title,
        "author": author,
        "digest": digest,
        "content": html,
        "thumb_media_id": thumb_media_id,
        "show_cover_pic": 1,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }


def import_markdown_article(filename: str, file_bytes: bytes) -> dict[str, Any]:
    try:
        markdown_text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        markdown_text = file_bytes.decode("utf-8-sig")
    if not markdown_text.strip():
        raise RuntimeError("上传的 Markdown 文件为空。")

    metadata, body = split_frontmatter(markdown_text)
    title = str(metadata.get("title", "")).strip() or first_heading(markdown_text) or Path(filename).stem or "未命名文章"
    summary = (
        str(metadata.get("digest", "")).strip()
        or str(metadata.get("summary", "")).strip()
        or str(metadata.get("description", "")).strip()
        or first_paragraph(markdown_text)
    )
    author = str(metadata.get("author", "")).strip()
    article_dir = unique_article_directory(title or Path(filename).stem)
    article_dir.mkdir(parents=True, exist_ok=True)
    article_asset_dir(article_dir).mkdir(parents=True, exist_ok=True)

    normalized_markdown = build_normalized_markdown(metadata, body, title=title, summary=summary, author=author)
    source_path = article_dir / "source.md"
    doocs_path = article_dir / "doocs.md"
    publish_pack_path = article_dir / "publish-pack.json"

    source_path.write_text(markdown_text.replace("\r\n", "\n"), encoding="utf-8")
    doocs_path.write_text(normalized_markdown, encoding="utf-8")
    publish_pack_path.write_text(
        json.dumps(build_publish_pack_payload(title, summary, author), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    state = default_studio_state()
    normalize_state_inplace(state)
    state["source"] = {
        "originalName": filename,
        "markdownPath": relative_to_root(source_path),
        "uploadedAt": now_text(),
        "warnings": import_warnings_from_markdown(markdown_text),
    }
    state["tone"]["theme"] = DEFAULT_THEME
    state["tone"]["primaryColor"] = default_primary_for_theme(DEFAULT_THEME)
    state["tone"]["updatedAt"] = now_text()
    state["typography"]["template"] = "default"
    state["typography"]["updatedAt"] = now_text()
    state["layout"]["theme"] = DEFAULT_THEME
    state["layout"]["template"] = "default"
    state["layout"]["updatedAt"] = now_text()
    save_studio_state(article_dir, state)

    source = state.get("source", {})
    warnings = source.get("warnings", []) if isinstance(source.get("warnings", []), list) else []
    warnings.append("已导入文章。请先选择风格、配色并确认提示词，再手动生成预览、封面和正文配图。")
    source["warnings"] = warnings
    save_studio_state(article_dir, state)

    return {
        "success": True,
        "message": "Markdown 已导入并创建文章。",
        "detail": article_detail(article_dir.name),
    }


def push_article_draft(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    article_dir = resolve_article_dir(slug)
    state = load_studio_state(article_dir)
    update_editor_state_from_payload(state, payload)
    theme = effective_theme_name(state)
    template = effective_template_name(state)
    theme_file = str(state.get("layout", {}).get("themeFile", "")).strip()
    reference_url = str(state.get("layout", {}).get("referenceUrl", "")).strip()
    cover_path_relative = str(payload.get("coverPath") or state.get("cover", {}).get("candidatePath") or "").strip()
    if not cover_path_relative:
        raise RuntimeError("推送草稿前必须先确认一张当前封面。")

    try:
        apply_layout_selection(
            article_dir,
            state,
            theme=theme,
            template=template,
            theme_file=theme_file,
            reference_url=reference_url,
        )
        state = load_studio_state(article_dir)
        resolved_cover = resolve_workspace_path(cover_path_relative)
        state["cover"]["candidatePath"] = relative_to_root(resolved_cover)
        pack, markdown = load_publish_inputs(article_dir)
        resolve_inline_target_state(markdown, state)
        draft_markdown = inject_inline_images(markdown, state.get("inlineImages", {}).get("items", []), mode="draft")
        typography = state.get("typography", {}) if isinstance(state.get("typography", {}), dict) else {}
        config = load_config()
        access_token = get_access_token(config)
        metadata_overrides = build_render_metadata(article_dir, state, mode="draft", wechat_safe=True, access_token=access_token)
        thumb_media_id = upload_cover_image(access_token, resolved_cover)
        resolved_theme, _theme_name, _template_name, _theme_file = resolve_render_theme(state)
        html = apply_html_typography_overrides(
            markdown_to_wechat_html(
                draft_markdown,
                theme=resolved_theme,
                template_name=None,
                metadata_overrides=metadata_overrides,
                wechat_safe=True,
            ),
            typography,
        )
        article = build_wechat_article_payload(pack, draft_markdown, thumb_media_id, html)
        result = create_draft(access_token, article)
        state["draft"] = {
            "mediaId": str(result.get("media_id", "")).strip(),
            "title": article["title"],
            "pushedAt": now_text(),
            "lastError": "",
            "theme": str(state.get("layout", {}).get("theme", DEFAULT_THEME)).strip() or DEFAULT_THEME,
            "template": str(state.get("layout", {}).get("template", "default")).strip() or "default",
            "themeFile": str(state.get("layout", {}).get("themeFile", "")).strip(),
        }
        state["preview"]["initialized"] = True
        state["preview"]["updatedAt"] = now_text()
        save_studio_state(article_dir, state)
    except Exception as error:  # noqa: BLE001
        state["draft"]["lastError"] = str(error)
        save_studio_state(article_dir, state)
        raise

    return action_response(slug, "已推送到公众号草稿箱。")


class AppHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def normalize_path(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/frontend", "/frontend/"}:
            self.path = "/index.html"
        elif parsed.path.startswith("/frontend/"):
            self.path = parsed.path[len("/frontend") :]

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/articles":
            self.send_json({"articles": build_articles_list()})
            return
        if path == "/api/settings/status":
            self.send_json(settings_status())
            return
        if path == "/api/assets":
            self.serve_asset(str(query.get("path", [""])[0]))
            return
        if match := ARTICLE_DETAIL_RE.match(path):
            self.send_json({"detail": article_detail(match.group("slug"))})
            return

        self.normalize_path()
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        self.normalize_path()
        super().do_HEAD()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)

        if DRAFT_IMPORT_RE.match(path):
            try:
                filename, file_bytes = parse_markdown_upload(raw_body, self.headers.get("Content-Type", ""))
                response = import_markdown_article(filename, file_bytes)
            except Exception as error:  # noqa: BLE001
                self.send_error_json(str(error), status=HTTPStatus.BAD_REQUEST)
                return
            self.send_json(response)
            return

        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self.send_error_json("Invalid JSON body.", status=HTTPStatus.BAD_REQUEST)
            return

        try:
            if match := LAYOUT_PREVIEW_RE.match(path):
                article_dir = resolve_article_dir(match.group("slug"))
                state = load_studio_state(article_dir)
                update_editor_state_from_payload(state, payload)
                template = effective_template_name(state)
                theme = effective_theme_name(state)
                theme_file = str(state.get("layout", {}).get("themeFile", "")).strip()
                reference_url = str(state.get("layout", {}).get("referenceUrl", "")).strip()
                apply_layout_selection(
                    article_dir,
                    state,
                    template=template,
                    theme=theme,
                    theme_file=theme_file,
                    reference_url=reference_url,
                )
                state["preview"]["initialized"] = True
                state["preview"]["updatedAt"] = now_text()
                save_studio_state(article_dir, state)
                response = action_response(match.group("slug"), "排版预览已刷新。")
            elif match := IMAGE_COVER_RE.match(path):
                response = generate_cover(match.group("slug"), payload)
            elif match := IMAGE_COVER_SELECT_RE.match(path):
                response = select_cover_candidate(match.group("slug"), payload)
            elif match := IMAGE_COVER_DELETE_RE.match(path):
                response = delete_cover_asset(match.group("slug"), payload)
            elif match := IMAGE_COVER_MODULE_RE.match(path):
                response = generate_cover_module(match.group("slug"), payload)
            elif match := IMAGE_COVER_MODULE_SELECT_RE.match(path):
                response = select_cover_module(match.group("slug"), payload)
            elif match := IMAGE_SECTION_RE.match(path):
                response = generate_section_modules(match.group("slug"), payload)
            elif match := IMAGE_SECTION_SELECT_RE.match(path):
                response = select_section_module(match.group("slug"), payload)
            elif match := IMAGE_INLINE_RE.match(path):
                response = generate_inline_images(match.group("slug"), payload)
            elif match := IMAGE_INLINE_SELECT_RE.match(path):
                response = select_inline_image(match.group("slug"), payload)
            elif match := IMAGE_INLINE_DELETE_RE.match(path):
                response = delete_inline_asset(match.group("slug"), payload)
            elif match := TEXT_BLOCK_UPDATE_RE.match(path):
                response = update_article_text_block(match.group("slug"), payload)
            elif match := DRAFT_PUSH_RE.match(path):
                response = push_article_draft(match.group("slug"), payload)
            else:
                self.send_error_json("Endpoint not found.", status=HTTPStatus.NOT_FOUND)
                return
        except Exception as error:  # noqa: BLE001
            self.send_error_json(str(error), status=HTTPStatus.BAD_REQUEST)
            return

        self.send_json(response)

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_asset(self, relative_path: str) -> None:
        clean_path = str(relative_path or "").strip()
        if not clean_path:
            self.send_error_json("Missing asset path.", status=HTTPStatus.BAD_REQUEST)
            return
        try:
            asset_path = resolve_workspace_path(clean_path)
        except FileNotFoundError as error:
            self.send_error_json(str(error), status=HTTPStatus.NOT_FOUND)
            return
        if not asset_path.is_file():
            self.send_error_json("Asset path is not a file.", status=HTTPStatus.BAD_REQUEST)
            return

        content_type, _encoding = mimetypes.guess_type(str(asset_path))
        body = asset_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: HTTPStatus) -> None:
        self.send_json({"success": False, "error": message}, status=status)


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 4173), AppHandler)
    print("Serving content factory on http://127.0.0.1:4173")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
