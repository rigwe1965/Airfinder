let allBookings = [];
let activeTab = 'all';
let cancelPending = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireLogin()) return;
  const user = Auth.getUser();
  document.getElementById('avatar').textContent = (user.first_name?.[0] || '') + (user.last_name?.[0] || '');
  document.getElementById('user-name').textContent = `${user.first_name} ${user.last_name}`;
  document.getElementById('user-email').textContent = user.email;

  try {
    allBookings = await api.get('/bookings');
    updateCounts();
    renderTab();
  } catch {
    document.getElementById('bookings-list').innerHTML = '<p class="text-gray">Could not load bookings.</p>';
  }

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activeTab = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderTab();
    });
  });

  document.getElementById('search-input').addEventListener('input', renderTab);
});

function updateCounts() {
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('cnt-all').textContent = allBookings.length;
  document.getElementById('cnt-upcoming').textContent = allBookings.filter(b => b.status === 'confirmed' && b.departure_date >= today).length;
  document.getElementById('cnt-past').textContent = allBookings.filter(b => b.status === 'confirmed' && b.departure_date < today).length;
  document.getElementById('cnt-cancelled').textContent = allBookings.filter(b => b.status === 'cancelled').length;
}

function filterBookings() {
  const today = new Date().toISOString().split('T')[0];
  const q = document.getElementById('search-input').value.trim().toLowerCase();
  let list = allBookings;

  if (activeTab === 'upcoming') list = list.filter(b => b.status === 'confirmed' && b.departure_date >= today);
  else if (activeTab === 'past')  list = list.filter(b => b.status === 'confirmed' && b.departure_date < today);
  else if (activeTab === 'cancelled') list = list.filter(b => b.status === 'cancelled');

  if (q) {
    list = list.filter(b =>
      b.reference.toLowerCase().includes(q) ||
      b.origin.toLowerCase().includes(q) ||
      b.destination.toLowerCase().includes(q) ||
      b.airline.toLowerCase().includes(q) ||
      (b.flight_number || '').toLowerCase().includes(q)
    );
  }
  return list;
}

function renderTab() {
  const list = filterBookings();
  const el = document.getElementById('bookings-list');
  if (list.length === 0) {
    const emptyMsg = {
      all: 'No bookings yet.',
      upcoming: 'No upcoming trips.',
      past: 'No past flights found.',
      cancelled: 'No cancelled bookings.',
    }[activeTab];
    el.innerHTML = `
      <div class="empty-tab">
        <div class="empty-tab-icon">✈</div>
        <h3>${emptyMsg}</h3>
        ${activeTab === 'all' || activeTab === 'upcoming'
          ? '<p>Ready to explore?</p><a href="/" class="btn btn-primary mt-3">Search Flights</a>'
          : '<p>Switch tabs to see other bookings.</p>'}
      </div>`;
    return;
  }
  el.innerHTML = list.map(b => renderCard(b)).join('');
}

