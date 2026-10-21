#!/usr/bin/env bash
# 図解用の作業フォルダを用意する。何度実行しても安全（入っているものは入れ直さない）。
#
# 使い方: bash scripts/setup.sh 作業フォルダ
#   例:   bash scripts/setup.sh ./zukai-work
#
# 作業フォルダに用意されるもの:
#   node_modules/  絵文字・手描き線・フォント（バージョン固定）
#   ink.js         手描き線の描画（assets/ink.js のコピー。毎回上書きして最新に保つ）
#   base.html      図の雛形（assets/base.html のコピー。既にあれば上書きしない）
#
# 出力: 成功時は標準出力に JSON 1行。進捗は標準エラーへ。
# 終了コード: 0=成功 / 2=引数エラー / 3=Node.js・npmがない / 4=Pythonがない / 5=ブラウザを用意できない
set -euo pipefail

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; }
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then usage; exit 0; fi
if [[ -z "${1:-}" ]]; then echo "Error: 作業フォルダを指定してください。" >&2; usage >&2; exit 2; fi

WORK="$1"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$WORK"
cd "$WORK"

command -v npm >/dev/null || { echo "Error: npm が見つかりません。Node.js 18以上を入れてください。" >&2; exit 3; }
command -v python3 >/dev/null || { echo "Error: python3 が見つかりません。Python 3.9以上を入れてください。" >&2; exit 4; }

PKGS=(@iconify-json/fluent-emoji-flat@1.2.6 roughjs@4.6.6 @fontsource/kiwi-maru@5.3.1 @fontsource/yomogi@5.3.0)
if [[ ! -f node_modules/roughjs/bundled/rough.js || ! -f node_modules/@iconify-json/fluent-emoji-flat/icons.json \
   || ! -d node_modules/@fontsource/kiwi-maru || ! -d node_modules/@fontsource/yomogi ]]; then
  echo "npm パッケージを入れています…" >&2
  [[ -f package.json ]] || npm init -y >/dev/null
  npm install --no-audit --no-fund "${PKGS[@]}" >&2
fi

if ! python3 -c "import playwright" 2>/dev/null; then
  echo "playwright（Python）を入れています…" >&2
  pip install -q playwright >&2 2>/dev/null || pip install -q --break-system-packages playwright >&2
fi

if ! python3 -c "from playwright.sync_api import sync_playwright as s; p=s().start(); p.chromium.launch().close(); p.stop()" 2>/dev/null; then
  echo "Chromium を入れています…" >&2
  python3 -m playwright install chromium >&2 || { echo "Error: Chromium を用意できませんでした。'python3 -m playwright install --with-deps chromium' を試してください。" >&2; exit 5; }
fi

cp "$SKILL_DIR/assets/ink.js" ./ink.js
[[ -f base.html ]] || cp "$SKILL_DIR/assets/base.html" ./base.html

printf '{"workdir": "%s", "ready": true}\n' "$(pwd)"
