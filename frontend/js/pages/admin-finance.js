document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireRole('super_admin', 'admin', 'finance')) return;
  try {
    const data = await Admin.loadFinance();
    document.getElementById('revenue-grid').innerHTML = `
      <div class="revenue-card"><div class="revenue-label">Total Revenue</div><div class="revenue-value">${Admin.formatCurrency(data.total_revenue_usd)}</div></div>
      <div class="revenue-card"><div class="revenue-label">Commission Earned</div><div class="revenue-value">${Admin.formatCurrency(data.commission_usd)}</div></div>
      <div class="revenue-card"><div class="revenue-label">Markup Revenue</div><div class="revenue-value">${Admin.formatCurrency(data.markup_usd)}</div></div>
      <div class="revenue-card"><div class="revenue-label">Service Fees</div><div class="revenue-value">${Admin.formatCurrency(data.service_fees_usd)}</div></div>
      <div class="revenue-card"><div class="revenue-label">Baggage Fees</div><div class="revenue-value">${Admin.formatCurrency(data.baggage_fees_usd)}</div></div>
      <div class="revenue-card"><div class="revenue-label">Confirmed Bookings</div><div class="revenue-value">${data.total_bookings}</div></div>`;
    document.getElementById('breakdown-body').innerHTML = `
      <div class="price-line"><span>Average booking value</span><span><strong>${Admin.formatCurrency(data.avg_booking_value)}</strong></span></div>
      <div class="price-line"><span>Commission (3% of base fare)</span><span>${Admin.formatCurrency(data.commission_usd)}</span></div>
      <div class="price-line"><span>Markup (8% of base fare)</span><span>${Admin.formatCurrency(data.markup_usd)}</span></div>
      <div class="price-line"><span>Service fee (€15/booking)</span><span>${Admin.formatCurrency(data.service_fees_usd)}</span></div>
      <div class="price-line"><span>Baggage fees</span><span>${Admin.formatCurrency(data.baggage_fees_usd)}</span></div>
      <hr class="divider">
      <div class="price-line total"><span>Total Airfinder Earnings</span><span style="color:var(--green);">${Admin.formatCurrency(data.total_revenue_usd)}</span></div>`;
  } catch (e) {
    document.getElementById('revenue-grid').innerHTML = '<p class="text-gray">No data yet. Make some bookings first!</p>';
    document.getElementById('breakdown-body').innerHTML = '';
  }
});
