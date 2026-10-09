let mcLegs = [];       // raw leg params [{origin,destination,date}]
let mcPax = {};        // {passengers, cabin}
let legResults = [];   // [{leg_num, origin, destination, date, flights:[]}]
let selections = {};   // {legNum: flight}

document.addEventListener('DOMContentLoaded', async () => {
  const rawLegs = sessionStorage.getItem('af_mc_legs');
  const rawPax = sessionStorage.getItem('af_mc_pax');
  if (!rawLegs || !rawPax) { window.location.href = '/'; return; }

  mcLegs = JSON.parse(rawLegs);
  mcPax = JSON.parse(rawPax);

  // Render itinerary header
  const itinParts = mcLegs.map((l, i) => {
    const arrow = i < mcLegs.length - 1 ? '<span class="mc-itinerary-arrow">→</span>' : '';
    return `<strong>${l.origin}</strong>${arrow}`;
  });
  itinParts.push(`<strong>${mcLegs[mcLegs.length - 1].destination}</strong>`);
  document.getElementById('mc-itinerary-bar').innerHTML = '✈ ' + itinParts.join(' ');

  // Show total bar placeholder
  document.getElementById('mc-total-bar').classList.remove('hidden');
  updateTotalBar();

  // Search all legs
  try {
    const data = await api.post('/flights/search/multicity', {
      legs: mcLegs,
      passengers: parseInt(mcPax.passengers),
      cabin: mcPax.cabin,
    });
    legResults = data.legs;
    renderLegPanels();
  } catch (e) {
    document.getElementById('mc-panels').innerHTML = `
      <div class="no-results">
        
        <h3>Search failed</h3>
        <p class="text-gray mt-1">${escapeHtml(e.message || 'Could not search flights. Please try again.')}</p>
        <a href="/" class="btn btn-primary mt-3">← New Search</a>
      </div>`;
  }
});

function renderLegPanels() {
  if (!legResults.length) {
    document.getElementById('mc-panels').innerHTML = '<p class="text-gray">No results.</p>';
    return;
  }

  document.getElementById('mc-panels').innerHTML = legResults.map(leg => `
    <div class="mc-leg-panel" id="leg-panel-${leg.leg_num}">
      <div class="mc-leg-panel-header">
        <div>
          <div class="mc-leg-label">Leg ${leg.leg_num} of ${legResults.length}</div>
          <div class="mc-leg-route">${leg.origin} → ${leg.destination} &nbsp;·&nbsp; ${leg.date} &nbsp;·&nbsp; ${leg.flights.length} option${leg.flights.length !== 1 ? 's' : ''}</div>
        </div>
        <div id="leg-badge-${leg.leg_num}"></div>
      </div>
      <div class="mc-leg-flights" id="leg-flights-${leg.leg_num}">
        ${leg.flights.length === 0
          ? '<p class="text-gray" style="padding:12px;">No flights found for this leg. Try different dates.</p>'
          : leg.flights.map(f => renderMcFlightCard(f, leg.leg_num)).join('')
        }
      </div>
    </div>
  `).join('');
}

