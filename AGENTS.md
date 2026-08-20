# 北九州物販事業者協同組合 公式サイト — 運用・保守 引継ぎ書（正本）

> 2026-08-20 に Claude Code から Codex へ運用・保守を移管（CEO指示）。
> **このファイルが本サイトの運用知識の正本。** 変更したらこのファイルも更新すること。
> 組織全体のルールは `C:\Users\goods\.codex\AGENTS.md` が正本。こちらはその下位。

## あなたの役割

このフォルダの静的サイト「北九州物販事業者協同組合 公式サイト」の保守担当。
オーナーは大保俊博CEO（**完全な非エンジニア**・Amazon FBA食品物販事業者・当組合の代表理事）。

### CEO対応の絶対ルール

- 専門用語を避け、平易な日本語（です・ます調）で報告する
- **手動工程を含む提案は禁止**（CEOの絶対指示）。自動化で完結させる
- コマンド操作をCEOに求めない。どうしても必要なら最後の1コマンドだけ渡す
- 「できない」と決めつける前に、手元の認証情報・APIで本当に不可能か確認する
  （2026-08-20、Cloudflare の設定変更を「ダッシュボード操作が必要」と誤って報告し、CEOから指摘を受けた。
   実際は wrangler の OAuth トークンに `pages:write` があり API で変更できた）

---

## サイト概要

| 項目 | 値 |
|---|---|
| 本番URL | https://kitakyushu-buppan.pages.dev |
| 独自ドメイン | https://www.kitakyusyubuppan.com （Cloudflare Pagesへ接続済み） |
| ホスティング | Cloudflare Pages（プロジェクト `kitakyushu-buppan`） |
| Cloudflareアカウント | `19534db9a0b4f7ad9de0571c82028bcd` |
| リポジトリ | https://github.com/goodspeedoffice-commits/kitakyushu-buppan-website （Private・ブランチ `master`） |
| 技術構成 | 素のHTML/CSS/JS（フレームワークなし）＋ Pages Functions ＋ D1 |
| データベース | Cloudflare D1 `kitakyushu-coop-contacts`（uuid `a290aa28-221c-4866-91d1-9c52090949d2`） |
| メール送信 | Brevo（組合アカウント「Kitakyushu Buppan Cooperative」・無料枠300通/日） |

### なぜ Cloudflare へ移したか

旧サイトは Wix の旧エディタ（Velo無効）で、**APIからページの新規作成・編集ができなかった**。
すべての更新がCEOの手作業になるため、CEO判断で Cloudflare Pages へ移行した（2026-08-20）。

---

## このサイトの目的（最重要）

**Amazon Adsパートナーネットワークへの申請要件を満たすこと**が最大の目的。
組合サイトとしての役割を保ちつつ、Amazon広告支援を正式なサービスとして公開している。

満たしている要件:
- 動作している事業用サイトで、ログインなしに全ページ閲覧できる
- 運営事業者（名称・代表者・所在地・連絡先・法人番号）を全ページのフッターに表示
- 広告関連サービスの内容が専用ページで明確に分かる
- プライバシーポリシーと広告データの取り扱い方針がある

---

## 現在の状態（2026-08-20時点）

- 全18HTML（公開ページ・保護ページ・404を含む）を運用
- 問い合わせフォームは本番で実送信テスト済み。D1保存＋メール通知とも稼働
- D1 の `contact_submissions` は0件（テスト行は削除済み）
- 静的チェック（`tools/check_site.py`）エラー0・警告0
- 独自ドメインのDNS切替は2026-08-20に完了
- 旧Wixサイトと初回移行版にあった事業説明・相談分野・ブログ記事・分類・アクセスマップを新サイトへ移植済み

---

## ディレクトリ構成

```
組合ホームページ/
├── AGENTS.md                  ← このファイル（運用知識の正本）
├── DEPLOY.md                  ← デプロイ・障害対応の手順
├── LEGACY_CONTENT_AUDIT.md    ← 旧Wix・初回移行版からの情報移植対応表
├── wrangler.toml              ← Pages設定（出力先 public / D1バインディング）
├── public/                    ← 静的サイト本体。ここがそのまま配信される
│   ├── index.html ほか17ページ
│   ├── css/style.css
│   ├── js/main.js
│   ├── _headers               ← セキュリティヘッダ・キャッシュ設定
│   ├── _redirects             ← 旧Wix URLからの301
│   ├── robots.txt
│   └── sitemap.xml
├── functions/api/contact.js   ← 問い合わせフォームの受け口
├── migrations/                ← D1のマイグレーション（0003以降）
└── tools/
    ├── check_site.py          ← 公開前チェック（デプロイ前に必ず実行）
    └── set_pages_env.py       ← 環境変数の再設定
```

### ページ一覧

