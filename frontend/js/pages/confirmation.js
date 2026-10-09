function copyRef(ref) {
  navigator.clipboard.writeText(ref).then(() => {
    const btn = document.getElementById('copy-ref-btn');
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy', 2000);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const raw = sessionStorage.getItem('af_booking');
  if (!raw) { window.location.href = '/'; return; }
  const b = JSON.parse(raw);
  const p = b.pricing;

  const bookedAt = b.created_at ? new Date(b.created_at).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }) : '';

  const checkinDate = b.departure_date ? (() => {
    const d = new Date(b.departure_date);
    d.setDate(d.getDate() - 1);
    return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
  })() : null;

  const flightStatusLink = b.flight_number && b.departure_date
    ? `<a href="/flight-status.html?flight=${encodeURIComponent(b.flight_number)}&date=${encodeURIComponent(b.departure_date)}" class="btn btn-secondary btn-sm" style="font-size:12px;padding:4px 12px;">✈ Track Flight</a>`
    : '';

  const baggageLabel = { carry_on: 'Carry-on only', checked_1: '1 Checked bag', checked_2: '2 Checked bags' }[b.baggage] || '';
  const seatLabel = { standard: 'Standard', window: 'Window', aisle: 'Aisle', extra_legroom: 'Extra legroom', front_row: 'Front row' }[b.seat_preference] || '';

  const isMc = b.is_multicity;

  document.getElementById('booking-details').innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;flex-wrap:wrap;gap:8px;">
      <div>
        <div style="font-size:1.2rem;font-weight:800;">${escapeHtml(b.origin)} → ${escapeHtml(b.destination)}</div>
        <div class="text-gray text-sm">${escapeHtml(b.airline)} · ${escapeHtml(b.flight_number || '')} · ${escapeHtml(b.departure_date)}</div>
        ${bookedAt ? `<div class="text-gray text-sm">Booked ${bookedAt}</div>` : ''}
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
        <span class="badge badge-green">Confirmed</span>
        ${flightStatusLink}
      </div>
    </div>

    <div class="price-line">
      <span>Reference</span>
      <span style="display:flex;align-items:center;gap:8px;">
        <span class="td-mono">${escapeHtml(b.reference)}</span>
        <button id="copy-ref-btn" ${Actions.attr('copyRef', [b.reference])} style="font-size:11px;padding:2px 8px;border:1px solid #d1d5db;border-radius:4px;background:#fff;cursor:pointer;color:#374151;">Copy</button>
      </span>
    </div>
    ${isMc ? `<div class="price-line"><span>Group Reference</span><span class="td-mono">${escapeHtml(b.group_reference)}</span></div>` : ''}
    <div class="price-line"><span>Cabin</span><span>${escapeHtml(b.cabin_class)}</span></div>
    <div class="price-line"><span>Passengers</span><span>${b.passenger_count}</span></div>
    ${baggageLabel ? `<div class="price-line"><span>Baggage</span><span>${baggageLabel}</span></div>` : ''}
    ${seatLabel ? `<div class="price-line"><span>Seat</span><span>${seatLabel}</span></div>` : ''}
    ${checkinDate ? `<div class="price-line"><span>Check-in opens</span><span>${checkinDate}</span></div>` : ''}
    <hr class="divider">
    <div class="price-line"><span>Base fare</span><span>${fmtCurrency(p.base_fare)}</span></div>
    <div class="price-line"><span>Markup</span><span>${fmtCurrency(p.markup)}</span></div>
    <div class="price-line"><span>Service fee</span><span>${fmtCurrency(p.service_fee)}</span></div>
    ${p.baggage_fee > 0 ? `<div class="price-line"><span>Baggage</span><span>${fmtCurrency(p.baggage_fee)}</span></div>` : ''}
    ${p.seat_fee > 0 ? `<div class="price-line"><span>Seat selection</span><span>${fmtCurrency(p.seat_fee)}</span></div>` : ''}
    <div class="price-line total"><span>Total Paid</span><span style="color:var(--green);">${fmtCurrency(p.total)}</span></div>`;
});

Actions.register({ copyRef });
