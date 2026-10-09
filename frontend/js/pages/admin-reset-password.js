const token = window.location.hash.slice(1);
if (!token) {
  document.getElementById('reset-form').classList.add('hidden');
  document.getElementById('invalid-token').classList.remove('hidden');
}

document.getElementById('new_password').addEventListener('input', function() {
  const v = this.value;
  const score = [v.length >= 8, /[A-Z]/.test(v), /[0-9]/.test(v), /[^A-Za-z0-9]/.test(v)].filter(Boolean).length;
  const colors = ['var(--red)', 'var(--red)', 'var(--amber)', 'var(--green-light)', 'var(--green)'];
  document.getElementById('strength-fill').style.width = `${score * 25}%`;
  document.getElementById('strength-fill').style.background = colors[score];
});

document.getElementById('reset-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const np = document.getElementById('new_password').value;
  const cp = document.getElementById('confirm_password').value;
  if (np !== cp) { showAlert('Passwords do not match.'); return; }
  if (np.length < 8) { showAlert('Password must be at least 8 characters.'); return; }

  const btn = document.getElementById('submit-btn');
  btn.disabled = true; btn.textContent = 'Resetting...';
  try {
    await api.post('/staff/auth/reset-password', { token, new_password: np });
    showAlert('Password reset! Redirecting to login...', 'success');
    setTimeout(() => { window.location.href = '/admin/login.html'; }, 2000);
  } catch (err) {
    if (err.message && err.message.includes('invalid or has expired')) {
      document.getElementById('reset-form').classList.add('hidden');
      document.getElementById('invalid-token').classList.remove('hidden');
    } else {
      showAlert(err.message || 'Reset failed. Try again.');
    }
    btn.disabled = false; btn.textContent = 'Reset Password';
  }
});

function togglePw(id) {
  const el = document.getElementById(id);
  el.type = el.type === 'password' ? 'text' : 'password';
}
function showAlert(msg, type = 'error') {
  document.getElementById('alert').innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
}

Actions.register({ togglePw });
