document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireLogin()) return;

  // Load profile from server (authoritative source)
  let user;
  try {
    user = await api.get('/auth/me');
  } catch {
    user = Auth.getUser();
  }
  if (!user) return;

  // Sidebar
  document.getElementById('avatar').textContent = (user.first_name?.[0] || '') + (user.last_name?.[0] || '');
  document.getElementById('user-name').textContent = `${user.first_name} ${user.last_name}`;
  document.getElementById('user-email').textContent = user.email;

  // Member since
  if (user.created_at) {
    const since = new Date(user.created_at).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
    document.getElementById('member-since').textContent = `✓ Member since ${since}`;
  }

  // Populate fields
  document.getElementById('first-name').value = user.first_name || '';
  document.getElementById('last-name').value = user.last_name || '';
  document.getElementById('email').value = user.email || '';
  document.getElementById('phone').value = user.phone || '';

  // Profile save
  document.getElementById('profile-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('save-profile-btn');
    const saving = document.getElementById('profile-saving');
    const alertEl = document.getElementById('profile-alert');
    clearAlert(alertEl);

    const first_name = document.getElementById('first-name').value.trim();
    const last_name = document.getElementById('last-name').value.trim();
    const phone = document.getElementById('phone').value.trim();

    if (!first_name || !last_name) {
      showAlert(alertEl, 'First name and last name are required.', 'error');
      return;
    }

    btn.disabled = true;
    saving.style.display = 'inline';
    try {
      const updated = await api.put('/auth/me', { first_name, last_name, phone });
      // Update stored token user data
      const stored = Auth.getUser();
      if (stored) {
        stored.first_name = updated.user.first_name;
        stored.last_name = updated.user.last_name;
        stored.phone = updated.user.phone;
        localStorage.setItem('af_user', JSON.stringify(stored));
      }
      document.getElementById('avatar').textContent = (updated.user.first_name?.[0] || '') + (updated.user.last_name?.[0] || '');
      document.getElementById('user-name').textContent = `${updated.user.first_name} ${updated.user.last_name}`;
      showAlert(alertEl, 'Profile updated successfully.', 'success');
    } catch (err) {
      showAlert(alertEl, err.message || 'Could not save profile.', 'error');
    } finally {
      btn.disabled = false;
      saving.style.display = 'none';
    }
  });

  // Password strength meter
  document.getElementById('new-pw').addEventListener('input', function () {
    const { score, label, color } = pwStrength(this.value);
    const bar = document.getElementById('pw-strength-bar');
    bar.style.width = (score * 25) + '%';
    bar.style.background = color;
    document.getElementById('pw-strength-label').textContent = this.value ? label : '';
    checkMatch();
  });

  document.getElementById('confirm-pw').addEventListener('input', checkMatch);

  function checkMatch() {
    const nw = document.getElementById('new-pw').value;
    const cf = document.getElementById('confirm-pw').value;
    const hint = document.getElementById('pw-match-hint');
    if (!cf) { hint.textContent = ''; return; }
    hint.textContent = nw === cf ? '✓ Passwords match' : '✗ Passwords do not match';
    hint.style.color = nw === cf ? 'var(--green)' : 'var(--red)';
  }

  // Password change
  document.getElementById('pw-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('save-pw-btn');
    const saving = document.getElementById('pw-saving');
    const alertEl = document.getElementById('pw-alert');
    clearAlert(alertEl);

    const current_password = document.getElementById('current-pw').value;
    const new_password = document.getElementById('new-pw').value;
    const confirm_password = document.getElementById('confirm-pw').value;

    if (!current_password || !new_password || !confirm_password) {
      showAlert(alertEl, 'All password fields are required.', 'error');
      return;
    }
    if (new_password !== confirm_password) {
      showAlert(alertEl, 'New passwords do not match.', 'error');
      return;
    }
    if (new_password.length < 8) {
      showAlert(alertEl, 'New password must be at least 8 characters.', 'error');
      return;
    }

    btn.disabled = true;
    saving.style.display = 'inline';
    try {
      const res = await api.post('/auth/change-password', { current_password, new_password, confirm_password });
      if (res && res.token) localStorage.setItem(Auth.TOKEN_KEY, res.token);
      showAlert(alertEl, 'Password changed successfully.', 'success');
      document.getElementById('pw-form').reset();
      document.getElementById('pw-strength-bar').style.width = '0%';
      document.getElementById('pw-strength-label').textContent = '';
      document.getElementById('pw-match-hint').textContent = '';
    } catch (err) {
      showAlert(alertEl, err.message || 'Could not change password.', 'error');
    } finally {
      btn.disabled = false;
      saving.style.display = 'none';
    }
  });
});

function pwStrength(pw) {
  let score = 0;
  if (pw.length >= 8)  score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  score = Math.min(score, 4);
  const map = [
    { label: 'Very weak', color: '#dc2626' },
    { label: 'Weak',      color: '#f59e0b' },
    { label: 'Fair',      color: '#f59e0b' },
    { label: 'Strong',    color: '#16a34a' },
    { label: 'Very strong', color: '#15803d' },
  ];
  return { score, ...map[score] };
}

function showAlert(el, msg, type) {
  el.textContent = msg;
  el.className = 'alert-inline ' + type;
  setTimeout(() => clearAlert(el), 5000);
}

function clearAlert(el) {
  el.textContent = '';
  el.className = 'alert-inline';
}
