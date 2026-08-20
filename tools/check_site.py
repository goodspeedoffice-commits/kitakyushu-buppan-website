"""公開前チェック（デプロイ前に必ず実行する）

    python tools/check_site.py

エラーが1件でもあると終了コード1を返す。デプロイはエラー0を確認してから行う。

見ているもの:
  - JSON-LD の構文
  - 内部リンクの行き先が実在するか
  - 公開ページに noindex が混ざっていないか
  - Amazon から認定・提携を受けていると誤認させる表現
  - ダミー・仮テキストの残骸
  - title / meta description / canonical の欠落
  - H1 の個数と見出しレベルの飛び
  - img の alt、target=_blank の rel=noopener
  - sitemap.xml と実ページの過不足
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "public"
SITE = "https://www.kitakyusyubuppan.com"

# Amazon から認定・提携を受けていると誤認させる表現（申請前後を問わず使用禁止）
FORBIDDEN = [
    "Amazon公式", "Amazon公認", "Amazon認定", "Amazon推奨", "Amazonと提携",
    "Amazonの代理", "Amazon Adsパートナー", "アマゾン公式", "公式パートナー",
    "認定代理店", "認定パートナー", "ベリファイドパートナー", "アドバンストパートナー",
]
# 上の語を含んでいても、否定文脈なら許容する（例:「〜を受けた事業者ではありません」）
NEGATION_HINTS = ["ではありません", "使用しません", "受けていません", "承認前", "使用禁止"]

DUMMY = [
    "lorem ipsum", "ダミー", "TODO", "FIXME", "ここに入力", "サンプルテキスト",
    'https://twitter.com/"', 'https://www.facebook.com/"', "example.com",
]

# noindex を許可するページ（検索結果に出す必要がないもの）
NOINDEX_OK = {"thanks.html", "404.html"}

errors: list[str] = []
warns: list[str] = []

pages = sorted(ROOT.glob("*.html"))
if not pages:
    sys.exit(f"HTMLが見つかりません: {ROOT}")

# 実在するパスの集合（Cloudflare Pages は /foo.html を /foo で配信する）
available = {"/"}
for p in pages:
    available.add("/" + p.stem)
    available.add("/" + p.name)
for extra in ["/css/style.css", "/js/main.js", "/robots.txt", "/sitemap.xml", "/api/contact"]:
    available.add(extra)

for p in pages:
    html = p.read_text(encoding="utf-8")
    name = p.name

    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(m.group(1))
        except Exception as e:
            errors.append(f"{name}: JSON-LD が不正 -> {e}")

    for m in re.finditer(r'(?:href|src)="(/[^"#]*)"', html):
        target = m.group(1).split("?")[0]
        if target not in available:
            errors.append(f"{name}: リンク切れの可能性 -> {target}")

    if re.search(r'name="robots"[^>]*noindex', html) and name not in NOINDEX_OK:
        errors.append(f"{name}: 公開ページに noindex が付いています")

    for word in FORBIDDEN:
        for m in re.finditer(re.escape(word), html):
            if any(h in html[m.end():m.end() + 120] for h in NEGATION_HINTS):
                continue
            errors.append(f"{name}: 誤認表現 '{word}' -> ...{html[max(0, m.start() - 40):m.end() + 60]}...")

    for word in DUMMY:
        if word.lower() in html.lower():
            errors.append(f"{name}: ダミー/仮テキストの疑い -> {word}")

    if not re.search(r"<title>.+?</title>", html, re.S):
        errors.append(f"{name}: <title> がありません")
    if name not in NOINDEX_OK:
        if not re.search(r'name="description"', html):
            errors.append(f"{name}: meta description がありません")
        if not re.search(r'rel="canonical"', html):
            errors.append(f"{name}: canonical がありません")

    h1_count = len(re.findall(r"<h1[ >]", html))
    if h1_count != 1:
        errors.append(f"{name}: H1 が {h1_count} 個あります（1個であるべき）")

    prev = 0
    for m in re.finditer(r"<h([1-6])[ >]", html):
        lvl = int(m.group(1))
        if prev and lvl > prev + 1:
            warns.append(f"{name}: 見出しが H{prev} から H{lvl} へ飛んでいます")
        prev = lvl

    for m in re.finditer(r"<img\b(?![^>]*\balt=)[^>]*>", html):
        errors.append(f"{name}: alt のない img -> {m.group(0)[:80]}")

    for m in re.finditer(r'<a\b[^>]*href="https?://[^"]+"[^>]*>', html):
        tag = m.group(0)
        if 'target="_blank"' in tag and "noopener" not in tag:
            errors.append(f"{name}: target=_blank に rel=noopener がありません -> {tag[:90]}")

# sitemap.xml と実ページの突き合わせ
sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
listed = {u or "/" for u in re.findall(rf"<loc>{re.escape(SITE)}(/[^<]*)</loc>", sitemap)}
public_pages = {"/" + p.stem for p in pages if p.name not in NOINDEX_OK and p.stem != "index"}
public_pages.add("/")
for u in sorted(public_pages - listed):
    errors.append(f"sitemap.xml: {u} が未掲載")
for u in sorted(listed - public_pages):
    errors.append(f"sitemap.xml: 実在しない {u} を掲載")

print(f"検査したページ: {len(pages)}")
print(f"エラー: {len(errors)} / 警告: {len(warns)}\n")
for e in errors:
    print("  [NG] " + e)
for w in warns:
    print("  [警告] " + w)

if errors:
    print("\nエラーが残っています。修正してから再実行してください。デプロイはまだしないこと。")
sys.exit(1 if errors else 0)
