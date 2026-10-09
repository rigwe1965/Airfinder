document.addEventListener('DOMContentLoaded', async () => {
  // Set default date (2 weeks from now)
  const d = new Date(); d.setDate(d.getDate() + 14);
  document.getElementById('departure_date').value = d.toISOString().split('T')[0];
  document.getElementById('departure_date').min = new Date().toISOString().split('T')[0];

  // Load airports datalist
  try {
    const airports = await Search.loadAirports();
    const dl = document.getElementById('airports-list');
    airports.forEach(a => {
      const opt = document.createElement('option');
      opt.value = `${a.city} (${a.code})`;
      dl.appendChild(opt);
    });
  } catch {}

  // Load featured routes
  loadFeaturedRoutes(false);

  // Tabs
  document.querySelectorAll('.search-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.search-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const t = tab.dataset.tab;
      document.getElementById('return-date-row').classList.toggle('hidden', t !== 'roundtrip');
      document.getElementById('panel-simple').classList.toggle('hidden', t === 'multicity');
      document.getElementById('panel-multicity').classList.toggle('hidden', t !== 'multicity');
    });
  });

  // Multi-city leg builder
  initMultiCity();

  // Manual search
  document.getElementById('searchBtn').addEventListener('click', doSearch);

  // AI search
  document.getElementById('aiSearchBtn').addEventListener('click', doAiSearch);
  document.getElementById('aiInput').addEventListener('keydown', e => { if (e.key === 'Enter') doAiSearch(); });
});

async function loadFeaturedRoutes(forceRefresh) {
  const grid = document.getElementById('featuredGrid');
  const subtitle = document.getElementById('featuredSubtitle');
  const btn = document.getElementById('refreshRoutesBtn');
  grid.innerHTML = '<div class="spinner" style="margin:20px auto;"></div>';
  if (btn) btn.disabled = true;
  try {
    const data = await Search.loadFeatured(forceRefresh);
    const routes = data.routes || [];
    if (!routes.length) throw new Error('empty');
    grid.innerHTML = routes.map(r => Search.renderFeaturedRoute(r)).join('');
    if (subtitle && data.fetched_at) {
      subtitle.textContent = `Top picks for African travelers — prices as of ${data.fetched_at} · departing ${data.search_date}`;
    }
  } catch {
    grid.innerHTML = '<p class="text-gray">Could not load featured routes.</p>';
    if (subtitle) subtitle.textContent = 'Top picks for African travelers';
  } finally {
    if (btn) btn.disabled = false;
  }
}

function extractIATA(str) {
  const m = str.match(/\(([A-Z]{3})\)/);
  return m ? m[1] : str.toUpperCase().slice(0, 3);
}

function doSearch() {
  const origin = extractIATA(document.getElementById('origin').value.trim());
  const destination = extractIATA(document.getElementById('destination').value.trim());
  const departure_date = document.getElementById('departure_date').value;
  const pc = document.getElementById('passengers_cabin').value.split('|');
  const return_date = document.getElementById('return_date').value;

  if (!origin || !destination || !departure_date) {
    alert('Please fill in From, To, and Date.');
    return;
  }

  const params = new URLSearchParams({ origin, destination, departure_date, passengers: pc[0], cabin: pc[1] });
  if (return_date) params.set('return_date', return_date);
  window.location.href = `/results.html?${params}`;
}

// ===== MULTI-CITY =====
let mcLegCount = 0;

function initMultiCity() {
  addMcLeg(); // start with 2 legs
  addMcLeg();
  document.getElementById('mc-add-leg-btn').addEventListener('click', () => {
    if (mcLegCount < 6) addMcLeg();
    else alert('Maximum 6 legs allowed.');
  });
  document.getElementById('mc-search-btn').addEventListener('click', doMultiCitySearch);
}

