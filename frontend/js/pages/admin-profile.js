document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireStaff()) return;
  try {
    const staff = await api.get('/staff/auth/me');
    document.getElementById('profile-name').textContent = `${staff.first_name} ${staff.last_name}`;
    document.getElementById('profile-email').textContent = staff.email;
    document.getElementById('profile-role').textContent = staff.role.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
    document.getElementById('profile-last-login').textContent = staff.last_login ? Admin.formatDate(staff.last_login) : 'First login';
  } catch {}

  document.getElementById('new_password').addEventListener('input', function() {
    const v = this.value;
    const score = [v.length >= 8, /[A-Z]/.test(v), /[0-9]/.test(v), /[^A-Za-z0-9]/.test(v)].filter(Boolean).length;
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
      showAlert('Password updated successfully!', 'success');
      document.getElementById('change-pw-form').reset();
      document.getElementById('strength-fill').style.width = '0';
    } catch (err) {
      showAlert(err.message || 'Failed to update password.', 'error');
    } finally {
      btn.disabled = false; btn.textContent = 'Update Password';
    }
  });
});

function togglePw(id) {
  const el = document.getElementById(id);
  el.type = el.type === 'password' ? 'text' : 'password';
}
function showAlert(msg, type = 'error') {
  document.getElementById('alert').innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
  setTimeout(() => { document.getElementById('alert').innerHTML = ''; }, 4000);
}

Actions.register({ togglePw });
