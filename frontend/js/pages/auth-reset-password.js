const token = window.location.hash.slice(1);
if (!token) { document.getElementById('alert').innerHTML = '<div class="alert alert-error">Invalid or missing reset token.</div>'; }

document.getElementById('toggle-pw').addEventListener('click', () => {
  const pw = document.getElementById('password');
  pw.type = pw.type === 'password' ? 'text' : 'password';
});

document.getElementById('reset-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const pw = document.getElementById('password').value;
  const confirm = document.getElementById('confirm').value;
  if (pw !== confirm) { document.getElementById('alert').innerHTML = '<div class="alert alert-error">Passwords do not match.</div>'; return; }

  const btn = document.getElementById('submit-btn');
  btn.disabled = true; btn.textContent = 'Resetting...';
  try {
    await api.post('/auth/reset-password', { token, password: pw });
    document.getElementById('alert').innerHTML = '<div class="alert alert-success">✓ Password reset! Redirecting to login...</div>';
    document.getElementById('reset-form').classList.add('hidden');
    setTimeout(() => { window.location.href = '/auth/login.html'; }, 2000);
  } catch (e) {
    document.getElementById('alert').innerHTML = `<div class="alert alert-error">${escapeHtml(e.message || 'Reset failed.')}</div>`;
    btn.disabled = false; btn.textContent = 'Reset Password';
  }
});