| URL | 役割 |
|---|---|
| `/` | トップ。Amazon支援を主サービスとして提示 |
| `/amazon-ads-support` | **Amazon広告運用・改善支援**（申請の核心ページ） |
| `/amazon-sales-support` | Amazon販売・商品ページ改善支援 |
| `/services` | 業務内容（組合の6事業） |
| `/consulting` | コンサルティングサービス |
| `/support-examples` | 支援内容の例（**実績ではない**と明記） |
| `/ad-data-policy` | 広告アカウント・データの取り扱い |
| `/privacy` | プライバシーポリシー |
| `/gaiyou` | 組合概要 |
| `/about` | 事務所紹介・アクセス |
| `/members` | 参加企業紹介 |
| `/partners` | 提携する就労支援事業所とクリエイターの紹介 |
| `/news` | お知らせ（展示会・商談会の出展情報） |
| `/contact` | お問い合わせフォーム |
| `/tokushoho` | 特定商取引法に基づく表記 |
| `/thanks` | 送信完了（noindex） |
| `404.html` | 404ページ（noindex） |

---

## 🚨 Amazonに関する表現ルール（絶対厳守）

パートナーネットワークの承認前後を問わず、**次の表現を使ってはいけない**。

> Amazon公式 / Amazon公認 / Amazon認定代理店 / Amazon認定パートナー / Amazon推奨 /
> Amazonと提携 / Amazonの代理 / Amazon Adsパートナー / パートナーネットワーク参加企業 /
> ベリファイド・アドバンスト等のステータス名

- Amazonのロゴ、Amazon Adsのロゴ、パートナーバッジ、認定バッジは**使用しない**
- Amazonの管理画面・レポート・教材のスクリーンショットを**転載しない**
- Amazonに似せた配色・ボタン・レイアウトにしない。組合独自のデザインを維持する

**使ってよい表現**: Amazon広告運用支援／Amazon広告改善支援／Amazon販売支援／
Amazonの商品ページ改善／スポンサープロダクト広告の設定支援

全ページのフッターに商標帰属と非提携の明記を入れてある。**ページを追加するときも必ず入れること。**
`tools/check_site.py` が禁止表現を機械的に検出する。

### 掲載してはいけないもの

- 架空の実績・顧客の声・数値。**売上/広告費/改善率は一切書かない**
- 効果や成果の保証を思わせる表現
- 取引先名・商品名（掲載許可を個別に得ていないため）
- 顔写真、取引先ロゴ、無断の商品画像

---

## デプロイ

```bash
python tools/check_site.py        # エラー0を確認してから
npx wrangler pages deploy
```

Pages側の本番ブランチは `master`（リポジトリと一致済み）なのでフラグは不要。
詳しい手順と障害対応は `DEPLOY.md` を参照。

### CSS / JS を変更したとき

`public/*.html` の `?v=YYYYMMDD` を更新する。忘れても `max-age=86400` で24時間以内に入れ替わる。

---

## 問い合わせフォームの仕組み

1. `public/contact.html` のフォームが `/api/contact` へJSONをPOST
2. `functions/api/contact.js` が検証 → **D1に保存** → メール通知
3. 成功なら `/thanks?id=受付番号` へ遷移

### 設計上の約束（壊さないこと）

- **D1への保存が成功して初めて「受付完了」**。保存に失敗したらHTTPエラーを返す
- **失敗を成功に見せない。** 送信に失敗したら画面に赤いエラーと電話/メールの代替導線を出す
  （移行前の旧コードは常に「受け付けました」と表示する偽成功バグがあった）
- メール通知が失敗しても問い合わせ自体は保存済みとして200を返し、
  `notification_status` に `failed` を記録して事実を残す

### 検証項目（フォームを触ったら再確認する）

必須5項目の欠落／メール形式／文字数超過／ハニーポット（`company_url`）／
同一IPの連投制限（10分3件で429）／GETは405。
2026-08-20 に全12ケースを実際に発火させて確認済み。

---

## メール通知

問い合わせが入ると `info@kitakyubuppan.com` と `goodspeedoffice@gmail.com` へ届く。
Reply-To に問い合わせ者が入るので、**そのまま返信すれば相手に届く**。

環境変数（すべて `secret_text`。理由は `DEPLOY.md` の警告を読むこと）:
`BREVO_API_KEY` / `CONTACT_NOTIFY_TO` / `CONTACT_NOTIFY_FROM`

再設定は `python tools/set_pages_env.py` → `npx wrangler pages deploy`。

### ⚠️ 既知の弱点

通知が失敗しても、その事実は D1 に記録されるだけで**誰にも通知されない**。
「メールが来ない＝問い合わせが無い」とCEOが誤解するリスクがある。定期的に確認すること:

