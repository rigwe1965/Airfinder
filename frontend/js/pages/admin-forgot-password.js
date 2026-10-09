document.getElementById('forgot-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('submit-btn');
  btn.disabled = true; btn.textContent = 'Sending...';
  clearAlert();
  try {
    const data = await api.post('/staff/auth/forgot-password', {
      email: document.getElementById('email').value,
    });
    if (data.reset_url) {
      // Mail not configured — show link on screen
      const box = document.getElementById('reset-link-box');
      const anchor = document.getElementById('reset-link-anchor');
      anchor.href = data.reset_url;
      anchor.textContent = data.reset_url;
      box.classList.remove('hidden');
      showAlert('Mail not configured. Use the link below to reset your password.', 'warning');
    } else {
      showAlert('Reset link sent! Check your email inbox.', 'success');
    }
  } catch (err) {
    showAlert(err.message || 'Something went wrong. Try again.', 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Send Reset Link';
  }
});
function showAlert(msg, type = 'error') {
  document.getElementById('alert').innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
}
function clearAlert() { document.getElementById('alert').innerHTML = ''; }
