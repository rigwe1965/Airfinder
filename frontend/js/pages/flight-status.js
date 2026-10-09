// Set default date to today
document.getElementById('dateInput').value = new Date().toISOString().slice(0, 10);

// Read query params on load
const params = new URLSearchParams(location.search);
if (params.get('flight')) {
  document.getElementById('flightInput').value = params.get('flight').toUpperCase();
  if (params.get('date')) document.getElementById('dateInput').value = params.get('date');
  lookupFlight();
}

document.getElementById('flightInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') lookupFlight();
});

function fillExample(code) {
  document.getElementById('flightInput').value = code;
  lookupFlight();
}

async function lookupFlight() {
  const fn = document.getElementById('flightInput').value.trim().toUpperCase();
  const date = document.getElementById('dateInput').value;
  if (!fn) { document.getElementById('flightInput').focus(); return; }

  document.getElementById('examplesBlock').style.display = 'none';
  document.getElementById('statusResult').innerHTML = `
    <div style="text-align:center;padding:60px 0;">
      <div class="spinner"></div>
      <p class="text-gray mt-2">Looking up ${escapeHtml(fn)}...</p>
    </div>`;

  try {
    const data = await api.get(`/flights/status?flight=${encodeURIComponent(fn)}&date=${date}`);
    renderStatus(data);
  } catch (e) {
    document.getElementById('statusResult').innerHTML = `
      <div class="alert alert-error">
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        ${escapeHtml(e.message || 'Could not retrieve flight status. Please try again.')}
      </div>`;
    document.getElementById('examplesBlock').style.display = '';
  }
}

