document.addEventListener('DOMContentLoaded', () => {
  Auth.redirectIfLoggedIn();

  document.getElementById('toggle-pw').addEventListener('click', () => {
    const pw = document.getElementById('password');
    pw.type = pw.type === 'password' ? 'text' : 'password';
  });

  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    btn.disabled = true; btn.textContent = 'Signing in...';
    clearAlert();
    try {
      const data = await api.post('/auth/login', {
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
      });
      Auth.save(data.token, { ...data.user, role: 'customer' });
      const redirect = sessionStorage.getItem('af_redirect_after_login') || '/account/dashboard.html';
      sessionStorage.removeItem('af_redirect_after_login');
      window.location.href = redirect;
    } catch (e) {
      showAlert(e.message || 'Login failed');
      btn.disabled = false; btn.textContent = 'Sign In';
    }
  });
});
function showAlert(msg) { document.getElementById('alert').innerHTML = `<div class="alert alert-error">${msg}</div>`; }
function clearAlert() { document.getElementById('alert').innerHTML = ''; }
