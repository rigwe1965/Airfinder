let currentPage = 1;

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireStaff()) return;
  loadBookings();
  document.getElementById('status-filter').addEventListener('change', () => { currentPage = 1; loadBookings(); });
});

async function loadBookings() {
  const status = document.getElementById('status-filter').value;
  try {
    const data = await Admin.loadAllBookings(currentPage, status);
    renderBookings(data.bookings);
    renderPagination(data.pages, data.page);
  } catch { document.getElementById('bookings-tbody').innerHTML = '<tr><td colspan="8" class="text-gray">Failed to load.</td></tr>'; }
}

function renderBookings(bookings) {
  if (!bookings.length) { document.getElementById('bookings-tbody').innerHTML = '<tr><td colspan="8" class="text-gray" style="text-align:center;padding:20px;">No bookings found.</td></tr>'; return; }
  document.getElementById('bookings-tbody').innerHTML = bookings.map(b => `
    <tr>
      <td class="td-mono">${escapeHtml(b.reference)}</td>
      <td><div class="text-sm">${escapeHtml(b.customer_name || 'Guest')}</div><div class="text-xs text-gray">${escapeHtml(b.customer_email || '')}</div></td>
      <td><strong>${escapeHtml(b.origin)} → ${escapeHtml(b.destination)}</strong></td>
      <td>${escapeHtml(b.departure_date)}</td>
      <td class="text-sm">${escapeHtml(b.airline)}</td>
      <td><strong>${Admin.formatCurrency(b.pricing.total)}</strong></td>
      <td>${Admin.statusBadge(b.status)}</td>
      <td>
        <select ${Actions.attr('updateStatus', [b.id, '$value'], 'change')} style="padding:4px 8px;border:1px solid var(--gray-200);border-radius:4px;font-size:12px;">
          <option value="">Change...</option>
          <option value="confirmed">Confirm</option>
          <option value="cancelled">Cancel</option>
          <option value="refunded">Refund</option>
        </select>
      </td>
    </tr>`).join('');
}

function renderPagination(pages, current) {
  if (pages <= 1) { document.getElementById('pagination').innerHTML = ''; return; }
  let html = `<button class="page-btn" ${Actions.attr('changePage', [current-1])} ${current<=1?'disabled':''}>← Prev</button>`;
  for (let i = 1; i <= pages; i++) html += `<button class="page-btn ${i===current?'active':''}" ${Actions.attr('changePage', [i])}>${i}</button>`;
  html += `<button class="page-btn" ${Actions.attr('changePage', [current+1])} ${current>=pages?'disabled':''}>Next →</button>`;
  document.getElementById('pagination').innerHTML = html;
}

function changePage(p) { currentPage = p; loadBookings(); }

async function updateStatus(id, status) {
  if (!status) return;
  try {
    await Admin.updateBooking(id, { status });
    Admin.showToast(`Booking status updated to ${status}`);
    loadBookings();
  } catch (e) { Admin.showToast(e.message, 'error'); }
}

Actions.register({ changePage, updateStatus });
