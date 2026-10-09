document.addEventListener('DOMContentLoaded', () => {
  Auth.redirectIfLoggedIn();

  document.getElementById('toggle-pw').addEventListener('click', () => {
    const pw = document.getElementById('password');
    pw.type = pw.type === 'password' ? 'text' : 'password';
  });

  document.getElementById('password').addEventListener('input', function() {
    const v = this.value;
    let score = 0;
    if (v.length >= 8) score++;
    if (/[A-Z]/.test(v)) score++;
    if (/[0-9]/.test(v)) score++;
    if (/[^A-Za-z0-9]/.test(v)) score++;
    const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
    const colors = ['', 'var(--red)', 'var(--amber)', 'var(--green-light)', 'var(--green)'];
    document.getElementById('strength-fill').style.width = `${score * 25}%`;
    document.getElementById('strength-fill').style.background = colors[score];
    document.getElementById('strength-label').textContent = labels[score];
  });

  document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    btn.disabled = true; btn.textContent = 'Creating account...';
    clearAlert();
    try {
      const data = await api.post('/auth/register', {
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
        first_name: document.getElementById('first_name').value,
        last_name: document.getElementById('last_name').value,
        phone: document.getElementById('phone').value,
      });
      Auth.save(data.token, { ...data.user, role: 'customer' });
      window.location.href = '/account/dashboard.html';
    } catch (e) {
      showAlert(e.message || 'Registration failed');
      btn.disabled = false; btn.textContent = 'Create Account';
    }
  });
});
function showAlert(msg) { document.getElementById('alert').innerHTML = `<div class="alert alert-error">${msg}</div>`; }
function clearAlert() { document.getElementById('alert').innerHTML = ''; }