function renderStatus(f) {
  const statusClass = { green: 'status-green', amber: 'status-amber', red: 'status-red', blue: 'status-blue' }[f.status_color] || 'status-green';
  const statusIcon = { on_time: '✓', delayed: '⚠', boarding: '🚪', departed: '✈', arrived: '✓', cancelled: '✕' }[f.status] || '•';

  // Determine step states
  const steps = ['Scheduled', 'Boarding', 'Departed', 'Arrived'];
  const stepState = { on_time: 0, delayed: 0, boarding: 1, departed: 2, arrived: 3, cancelled: -1 }[f.status];

  const stepHTML = steps.map((label, i) => {
    const isDone = stepState > i;
    const isActive = stepState === i;
    const cls = isDone ? 'done' : isActive ? 'active' : '';
    const lineCls = isDone ? 'done' : '';
    const dot = isDone ? '✓' : (i + 1);
    const lineEl = i < steps.length - 1 ? `<div class="step-line ${lineCls}"></div>` : '';
    return `<div class="step"><div class="step-dot ${cls}">${dot}</div><div class="step-label ${cls}">${label}</div></div>${lineEl}`;
  }).join('');

  const cancelledBanner = f.status === 'cancelled' ? `
    <div style="background:#fee2e2;border:1px solid #fca5a5;border-radius:var(--radius-sm);padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:10px;">
      <span style="font-size:20px;">✕</span>
      <div>
        <div style="font-weight:700;color:#991b1b;">Flight Cancelled</div>
        <div style="font-size:13px;color:#b91c1c;margin-top:2px;">Please contact your airline or check your booking for rebooking options.</div>
      </div>
    </div>` : '';

  const depActualClass = f.delay_minutes > 0 ? 'delayed' : '';
  const nextDayNote = f.next_day_arrival ? ' <span style="font-size:11px;color:var(--amber);font-weight:600;">+1</span>' : '';

  document.getElementById('statusResult').innerHTML = `
    <div class="mock-notice">
      ⚠ Flight status shown is simulated demo data — not a live feed.
    </div>

    ${cancelledBanner}

    <div class="flight-header-card">
      <div class="flight-header-top">
        <div>
          <div class="flight-num">${escapeHtml(f.flight_number)}</div>
          <div class="airline-info">${escapeHtml(f.airline)} · ${escapeHtml(f.aircraft)}</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
          <span class="status-pill ${statusClass}">${statusIcon} ${f.status_label}</span>
          <div style="text-align:right;color:rgba(255,255,255,.7);font-size:12px;">${escapeHtml(f.date)}</div>
        </div>
      </div>

      <div class="flight-route">
        <div class="route-airport">
          <div class="route-code">${f.origin.code}</div>
          <div class="route-city">${f.origin.city}, ${f.origin.country}</div>
          <div class="route-airport-name">${f.origin.name}</div>
          <div class="route-times">
            <div class="route-sched">${f.scheduled_departure}</div>
            ${f.delay_minutes > 0 ? `<div class="route-actual ${depActualClass}">Actual: ${f.actual_departure}</div>` : ''}
            ${f.status === 'on_time' ? '<div class="route-actual" style="color:var(--green);">On Time</div>' : ''}
          </div>
        </div>

        <div class="flight-line-wrap">
          <svg width="160" height="24" viewBox="0 0 160 24" fill="none" class="flight-line-svg" style="display:block;margin:0 auto;">
            <line x1="0" y1="12" x2="68" y2="12" stroke="#e5e7eb" stroke-width="2"/>
            <text x="80" y="17" text-anchor="middle" font-size="18" fill="#407E3C">✈</text>
            <line x1="92" y1="12" x2="160" y2="12" stroke="#e5e7eb" stroke-width="2"/>
          </svg>
          <div class="duration-label">${f.duration_hours}h · ${f.distance_km.toLocaleString()} km</div>
          <div class="nonstop-label">Nonstop</div>
        </div>

        <div class="route-airport route-dest">
          <div class="route-code">${f.destination.code}</div>
          <div class="route-city">${f.destination.city}, ${f.destination.country}</div>
          <div class="route-airport-name">${f.destination.name}</div>
          <div class="route-times">
            <div class="route-sched">${f.scheduled_arrival}${nextDayNote}</div>
            ${f.delay_minutes > 0 ? `<div class="route-actual ${depActualClass}">Est: ${f.estimated_arrival}${nextDayNote}</div>` : ''}
          </div>
        </div>
      </div>

      <div class="info-grid">
        <div class="info-cell">
          <div class="info-label">Terminal</div>
          <div class="info-value highlight">${f.terminal}</div>
        </div>
        <div class="info-cell">
          <div class="info-label">Gate</div>
          <div class="info-value highlight">${f.status === 'cancelled' ? '—' : f.gate}</div>
        </div>
        <div class="info-cell">
          <div class="info-label">Aircraft</div>
          <div class="info-value">${f.aircraft}</div>
        </div>
        <div class="info-cell">
          <div class="info-label">${f.status === 'arrived' ? 'Baggage Belt' : 'Delay'}</div>
          <div class="info-value ${f.delay_minutes > 0 ? '' : 'highlight'}">
            ${f.status === 'arrived' && f.baggage_belt ? `Belt ${f.baggage_belt}` : f.delay_minutes > 0 ? `+${f.delay_minutes} min` : f.status === 'cancelled' ? '—' : 'None'}
          </div>
        </div>
      </div>
    </div>

    ${f.status !== 'cancelled' ? `
    <div class="progress-card">
      <div class="progress-title">Flight Progress</div>
      <div class="progress-steps">${stepHTML}</div>
    </div>` : ''}

    <div style="margin-top:16px;display:flex;gap:10px;flex-wrap:wrap;">
      <a href="/" class="btn btn-secondary btn-sm">← Search Flights</a>
      <button class="btn btn-secondary btn-sm" data-click="lookupFlight">↻ Refresh</button>
      <button class="btn btn-secondary btn-sm" data-click="shareStatus">Share</button>
    </div>
  `;
}

function shareStatus() {
  const fn = document.getElementById('flightInput').value.trim().toUpperCase();
  const date = document.getElementById('dateInput').value;
  const url = `${location.origin}/flight-status.html?flight=${fn}&date=${date}`;
  if (navigator.share) {
    navigator.share({ title: `${fn} Status`, url });
  } else {
    navigator.clipboard.writeText(url).then(() => alert('Link copied!'));
  }
}

// Navbar mobile
document.getElementById('menuBtn').addEventListener('click', () => {
  document.getElementById('navLinks').classList.toggle('mobile-open');
});
document.getElementById('logoutBtn')?.addEventListener('click', e => {
  e.preventDefault();
  localStorage.removeItem('af_token');
  localStorage.removeItem('af_user');
  location.href = '/';
});

Actions.register({ fillExample, lookupFlight, shareStatus });
