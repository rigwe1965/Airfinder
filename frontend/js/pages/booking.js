let flight = null;
let passengerCount = 1;
let mcBooking = null;
let _priceTimer = null;
const PRICE_LOCK_SECS = 900; // 15 min

function startPriceLockCountdown(seatsLeft) {
  const bar = document.getElementById('price-validity-bar');
  const cdEl = document.getElementById('price-validity-countdown');
  const urgEl = document.getElementById('seat-urgency');
  bar.style.display = 'flex';
  if (seatsLeft && seatsLeft <= 5) {
    urgEl.textContent = `🔴 Only ${seatsLeft} seat${seatsLeft === 1 ? '' : 's'} left!`;
    urgEl.style.display = '';
  }
  let secs = PRICE_LOCK_SECS;
  function fmt(s) { return `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`; }
  cdEl.textContent = fmt(secs);
  _priceTimer = setInterval(() => {
    secs--;
    if (secs <= 0) {
      clearInterval(_priceTimer);
      bar.style.background = '#fee2e2';
      bar.style.borderColor = '#fca5a5';
      cdEl.textContent = 'EXPIRED';
      cdEl.style.color = '#dc2626';
      showAlert('Price lock expired. Please go back and re-select this flight to get a fresh price.', 'error');
      document.getElementById('complete-booking-btn').disabled = true;
    } else {
      cdEl.textContent = fmt(secs);
      if (secs <= 60) cdEl.style.color = '#dc2626';
    }
  }, 1000);
}

