document.getElementById('new_password').addEventListener('input', function() {
  const v = this.value;
  let score = [v.length >= 8, /[A-Z]/.test(v), /[0-9]/.test(v), /[^A-Za-z0-9]/.test(v)].filter(Boolean).length;
  const colors = ['var(--red)', 'var(--red)', 'var(--amber)', 'var(--green-light)', 'var(--green)'];
  document.getElementById('strength-fill').style.width = `${score * 25}%`;
  document.getElementById('strength-fill').style.background = colors[score];
});

document.getElementById('change-pw-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const np = document.getElementById('new_password').value;
  const cp = document.getElementById('confirm_password').value;
  if (np !== cp) { showAlert('Passwords do not match.', 'error'); return; }
  if (np.length < 8) { showAlert('Password must be at least 8 characters.', 'error'); return; }

  const btn = document.getElementById('submit-btn');
  btn.disabled = true; btn.textContent = 'Saving...';
  try {
    const data = await api.post('/staff/auth/change-password', {
      current_password: document.getElementById('current_password').value,
      new_password: np,
    });
    Auth.saveStaff(data.token, data.staff);
    showAlert('Password changed successfully! Redirecting...', 'success');
    setTimeout(() => { window.location.href = '/admin/dashboard.html'; }, 1500);
  } catch (e) {
    showAlert(e.message || 'Failed to change password.', 'error');
    btn.disabled = false; btn.textContent = 'Set New Password';
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
