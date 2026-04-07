from __future__ import annotations

import json
import os
import secrets
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError


FEISHU_BASE_URL = os.environ.get("FEISHU_OPEN_BASE_URL", "https://open.feishu.cn/open-apis").rstrip("/")
DEFAULT_REDIRECT_URI = "http://127.0.0.1:14578/callback"
DEFAULT_AUTH_CACHE_PATH = Path.home() / ".codex" / "feishu-auth" / "content-system-sync.json"


class AuthRequiredError(RuntimeError):
    """Raised when user auth has not been completed yet."""


class TokenRefreshError(RuntimeError):
    """Raised when a cached user token cannot be refreshed."""


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def require_env(name: str) -> str:
    value = clean_text(os.environ.get(name))
    if not value:
        raise RuntimeError(f"缺少环境变量：`{name}`。")
    return value


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def token_cache_path() -> Path:
    override = clean_text(os.environ.get("FEISHU_USER_AUTH_CACHE_PATH"))
    if override:
        return Path(override).expanduser()
    return DEFAULT_AUTH_CACHE_PATH


def redirect_uri() -> str:
    value = clean_text(os.environ.get("FEISHU_OAUTH_REDIRECT_URI"))
    return value or DEFAULT_REDIRECT_URI


def feishu_request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{FEISHU_BASE_URL}{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)

    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read().decode(charset, errors="ignore")
    except HTTPError as error:
        charset = error.headers.get_content_charset() or "utf-8"
        body = error.read().decode(charset, errors="ignore")
    except URLError as error:
        raise RuntimeError(f"飞书接口请求失败：{clean_text(error.reason) or error}") from error

    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"飞书接口返回了非 JSON 响应：{body[:200]}") from error

    if decoded.get("code") not in {0, "0", None}:
        raise RuntimeError(clean_text(decoded.get("msg") or decoded))
    return decoded


def auth_headers() -> tuple[str, str, str]:
    return require_env("FEISHU_APP_ID"), require_env("FEISHU_APP_SECRET"), redirect_uri()


def build_authorization_url(*, app_id: str, redirect_uri_value: str, state: str) -> str:
    query = urllib.parse.urlencode(
        {
            "app_id": app_id,
            "redirect_uri": redirect_uri_value,
            "state": state,
        }
    )
    return f"{FEISHU_BASE_URL}/authen/v1/index?{query}"


def _extract_token_payload(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    if isinstance(data, dict) and data:
        return data
    return response


def _normalize_cached_payload(payload: dict[str, Any], *, source: str) -> dict[str, Any]:
    app_id, _, current_redirect_uri = auth_headers()
    data = _extract_token_payload(payload)
    access_token = clean_text(data.get("access_token") or data.get("user_access_token"))
    refresh_token = clean_text(data.get("refresh_token"))
    expires_in = int(data.get("expires_in") or 0)
    refresh_expires_in = int(data.get("refresh_expires_in") or data.get("refresh_token_expires_in") or 0)

    issued_at = now_utc()
    expires_at = issued_at + timedelta(seconds=max(expires_in, 0))
    refresh_expires_at = issued_at + timedelta(seconds=max(refresh_expires_in, 0)) if refresh_expires_in else None

    normalized = {
        "cache_version": 1,
        "token_source": source,
        "app_id": app_id,
        "redirect_uri": current_redirect_uri,
        "token_type": clean_text(data.get("token_type")) or "Bearer",
        "scope": clean_text(data.get("scope")),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "refresh_expires_in": refresh_expires_in,
        "issued_at": isoformat_utc(issued_at),
        "expires_at": isoformat_utc(expires_at),
        "expires_at_epoch": int(expires_at.timestamp()),
        "saved_at": isoformat_utc(issued_at),
        "name": clean_text(data.get("name")),
        "en_name": clean_text(data.get("en_name")),
        "avatar_url": clean_text(data.get("avatar_url")),
        "open_id": clean_text(data.get("open_id")),
        "union_id": clean_text(data.get("union_id")),
        "tenant_key": clean_text(data.get("tenant_key")),
    }
    if refresh_expires_at is not None:
        normalized["refresh_expires_at"] = isoformat_utc(refresh_expires_at)
        normalized["refresh_expires_at_epoch"] = int(refresh_expires_at.timestamp())
    return normalized


def save_user_token_cache(payload: dict[str, Any]) -> Path:
    target = token_cache_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized = _normalize_cached_payload(payload, source="authorization_code")
    target.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    target.chmod(0o600)
    return target


def load_user_token_cache() -> dict[str, Any] | None:
    target = token_cache_path()
    if not target.exists():
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"飞书用户授权缓存格式非法：{target}")
    return payload


def exchange_code_for_user_token(code: str) -> dict[str, Any]:
    app_id, app_secret, _ = auth_headers()
    return feishu_request(
        "POST",
        "/authen/v1/access_token",
        payload={
            "grant_type": "authorization_code",
            "code": code,
            "app_id": app_id,
            "app_secret": app_secret,
        },
    )


