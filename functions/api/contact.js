/**
 * お問い合わせフォームの受け口（Cloudflare Pages Functions）
 *
 * 動作:
 *   1. 入力を検証する（必須項目・形式・長さ・ハニーポット・同一IPの連投）
 *   2. D1 に保存する ← ここが成功して初めて「受付完了」とみなす
 *   3. RESEND_API_KEY と CONTACT_NOTIFY_TO が設定されていればメール通知も送る
 *
 * 設計方針:
 *   - 保存に失敗したら必ずエラーを返す。成功したように見せない。
 *   - メール通知は任意機能。未設定・失敗でも保存済みなら 200 を返すが、
 *     notified:false と notifyError をレスポンスに含め、console.error にも出す。
 *     （通知が死んでいることに気づけないまま放置される状態を作らない）
 */

const MAX = {
  company: 100,
  name: 60,
  email: 150,
  phone: 30,
  amazon_status: 60,
  message: 4000,
  support: 40, // 各選択肢の長さ上限
};

const SUPPORT_MAX_ITEMS = 20;

// 同一IPからの連投制限
const RATE_LIMIT_WINDOW_MINUTES = 10;
const RATE_LIMIT_MAX_SUBMISSIONS = 3;

const json = (status, body) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
    },
  });

const asText = (value) => (typeof value === 'string' ? value.trim() : '');

function validate(payload) {
  const errors = [];

  // ハニーポット。人間には見えない項目なので、埋まっていれば機械による送信。
  if (asText(payload.company_url) !== '') {
    return { botDetected: true, errors: [] };
  }

  const company = asText(payload.company);
  const name = asText(payload.name);
  const email = asText(payload.email);
  const phone = asText(payload.phone);
  const amazonStatus = asText(payload.amazon_status);
  const message = asText(payload.message);

  if (!company) errors.push('会社名・事業者名を入力してください。');
  else if (company.length > MAX.company) errors.push('会社名・事業者名が長すぎます。');

  if (!name) errors.push('ご担当者名を入力してください。');
  else if (name.length > MAX.name) errors.push('ご担当者名が長すぎます。');

  if (!email) errors.push('メールアドレスを入力してください。');
  else if (email.length > MAX.email) errors.push('メールアドレスが長すぎます。');
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.push('メールアドレスの形式が正しくありません。');

  if (phone.length > MAX.phone) errors.push('電話番号が長すぎます。');
  if (amazonStatus.length > MAX.amazon_status) errors.push('販売状況の値が不正です。');

  if (!message) errors.push('ご相談内容を入力してください。');
  else if (message.length > MAX.message) errors.push('ご相談内容が長すぎます。4000文字以内でご記入ください。');

  if (asText(payload.privacy_agreed) === '') {
    errors.push('プライバシーポリシーへの同意が必要です。');
  }

  // 希望する支援（チェックボックス）は文字列 or 配列で届く
  let support = payload.support ?? [];
  if (typeof support === 'string') support = support === '' ? [] : [support];
  if (!Array.isArray(support)) {
    errors.push('希望する支援の値が不正です。');
    support = [];
  } else if (support.length > SUPPORT_MAX_ITEMS) {
    errors.push('希望する支援の選択数が多すぎます。');
    support = support.slice(0, SUPPORT_MAX_ITEMS);
  } else {
    support = support.map(asText).filter((v) => v !== '' && v.length <= MAX.support);
  }

  return {
    botDetected: false,
    errors,
    values: { company, name, email, phone, amazonStatus, message, support },
  };
}

function buildReceiptId(now) {
  // 受付番号の日付部分は日本時間。CEO・担当者が受付日と突き合わせやすくするため。
  const jst = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
    .format(now)
    .replace(/-/g, '');
  const suffix = crypto.randomUUID().replace(/-/g, '').slice(0, 6).toUpperCase();
  return `KB-${jst}-${suffix}`;
}

// 送信元IPを取れる範囲で特定する。Cloudflare上では CF-Connecting-IP が必ず付く。
function resolveClientIp(request) {
  const direct = request.headers.get('CF-Connecting-IP');
  if (direct) return direct;
  const forwarded = request.headers.get('X-Forwarded-For');
  if (forwarded) return forwarded.split(',')[0].trim();
  return '';
}

async function sendNotification(env, record) {
  const apiKey = env.RESEND_API_KEY;
  const to = env.CONTACT_NOTIFY_TO;
  const from = env.CONTACT_NOTIFY_FROM;

  if (!apiKey || !to || !from) {
    return {
      notified: false,
      reason:
        'メール通知は未設定です（RESEND_API_KEY / CONTACT_NOTIFY_TO / CONTACT_NOTIFY_FROM のいずれかが未登録）。問い合わせ内容はデータベースに保存済みです。',
    };
  }

  const lines = [
    `受付番号: ${record.receiptId}`,
    `受付日時: ${record.createdAt}`,
    '',
    `会社名・事業者名: ${record.company}`,
    `ご担当者名: ${record.name}`,
    `メールアドレス: ${record.email}`,
    `電話番号: ${record.phone || '（未入力）'}`,
    `Amazonでの販売状況: ${record.amazonStatus || '（未選択）'}`,
    `希望する支援: ${record.support.length ? record.support.join(' / ') : '（未選択）'}`,
    '',
    'ご相談内容:',
    record.message,
  ];

  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from,
      to: [to],
      reply_to: record.email,
      subject: `【サイト問い合わせ】${record.company} 様（${record.receiptId}）`,
      text: lines.join('\n'),
    }),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`Resend API がエラーを返しました (HTTP ${res.status}): ${detail.slice(0, 300)}`);
  }

  return { notified: true, reason: null };
}