function addMcLeg() {
  mcLegCount++;
  const idx = mcLegCount;
  const today = new Date();
  today.setDate(today.getDate() + 14 + (idx - 1) * 3);
  const defaultDate = today.toISOString().split('T')[0];
  const min = new Date().toISOString().split('T')[0];

  const div = document.createElement('div');
  div.className = 'mc-leg';
  div.dataset.leg = idx;
  div.innerHTML = `
    <div class="mc-leg-num" style="grid-column:1/-1;">Leg ${idx}</div>
    <div class="search-field">
      <div class="search-field-label">From</div>
      <input class="form-control mc-origin" data-leg="${idx}" placeholder="City or IATA" list="airports-list">
    </div>
    <div class="mc-arrow">→</div>
    <div class="search-field">
      <div class="search-field-label">To</div>
      <input class="form-control mc-dest" data-leg="${idx}" placeholder="City or IATA" list="airports-list">
    </div>
    <div class="search-field">
      <div class="search-field-label">Date</div>
      <input class="form-control mc-date" data-leg="${idx}" type="date" value="${defaultDate}" min="${min}">
    </div>
    ${idx > 2 ? `<button class="mc-remove" ${Actions.attr('removeMcLeg', ['$el'])} title="Remove leg">✕</button>` : '<div></div>'}
  `;
  document.getElementById('mc-legs-container').appendChild(div);
}

function removeMcLeg(btn) {
  btn.closest('.mc-leg').remove();
  mcLegCount--;
  // Re-number remaining legs
  document.querySelectorAll('.mc-leg').forEach((el, i) => {
    el.querySelector('.mc-leg-num').textContent = `Leg ${i + 1}`;
    el.dataset.leg = i + 1;
  });
}

function doMultiCitySearch() {
  const legs = [];
  let valid = true;
  document.querySelectorAll('.mc-leg').forEach((legEl, i) => {
    const origin = extractIATA(legEl.querySelector('.mc-origin').value.trim());
    const destination = extractIATA(legEl.querySelector('.mc-dest').value.trim());
    const date = legEl.querySelector('.mc-date').value;
    if (!origin || !destination || !date) { valid = false; }
    legs.push({ origin, destination, date });
  });

  if (!valid || legs.length < 2) {
    alert('Please fill in From, To, and Date for all legs.');
    return;
  }

  const pc = document.getElementById('mc-passengers-cabin').value.split('|');
  sessionStorage.setItem('af_mc_legs', JSON.stringify(legs));
  sessionStorage.setItem('af_mc_pax', JSON.stringify({ passengers: pc[0], cabin: pc[1] }));
  window.location.href = '/multicity.html';
}

async function submitDemoRequest(e) {
  e.preventDefault();
  const btn = document.getElementById('demo-submit-btn');
  btn.textContent = 'Sending...'; btn.disabled = true;
  const payload = {
    name: document.getElementById('demo-name').value,
    company: document.getElementById('demo-company').value,
    email: document.getElementById('demo-email').value,
    phone: document.getElementById('demo-phone').value,
    message: document.getElementById('demo-message').value,
  };
  try {
    await api.post('/demo-request', payload);
  } catch {}
  document.getElementById('demo-form-wrap').innerHTML = `
    <div style="text-align:center;padding:20px 0;">
      <div style="width:56px;height:56px;background:#e8f5e4;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#407E3C" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      </div>
      <h4 style="color:#407E3C;margin-bottom:8px;">Request Received!</h4>
      <p class="text-sm text-gray">Thanks, <strong>${escapeHtml(payload.name.split(' ')[0])}</strong>. We'll reach out to <strong>${escapeHtml(payload.email)}</strong> within 24 hours to schedule your demo.</p>
    </div>`;
}

async function doAiSearch() {
  const query = document.getElementById('aiInput').value.trim();
  if (!query) return;
  const btn = document.getElementById('aiSearchBtn');
  btn.textContent = '...'; btn.disabled = true;
  try {
    const data = await Search.aiSearch(query);
    if (data.parsed && data.parsed.origin && data.parsed.destination) {
      const p = data.parsed;
      const params = new URLSearchParams({
        origin: p.origin, destination: p.destination,
        departure_date: p.departure_date, passengers: p.passengers, cabin: p.cabin,
        ai_query: query,
      });
      window.location.href = `/results.html?${params}`;
    } else {
      alert("Couldn't parse that query. Try: 'flight from Lagos to London next month'");
    }
  } catch (e) {
    alert('Search failed. Please try again.');
  } finally {
    btn.textContent = 'Search'; btn.disabled = false;
  }
}

Actions.register({ loadFeaturedRoutes, removeMcLeg, submitDemoRequest });