function renderMcFlightCard(flight, legNum) {
  const p = flight.pricing;
  const isAfrica = flight.is_africa_route;
  return `
    <div class="flight-card ${isAfrica ? 'africa-direct' : ''}" id="mc-card-${legNum}-${flight.id}" style="margin-bottom:10px;">
      <div class="flight-card-header">
        <div class="flight-airline">
          <div class="airline-logo">${flight.airline_code}</div>
          <div>
            <div class="airline-name">${flight.airline}</div>
            <div class="airline-flight">${flight.flight_number}</div>
          </div>
        </div>
        <div style="flex:1;display:flex;align-items:center;justify-content:center;gap:16px;padding:0 16px;">
          <div class="flight-time">
            <div class="flight-time-val">${flight.departure_time}</div>
            <div class="flight-time-code">${flight.origin}</div>
          </div>
          <div class="flight-line">
            <div class="flight-line-track"><div class="line"></div><span class="plane-icon">✈</span><div class="line"></div></div>
            <div class="flight-duration">${Search.formatDuration(flight.duration_hours)}</div>
            <div class="flight-stops ${flight.stops === 0 ? 'nonstop' : ''}">${flight.stops_label}</div>
          </div>
          <div class="flight-time">
            <div class="flight-time-val">${flight.arrival_time}</div>
            <div class="flight-time-code">${flight.destination}</div>
          </div>
        </div>
        <div style="text-align:right;">
          ${isAfrica ? '<span class="africa-badge">✈ Direct</span>' : ''}
          <div class="text-sm text-gray">${flight.available_seats} seats</div>
        </div>
      </div>
      <div class="flight-card-pricing">
        <div class="true-cost">
          <div class="true-cost-label">Leg price — True Cost</div>
          <div class="true-cost-total">${fmtCurrency(p.total)}</div>
          <div class="true-cost-breakdown">
            <span class="cost-item">Base ${fmtCurrency(p.base_fare)}</span>
            <span class="cost-item">Markup ${fmtCurrency(p.markup)}</span>
            <span class="cost-item">Fee ${fmtCurrency(p.service_fee)}</span>
          </div>
        </div>
        <div class="flight-card-actions">
          <button class="mc-select-btn" id="mc-sel-${legNum}-${flight.id}"
            ${Actions.attr('selectLegFlight', [legNum, flight.id])}>
            Select This Flight
          </button>
        </div>
      </div>
    </div>`;
}

function selectLegFlight(legNum, flightId) {
  const leg = legResults.find(l => l.leg_num === legNum);
  const flight = leg.flights.find(f => f.id === flightId);
  selections[legNum] = flight;

  // Update button states for this leg
  leg.flights.forEach(f => {
    const btn = document.getElementById(`mc-sel-${legNum}-${f.id}`);
    if (btn) btn.classList.toggle('active', f.id === flightId);
  });

  // Mark panel as selected
  document.getElementById(`leg-panel-${legNum}`).classList.add('selected');
  document.getElementById(`leg-badge-${legNum}`).innerHTML =
    `<span class="mc-selected-badge">✓ Selected · ${fmtCurrency(flight.pricing.total)}</span>`;

  updateTotalBar();
}

function updateTotalBar() {
  const totalLegs = legResults.length || mcLegs.length;
  const selectedCount = Object.keys(selections).length;
  const combinedTotal = Object.values(selections).reduce((s, f) => s + f.pricing.total, 0);

  document.getElementById('mc-combined-total').textContent = fmtCurrency(combinedTotal);
  document.getElementById('mc-total-label').textContent =
    selectedCount === totalLegs
      ? `All ${totalLegs} legs selected — ready to book!`
      : `${selectedCount} of ${totalLegs} legs selected`;

  const allSelected = selectedCount === totalLegs && totalLegs > 0;
  document.getElementById('mc-book-btn').disabled = !allSelected;
}

function proceedToBooking() {
  const legs = legResults.map(leg => {
    const flight = selections[leg.leg_num];
    return {
      leg_num: leg.leg_num,
      flight_id: flight.id,
      origin: flight.origin,
      destination: flight.destination,
      date: leg.date,
      airline: flight.airline,
      flight_number: flight.flight_number,
      base_fare: flight.pricing.base_fare,
      quote: flight.quote,
      pricing: flight.pricing,
      departure_time: flight.departure_time,
      arrival_time: flight.arrival_time,
      cabin: mcPax.cabin,
    };
  });

  sessionStorage.setItem('af_mc_booking', JSON.stringify({
    legs,
    passengers: parseInt(mcPax.passengers),
    cabin: mcPax.cabin,
    combined_total: Object.values(selections).reduce((s, f) => s + f.pricing.total, 0),
  }));
  sessionStorage.removeItem('af_mc_legs');
  sessionStorage.removeItem('af_mc_pax');
  window.location.href = '/booking.html';
}

Actions.register({ proceedToBooking, selectLegFlight });
