# Airfinder — Project Notes

## Stack
- Backend: Python + Flask (port 5000)
- DB: SQLite (airfinder.db) via SQLAlchemy
- Auth: JWT + bcrypt
- Frontend: Vanilla HTML/CSS/JS in /frontend/

## Run
```
python backend/app.py
```

## Default Credentials
- Super Admin: set via SUPER_ADMIN_EMAIL / SUPER_ADMIN_PASSWORD env vars (required; app refuses to start without them; must change password on first login). See .env.example
- Staff accounts: created by admin, emailed temp password, must change on first login

## Key APIs
- POST /api/auth/register — customer signup
- POST /api/auth/login — customer login
- POST /api/staff/auth/login — staff login
- POST /api/staff/auth/change-password — force change (works even with must_change_password=True)
- GET /api/flights/search — flight search
- POST /api/flights/search/ai — NL query search
- POST /api/flights/search/multicity — multi-leg search
- POST /api/bookings — create booking (auth required)
- POST /api/bookings/multicity — multi-city booking (auth required)
- GET /api/flights/status?flight=XX&date=YYYY-MM-DD — flight status/tracking (mock, deterministic)
- GET /api/admin/dashboard — admin stats
- GET /api/admin/staff — staff list
- POST /api/admin/staff — create staff
- GET /api/admin/finance/summary — revenue data

## Roles
super_admin > admin > agent > finance > customer

## Revenue Config (.env)
DEFAULT_MARKUP_PERCENT=8
DEFAULT_SERVICE_FEE_USD=15
DEFAULT_COMMISSION_PERCENT=3

## Frontend Pages
- / (index.html) — search homepage
- /results.html — search results
- /booking.html — booking flow
- /confirmation.html — booking confirmed
- /multicity.html — multi-city results + booking
- /flight-status.html — flight tracking page (NEW)
- /auth/login.html, /auth/register.html, /auth/forgot-password.html
- /account/dashboard.html, /account/bookings.html, /account/profile.html
- /admin/* — staff portal

## Flight Status Page (/flight-status.html)
- Params: flight number + date
- Deterministic mock: same flight+date always returns same status (hashlib.md5 seed)
- Shows: status pill, 4-step progress bar, terminal/gate/aircraft/delay info, share button
- 8 quick-lookup examples pre-loaded
- URL param support: ?flight=XX&date=YYYY-MM-DD

## Airport Database (backend/services/mock_flights.py)
- 191 airports with lat/lon coordinates across all regions
- Germany: FRA, MUC, DUS, BER, HAM, STR, CGN, NUE, HAJ, LEJ, DRS, BSL, FKB
- Nigeria: LOS, ABV, PHC, KAN, ENU
- Full coverage: West/East/Southern/North Africa, Middle East, UK, France, Benelux,
  Switzerland, Austria, Spain, Portugal, Italy, Scandinavia, Eastern Europe, Greece,
  Americas (27), Asia (28), Oceania (6)
- Haversine formula for accurate flight durations (not hardcoded lookup table)
- lru_cache on _estimate_duration for performance

## Airline Routing Logic
- 50 airlines across 6 regions, each with `longhaul: bool` flag
- `_eligible_airlines(origin_region, dest_region)`: builds pool per route
  - Same region: only carriers from that region
  - Cross-region: longhaul carriers from both regions + all Middle East carriers
  - Fallback: add any longhaul airline if pool < 4
- `AIRPORT_CARRIERS` whitelist: secondary/regional airports get only airlines that
  actually serve them. Examples:
  - PHC: Air Peace, Arik Air, IbomAir, Ethiopian, Kenya Airways, RwandAir
  - KAN, ENU: Nigerian domestic carriers only
  - STR/CGN/NUE/HAJ/LEJ/DRS: Lufthansa/Eurowings/LCCs only (no longhaul)
  - West Africa regional (DLA, LFW, COO, OUA, BKO, CKY): Air France, Royal Air Maroc,
    ASKY, Ethiopian only
- `_apply_airport_restrictions(pool, origin, destination)` enforces whitelist after
  regional eligibility filtering

## Navbar — All Pages
Every page has Flight Status link in navbar. Auth-aware: data-auth-login / data-auth-logout
attributes + hidden CSS class handled by auth.js.

## Currency
All prices display in EUR (locale.js handles USD→EUR conversion client-side).

## Frontend Security Conventions (CSP)
The server sends `script-src 'self'` — **no inline `<script>` blocks, no `onclick=`/`onchange=`/`onsubmit=`
attributes, no `javascript:` URLs** (a test fails if any appear).
- Page logic lives in `/js/pages/<page>.js`; every page loads `/js/csp-actions.js` first.
- Wire events with `data-click="fn" data-args='["a",1]'` (also `data-change`, `data-submit`).
  In JS templates use `${Actions.attr('fn', [id, value])}`. Arg tokens: `'$el'`, `'$event'`, `'$value'`.
- A function is callable from markup only if registered: `Actions.register({ fn })` at the end of its script.
- Built-ins: `unhide(id)`, `hide(id)`, `closeOnBackdrop`, `navigate(path)`, `goBack`.
- Always wrap user-derived values in `escapeHtml()` before putting them in `innerHTML`.