function checkStaleSession(storedAt) {
  if (!storedAt) return;
  const ageMin = (Date.now() - new Date(storedAt).getTime()) / 60000;
  if (ageMin > 20) {
    showAlert(`⚠ Flight data is ${Math.round(ageMin)} minutes old — price may have changed. <a href="#" ${Actions.attr('goBack', ['$event'])} style="color:inherit;font-weight:700;text-decoration:underline;">Go back to refresh</a>`, 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (!Auth.requireLogin()) return;

  // Multi-city mode
  const rawMc = sessionStorage.getItem('af_mc_booking');
  if (rawMc) {
    mcBooking = JSON.parse(rawMc);
    passengerCount = mcBooking.passengers || 1;
    renderMcFlightSummary();
    renderPassengerForms();
    renderMcPriceSummary();
    startPriceLockCountdown(null);
    document.getElementById('next-to-addons').addEventListener('click', validatePassengers);
    document.getElementById('next-to-payment').addEventListener('click', () => goToStep(3));
    document.getElementById('complete-booking-btn').addEventListener('click', completeMcBooking);
    document.querySelectorAll('input[name=baggage], input[name=seat]').forEach(el => {
      el.addEventListener('change', renderMcPriceSummary);
    });
    return;
  }

  const raw = sessionStorage.getItem('af_flight');
  if (!raw) { window.location.href = '/'; return; }
  flight = JSON.parse(raw);
  passengerCount = flight.passengers || 1;

  checkStaleSession(sessionStorage.getItem('af_flight_saved_at'));
  startPriceLockCountdown(flight.available_seats);

  renderFlightSummary();
  renderPassengerForms();
  updatePriceSummary();

  // Add-on change listeners
  document.querySelectorAll('input[name=baggage], input[name=seat]').forEach(el => {
    el.addEventListener('change', updatePriceSummary);
  });

  document.getElementById('next-to-addons').addEventListener('click', validatePassengers);
  document.getElementById('next-to-payment').addEventListener('click', () => goToStep(3));
  document.getElementById('complete-booking-btn').addEventListener('click', completeBooking);

  // Card formatting
  document.getElementById('card-number').addEventListener('input', function() {
    this.value = this.value.replace(/\D/g, '').replace(/(\d{4})/g, '$1 ').trim().slice(0, 19);
  });
  document.getElementById('card-expiry').addEventListener('input', function() {
    this.value = this.value.replace(/\D/g, '').replace(/(\d{2})(\d)/, '$1/$2').slice(0, 5);
  });
});

function renderFlightSummary() {
  const p = flight.pricing;
  document.getElementById('flight-summary').innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
      <div>
        <div style="font-size:1.2rem;font-weight:800;">${escapeHtml(flight.origin)} → ${escapeHtml(flight.destination)}</div>
        <div class="text-gray text-sm">${escapeHtml(flight.airline)} · ${escapeHtml(flight.flight_number)} · ${escapeHtml(flight.departure_date)}</div>
        <div class="text-gray text-sm">${flight.departure_time} → ${flight.arrival_time} · ${flight.cabin}</div>
        ${flight.is_africa_route ? '<span class="badge badge-green mt-1">✈ Direct</span>' : ''}
      </div>
      <div style="text-align:right;">
        <div style="font-size:1.4rem;font-weight:900;color:var(--green);">${fmtCurrency(p.total)}</div>
        <div class="text-gray text-sm">for ${passengerCount} passenger${passengerCount>1?'s':''}</div>
      </div>
    </div>`;
}

function renderPassengerForms() {
  const container = document.getElementById('passengers-container');
  container.innerHTML = '';
  for (let i = 0; i < passengerCount; i++) {
    container.innerHTML += `
      <div class="passenger-block">
        <div class="passenger-title">Passenger ${i+1}${i === 0 ? ' (Primary)' : ''}</div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">First Name</label>
            <input class="form-control pax-first" data-pax="${i}" placeholder="John" required>
          </div>
          <div class="form-group">
            <label class="form-label">Last Name</label>
            <input class="form-control pax-last" data-pax="${i}" placeholder="Doe" required>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Date of Birth</label>
            <input class="form-control pax-dob" data-pax="${i}" type="date" required>
          </div>
          <div class="form-group">
            <label class="form-label">Passport Number</label>
            <input class="form-control pax-passport" data-pax="${i}" placeholder="A1234567" required>
          </div>
        </div>
        ${i === 0 ? `
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Email</label>
            <input class="form-control pax-email" data-pax="0" type="email" placeholder="john@example.com">
          </div>
          <div class="form-group">
            <label class="form-label">Phone</label>
            <input class="form-control pax-phone" data-pax="0" placeholder="+234 800 000 0000">
          </div>
        </div>` : ''}
      </div>`;
  }
}

function validatePassengers() {
  const firsts = document.querySelectorAll('.pax-first');
  const lasts = document.querySelectorAll('.pax-last');
  for (let i = 0; i < passengerCount; i++) {
    if (!firsts[i].value.trim() || !lasts[i].value.trim()) {
      showAlert('Please fill in all passenger names.', 'error'); return;
    }
  }
  goToStep(2);
}

function goToStep(n) {
  [1,2,3].forEach(i => {
    document.getElementById(`step-panel-${i}`).classList.toggle('hidden', i !== n);
    const stepEl = document.getElementById(`step-${i}`);
    stepEl.classList.toggle('active', i === n);
    stepEl.classList.toggle('done', i < n);
  });
  updatePriceSummary();
  window.scrollTo(0, 0);
}

function getAddons() {
  const baggage = document.querySelector('input[name=baggage]:checked')?.value || 'carry_on';
  const seat = document.querySelector('input[name=seat]:checked')?.value || 'standard';
  return { baggage, seat };
}

async function updatePriceSummary() {
  if (!flight) return; // multi-city bookings render their own summary
  const { baggage, seat } = getAddons();
  try {
    const pricing = await api.post('/flights/pricing/calculate', {
      base_fare: flight.pricing.base_fare,
      passengers: passengerCount,
      baggage, seat,
    });
    renderPriceBreakdown(pricing);
  } catch {
    renderPriceBreakdown(flight.pricing);
  }
}

function renderPriceBreakdown(p) {
  document.getElementById('price-breakdown').innerHTML = `
    <div class="price-line"><span>Base fare (×${p.passengers || passengerCount})</span><span>${fmtCurrency(p.base_fare * (p.passengers || passengerCount))}</span></div>
    <div class="price-line"><span>Markup (${p.markup_pct || 8}%)</span><span>${fmtCurrency(p.markup * (p.passengers || passengerCount))}</span></div>
    <div class="price-line"><span>Service fee</span><span>${fmtCurrency(p.service_fee)}</span></div>
    ${p.baggage_fee > 0 ? `<div class="price-line"><span>Baggage</span><span>${fmtCurrency(p.baggage_fee)}</span></div>` : ''}
    ${p.seat_fee > 0 ? `<div class="price-line"><span>Seat selection</span><span>${fmtCurrency(p.seat_fee)}</span></div>` : ''}
    <div class="price-line total"><span>Total</span><span style="color:var(--green);">${fmtCurrency(p.total)}</span></div>
    <div class="text-xs text-gray" style="margin-top:8px;">We earn: commission ${p.commission ? fmtCurrency(p.commission) : '—'} + service fee ${fmtCurrency(p.service_fee)}</div>`;
}

function getPassengers() {
  const passengers = [];
  document.querySelectorAll('.pax-first').forEach((el, i) => {
    passengers.push({
      first_name: el.value.trim(),
      last_name: document.querySelectorAll('.pax-last')[i].value.trim(),
      dob: document.querySelectorAll('.pax-dob')[i].value,
      passport: document.querySelectorAll('.pax-passport')[i].value.trim(),
    });
  });
  return passengers;
}

async function completeBooking() {
  const btn = document.getElementById('complete-booking-btn');
  btn.disabled = true; btn.textContent = 'Processing...';

  const { baggage, seat } = getAddons();
  const pricingRes = await api.post('/flights/pricing/calculate', {
    base_fare: flight.pricing.base_fare, passengers: passengerCount, baggage, seat,
  });

  try {
    const result = await api.post('/bookings', {
      flight_id: flight.id,
      origin: flight.origin,
      destination: flight.destination,
      departure_date: flight.departure_date,
      airline: flight.airline,
      flight_number: flight.flight_number,
      cabin: flight.cabin,
      base_fare: flight.pricing.base_fare,
      quote: flight.quote,
      passengers: getPassengers(),
      baggage, seat,
    });
    sessionStorage.setItem('af_booking', JSON.stringify(result.booking));
    sessionStorage.removeItem('af_flight');
    window.location.href = '/confirmation.html';
  } catch (e) {
    showAlert(e.message || 'Booking failed. Please try again.', 'error');
    btn.disabled = false; btn.textContent = 'Complete Booking';
  }
}

function showAlert(msg, type = 'error') {
  document.getElementById('alert-container').innerHTML =
    `<div class="alert alert-${type}">${msg}</div>`;
  window.scrollTo(0, 0);
}

// ===== MULTI-CITY FUNCTIONS =====
function renderMcFlightSummary() {
  const legs = mcBooking.legs;
  const route = legs.map((l, i) => `${l.origin}${i === legs.length - 1 ? ' → ' + l.destination : ''}`).join(' → ');
  document.getElementById('flight-summary').innerHTML = `
    <div style="margin-bottom:8px;">
      <span class="badge badge-blue">✈ Multi-city · ${legs.length} Legs</span>
    </div>
    ${legs.map((leg, i) => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;${i < legs.length - 1 ? 'border-bottom:1px solid var(--gray-100);' : ''}">
        <div>
          <div style="font-weight:700;">Leg ${i+1}: ${escapeHtml(leg.origin)} → ${escapeHtml(leg.destination)}</div>
          <div class="text-gray text-sm">${escapeHtml(leg.airline)} · ${escapeHtml(leg.flight_number)} · ${escapeHtml(leg.date)}</div>
          <div class="text-gray text-sm">${leg.departure_time} → ${leg.arrival_time} · ${leg.cabin}</div>
        </div>
        <div style="font-weight:700;color:var(--green);">${fmtCurrency(leg.pricing.total)}</div>
      </div>`).join('')}
    <div style="display:flex;justify-content:space-between;margin-top:10px;font-size:1.1rem;font-weight:900;">
      <span>Combined Total</span>
      <span style="color:var(--green);">${fmtCurrency(mcBooking.combined_total)}</span>
    </div>`;
}

function renderMcPriceSummary() {
  const baggage = document.querySelector('input[name=baggage]:checked')?.value || 'carry_on';
  const seat = document.querySelector('input[name=seat]:checked')?.value || 'standard';
  const BAGGAGE = { carry_on: 0, checked_1: 35, checked_2: 60 };
  const SEAT = { standard: 0, window: 15, aisle: 10, extra_legroom: 45, front_row: 30 };
  const baggageFee = (BAGGAGE[baggage] || 0) * passengerCount * mcBooking.legs.length;
  const seatFee = (SEAT[seat] || 0) * passengerCount * mcBooking.legs.length;
  const addons = baggageFee + seatFee;
  const grandTotal = mcBooking.combined_total + addons;

  document.getElementById('price-breakdown').innerHTML = `
    ${mcBooking.legs.map((leg, i) => `
      <div class="price-line text-sm">
        <span>Leg ${i+1}: ${leg.origin}→${leg.destination}</span>
        <span>${fmtCurrency(leg.pricing.total)}</span>
      </div>`).join('')}
    <hr class="divider">
    <div class="price-line"><span>Subtotal (${mcBooking.legs.length} legs)</span><span>${fmtCurrency(mcBooking.combined_total)}</span></div>
    ${baggageFee > 0 ? `<div class="price-line"><span>Baggage (all legs)</span><span>${fmtCurrency(baggageFee)}</span></div>` : ''}
    ${seatFee > 0 ? `<div class="price-line"><span>Seat selection (all legs)</span><span>${fmtCurrency(seatFee)}</span></div>` : ''}
    <div class="price-line total"><span>Grand Total</span><span style="color:var(--green);">${fmtCurrency(grandTotal)}</span></div>`;
}

async function completeMcBooking() {
  const btn = document.getElementById('complete-booking-btn');
  btn.disabled = true; btn.textContent = 'Processing...';

  const baggage = document.querySelector('input[name=baggage]:checked')?.value || 'carry_on';
  const seat = document.querySelector('input[name=seat]:checked')?.value || 'standard';

  try {
    const result = await api.post('/bookings/multicity', {
      legs: mcBooking.legs,
      passengers: getPassengers(),
      baggage, seat,
      cabin: mcBooking.cabin,
    });
    sessionStorage.setItem('af_booking', JSON.stringify({
      ...result.bookings[0],
      is_multicity: true,
      group_reference: result.group_reference,
      total_legs: result.total_legs,
      combined_total_usd: result.combined_total_usd,
    }));
    sessionStorage.removeItem('af_mc_booking');
    window.location.href = '/confirmation.html';
  } catch (e) {
    showAlert(e.message || 'Booking failed. Please try again.', 'error');
    btn.disabled = false; btn.textContent = 'Complete Booking';
  }
}

Actions.register({ goToStep });
