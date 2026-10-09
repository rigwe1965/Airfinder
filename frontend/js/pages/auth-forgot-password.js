document.getElementById('forgot-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('submit-btn');
  btn.disabled = true; btn.textContent = 'Sending...';
  try {
    await api.post('/auth/forgot-password', { email: document.getElementById('email').value });
    document.getElementById('alert').innerHTML = '<div class="alert alert-success">✓ If that email exists, a reset link has been sent. Check your inbox.</div>';
    document.getElementById('forgot-form').classList.add('hidden');
  } catch {
    document.getElementById('alert').innerHTML = '<div class="alert alert-error">Something went wrong. Try again.</div>';
    btn.disabled = false; btn.textContent = 'Send Reset Link';
  }
});
