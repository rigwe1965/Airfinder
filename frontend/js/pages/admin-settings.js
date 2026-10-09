document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireRole('super_admin')) return;
  try {
    const s = await api.get('/admin/settings');
    document.getElementById('cfg-markup').textContent = `${s.markup_percent}%`;
    document.getElementById('cfg-fee').textContent = `€${s.service_fee_usd}`;
    document.getElementById('cfg-commission').textContent = `${s.commission_percent}%`;
    document.getElementById('settings-body').innerHTML = `
      <div class="price-line"><span>Markup</span><span>${s.markup_percent}% of base fare</span></div>
      <div class="price-line"><span>Service Fee</span><span>€${s.service_fee_usd} per booking</span></div>
      <div class="price-line"><span>Commission</span><span>${s.commission_percent}% of base fare</span></div>`;
  } catch { document.getElementById('settings-body').innerHTML = '<p class="text-gray">Could not load settings.</p>'; }
});