def refresh_user_access_token(refresh_token: str) -> dict[str, Any]:
    app_id, app_secret, _ = auth_headers()
    return feishu_request(
        "POST",
        "/authen/v1/refresh_access_token",
        payload={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "app_id": app_id,
            "app_secret": app_secret,
        },
    )


def cache_is_fresh(cache: dict[str, Any], *, leeway_seconds: int = 120) -> bool:
    token = clean_text(cache.get("access_token"))
    expires_at_epoch = int(cache.get("expires_at_epoch") or 0)
    if not token or not expires_at_epoch:
        return False
    return expires_at_epoch > int(time.time()) + leeway_seconds


def cache_refresh_is_valid(cache: dict[str, Any], *, leeway_seconds: int = 120) -> bool:
    refresh_token = clean_text(cache.get("refresh_token"))
    refresh_expires_at_epoch = int(cache.get("refresh_expires_at_epoch") or 0)
    if not refresh_token:
        return False
    if not refresh_expires_at_epoch:
        return True
    return refresh_expires_at_epoch > int(time.time()) + leeway_seconds


def save_refreshed_user_token_cache(payload: dict[str, Any]) -> dict[str, Any]:
    target = token_cache_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized = _normalize_cached_payload(payload, source="refresh_token")
    target.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    target.chmod(0o600)
    return normalized


def ensure_user_access_token() -> tuple[str, dict[str, Any]]:
    cache = load_user_token_cache()
    if cache is None:
        raise AuthRequiredError(
            "尚未完成飞书用户授权。请先运行 `feishu-user-auth`，完成浏览器授权后再同步。"
        )

    if cache_is_fresh(cache):
        return clean_text(cache.get("access_token")), cache

    if not cache_refresh_is_valid(cache):
        raise TokenRefreshError("飞书用户 refresh_token 已过期或不可用，请重新运行 `feishu-user-auth`。")

    try:
        refreshed = refresh_user_access_token(clean_text(cache.get("refresh_token")))
    except Exception as error:  # noqa: BLE001
        raise TokenRefreshError(f"飞书用户 token 刷新失败：{clean_text(error) or error}") from error

    normalized = save_refreshed_user_token_cache(refreshed)
    access_token = clean_text(normalized.get("access_token"))
    if not access_token:
        raise TokenRefreshError("飞书用户 token 刷新后未返回 access_token。")
    return access_token, normalized


def run_browser_authorization(*, timeout_seconds: int = 300) -> dict[str, Any]:
    app_id, _, redirect_uri_value = auth_headers()
    parsed = urllib.parse.urlparse(redirect_uri_value)
    if parsed.scheme != "http":
        raise RuntimeError("当前仅支持本地 `http://127.0.0.1` 回调地址。")
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("当前仅支持 `127.0.0.1` 或 `localhost` 作为飞书 OAuth 回调地址。")
    if not parsed.port:
        raise RuntimeError("飞书 OAuth 回调地址必须显式包含端口。")

    callback_path = parsed.path or "/"
    auth_state = secrets.token_urlsafe(24)
    auth_url = build_authorization_url(app_id=app_id, redirect_uri_value=redirect_uri_value, state=auth_state)
    received: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            request_target = urllib.parse.urlparse(self.path)
            if request_target.path != callback_path:
                self.send_response(404)
                self.end_headers()
                return

            params = urllib.parse.parse_qs(request_target.query, keep_blank_values=True)
            for key, values in params.items():
                if values:
                    received[key] = values[0]

            if received.get("state") != auth_state:
                body = "Feishu OAuth state 校验失败，请返回 Codex 重新发起授权。"
                self.send_response(400)
            elif received.get("error"):
                body = f"Feishu 授权未完成：{clean_text(received.get('error_description') or received.get('error'))}"
                self.send_response(400)
            else:
                body = "飞书授权已完成，可以回到 Codex 继续同步。"
                self.send_response(200)

            encoded = body.encode("utf-8")
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    try:
        server = ThreadingHTTPServer((parsed.hostname, parsed.port), CallbackHandler)
    except OSError as error:
        raise RuntimeError(f"无法启动本地飞书 OAuth 回调端口 `{parsed.port}`：{clean_text(error)}") from error

    server.timeout = 0.5
    opened_browser = webbrowser.open(auth_url, new=1, autoraise=True)
    deadline = time.monotonic() + max(timeout_seconds, 15)
    try:
        while time.monotonic() < deadline:
            server.handle_request()
            if received:
                break
    finally:
        server.server_close()

    if not received:
        raise RuntimeError(
            "飞书用户授权超时。请确认飞书应用已配置网页应用能力、回调地址，并重试授权。"
        )
    if received.get("error"):
        raise RuntimeError(
            f"飞书用户未完成授权：{clean_text(received.get('error_description') or received.get('error'))}"
        )

    code = clean_text(received.get("code"))
    if not code:
        raise RuntimeError("飞书 OAuth 回调中未返回 `code`。")

    token_payload = exchange_code_for_user_token(code)
    cache_path = save_user_token_cache(token_payload)
    cache = load_user_token_cache() or {}
    return {
        "auth_url": auth_url,
        "redirect_uri": redirect_uri_value,
        "cache_path": str(cache_path),
        "opened_browser": opened_browser,
        "cache": cache,
    }
