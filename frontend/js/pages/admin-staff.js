let staffList = [];
const isSuperAdmin = () => Auth.getRole() === 'super_admin';

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireRole('super_admin', 'admin')) return;
  loadStaff();
  document.getElementById('search-input').addEventListener('input', function() {
    const q = this.value.toLowerCase();
    renderStaff(staffList.filter(s =>
      s.email.includes(q) ||
      s.first_name.toLowerCase().includes(q) ||
      s.last_name.toLowerCase().includes(q)
    ));
  });
});

async function loadStaff() {
  try {
    staffList = await Admin.loadStaff();
    renderStaff(staffList);
  } catch {
    document.getElementById('staff-tbody').innerHTML = '<tr><td colspan="6" class="text-gray">Failed to load staff.</td></tr>';
  }
}

function renderStaff(list) {
  if (!list.length) {
    document.getElementById('staff-tbody').innerHTML = '<tr><td colspan="6" class="text-gray" style="text-align:center;padding:20px;">No staff found.</td></tr>';
    return;
  }
  const superAdmin = isSuperAdmin();
  document.getElementById('staff-tbody').innerHTML = list.map(s => `
    <tr>
      <td><strong>${escapeHtml(s.first_name)} ${escapeHtml(s.last_name)}</strong></td>
      <td>${escapeHtml(s.email)}</td>
      <td>${Admin.roleBadge(s.role)}</td>
      <td>${s.is_active ? '<span class="badge badge-green">Active</span>' : '<span class="badge badge-red">Inactive</span>'}</td>
      <td class="text-sm text-gray">${s.last_login ? new Date(s.last_login).toLocaleDateString('de-DE') : 'Never'}</td>
      <td style="display:flex;gap:6px;flex-wrap:wrap;">
        <button class="btn btn-secondary btn-sm" ${Actions.attr('openEditModal', [s.id])}>Edit</button>
        <button class="btn btn-secondary btn-sm" ${Actions.attr('resetPassword', [s.id, s.first_name])}>Reset PW</button>
        <button class="btn btn-sm ${s.is_active ? 'btn-danger' : 'btn-primary'}" ${Actions.attr('toggleActive', [s.id, !s.is_active])}>${s.is_active ? 'Deactivate' : 'Activate'}</button>
        ${superAdmin ? `<button class="btn btn-sm btn-danger" ${Actions.attr('deleteStaff', [s.id, s.first_name + ' ' + s.last_name])}>Delete</button>` : ''}
      </td>
    </tr>`).join('');
}

// Create modal
function openCreateModal() {
  document.getElementById('create-modal').classList.remove('hidden');
  document.getElementById('create-success').classList.add('hidden');
  document.getElementById('create-staff-form').classList.remove('hidden');
  document.getElementById('modal-alert').innerHTML = '';
}
function closeCreateModal() {
  document.getElementById('create-modal').classList.add('hidden');
  document.getElementById('create-staff-form').reset();
  loadStaff();
}

document.getElementById('create-staff-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('create-btn');
  btn.disabled = true; btn.textContent = 'Creating...';
  document.getElementById('modal-alert').innerHTML = '';
  try {
    const tempPw = document.getElementById('cf_temp_password').value.trim();
    const payload = {
      first_name: document.getElementById('cf_first').value,
      last_name: document.getElementById('cf_last').value,
      email: document.getElementById('cf_email').value,
      role: document.querySelector('input[name=cf_role]:checked').value,
    };
    if (tempPw) payload.temp_password = tempPw;
    const data = await Admin.createStaff(payload);
    document.getElementById('create-staff-form').classList.add('hidden');
    document.getElementById('cred-box').innerHTML =
      `<p class="text-sm"><strong>Email:</strong> ${escapeHtml(data.staff.email)}</p>` +
      `<p class="text-sm mt-1"><strong>Temp Password:</strong> <code style="background:var(--gray-100);padding:2px 6px;border-radius:4px;">${escapeHtml(data.temp_password)}</code></p>` +
      `<p class="text-xs text-gray mt-1">Share this securely. Staff must change it on first login.</p>`;
    document.getElementById('create-success').classList.remove('hidden');
  } catch (err) {
    document.getElementById('modal-alert').innerHTML = `<div class="alert alert-error">${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false; btn.textContent = 'Create Account';
  }
});

// Edit modal
function openEditModal(id) { const s = staffList.find(x => x.id === id); if (!s) return;
  document.getElementById('edit-modal').classList.remove('hidden');
  document.getElementById('edit-modal-alert').innerHTML = '';
  document.getElementById('ef_id').value = s.id;
  document.getElementById('ef_first').value = s.first_name;
  document.getElementById('ef_last').value = s.last_name;
  document.getElementById('ef_email').value = s.email;
  const roleRadio = document.querySelector(`input[name=ef_role][value="${s.role}"]`);
  if (roleRadio) roleRadio.checked = true;
  document.querySelector(`input[name=ef_status][value="${s.is_active ? 'active' : 'inactive'}"]`).checked = true;
  // Show super_admin option only to super admins editing super admin accounts
  document.getElementById('ef_role_super_admin_option').style.display = isSuperAdmin() ? '' : 'none';
}
function closeEditModal() {
  document.getElementById('edit-modal').classList.add('hidden');
}

document.getElementById('edit-staff-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('edit-btn');
  btn.disabled = true; btn.textContent = 'Saving...';
  document.getElementById('edit-modal-alert').innerHTML = '';
  try {
    const id = document.getElementById('ef_id').value;
    const payload = {
      first_name: document.getElementById('ef_first').value,
      last_name: document.getElementById('ef_last').value,
      email: document.getElementById('ef_email').value,
      role: document.querySelector('input[name=ef_role]:checked').value,
      is_active: document.querySelector('input[name=ef_status]:checked').value === 'active',
    };
    await Admin.updateStaff(id, payload);
    closeEditModal();
    Admin.showToast('Staff member updated');
    loadStaff();
  } catch (err) {
    document.getElementById('edit-modal-alert').innerHTML = `<div class="alert alert-error">${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false; btn.textContent = 'Save Changes';
  }
});

async function resetPassword(id, name) {
  if (!confirm(`Reset password for ${name}?`)) return;
  try {
    const data = await Admin.resetStaffPassword(id);
    Admin.showToast(`Password reset. Temp: ${data.temp_password}`);
  } catch (err) { Admin.showToast(err.message, 'error'); }
}

async function toggleActive(id, isActive) {
  try {
    await Admin.updateStaff(id, { is_active: isActive });
    Admin.showToast(isActive ? 'Staff activated' : 'Staff deactivated');
    loadStaff();
  } catch (err) { Admin.showToast(err.message, 'error'); }
}

async function deleteStaff(id, name) {
  if (!confirm(`Permanently delete ${name}? This cannot be undone.`)) return;
  try {
    await Admin.deleteStaff(id);
    Admin.showToast(`${name} deleted`);
    loadStaff();
  } catch (err) { Admin.showToast(err.message, 'error'); }
}

Actions.register({ closeCreateModal, closeEditModal, deleteStaff, openCreateModal, openEditModal, resetPassword, toggleActive });
