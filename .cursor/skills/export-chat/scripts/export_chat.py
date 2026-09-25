#!/usr/bin/env python3
"""Export a Cursor agent transcript to chat-exports/<session-start>/chat.md."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

TIMESTAMP_RE = re.compile(r"<timestamp>(.*?)</timestamp>", re.S)
USER_QUERY_RE = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.S)
STAMP_FORMATS = (
    "%A, %b %d, %Y, %I:%M %p",
    "%A, %B %d, %Y, %I:%M %p",
)


def repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "AGENTS.md").is_file():
            return candidate
    raise SystemExit("AGENTS.md が見つかりません。リポジトリ直下で実行してください。")


def parse_stamp(raw: str) -> datetime:
    text = raw.strip()
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text).strip()
    for fmt in STAMP_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise SystemExit(f"セッション開始時刻を解釈できません: {raw.strip()}")


def message_texts(entry: dict) -> list[str]:
    content = (entry.get("message") or {}).get("content")
    if not isinstance(content, list):
        return []
    texts = []
    for block in content:
        if block.get("type") == "text" and block.get("text", "").strip():
            texts.append(block["text"].strip())
    return texts


def user_body(text: str) -> tuple[str, str]:
    stamp = ""
    matched = TIMESTAMP_RE.search(text)
    if matched:
        stamp = matched.group(1).strip()
    query = USER_QUERY_RE.search(text)
    body = query.group(1).strip() if query else text.strip()
    return stamp, body


def load_entries(path: Path) -> list[dict]:
    entries = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no}: JSON として読めません: {exc}") from exc
    return entries


def session_start(entries: list[dict]) -> datetime:
    for entry in entries:
        if entry.get("role") != "user":
            continue
        for text in message_texts(entry):
            matched = TIMESTAMP_RE.search(text)
            if matched:
                return parse_stamp(matched.group(1))
    raise SystemExit("最初のユーザー発言に <timestamp> がありません。")


def render(entries: list[dict], started: datetime) -> str:
    parts = [
        "# チャット書き出し\n\n",
        f"セッション開始: {started:%Y-%m-%d %H:%M}\n",
    ]
    for entry in entries:
        role = entry.get("role")
        texts = message_texts(entry)
        if not texts:
            continue
        if role == "user":
            stamp, body = user_body("\n\n".join(texts))
            if not body:
                continue
            parts.append("\n## ユーザー\n\n")
            if stamp:
                parts.append(f"*{stamp}*\n\n")
            parts.append(body + "\n")
        elif role == "assistant":
            body = "\n\n".join(texts).strip()
            if not body:
                continue
            parts.append("\n## アシスタント\n\n")
            parts.append(body + "\n")
    return "".join(parts)


def discover(match: str) -> Path:
    root = Path.home() / ".cursor" / "projects"
    if not root.is_dir():
        raise SystemExit(f"トランスクリプトの探索先がありません: {root}")
    found = []
    for path in root.glob("*/agent-transcripts/*/*.jsonl"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if match in text:
            found.append(path)
    if not found:
        raise SystemExit(f"「{match}」を含むトランスクリプトが見つかりません。")
    found.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return found[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--transcript", type=Path, help="対象セッションの .jsonl")
    source.add_argument("--match", help="このセッションの発言に含まれる一意な文字列")
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="chat-exports を置くリポジトリ。省略時は AGENTS.md があるディレクトリ",
    )
    args = parser.parse_args()

    transcript = args.transcript if args.transcript else discover(args.match)
    if not transcript.is_file():
        raise SystemExit(f"トランスクリプトがありません: {transcript}")

    root = args.repo_root.resolve() if args.repo_root else repo_root(Path.cwd())
    entries = load_entries(transcript)
    started = session_start(entries)
    destination = root / "chat-exports" / f"{started:%Y-%m-%d-%H%M}" / "chat.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(entries, started), encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
