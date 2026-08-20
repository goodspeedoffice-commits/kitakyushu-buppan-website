# デプロイ手順（北九州物販事業者協同組合 公式サイト）

## 構成

| 項目 | 値 |
|---|---|
| ホスティング | Cloudflare Pages（プロジェクト名 `kitakyushu-buppan`） |
| 本番URL | https://kitakyushu-buppan.pages.dev |
| 独自ドメイン | https://www.kitakyusyubuppan.com （Cloudflare Pagesへ接続済み） |
| 静的ファイル | `public/` |
| サーバー処理 | `functions/api/contact.js`（お問い合わせフォームの受け口） |
| データベース | Cloudflare D1 `kitakyushu-coop-contacts` / テーブル `contact_submissions` |

## デプロイ

```bash
npx wrangler pages deploy
```

Cloudflare Pages 側の本番ブランチは `master`（このリポジトリのブランチと一致）。
フラグを付けずに実行すれば本番へ反映される。2026-08-20 に実際にデプロイして Production 判定を確認済み。

> 以前は Pages 側が `main` を本番としていたため `--branch main` が必要だったが、
> 付け忘れると本番が更新されないまま成功表示になる事故が起きるため、`master` へ揃えた。

## 独自ドメインのDNS

権威DNSはWixで管理している。`www.kitakyusyubuppan.com` のCNAMEは
`kitakyushu-buppan.pages.dev`（TTL 3600）。2026-08-20にWix Domain DNS APIで切替済み。
メール用MX・TXT、ネームサーバー、ルートドメインのAレコードは変更していない。

誤ってWixサイトへ戻した場合は、Wix Domain DNS APIで `www` のCNAMEだけを
`cdn1.wixdns.net` から `kitakyushu-buppan.pages.dev` へ戻し、権威DNSと公開DNSの両方で確認する。

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

## メール通知（稼働中）

問い合わせがあると Brevo 経由でメールが届く。2026-08-20 に実送信で配信確認済み。

| 変数 | 値 | 種別 |
|---|---|---|
| `BREVO_API_KEY` | 組合の Brevo アカウントのキー | secret_text |
| `CONTACT_NOTIFY_TO` | `info@kitakyubuppan.com,goodspeedoffice@gmail.com` | secret_text |
| `CONTACT_NOTIFY_FROM` | `info@kitakyubuppan.com`（Brevo で認証済みの送信元） | secret_text |

メールの Reply-To には問い合わせ者のアドレスが入るので、**そのまま返信すれば相手に届く**。

> ### ⚠️ 環境変数は必ず secret_text で登録する
> `wrangler pages deploy` は、**wrangler.toml に書かれていない平文（plain_text）の環境変数を削除する**。
> 暗号化（secret_text）で登録したものは消えない。
> 2026-08-20 に `CONTACT_NOTIFY_TO` / `CONTACT_NOTIFY_FROM` を平文で入れてデプロイし、実際に消えた。

> ### ⚠️ PowerShell のパイプで secret を登録しない
> `$key | npx wrangler pages secret put ...` は改行が混入し、Brevo が 401「Key not found」を返した。
> 登録は Cloudflare API を直接使うか、値を確認してから手入力する。

登録内容の確認（値は表示されない）:

```bash
npx wrangler pages secret list --project-name kitakyushu-buppan
```

### 通知が届かなくなったときの調べ方

`notification_status` に結果が残る。`sent` 以外が続いていたら通知が壊れている。

```bash
npx wrangler d1 execute kitakyushu-coop-contacts --remote --command "SELECT notification_status, COUNT(*) FROM contact_submissions GROUP BY notification_status;"
```

| 値 | 意味 |
|---|---|
| `sent` | 送信済み |
| `skipped` | 変数が未設定のため送っていない |
| `failed` | 送信を試みて失敗した |

**既知の弱点**: 通知が失敗しても、その事実は D1 に記録されるだけで誰にも通知されない。
「メールが来ない＝問い合わせが無い」と誤解しないよう、定期的に上のクエリで確認するか、
日次の自動チェックを別途用意する。

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
