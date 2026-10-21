"""Fluent Emoji Flat の絵文字名を英単語で探す。

使い方:
  python3 scripts/find_emoji.py 単語 [単語...] [--workdir 作業フォルダ] [--limit 30]

  例: python3 scripts/find_emoji.py robot
      python3 scripts/find_emoji.py office worker --workdir ./zukai-work

  すべての単語を名前に含むものを返す。肌の色違い（-light, -dark など）は除く。

出力（標準出力・JSON 1行）: {"query": [...], "names": [...], "total": 件数}
終了コード: 0=成功（0件でも0） 2=引数エラー 3=作業フォルダが未準備
"""
import argparse, json, pathlib, re, sys

TONE = re.compile(r"-(light|medium-light|medium|medium-dark|dark)$")


def main():
    ap = argparse.ArgumentParser(description="Fluent Emoji Flat の絵文字名を英単語で探す")
    ap.add_argument("words", nargs="+", help="英単語（例: robot, office, book）")
    ap.add_argument("--workdir", default=".", help="setup.sh で用意した作業フォルダ（既定: カレント）")
    ap.add_argument("--limit", type=int, default=30, help="最大件数（既定: 30）")
    a = ap.parse_args()

    p = pathlib.Path(a.workdir) / "node_modules/@iconify-json/fluent-emoji-flat/icons.json"
    if not p.is_file():
        print(f"Error: 絵文字データがありません: {p}\n       先に実行: bash scripts/setup.sh {a.workdir}", file=sys.stderr)
        sys.exit(3)
    names = json.loads(p.read_text())["icons"].keys()
    words = [w.lower() for w in a.words]
    hits = sorted((n for n in names if all(w in n for w in words) and not TONE.search(n)), key=len)
    print(json.dumps({"query": words, "names": hits[: a.limit], "total": len(hits)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
