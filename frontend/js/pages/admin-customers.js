let currentPage = 1;
let searchTimer;

document.addEventListener('DOMContentLoaded', () => {
  if (!Auth.requireStaff()) return;
  loadCustomers();
  document.getElementById('search-input').addEventListener('input', function() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { currentPage = 1; loadCustomers(this.value); }, 300);
  });
});

async function loadCustomers(search = '') {
  try {
    const data = await Admin.loadCustomers(currentPage, search);
    renderCustomers(data.customers);
    renderPagination(data.pages, data.page);
  } catch { document.getElementById('customers-tbody').innerHTML = '<tr><td colspan="7" class="text-gray">Failed to load.</td></tr>'; }
}

function renderCustomers(customers) {
  if (!customers.length) { document.getElementById('customers-tbody').innerHTML = '<tr><td colspan="7" class="text-gray" style="text-align:center;padding:20px;">No customers found.</td></tr>'; return; }
  document.getElementById('customers-tbody').innerHTML = customers.map(c => `
    <tr>
      <td><strong>${escapeHtml(c.first_name)} ${escapeHtml(c.last_name)}</strong></td>
      <td>${escapeHtml(c.email)}</td>
      <td>${escapeHtml(c.phone) || '—'}</td>
      <td>${c.booking_count}</td>
      <td>${Admin.formatCurrency(c.total_spent)}</td>
      <td class="text-sm text-gray">${Admin.formatDate(c.created_at)}</td>
      <td>${c.is_active ? '<span class="badge badge-green">Active</span>' : '<span class="badge badge-red">Inactive</span>'}</td>
    </tr>`).join('');
}

function renderPagination(pages, current) {
  if (pages <= 1) { document.getElementById('pagination').innerHTML = ''; return; }
  let html = `<button class="page-btn" ${Actions.attr('changePage', [current-1])} ${current<=1?'disabled':''}>← Prev</button>`;
  for (let i = 1; i <= Math.min(pages, 10); i++) html += `<button class="page-btn ${i===current?'active':''}" ${Actions.attr('changePage', [i])}>${i}</button>`;
  html += `<button class="page-btn" ${Actions.attr('changePage', [current+1])} ${current>=pages?'disabled':''}>Next →</button>`;
  document.getElementById('pagination').innerHTML = html;
}

function changePage(p) { currentPage = p; loadCustomers(document.getElementById('search-input').value); }

Actions.register({ changePage });
