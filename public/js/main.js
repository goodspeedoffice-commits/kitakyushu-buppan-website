// ハンバーガーメニュー
const hamburger = document.querySelector('.hamburger');
const nav = document.querySelector('.site-nav');

if (hamburger && nav) {
  hamburger.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    hamburger.classList.toggle('open', open);
    hamburger.setAttribute('aria-expanded', open ? 'true' : 'false');
    hamburger.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
  });

  nav.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('open');
      nav.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      hamburger.setAttribute('aria-label', 'メニューを開く');
    });
  });
}

// 現在地のナビをハイライト（拡張子なしURL・.html どちらでも一致させる）
(() => {
  const normalize = (p) => {
    if (!p) return '/';
    let path = p.split('#')[0].split('?')[0];
    path = path.replace(/index\.html$/, '').replace(/\.html$/, '');
    if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
    return path === '' ? '/' : path;
  };

  const current = normalize(location.pathname);

  document.querySelectorAll('.site-nav a').forEach(link => {
    if (normalize(link.getAttribute('href')) === current) {
      link.classList.add('active');
      link.setAttribute('aria-current', 'page');
    }
  });
})();

// お問い合わせフォーム送信
const form = document.getElementById('contact-form');
if (form) {
  const statusBox = document.getElementById('form-status');
  const btn = form.querySelector('button[type="submit"]');

  const showError = (message) => {
    if (!statusBox) return;
    statusBox.className = 'form-status error';
    statusBox.textContent = message;
    statusBox.hidden = false;
    statusBox.setAttribute('tabindex', '-1');
    statusBox.focus();
    statusBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!form.reportValidity()) return;

    const original = btn.textContent;
    btn.textContent = '送信中…';
    btn.disabled = true;
    if (statusBox) statusBox.hidden = true;

    try {
      // 同名チェックボックス（希望する支援）は配列にまとめる
      const fd = new FormData(form);
      const payload = {};
      for (const key of new Set(fd.keys())) {
        const values = fd.getAll(key);
        payload[key] = values.length > 1 ? values : values[0];
      }

      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok || !data.ok) {
        throw new Error(data.message || '送信に失敗しました。');
      }

      const params = data.receiptId ? '?id=' + encodeURIComponent(data.receiptId) : '';
      location.href = '/thanks' + params;
    } catch (err) {
      btn.textContent = original;
      btn.disabled = false;
      showError(
        '送信できませんでした。恐れ入りますが、時間をおいて再度お試しいただくか、' +
        'メール info@kitakyubuppan.com またはお電話 0948-24-6315 までご連絡ください。'
      );
    }
  });
}
