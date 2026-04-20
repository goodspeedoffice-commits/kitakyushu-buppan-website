// Hamburger menu
const hamburger = document.querySelector('.hamburger');
const nav = document.querySelector('.site-nav');

if (hamburger && nav) {
  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    nav.classList.toggle('open');
  });

  nav.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('open');
      nav.classList.remove('open');
    });
  });
}

// Active nav link
const currentPage = location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.site-nav a').forEach(link => {
  const href = link.getAttribute('href');
  if (href === currentPage || (currentPage === '' && href === 'index.html')) {
    link.classList.add('active');
  }
});

// Contact form
const form = document.getElementById('contact-form');
if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    btn.textContent = '送信中...';
    btn.disabled = true;

    const data = new FormData(form);
    fetch('/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(data).toString()
    })
      .then(() => {
        form.innerHTML = '<p style="text-align:center;color:var(--primary);font-weight:600;padding:32px 0">お問い合わせを受け付けました。<br>担当者よりご連絡いたします。</p>';
      })
      .catch(() => {
        btn.textContent = '送信する';
        btn.disabled = false;
        alert('送信に失敗しました。恐れ入りますが、メールにてお問い合わせください。');
      });
  });
}
