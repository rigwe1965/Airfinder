document.addEventListener('DOMContentLoaded', () => {
  // Redirect if already staff-logged in
  if (Auth.isLoggedIn() && Auth.isStaff()) {
    window.location.href = '/admin/dashboard.html';
    return;
  }

  document.getElementById('toggle-pw').addEventListener('click', () => {
    const pw = document.getElementById('password');
    pw.type = pw.type === 'password' ? 'text' : 'password';
  });

  document.getElementById('staff-login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    btn.disabled = true; btn.textContent = 'Signing in...';
    clearAlert();
    try {
      const data = await api.post('/staff/auth/login', {
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
      });
      Auth.saveStaff(data.token, data.staff);

      if (data.must_change_password) {
        window.location.href = '/admin/change-password.html';
      } else {
        window.location.href = '/admin/dashboard.html';
      }
    } catch (e) {
      showAlert(e.message || 'Login failed. Check your credentials.');
      btn.disabled = false; btn.textContent = 'Sign In to Staff Portal';
    }
  });
});
function showAlert(msg) { document.getElementById('alert').innerHTML = `<div class="alert alert-error">${msg}</div>`; }
function clearAlert() { document.getElementById('alert').innerHTML = ''; }
