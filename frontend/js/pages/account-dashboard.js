document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireLogin()) return;
  const user = Auth.getUser();
  if (!user) return;

  document.getElementById('avatar').textContent = (user.first_name?.[0] || '') + (user.last_name?.[0] || '');
  document.getElementById('user-name').textContent = `${user.first_name} ${user.last_name}`;
  document.getElementById('user-email').textContent = user.email;
  document.getElementById('greeting-name').textContent = user.first_name;

  try {
    const bookings = await api.get('/bookings');
    const today = new Date().toISOString().split('T')[0];

    // Stats
    document.getElementById('stat-bookings').textContent = bookings.length;
    const confirmed = bookings.filter(b => b.status === 'confirmed');
    const spent = confirmed.reduce((s, b) => s + b.pricing.total, 0);
    document.getElementById('stat-spent').textContent = fmtCurrency(spent);
    const upcoming = confirmed.filter(b => b.departure_date >= today);
    document.getElementById('stat-upcoming').textContent = upcoming.length;

    // Next trip hero
    const nextTrip = upcoming.sort((a, b) => a.departure_date.localeCompare(b.departure_date))[0];
    if (nextTrip) {
      const depDate = new Date(nextTrip.departure_date);
      const daysOut = Math.ceil((depDate - new Date()) / 86400000);
      document.getElementById('next-trip-section').innerHTML = `
        <div class="next-trip-card">
          <div>
            <div class="next-trip-label">✈ Your Next Trip</div>
            <div class="next-trip-route">${escapeHtml(nextTrip.origin)} → ${escapeHtml(nextTrip.destination)}</div>
            <div class="next-trip-meta">${escapeHtml(nextTrip.airline)}${nextTrip.flight_number ? ' · ' + escapeHtml(nextTrip.flight_number) : ''} · ${escapeHtml(nextTrip.cabin_class)}</div>
            <div class="next-trip-meta">${formatDate(nextTrip.departure_date)}</div>
            <div class="next-trip-ref">${nextTrip.reference}</div>
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:12px;">
            <div class="next-trip-days">
              <div class="next-trip-days-num">${daysOut}</div>
              <div class="next-trip-days-label">day${daysOut !== 1 ? 's' : ''} to go</div>
            </div>
            <a href="/account/bookings.html" class="btn btn-sm next-trip-cta">View booking</a>
          </div>
        </div>`;
    }

    // Recent bookings list
    const recent = bookings.slice(0, 5);
    if (recent.length === 0) {
      document.getElementById('recent-bookings').innerHTML =
        '<div class="card card-body text-center"><p class="text-gray">No bookings yet.</p><a href="/" class="btn btn-primary mt-2">Search Flights</a></div>';
    } else {
      document.getElementById('recent-bookings').innerHTML = recent.map(b => `
        <div class="recent-booking-card">
          <div class="rbc-route">${escapeHtml(b.origin)} → ${escapeHtml(b.destination)}</div>
          <div class="rbc-meta">
            <div class="rbc-airline">${escapeHtml(b.airline)}${b.flight_number ? ' · ' + escapeHtml(b.flight_number) : ''}</div>
            <div class="rbc-date">${formatDate(b.departure_date)} · ${escapeHtml(b.cabin_class)} · ${b.passenger_count} pax</div>
          </div>
          <div class="rbc-right">
            <span class="badge ${statusBadge(b.status)}">${b.status}</span>
            <div class="rbc-total">${fmtCurrency(b.pricing.total)}</div>
            <div class="rbc-ref">${b.reference}</div>
          </div>
        </div>`).join('');
    }
  } catch (e) {
    document.getElementById('recent-bookings').innerHTML = '<p class="text-gray">Could not load bookings.</p>';
  }
});

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function statusBadge(s) {
  return s === 'confirmed' ? 'badge-green' : s === 'cancelled' ? 'badge-red' : 'badge-amber';
}
