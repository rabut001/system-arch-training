---
name: export-chat
description: >-
  このリポジトリのチャットを chat-exports へ Markdown で書き出す。ユーザーがチャットのエクスポート、
  会話ログの出力、chat-exports への保存を頼んだときに使う。
---

# チャットの書き出し

会話本文の変換はスクリプトで行う。手で Markdown を組み立てない。

## 手順

1. このセッションのトランスクリプトを渡して、リポジトリ直下で実行する。

```bash
python3 .cursor/skills/export-chat/scripts/export_chat.py --transcript "<トランスクリプトの jsonl>"
```

トランスクリプトは、現在のエージェントストアの ID と同じ名前である。ストアが `.../<id>/files` なら、ワークスペースの `agent-transcripts/<id>/<id>.jsonl` を渡す。発言の一節では探さない。

2. 標準出力に出たパスを、書き出したファイルとしてユーザーに伝える。
3. 頼まれない限りコミットしない。

`chat-exports/` はログであり、アプリの資産ではない。実装や仕様の根拠にしない。仕様は `AGENTS.md` を参照する。

## 出力

セッション開始時刻のフォルダに上書きする。同名フォルダがあれば `chat.md` を置き換える。

```text
chat-exports/YYYY-MM-DD-HHMM/chat.md
```

時刻は最初のユーザー発言の `<timestamp>` から取る。並びは名前の昇順が時系列になる。ツール呼び出しは含めず、ユーザーとアシスタントの本文だけを書く。
