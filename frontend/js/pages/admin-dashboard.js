document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireStaff()) return;

  const canSeeCustomers = ['super_admin', 'admin', 'agent'].includes(Auth.getRole());
  const [dashData, bookingsData, customersData] = await Promise.all([
    Admin.loadDashboard().catch(() => null),
    Admin.loadAllBookings(1).catch(() => null),
    canSeeCustomers ? Admin.loadCustomers(1).catch(() => null) : Promise.resolve(null),
  ]);

  if (dashData) {
    const b = dashData.bookings;
    const r = dashData.revenue;
    let html = `
      <div class="stat-card green"><div class="stat-label">Total Bookings</div><div class="stat-value">${b.total}</div><div class="stat-icon"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2z"/></svg></div></div>
      <div class="stat-card blue"><div class="stat-label">Confirmed</div><div class="stat-value">${b.confirmed}</div><div class="stat-icon"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div></div>
      <div class="stat-card amber"><div class="stat-label">Total Revenue</div><div class="stat-value">${Admin.formatCurrency(r.total_usd)}</div><div class="stat-icon"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10h12"/><path d="M4 14h9"/><path d="M19 6a7.7 7.7 0 0 0-5.2-2A7.9 7.9 0 0 0 6 12c0 4.4 3.5 8 7.8 8 2 0 3.8-.8 5.2-2"/></svg></div></div>
      <div class="stat-card green"><div class="stat-label">Total Customers</div><div class="stat-value">${dashData.customers}</div><div class="stat-icon"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div></div>`;
    if (dashData.staff !== undefined) {
      html += `<div class="stat-card"><div class="stat-label">Staff Members</div><div class="stat-value">${dashData.staff}</div><div class="stat-icon"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></div></div>`;
    }
    document.getElementById('stat-grid').innerHTML = html;
  }

  if (bookingsData?.bookings) {
    document.getElementById('recent-bookings-tbody').innerHTML =
      bookingsData.bookings.slice(0,8).map(b => `
        <tr>
          <td class="td-mono">${b.reference}</td>
          <td>${b.origin}→${b.destination}</td>
          <td>${Admin.formatCurrency(b.pricing.total)}</td>
          <td>${Admin.statusBadge(b.status)}</td>
        </tr>`).join('') || '<tr><td colspan="4" class="text-gray">No bookings</td></tr>';
  }

  if (customersData?.customers) {
    document.getElementById('recent-customers-tbody').innerHTML =
      customersData.customers.slice(0,8).map(c => `
        <tr>
          <td>${escapeHtml(c.first_name)} ${escapeHtml(c.last_name)}</td>
          <td class="text-sm">${escapeHtml(c.email)}</td>
          <td>${c.booking_count}</td>
        </tr>`).join('') || '<tr><td colspan="3" class="text-gray">No customers</td></tr>';
  }
});
