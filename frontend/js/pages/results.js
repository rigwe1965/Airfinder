const params = new URLSearchParams(window.location.search);
const origin = params.get('origin') || '';
const destination = params.get('destination') || '';
const departure_date = params.get('departure_date') || '';
const passengers = params.get('passengers') || '1';
const cabin = params.get('cabin') || 'economy';
const return_date = params.get('return_date') || '';
const ai_query = params.get('ai_query') || '';

let _autoRefreshTimer = null;
let _countdownInterval = null;
const AUTO_REFRESH_SECS = 300;

function _setFetchedAt() {
  const now = new Date();
  const hhmm = now.toUTCString().slice(17, 22) + ' UTC';
  document.getElementById('prices-fetched-at').textContent = hhmm;
  document.getElementById('prices-meta').style.display = '';
  _startCountdown();
}

function _startCountdown() {
  if (_countdownInterval) clearInterval(_countdownInterval);
  if (_autoRefreshTimer) clearTimeout(_autoRefreshTimer);
  let secs = AUTO_REFRESH_SECS;
  const el = document.getElementById('refresh-countdown');
  el.textContent = `auto-refresh in ${secs}s`;
  _countdownInterval = setInterval(() => {
    secs--;
    if (secs <= 0) {
      clearInterval(_countdownInterval);
      el.textContent = 'refreshing…';
    } else {
      el.textContent = `auto-refresh in ${secs}s`;
    }
  }, 1000);
  _autoRefreshTimer = setTimeout(() => refreshResults(true), AUTO_REFRESH_SECS * 1000);
}

async function loadResults() {
  const btn = document.getElementById('refresh-results-btn');
  if (btn) btn.disabled = true;
  document.getElementById('results-container').innerHTML = `
    <div style="text-align:center;padding:60px 20px;">
      <div class="spinner"></div>
      <p class="text-gray mt-2">Finding the best flights...</p>
    </div>`;
  document.getElementById('results-count').textContent = 'Searching...';
  try {
    const data = await Search.searchFlights({ origin, destination, departure_date, passengers, cabin, return_date });
    Search.results = data.results || [];
    populateAirlineFilter(Search.results);
    setPriceFilterMax(Search.results);
    applyFilters();
    _setFetchedAt();
  } catch (e) {
    document.getElementById('results-container').innerHTML = `
      <div class="no-results">
        <h3>No flights found</h3>
        <p class="text-gray mt-1">Try different dates or a different route.</p>
        <a href="/" class="btn btn-primary mt-3">New Search</a>
      </div>`;
    document.getElementById('results-count').textContent = 'No results';
  }
  if (btn) btn.disabled = false;
}

function refreshResults(auto = false) {
  loadResults();
}

document.addEventListener('DOMContentLoaded', async () => {
  document.getElementById('sr-origin').value = origin;
  document.getElementById('sr-destination').value = destination;
  document.getElementById('sr-date').value = departure_date;

  // Sync passengers/cabin dropdown to current search params
  const paxCabinVal = `${passengers}|${cabin}`;
  const paxSelect = document.getElementById('sr-passengers');
  const matchOpt = Array.from(paxSelect.options).find(o => o.value === paxCabinVal);
  if (matchOpt) matchOpt.selected = true;

  if (ai_query) {
    const info = document.getElementById('ai-query-info');
    info.classList.remove('hidden');
    info.textContent = `AI interpreted: "${ai_query}" → ${origin} → ${destination}`;
  }

  await loadResults();

  document.getElementById('sort-select').addEventListener('change', applyFilters);
  document.querySelectorAll('.filter-stops, .filter-ota').forEach(el => el.addEventListener('change', applyFilters));
  document.querySelectorAll('.filter-deptime').forEach(el => el.addEventListener('change', applyFilters));

  document.getElementById('price-filter').addEventListener('input', function() {
    document.getElementById('price-label').textContent = `€${this.value}`;
    applyFilters();
  });

  document.getElementById('duration-filter').addEventListener('input', function() {
    const v = parseInt(this.value);
    document.getElementById('duration-label').textContent = v >= 24 ? 'Any' : `${v}h`;
    applyFilters();
  });

  document.getElementById('clear-filters').addEventListener('click', clearFilters);

  document.getElementById('sr-search-btn').addEventListener('click', () => {
    const o = document.getElementById('sr-origin').value.trim().toUpperCase().slice(0,3);
    const d = document.getElementById('sr-destination').value.trim().toUpperCase().slice(0,3);
    const dt = document.getElementById('sr-date').value;
    const [pax, cb] = document.getElementById('sr-passengers').value.split('|');
    window.location.href = `/results.html?origin=${o}&destination=${d}&departure_date=${dt}&passengers=${pax}&cabin=${cb}`;
  });

  // Flexible date grid toggle
  let flexLoaded = false;
  document.getElementById('flex-date-btn').addEventListener('click', async () => {
    const grid = document.getElementById('flex-date-grid');
    const btn = document.getElementById('flex-date-btn');
    if (grid.style.display === 'flex') {
      grid.style.display = 'none';
      btn.textContent = '📅 Show nearby date prices (±3 days)';
      return;
    }
    if (!flexLoaded && origin && destination && departure_date) {
      btn.textContent = 'Loading...';
      btn.disabled = true;
      try {
        const qs = new URLSearchParams({ origin, destination, date: departure_date, passengers, cabin });
        const data = await api.get(`/flights/search/flexible?${qs}`);
        grid.innerHTML = data.grid.map(g => {
          const isTarget = g.is_target;
          const isCheap = g.is_cheapest;
          const price = g.price != null ? fmtCurrency(g.price) : '—';
          const bg = isCheap ? 'background:var(--green);color:#fff;' : isTarget ? 'background:#f0fdf4;border:2px solid var(--green);' : 'background:#f9fafb;border:1px solid #e5e7eb;';
          return `<div ${Actions.attr('navigate', [`/results.html?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&departure_date=${encodeURIComponent(g.date)}&passengers=${encodeURIComponent(passengers)}&cabin=${encodeURIComponent(cabin)}`])}
            style="cursor:pointer;border-radius:10px;padding:10px 14px;text-align:center;min-width:80px;${bg}">
            <div style="font-size:11px;font-weight:600;opacity:.7;">${g.day}</div>
            <div style="font-size:12px;">${g.date.slice(5)}</div>
            <div style="font-size:14px;font-weight:700;margin-top:4px;">${price}</div>
            ${isCheap ? '<div style="font-size:10px;font-weight:700;margin-top:2px;">CHEAPEST</div>' : ''}
          </div>`;
        }).join('');
        flexLoaded = true;
      } catch (e) {
        grid.innerHTML = '<span style="font-size:13px;color:var(--gray-400);">Could not load date grid.</span>';
      }
      btn.disabled = false;
    }
    grid.style.display = 'flex';
    btn.textContent = '📅 Hide nearby date prices';
  });
});

