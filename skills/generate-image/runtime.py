from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


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


def download_binary(url: str, output_path: Path) -> None:
    ensure_parent(output_path)
    value = str(url or "").strip()
    if not value:
        raise RuntimeError("下载图片失败：缺少可用地址。")

    parsed = urlparse(value)
    if parsed.scheme in {"", "file"}:
        local_value = unquote(parsed.path) if parsed.scheme == "file" else value
        local_path = Path(local_value).expanduser()
        if local_path.exists() and local_path.is_file():
            output_path.write_bytes(local_path.read_bytes())
            return

    request = urllib.request.Request(value, headers={"User-Agent": "content-factory/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            output_path.write_bytes(response.read())
    except urllib.error.URLError as error:
        raise RuntimeError(f"下载图片失败：{error}") from error


def compose_image_style(base_style: str, custom_prompt: str) -> str:
    custom = str(custom_prompt or "").strip()
    if not custom:
        return base_style
    base = str(base_style or "").strip()
    if "【用户补充】" in base:
        prefix = base.split("【用户补充】", 1)[0].rstrip()
        return f"{prefix}\n\n【用户补充】\n{custom}"
    return f"{base}\n\n【用户补充】\n{custom}"


def generate_image_asset(
    *,
    title: str,
    summary: str,
    article_path: Path,
    preset: str,
    style: str,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    command = [
        "md2wechat",
        "generate_image",
        "--preset",
        preset,
        "--title",
        title,
        "--summary",
        summary,
        "--article",
        str(article_path.resolve()),
        "--style",
        style,
        "--json",
    ]
    payload = run_json_command(command, cwd=workspace_root or WORKSPACE_ROOT)
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        data = {}
    original_url = str(data.get("original_url", "")).strip()
    wechat_url = str(data.get("wechat_url", "")).strip()
    preview_url = usable_generated_asset_url(original_url) or usable_generated_asset_url(wechat_url)
    draft_url = usable_generated_asset_url(wechat_url) or usable_generated_asset_url(original_url)
    if not preview_url and not draft_url:
        raise RuntimeError("图片生成成功，但没有返回可用地址。")
    return {
        "prompt": str(data.get("prompt", "")).strip(),
        "previewUrl": preview_url,
        "draftUrl": draft_url,
        "mediaId": str(data.get("media_id", "")).strip(),
        "width": data.get("width"),
        "height": data.get("height"),
    }