```bash
npx wrangler d1 execute kitakyushu-coop-contacts --remote --command "SELECT notification_status, COUNT(*) FROM contact_submissions GROUP BY notification_status;"
```

日次の自動チェックを入れるかはCEO判断待ち（2026-08-20時点で未着手）。

---

## D1 スキーマ

テーブル `contact_submissions`。`0001` `0002` は本リポジトリ作成前に適用済みでファイルが無い。

| 列 | 内容 |
|---|---|
| `receipt_id` | 受付番号 `KB-YYYYMMDD-XXXXXX`（日付は日本時間） |
| `created_at` | UTC ISO8601 |
| `name` / `email` | 担当者名・メール |
| `organization` | **会社名・事業者名**（`company` ではない） |
| `subject` | 希望する支援の要約 |
| `message` | 相談内容 |
| `consent` | プライバシーポリシー同意（1固定） |
| `status` | `new` |
| `notification_status` | `sent` / `skipped` / `failed` |
| `notified_at` | 送信時刻 |
| `phone` / `amazon_status` / `support` / `ip` / `user_agent` | 0003で追加。`support` はJSON配列 |

マイグレーション追加は `0004_` 以降。適用は
`npx wrangler d1 migrations apply kitakyushu-coop-contacts --remote`。

---

## 独自ドメインと旧サイト情報の移行（2026-08-20完了）

- Cloudflare Pages のカスタムドメイン `www.kitakyusyubuppan.com` は接続済み
- Wix管理DNSの `www` CNAME は `kitakyushu-buppan.pages.dev` を指す
- 旧Wixサイトの固定ページ9件、ブログ記事2件、ブログ分類4件を直接取得して照合済み
- 初回コミット `675ea4b` に残っていた旧事業説明とも照合済み
- `tools/check_site.py` は、移植した主要情報が将来消えた場合もエラーにする

移植時に除外した旧情報:
- 若松区今光の旧住所と旧電話番号（現在の主たる事務所ではない）
- 根拠未確認の「Amazonベストセラーを獲得」「Amazon物販に革命」等の実績・誇張表現
- 「月額制」等、現行の契約条件として確認できていない表現

サイト側の移行作業は完了。Amazon Adsパートナーネットワークへの申請実行は本サイト保守とは別工程。

---

## 確認が取れていない事項（勝手に埋めないこと）

| 項目 | 状況 |
|---|---|
| 設立年月 | 登記簿を未確認。国税庁の「法人番号指定年月日 2018年11月27日」のみ記載している |
| 参加企業2名（池松真吾氏・山田智也氏）の屋号 | 旧サイトでも空欄。代表者名のみ掲載 |
| 特商法表記の取引条件 | 旧Wixに記載が無く、実態に沿う形でこちらが整えた。CEOの承認待ち |
| `/ad-data-policy` の各項目 | 保存期間・契約終了後の削除・インシデント窓口が実運用できているかCEO確認待ち |
| 支援実績の公開許可 | 未取得。だから `/support-examples` は「例」であって実績ではないと明記している |

---

## 確定している事業者情報（国税庁法人番号公表サイトで照合済み）

- 法人番号: **3290805009155**
- 商号: 北九州物販事業者協同組合
- 主たる事務所: **〒820-0066 福岡県飯塚市幸袋781-258**（令和8年2月5日変更）
  - 旧: 福岡県北九州市若松区今光1丁目1番8号 → **サイトには載せない**（2026-08-20 CEO判断）
- 代表理事: 大保 俊博 ／ TEL・FAX 0948-24-6315 ／ info@kitakyubuppan.com

⚠️ **ドメイン混同注意**: 組合公式サイトは `kitakyusyubuppan.com`（**syu** が入る）。
メールアドレスは `kitakyubuppan.com`（syuなし）。別ドメインなので取り違えないこと。

---

## 事業文脈（判断に使うもの）

- 組合は現役Amazonセラーの集まり。支援形態は**販売代行／運用支援／ハイブリッド**の3つ
- 得意分野は食品・地域商品・中小メーカーの商品・FBA利用商品
- 福岡県内2か所の就労支援事業所と提携し、Amazon納品の実務体制を持つ
- 業務委託契約で確認済みのクリエイターと連携し、EC・広告用画像、動画、バナー等の制作を案内する
- 福岡県中小企業団体中央会（筑豊支所）へ、定款変更・登記・決算関係書類等の相談・確認を継続している
- 取引金融機関はゆうちょ銀行
- 2026年10月6-7日に Food EXPO Kyushu 2026 へ出展予定（`/news` に掲載済み）
- 広告アカウントは広告主の所有。組合はログインID/パスワードを預からず、
  Amazonの正規の権限付与方法だけを使う。**この方針はサイトに公開しているので必ず守る**
