-- 既存の contact_submissions テーブル（0001 / 0002 で作成済み）に、
-- 新しいお問い合わせフォームで受け取る項目を追加する。
--
-- 既存列: id, name, email, organization, subject, message, consent,
--         status, created_at, notification_status, notified_at
--
-- SQLite の ALTER TABLE ADD COLUMN は IF NOT EXISTS を持たないため、
-- このマイグレーションは1回だけ適用される前提（d1_migrations が二重適用を防ぐ）。

ALTER TABLE contact_submissions ADD COLUMN receipt_id TEXT;
ALTER TABLE contact_submissions ADD COLUMN phone TEXT;
ALTER TABLE contact_submissions ADD COLUMN amazon_status TEXT;
ALTER TABLE contact_submissions ADD COLUMN support TEXT;      -- JSON配列（希望する支援）
ALTER TABLE contact_submissions ADD COLUMN ip TEXT;
ALTER TABLE contact_submissions ADD COLUMN user_agent TEXT;

-- 受付番号は一意。既存行は receipt_id が NULL だが、SQLite の UNIQUE は
-- 複数の NULL を許容するため既存データ（現在0件）と衝突しない。
CREATE UNIQUE INDEX IF NOT EXISTS idx_contact_receipt
  ON contact_submissions (receipt_id);

-- 同一IPの連投チェックで使う
CREATE INDEX IF NOT EXISTS idx_contact_ip_created
  ON contact_submissions (ip, created_at);

-- 受付日時の新しい順に一覧するため
CREATE INDEX IF NOT EXISTS idx_contact_created
  ON contact_submissions (created_at DESC);