function renderCard(b) {
  const today = new Date().toISOString().split('T')[0];
  const isUpcoming = b.status === 'confirmed' && b.departure_date >= today;
  const p = b.pricing;

  const paxHtml = (b.passengers || []).map(px => `
    <div class="pax-item">
      <span class="pax-name">${escapeHtml(px.first_name)} ${escapeHtml(px.last_name)}</span>
      ${px.passport ? `<span class="pax-passport">${escapeHtml(px.passport)}</span>` : ''}
    </div>`).join('') || '<div class="pax-item"><span class="pax-name">' + b.passenger_count + ' passenger(s)</span></div>';

  const cancelBtn = isUpcoming
    ? `<button class="btn btn-secondary btn-sm" ${Actions.attr('toggleCancel', [b.id])}>Cancel Booking</button>`
    : '';

  const cancelInline = `
    <div class="cancel-inline" id="cancel-${b.id}" style="display:none;">
      <p>Are you sure you want to cancel booking <strong>${b.reference}</strong>? This cannot be undone.</p>
      <div class="cancel-inline-btns">
        <button class="btn btn-danger btn-sm" ${Actions.attr('confirmCancel', [b.id])}>Yes, cancel it</button>
        <button class="btn btn-secondary btn-sm" ${Actions.attr('toggleCancel', [b.id])}>Keep booking</button>
      </div>
    </div>`;

  return `
    <div class="booking-card" id="card-${b.id}">
      <div class="booking-card-header">
        <div class="booking-ref-group">
          <span class="booking-ref">${b.reference}</span>
          ${b.is_multicity ? '<span class="multicity-badge">Multi-city</span>' : ''}
          ${b.group_reference ? `<span style="font-size:11px;color:var(--gray-400);font-family:monospace;">Group: ${b.group_reference}</span>` : ''}
        </div>
        <div class="booking-header-right">
          <span class="badge ${statusBadge(b.status)}">${b.status}</span>
          ${cancelBtn}
        </div>
      </div>

      <div class="booking-body">
        <div class="booking-route-big">${escapeHtml(b.origin)} → ${escapeHtml(b.destination)}</div>
        <div class="booking-flight-meta">
          <span>✈ ${escapeHtml(b.airline)}${b.flight_number ? ' ' + escapeHtml(b.flight_number) : ''}</span>
          <span>📅 ${formatDate(b.departure_date)}</span>
          <span>💺 ${capitalize(b.cabin_class)}</span>
          <span>👤 ${b.passenger_count} passenger${b.passenger_count !== 1 ? 's' : ''}</span>
          <span style="color:var(--gray-400);font-size:12px;">Booked ${formatDate(b.created_at?.split('T')[0] || '')}</span>
        </div>

        <div class="booking-sections">
          <div>
            <div class="booking-section-title">Passengers</div>
            <div>${paxHtml}</div>
          </div>
          <div>
            <div class="booking-section-title">Price Breakdown</div>
            <div class="price-rows">
              <div class="price-row"><span>Base fare</span><span class="price-val">${fmtCurrency(p.base_fare)}</span></div>
              <div class="price-row"><span>Markup</span><span class="price-val">${fmtCurrency(p.markup)}</span></div>
              <div class="price-row"><span>Service fee</span><span class="price-val">${fmtCurrency(p.service_fee)}</span></div>
              ${p.baggage_fee > 0 ? `<div class="price-row"><span>Baggage</span><span class="price-val">${fmtCurrency(p.baggage_fee)}</span></div>` : ''}
              ${p.seat_fee > 0 ? `<div class="price-row"><span>Seat</span><span class="price-val">${fmtCurrency(p.seat_fee)}</span></div>` : ''}
              <div class="price-row total"><span>Total</span><span class="price-val">${fmtCurrency(p.total)}</span></div>
            </div>
          </div>
        </div>

        ${isUpcoming ? `<div class="cancel-section">${cancelInline}</div>` : ''}
      </div>
    </div>`;
}

function toggleCancel(id) {
  const el = document.getElementById('cancel-' + id);
  if (!el) return;
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

async function confirmCancel(id) {
  const btn = document.querySelector(`#cancel-${id} .btn-danger`);
  if (btn) { btn.disabled = true; btn.textContent = 'Cancelling...'; }
  try {
    await api.post(`/bookings/${id}/cancel`, {});
    const booking = allBookings.find(b => b.id === id);
    if (booking) booking.status = 'cancelled';
    showAlert('Booking cancelled successfully.', 'success');
    updateCounts();
    renderTab();
  } catch (e) {
    showAlert(e.message || 'Could not cancel booking.', 'error');
    if (btn) { btn.disabled = false; btn.textContent = 'Yes, cancel it'; }
  }
}

function showAlert(msg, type) {
  const el = document.getElementById('alert');
  el.innerHTML = `<div class="alert alert-${type}" style="margin-bottom:16px;padding:12px 16px;border-radius:var(--radius-sm);background:${type === 'success' ? 'var(--green-pale)' : '#fef2f2'};color:${type === 'success' ? 'var(--green-dark)' : 'var(--red)'};font-size:14px;font-weight:500;">${msg}</div>`;
  setTimeout(() => { el.innerHTML = ''; }, 4000);
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function statusBadge(s) {
  return s === 'confirmed' ? 'badge-green' : s === 'cancelled' ? 'badge-red' : 'badge-amber';
}

function capitalize(s) {
  return (s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

Actions.register({ confirmCancel, toggleCancel });