function populateAirlineFilter(results) {
  const airlines = [...new Set(results.map(f => f.airline))].sort();
  if (airlines.length < 2) { document.getElementById('airline-filter-group').style.display = 'none'; return; }
  const container = document.getElementById('airline-checkboxes');
  container.innerHTML = airlines.map(a =>
    `<label class="filter-option"><input type="checkbox" class="filter-airline" value="${a}" checked> ${a}</label>`
  ).join('');
  document.querySelectorAll('.filter-airline').forEach(el => el.addEventListener('change', applyFilters));
  document.getElementById('airline-filter-group').style.display = '';
}

function setPriceFilterMax(results) {
  if (!results.length) return;
  const maxPrice = Math.ceil(Math.max(...results.map(f => f.pricing.total)) / 50) * 50;
  const slider = document.getElementById('price-filter');
  slider.max = maxPrice;
  slider.value = maxPrice;
  document.getElementById('price-label').textContent = `€${maxPrice}`;
}

function depTimeSlot(timeStr) {
  const h = parseInt(timeStr.split(':')[0]);
  if (h >= 6 && h < 12) return 'morning';
  if (h >= 12 && h < 18) return 'afternoon';
  if (h >= 18) return 'evening';
  return 'night';
}

function applyFilters() {
  let results = [...Search.results];

  const allowedStops = Array.from(document.querySelectorAll('.filter-stops:checked')).map(el => parseInt(el.value));
  results = results.filter(f => allowedStops.includes(Math.min(f.stops, 2)));

  const maxPrice = parseFloat(document.getElementById('price-filter').value);
  results = results.filter(f => f.pricing.total <= maxPrice);

  const allowedTimes = Array.from(document.querySelectorAll('.filter-deptime:checked')).map(el => el.value);
  if (allowedTimes.length < 4) {
    results = results.filter(f => allowedTimes.includes(depTimeSlot(f.departure_time)));
  }

  const maxDur = parseInt(document.getElementById('duration-filter').value);
  if (maxDur < 24) {
    results = results.filter(f => f.duration_hours <= maxDur);
  }

  const airlineBoxes = document.querySelectorAll('.filter-airline');
  if (airlineBoxes.length > 0) {
    const allowedAirlines = Array.from(document.querySelectorAll('.filter-airline:checked')).map(el => el.value);
    results = results.filter(f => allowedAirlines.includes(f.airline));
  }

  const sort = document.getElementById('sort-select').value;
  if (sort === 'price') results.sort((a, b) => a.pricing.total - b.pricing.total);
  if (sort === 'duration') results.sort((a, b) => a.duration_hours - b.duration_hours);
  if (sort === 'stops') results.sort((a, b) => a.stops - b.stops);
  if (sort === 'trust') results.sort((a, b) => b.airline_trust_score - a.airline_trust_score);
  if (sort === 'co2') results.sort((a, b) => (a.co2_kg_per_pax || 9999) - (b.co2_kg_per_pax || 9999));

  Search.filteredResults = results;
  renderResults(results);
}

function renderResults(results) {
  const count = results.length;
  document.getElementById('results-count').textContent =
    count > 0 ? `${count} flight${count !== 1 ? 's' : ''} found — ${origin} → ${destination}` : 'No flights match your filters';

  if (count === 0) {
    document.getElementById('results-container').innerHTML = `
      <div class="no-results">
        <h3>No flights match your filters</h3>
        <p class="text-gray mt-1">Try relaxing your filters.</p>
      </div>`;
    return;
  }

  document.getElementById('results-container').innerHTML = results.map(f => Search.renderFlightCard(f)).join('');
}

function clearFilters() {
  document.querySelectorAll('.filter-stops, .filter-deptime, .filter-airline').forEach(el => el.checked = true);
  setPriceFilterMax(Search.results);
  document.getElementById('duration-filter').value = 24;
  document.getElementById('duration-label').textContent = 'Any';
  applyFilters();
}

Actions.register({ refreshResults });