export async function onRequestPost({ request, env }) {
  let payload;
  try {
    payload = await request.json();
  } catch {
    return json(400, { ok: false, message: '送信データを読み取れませんでした。' });
  }

  const { botDetected, errors, values } = validate(payload);

  if (botDetected) {
    console.error('[contact] ハニーポットに入力があったため拒否しました。');
    return json(400, { ok: false, message: '送信を受け付けられませんでした。' });
  }

  if (errors.length > 0) {
    return json(400, { ok: false, message: errors.join(' ') });
  }

  if (!env.DB) {
    // バインディング設定漏れ。無言で握りつぶすと問い合わせが消えるので必ず失敗させる。
    console.error('[contact] D1 バインディング DB が未設定です。問い合わせを保存できません。');
    return json(503, {
      ok: false,
      message: '現在フォームをご利用いただけません。お手数ですが、メールまたはお電話でご連絡ください。',
    });
  }

  const now = new Date();
  const createdAt = now.toISOString();
  const receiptId = buildReceiptId(now);
  const ip = resolveClientIp(request);

  if (!ip) {
    // IPが取れないと連投制限が効かない。黙って素通りさせず記録に残す。
    console.error('[contact] 送信元IPを特定できませんでした。この送信は連投制限の対象外です。');
  }
  const userAgent = (request.headers.get('User-Agent') || '').slice(0, 300);

  // 同一IPからの連投チェック（保存前に確認する）
  if (ip) {
    try {
      const since = new Date(now.getTime() - RATE_LIMIT_WINDOW_MINUTES * 60 * 1000).toISOString();
      const row = await env.DB.prepare(
        'SELECT COUNT(*) AS c FROM contact_submissions WHERE ip = ?1 AND created_at > ?2'
      )
        .bind(ip, since)
        .first();

      if (row && Number(row.c) >= RATE_LIMIT_MAX_SUBMISSIONS) {
        return json(429, {
          ok: false,
          message:
            '短時間に複数回送信されています。しばらく時間をおいてから、もう一度お試しください。お急ぎの場合はお電話ください。',
        });
      }
    } catch (err) {
      // 連投チェックの失敗で問い合わせ自体を止めない。ただし黙らせない。
      console.error('[contact] 連投チェックに失敗しました:', err && err.message);
    }
  }

  const record = {
    receiptId,
    createdAt,
    company: values.company,
    name: values.name,
    email: values.email,
    phone: values.phone,
    amazonStatus: values.amazonStatus,
    support: values.support,
    message: values.message,
  };

  try {
    // 列構成は migrations/0001・0002（既存）＋ 0003（追加分）に対応する。
    // organization = 会社名・事業者名、subject = 希望する支援の要約、consent = 同意チェック。
    await env.DB.prepare(
      `INSERT INTO contact_submissions
         (receipt_id, created_at, name, email, organization, subject, message,
          consent, status, notification_status,
          phone, amazon_status, support, ip, user_agent)
       VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, 1, 'new', 'pending', ?8, ?9, ?10, ?11, ?12)`
    )
      .bind(
        receiptId,
        createdAt,
        record.name,
        record.email,
        record.company,
        record.support.length ? record.support.join(' / ') : 'Amazon広告・販売支援のご相談',
        record.message,
        record.phone,
        record.amazonStatus,
        JSON.stringify(record.support),
        ip,
        userAgent
      )
      .run();
  } catch (err) {
    console.error('[contact] D1 への保存に失敗しました:', err && err.message);
    return json(500, {
      ok: false,
      message:
        '送信の保存に失敗しました。お手数ですが、メール info@kitakyubuppan.com またはお電話 0948-24-6315 までご連絡ください。',
    });
  }

  // ここから先は保存済み。通知に失敗しても問い合わせは失われない。
  let notified = false;
  let notifyError = null;
  let notificationStatus = 'failed';

  try {
    const result = await sendNotification(env, record);
    notified = result.notified;
    notificationStatus = result.notified ? 'sent' : 'skipped';
    if (!result.notified) {
      notifyError = result.reason;
      console.error(`[contact] ${receiptId}: ${result.reason}`);
    }
  } catch (err) {
    notifyError = err && err.message ? err.message : String(err);
    console.error(`[contact] ${receiptId}: メール通知に失敗しました:`, notifyError);
  }

  // 通知の結果を行に書き戻す。未送信・失敗が DB 側からも分かるようにする。
  try {
    await env.DB.prepare(
      'UPDATE contact_submissions SET notification_status = ?1, notified_at = ?2 WHERE receipt_id = ?3'
    )
      .bind(notificationStatus, notified ? new Date().toISOString() : null, receiptId)
      .run();
  } catch (err) {
    console.error(`[contact] ${receiptId}: 通知ステータスの更新に失敗しました:`, err && err.message);
  }

  return json(200, { ok: true, receiptId, notified, notifyError });
}

// POST 以外は明示的に拒否する
export async function onRequest({ request }) {
  if (request.method === 'POST') {
    // onRequestPost が処理するため、ここには到達しない
    return json(500, { ok: false, message: 'ルーティングエラー' });
  }
  return json(405, { ok: false, message: 'このエンドポイントは POST のみ受け付けます。' });
}
