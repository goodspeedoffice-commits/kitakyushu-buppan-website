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
  - 旧Wixサイトから移した主要情報の欠落再発
"""
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROOT = PROJECT_ROOT / "public"
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

# 旧サイトにあった情報を再び削りすぎないための移行完了ゲート。
# 文言の全面固定ではなく、各情報分野が現行ページに存在することを確認する。
REQUIRED_MIGRATED_CONTENT = {
    "index.html": [
        "物販事業者をつなぎ", "ともに成長する協同組合",
        "九州・沖縄・山口", "北九州市・飯塚市を拠点に、九州・沖縄・山口の物販事業者の連携と成長を支援します",
        "共同仕入事業", "商品拡販支援事業", "商品企画開発事業",
        "共同販売事業", "物販サポート事業", "商品買取再販事業",
        'href="/members"', "参加企業紹介", 'href="/partners"',
        'href="/members-only"',
        "https://www.youtube.com/@obo5290",
        "https://instagram.com/kitakyubuppan/",
        "https://www.facebook.com/kitakyubuppan",
        "/images/site/analytics-dashboard-stock.avif",
        "/images/site/ecommerce-packing-stock.avif",
        "/images/site/consulting-meeting-stock.avif",
    ],
    "services.html": [
        'id="joint-purchasing"', 'id="product-expansion"',
        'id="product-development"', "ECモール、実店舗、SNS",
        "量販店、個人商店、卸売事業者、個人",
    ],
    "consulting.html": [
        "Amazon出品・運用支援", "カタログ作成・検索対策",
        "商品リサーチ・仕入れ戦略", "メーカー・卸売事業者との商談支援",
        "広告・販促計画", "運用支援・EC化支援",
        "/images/site/consulting-meeting-stock.avif",
    ],
    "news.html": [
        'id="food-expo-2026"', 'id="shinkin-2023"',
        "2026年10月6日（火）・7日（水）", "福岡国際センター",
        "2023年11月8日", "マリンメッセ福岡", "A-036",
        "執筆：大保 俊博", "執筆：管理人",
        "記事の分類", "活動報告", "組合商品紹介",
        "組合参加事業者紹介", "組合サービス紹介",
        "/images/site/shinkin-event-2023.avif",
        "/images/site/exhibition-members.avif",
    ],
    "about.html": [
        "アクセスマップ", 'id="access-map"', "九州・沖縄・山口",
        "/images/site/cooperative-booth-members.avif",
    ],
    "amazon-sales-support.html": ["/images/site/ecommerce-packing-stock.avif"],
    "amazon-ads-support.html": ["/images/site/analytics-dashboard-stock.avif"],
    "members.html": [
        "goodspeed office", "株式会社FUJIEN", "imaimashop", "Shop kikyou",
        "Cinnamon House", "池松 真吾", "山田 智也",
        "https://goodspeedoffice.hanbai-lab.com/", "https://fujien-inc.co.jp/",
        "https://www.instagram.com/goodspeed1978/?hl=ja",
        "https://x.com/greenspeed17", "https://www.facebook.com/tosihiro.obo",
        "/images/members/goodspeed-office.avif",
        "/images/members/fujien.avif", "/images/members/member-placeholder.avif",
        "/images/members/shop-kikyou.avif", "/images/members/cinnamon-house.avif",
        "/images/members/kitakyushu-coop.avif",
        'aria-hidden="true"',
    ],
    "partners.html": [
        "八幡東就労支援センターすずらん",
        "社会福祉法人 北九州フレンド社",
        "實松 夏連",
        "デザイナー／業務委託パートナー",
        "EC・広告用画像、バナー制作",
        "梱包・FBA納品準備",
    ],
    "gaiyou.html": [
        "取引金融機関", "ゆうちょ銀行",
        "福岡県中小企業団体中央会", "筑豊支所",
        "定款変更", "決算関係書類",
    ],
    "contact.html": [
        "〒820-0066", "福岡県飯塚市幸袋781-258",
        "0948-24-6315", "info@kitakyubuppan.com",
    ],
}

# 旧サイトにあっても、根拠未確認・現状不一致のため戻してはいけない情報。
DISALLOWED_STALE_OR_UNVERIFIED = [
    "Amazonベストセラーを獲得", "Amazon物販に革命をもたらす",
    "〒808-0074", "北九州市若松区今光1-1-8", "093-772-1320",
    "同じ条件で別の組合員へ販売業務を引き継げます",
    "https://www.youtube.com/@kitakyushu_buppan",
    "https://www.instagram.com/kitakyushu_buppan/",
    "https://www.facebook.com/kitakyushubuppan/",
    "https://microgolfgear.com/",
    "旧サイトで掲載していた各事業者のロゴ・アイコンを引き継いでいます。",
]

REQUIRED_REDIRECTS = {
    "/about-5": "/consulting",
    "/general-5": "/tokushoho",
    "/map": "/about#access-map",
    "/blank": "/members-only",
    "/複製-共同仕入事業": "/services#product-expansion",
    "/複製-商品拡販支援事業": "/services#product-development",
    "/複製-コンサルティングサービス": "/services#joint-purchasing",
    "/blog": "/news",
    "/blog/categories/活動報告": "/news#category-activity",
    "/blog/categories/組合商品紹介": "/news#category-products",
    "/blog/categories/組合参加事業者紹介": "/news#category-members",
    "/blog/categories/組合サービス紹介": "/news#category-services",
    "/post/food-expo-kyushu-2026に出展します-10月6日・7日-福岡国際センター": "/news#food-expo-2026",
    "/post/第７回しんきん合同商談会に出展いたします！": "/news#shinkin-2023",
}

# noindex を許可するページ（検索結果に出す必要がないもの）
# members-only.html は Cloudflare Access で保護する非公開ページ。
NOINDEX_OK = {"thanks.html", "404.html", "members-only.html"}
PRIVATE_PAGES = {"members-only.html"}

errors: list[str] = []
warns: list[str] = []

pages = sorted(ROOT.glob("*.html"))
if not pages:
    sys.exit(f"HTMLが見つかりません: {ROOT}")

# 実在するパスの集合（Cloudflare Pages は /foo.html を /foo で配信する）
available = {"/"}
for asset in ROOT.rglob("*"):
    if asset.is_file():
        available.add("/" + asset.relative_to(ROOT).as_posix())
for p in pages:
    available.add("/" + p.stem)
    available.add("/" + p.name)
for extra in ["/api/contact"]:
    available.add(extra)

for p in pages:
    html = p.read_text(encoding="utf-8")
    name = p.name

    # 公開ページの上部メニューに、提携先と組合員専用ページへの入口を維持する。
    if name != "members-only.html":
        nav_match = re.search(r'<nav class="site-nav".*?</nav>', html, re.S)
        if not nav_match:
            errors.append(f"{name}: 上部メニューがありません")
        else:
            nav = nav_match.group(0)
            for required_link in ['href="/partners"', 'href="/members-only"']:
                if required_link not in nav:
                    errors.append(f"{name}: 上部メニューの必須リンクが欠けています -> {required_link}")

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
    if name in PRIVATE_PAGES and not re.search(r'name="robots"[^>]*noindex', html):
        errors.append(f"{name}: 非公開ページに noindex がありません")

    for word in FORBIDDEN:
        for m in re.finditer(re.escape(word), html):
            if any(h in html[m.end():m.end() + 120] for h in NEGATION_HINTS):
                continue
            errors.append(f"{name}: 誤認表現 '{word}' -> ...{html[max(0, m.start() - 40):m.end() + 60]}...")

    for word in DUMMY:
        if word.lower() in html.lower():
            errors.append(f"{name}: ダミー/仮テキストの疑い -> {word}")

    for word in DISALLOWED_STALE_OR_UNVERIFIED:
        if word in html:
            errors.append(f"{name}: 未確認または旧情報が再掲載されています -> {word}")

    for required in REQUIRED_MIGRATED_CONTENT.get(name, []):
        if required not in html:
            errors.append(f"{name}: 旧サイトから移した主要情報が欠けています -> {required}")

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

# 旧Wixトップの背景画像がCSSから外れたり、画像本体が消えたりしないことを確認する。
style_css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
hero_image = ROOT / "images" / "site" / "original-home-hero.jpg"
if '/images/site/original-home-hero.jpg' not in style_css:
    errors.append("style.css: 旧Wixトップ背景画像の指定がありません")
if not hero_image.exists():
    errors.append("images/site/original-home-hero.jpg: 旧Wixトップ背景画像がありません")

# sitemap.xml と実ページの突き合わせ
sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
listed = {u or "/" for u in re.findall(rf"<loc>{re.escape(SITE)}(/[^<]*)</loc>", sitemap)}
public_pages = {"/" + p.stem for p in pages if p.name not in NOINDEX_OK and p.stem != "index"}
public_pages.add("/")
for u in sorted(public_pages - listed):
    errors.append(f"sitemap.xml: {u} が未掲載")
for u in sorted(listed - public_pages):
    errors.append(f"sitemap.xml: 実在しない {u} を掲載")

# 旧Wix URLの転送先と、組合員専用ページの保護経路を確認する。
redirects_text = (ROOT / "_redirects").read_text(encoding="utf-8")
redirects = {}
for line in redirects_text.splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split()
    if len(parts) >= 2:
        redirects[parts[0]] = parts[1]
for source, destination in REQUIRED_REDIRECTS.items():
    if redirects.get(source) != destination:
        errors.append(f"_redirects: 旧URL {source} の転送先が {destination} ではありません")

middleware_path = PROJECT_ROOT / "functions" / "_middleware.js"
if not middleware_path.exists():
    errors.append("functions/_middleware.js: 独自ドメインの組合員専用ページ保護がありません")
else:
    middleware = middleware_path.read_text(encoding="utf-8")
    for required in [
        "www.kitakyusyubuppan.com", "kitakyusyubuppan.com",
        "/members-only", "/members-only.html",
        "https://kitakyushu-buppan.pages.dev/members-only",
    ]:
        if required not in middleware:
            errors.append(f"functions/_middleware.js: 専用ページ保護の必須設定が欠けています -> {required}")

print(f"検査したページ: {len(pages)}")
print(f"エラー: {len(errors)} / 警告: {len(warns)}\n")
for e in errors:
    print("  [NG] " + e)
for w in warns:
    print("  [警告] " + w)

if errors:
    print("\nエラーが残っています。修正してから再実行してください。デプロイはまだしないこと。")
sys.exit(1 if errors else 0)
