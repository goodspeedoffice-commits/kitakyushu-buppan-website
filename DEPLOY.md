# デプロイ手順（北九州物販事業者協同組合 公式サイト）

## 構成

| 項目 | 値 |
|---|---|
| ホスティング | Cloudflare Pages（プロジェクト名 `kitakyushu-buppan`） |
| 本番URL | https://kitakyushu-buppan.pages.dev |
| 独自ドメイン | https://www.kitakyusyubuppan.com （**未接続**。現在はWixを指している） |
| 静的ファイル | `public/` |
| サーバー処理 | `functions/api/contact.js`（お問い合わせフォームの受け口） |
| データベース | Cloudflare D1 `kitakyushu-coop-contacts` / テーブル `contact_submissions` |

## デプロイ

```bash
npx wrangler pages deploy --branch main
```

> **`--branch main` は必須。**
> Cloudflare Pages 側の本番ブランチが `main` である一方、このリポジトリのブランチは `master`。
> 省略すると `master` 扱いになり、本番ではなくプレビュー環境へデプロイされる。

## データベースのマイグレーション

```bash
npx wrangler d1 migrations apply kitakyushu-coop-contacts --remote
```

`migrations/` に SQL を追加してから実行する。番号は既存の続き（`0004_` 以降）を使う。
`0001` `0002` は本リポジトリ作成前に適用済みのため、ファイルとしては存在しない。

## お問い合わせ内容の確認

```bash
npx wrangler d1 execute kitakyushu-coop-contacts --remote --command "SELECT receipt_id, created_at, organization, name, email, subject, notification_status FROM contact_submissions ORDER BY id DESC LIMIT 20;"
```

## メール通知を有効にする（任意）

現在は D1 への保存のみ。メール通知を使う場合は、以下3つを Secrets に登録すると自動的に送信されるようになる。
コード変更は不要。

```bash
npx wrangler pages secret put RESEND_API_KEY --project-name kitakyushu-buppan
npx wrangler pages secret put CONTACT_NOTIFY_TO --project-name kitakyushu-buppan
npx wrangler pages secret put CONTACT_NOTIFY_FROM --project-name kitakyushu-buppan
```

未登録の間は `notification_status` が `skipped` として記録される（通知されていないことが後から分かる）。

## CSS / JS を更新したとき

`public/*.html` の `?v=YYYYMMDD` を当日の日付に更新する。
更新を忘れても `Cache-Control: max-age=86400` により24時間以内には入れ替わる。

## ローカル確認

```bash
npx wrangler pages dev --port 8788
```

初回はローカルD1に本番と同じスキーマを作る必要がある。
`migrations/` の適用だけでは `0001` `0002` 相当のテーブルが無いため、
本番のスキーマを写した上で `npx wrangler d1 migrations apply kitakyushu-coop-contacts --local` を実行する。
