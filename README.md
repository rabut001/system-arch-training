# システムアーキテクト 午前Ⅱ 演習

IPA が公開しているシステムアーキテクト試験の午前Ⅱを、1問ずつ解く静的サイトです。公開先は [https://rabut001.github.io/system-arch-training/](https://rabut001.github.io/system-arch-training/) です。

平成21年度秋期から令和7年度春期まで（令和2年度を除く16回）を収録し、各回は25問です。問題は切り出した画像で表示し、ア〜エを選んで結果を確認します。解説は学習用に書いたもので、IPA の公式解説ではありません。進捗はブラウザの `localStorage` に残し、アカウントや端末間の同期はしません。

仕様の判断は [AGENTS.md](AGENTS.md) に書いてあります。`exams/` の収録範囲とファイル名は、このファイルの「過去問題」を参照します。

## フォルダ

| パス | 内容 |
| --- | --- |
| `exams/` | 問題冊子・解答例・採点講評の PDF と `manifest.json` |
| `scripts/` | 午前Ⅱの問題冊子を1問ずつ画像に切り出す Python |
| `data/` | 回ごとの JSON と問題画像。サイトが読む元データ |
| `web/` | 演習サイト（Vite + React + TypeScript） |
| `.devcontainer/` | 開発コンテナ（Node.js 22、Python 3.12、PyMuPDF） |
| `.github/workflows/` | GitHub Pages への公開 |

`chat-exports/` は会話の書き出しです。サイトの素材でも、仕様の参照先でもありません。

回ごとの JSON は `data/<id>.json` にあり、`id`、`title`、`questions` を持ちます。問は `no`（1〜25）、`answer`（ア、イ、ウ、エ）、`image`（問題画像への相対パス）、`explanation`（学習用の解説）です。画像は `data/<id>/q01.png` から `q25.png` です。

## 開発

開発は `.devcontainer/` のコンテナで行います。画面は次で起動します。

```sh
npm run dev --prefix web
```

開発サーバは [http://localhost:5173/system-arch-training/](http://localhost:5173/system-arch-training/) です。一覧は `/system-arch-training/`、選んだ回は `/system-arch-training/<id>/`（例: `/system-arch-training/2025-r07-haru/`）です。

ビルドは `npm run build --prefix web` です。成果物は `web/dist` で、ビルド時に `data/` をそこへコピーし、同じアプリを `404.html` としても置きます。`main` への push で `web/`、`data/`、または公開用ワークフローが変わったとき、GitHub Actions が GitHub Pages へ載せます。手動でも実行できます。サイトに載るのはアプリ、問題画像、問題 JSON、出典表記です。午後問題と解答の PDF は含めません。

問題画像の切り出しは次です。出力先を省略すると `data/<回のディレクトリ名>/` に書き出します。

```sh
python scripts/cut_am2_questions.py exams/2025-r07-haru
```

正解は `am2-kaitou.pdf` から取り、解説とともに回の JSON に保存します。画面の実行時には解説を生成しません。

## 過去問題

独立行政法人情報処理推進機構（IPA）が公開しているシステムアーキテクト試験（SA）の問題冊子・解答例・採点講評です。取得日は 2026-09-25 です。

出典: [過去問題 | IPA](https://www.ipa.go.jp/shiken/mondai-kaiotu/index.html)

IPA は、公表している過去の試験問題について、法令に特別の定めがある場合を除き許諾や使用料は不要であり、ダウンロードでの利用も問題ないとしています。著作権は放棄されていません。出典の明記など、使用時の留意点は [試験制度に関するよくある質問](https://www.ipa.go.jp/shiken/faq.html) の「その他」を確認してください。

### 収録範囲

制度改正後の SA（平成21年度以降）で、IPA の過去問題ページに掲載されている回です。各回 10 ファイル、合計 160 ファイル（約 148 MB）です。

| 期間 | 実施時期 | フォルダ |
| --- | --- | --- |
| 平成21年度〜平成30年度 | 秋期 | `exams/2009-h21-aki` 〜 `exams/2018-h30-aki` |
| 令和元年度 | 秋期 | `exams/2019-r01-aki` |
| 令和3年度〜令和7年度 | 春期 | `exams/2021-r03-haru` 〜 `exams/2025-r07-haru` |

令和2年度は新型コロナウイルス感染症の影響で春期試験が中止され、SA の問題は公開されていません。令和8年度の過去問題ページは、取得時点では未掲載でした。

午前Ⅰは高度試験の共通問題です。SA と同じ回の問題冊子と解答例を、各年度フォルダに入れています。演習サイトが使うのは午前Ⅱだけです。

### ファイル名

| ファイル | 内容 |
| --- | --- |
| `am1-mondai.pdf` / `am1-kaitou.pdf` | 午前Ⅰ 問題冊子 / 解答例 |
| `am2-mondai.pdf` / `am2-kaitou.pdf` | 午前Ⅱ 問題冊子 / 解答例 |
| `pm1-mondai.pdf` / `pm1-kaitou.pdf` / `pm1-saiten.pdf` | 午後Ⅰ 問題冊子 / 解答例 / 採点講評 |
| `pm2-mondai.pdf` / `pm2-kaitou.pdf` / `pm2-saiten.pdf` | 午後Ⅱ 問題冊子 / 解答例 / 採点講評 |

元の URL と IPA 側のファイル名は `exams/manifest.json` に記録しています。
