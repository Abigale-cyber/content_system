#!/usr/bin/env python3
"""Push Markdown report to Feishu chat via lark-cli."""

import argparse
import os
import subprocess
import sys

DEFAULT_CHAT_ID = "oc_5957da1b76ad64aa9b037eebb2899999"
MAX_CONTENT_LEN = 3500


def main():
    parser = argparse.ArgumentParser(description="Push Markdown report to Feishu chat")
    parser.add_argument("--input", required=True, help="Markdown file path, or '-' for stdin")
    parser.add_argument("--chat-id", default=os.environ.get("FEISHU_CHAT_ID", DEFAULT_CHAT_ID))
    parser.add_argument("--dry-run", action="store_true", help="Print command without executing")
    args = parser.parse_args()

    if args.input == "-":
        content = sys.stdin.read()
    else:
        if not os.path.isfile(args.input):
            print(f"Error: file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()

    if not content.strip():
        print("Error: empty content", file=sys.stderr)
        sys.exit(1)

    if len(content) > MAX_CONTENT_LEN:
        content = content[:MAX_CONTENT_LEN] + "\n\n... (内容过长已截断)"
        print(f"Warning: content truncated to {MAX_CONTENT_LEN} chars", file=sys.stderr)

    cmd = [
        "npx", "@larksuite/cli", "im", "+messages-send",
        "--chat-id", args.chat_id,
        "--as", "bot",
        "--markdown", content,
    ]

    if args.dry_run:
        print(f"[DRY RUN] Would send {len(content)} chars to chat {args.chat_id}")
        print(f"Preview:\n{content[:500]}{'...' if len(content) > 500 else ''}")
        return

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"Pushed to Feishu chat {args.chat_id}", file=sys.stderr)
        else:
            print(f"Failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Timeout: Feishu push took too long", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: npx not found. Ensure Node.js and lark-cli are installed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
