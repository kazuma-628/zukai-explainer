# /// script
# requires-python = ">=3.9"
# dependencies = ["playwright>=1.40"]
# ///
"""図解HTMLをPNGとPDFに書き出し、はみ出し・重なりを自動検出する。

使い方:
  python3 scripts/build.py 作業フォルダ/図.html [--out 出力.png]

  - HTMLは setup.sh で用意した作業フォルダの中に置くこと（node_modules と ink.js を相対パスで読むため）
  - HTML内の {{絵文字名:サイズ}} を Fluent Emoji Flat の絵に置き換える（例: {{robot:160}}）
  - --out を省くと、HTMLと同じ場所に同じ名前の .png と .pdf を書き出す

出力（標準出力・JSON 1行）:
  {"png": "...", "pdf": "...", "warnings": ["...", ...]}
  warnings が空でなければ、HTMLを直して再実行する。

終了コード:
  0=成功（警告があっても0） 2=引数エラー 3=作業フォルダが未準備 4=絵文字名が見つからない 5=描画に失敗
"""
import argparse, json, pathlib, re, sys


def fail(code, msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


CHECK_JS = r"""
() => {
  const out = [];
  const page = document.getElementById('page').getBoundingClientRect();
  const label = el => (el.textContent || el.className || el.tagName).trim().replace(/\s+/g,' ').slice(0, 24);
  const inside = (a, b, t=3) => a.left >= b.left - t && a.top >= b.top - t && a.right <= b.right + t && a.bottom <= b.bottom + t;
  const hit = (a, b) => !(a.right <= b.left || b.right <= a.left || a.bottom <= b.top || b.bottom <= a.top);
  document.querySelectorAll('[data-rough]').forEach(box => {
    const kind = box.dataset.rough;
    if (['arrow','shelf','conveyor'].includes(kind)) return;
    const br = box.getBoundingClientRect();
    const walker = document.createTreeWalker(box, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      if (!n.textContent.trim()) continue;
      if (n.parentElement.closest('[data-rough]') !== box) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const r of rg.getClientRects()) if (!inside(r, br)) { out.push(`文字が枠(${kind})からはみ出し: 「${n.textContent.trim().slice(0,20)}」`); break; }
    }
  });
  // 文字が縁に近すぎる（吹き出しは楕円なので88%、カード・札は95%を超えると窮屈に見える）
  document.querySelectorAll('[data-rough=bubble],[data-rough=card],[data-rough=pill],[data-rough=circle]').forEach(box => {
    const br = box.getBoundingClientRect(); let l = Infinity, r = -Infinity;
    const walker = document.createTreeWalker(box, NodeFilter.SHOW_TEXT); let n;
    while ((n = walker.nextNode())) {
      if (!n.textContent.trim() || n.parentElement.closest('[data-rough]') !== box) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const q of rg.getClientRects()) { l = Math.min(l, q.left); r = Math.max(r, q.right); }
    }
    const limit = box.dataset.rough === 'bubble' || box.dataset.rough === 'circle' ? 0.88 : 0.95;
    if (r > l && (r - l) > limit * br.width) out.push(`文字が枠(${box.dataset.rough})の縁に近い: 「${label(box)}」 幅を${Math.ceil((r - l) / limit - br.width)}px以上広げる`);
  });
  document.querySelectorAll('#page .layer *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width && !inside(r, page, 1)) out.push(`ページ外: 「${label(el)}」`);
  });
  const bubbles = [...document.querySelectorAll('[data-rough=bubble]')];
  const pics = [...document.querySelectorAll('.e')];
  bubbles.forEach((b, i) => {
    const r = b.getBoundingClientRect();
    bubbles.slice(i+1).forEach(o => { if (hit(r, o.getBoundingClientRect())) out.push(`吹き出しが重なり: 「${label(b)}」と「${label(o)}」`); });
    pics.forEach(p => { const pr = p.getBoundingClientRect();
      const ov = Math.max(0, Math.min(r.right, pr.right) - Math.max(r.left, pr.left)) * Math.max(0, Math.min(r.bottom, pr.bottom) - Math.max(r.top, pr.top));
      if (ov > 0.15 * pr.width * pr.height) out.push(`吹き出しが絵に重なり: 「${label(b)}」`); });
  });
  return [...new Set(out)];
}
"""


def main():
    ap = argparse.ArgumentParser(description="図解HTMLをPNG/PDFに書き出し、はみ出し・重なりを検出する")
    ap.add_argument("html", help="作業フォルダ内の図解HTML")
    ap.add_argument("--out", help="出力PNGのパス（省略時はHTMLと同名の .png）")
    a = ap.parse_args()

    src = pathlib.Path(a.html).resolve()
    if not src.is_file():
        fail(2, f"HTMLが見つかりません: {src}")
    work = src.parent
    icons_path = work / "node_modules/@iconify-json/fluent-emoji-flat/icons.json"
    if not icons_path.is_file() or not (work / "ink.js").is_file():
        fail(3, f"作業フォルダが未準備です: {work}\n       先に実行: bash scripts/setup.sh {work}")

    icons = json.loads(icons_path.read_text())
    dw, dh = icons.get("width", 32), icons.get("height", 32)

    def emoji(m):
        name, size = m.group(1), m.group(2)
        ic = icons["icons"].get(name)
        if ic is None and name in icons.get("aliases", {}):
            ic = icons["icons"].get(icons["aliases"][name].get("parent", ""))
        if ic is None:
            fail(4, f"絵文字名が見つかりません: {name}\n       探す: python3 scripts/find_emoji.py {name.split('-')[0]}")
        w, h = ic.get("width", dw), ic.get("height", dh)
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
                f'aria-hidden="true" style="display:inline-block;vertical-align:middle">{ic["body"]}</svg>')

    html = re.sub(r"<!--.*?-->", "", src.read_text(), flags=re.S)
    html = re.sub(r"\{\{([a-z0-9-]+):(\d+)\}\}", emoji, html)
    built = work / (src.stem + ".built.html")
    built.write_text(html)

    png = pathlib.Path(a.out).resolve() if a.out else src.with_suffix(".png")
    pdf = png.with_suffix(".pdf")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fail(3, "playwright がありません。先に実行: bash scripts/setup.sh 作業フォルダ")
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 2000, "height": 1400})
            pg.goto(built.as_uri())
            pg.wait_for_selector("body[data-ready='1']", timeout=20000)
            box = pg.locator("#page").bounding_box()
            pg.locator("#page").screenshot(path=str(png))
            pg.pdf(path=str(pdf), width=f"{int(box['width'])}px", height=f"{int(box['height'])}px", print_background=True)
            warns = pg.evaluate(CHECK_JS)
            b.close()
    except Exception as e:  # noqa: BLE001
        fail(5, f"描画に失敗しました: {e}\n       HTMLに #page・#ink・<script src=\"ink.js\"> があるか確認してください（base.html が雛形）")

    print(json.dumps({"png": str(png), "pdf": str(pdf), "warnings": warns}, ensure_ascii=False))


if __name__ == "__main__":
    main()
