import pytest
from backend.models.database import db
from backend.models.staff import Staff

BOOKING = {
    'flight_id': 'x', 'origin': 'LOS', 'destination': 'LHR', 'departure_date': '2026-12-01',
    'airline': 'Test Air', 'base_fare': 500, 'passengers': [{'first_name': 'A', 'last_name': 'B'}],
}


def _customer_token(client, email='sec@example.com', first='Sec'):
    r = client.post('/api/auth/register', json={
        'email': email, 'password': 'Passw0rd!', 'first_name': first, 'last_name': 'Tester'})
    return r, (r.get_json() or {}).get('token')


def test_staff_forgot_password_never_returns_link(client, app, monkeypatch):
    from backend.routes import auth_staff

    def boom(*a, **k):
        raise RuntimeError('smtp down')
    monkeypatch.setattr(auth_staff.mail, 'send', boom)
    with app.app_context():
        email = Staff.query.first().email
    r = client.post('/api/staff/auth/forgot-password', json={'email': email}, headers={'Host': 'evil.example'})
    assert r.status_code == 200
    assert 'reset_url' not in r.get_json()
    assert 'evil.example' not in r.get_data(as_text=True)


@pytest.mark.parametrize('fare', [-500, 0, 'nan', 'inf', 1e9, 'abc', None])
def test_booking_rejects_bad_fare(client, fare):
    _, token = _customer_token(client)
    r = client.post('/api/bookings', json={**BOOKING, 'base_fare': fare},
                    headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 400


def test_booking_rejects_bad_passengers(client):
    _, token = _customer_token(client)
    h = {'Authorization': f'Bearer {token}'}
    assert client.post('/api/bookings', json={**BOOKING, 'passengers': 'x' * 50}, headers=h).status_code == 400
    assert client.post('/api/bookings', json={**BOOKING, 'passengers': [{}] * 10}, headers=h).status_code == 400


def test_multicity_validates_legs(client):
    _, token = _customer_token(client)
    h = {'Authorization': f'Bearer {token}'}
    bad = {'legs': [{'base_fare': -5, 'flight_id': 'a', 'origin': 'LOS', 'destination': 'LHR', 'date': 'd', 'airline': 'x'}] * 2,
           'passengers': [{}]}
    assert client.post('/api/bookings/multicity', json=bad, headers=h).status_code == 400
    assert client.post('/api/bookings/multicity', json={'legs': [{}, {}], 'passengers': [{}]}, headers=h).status_code == 400


def test_register_rejects_html_names(client):
    r, _ = _customer_token(client, email='x@example.com', first='<img src=x onerror=alert(1)>')
    assert r.status_code == 400


def test_register_allows_apostrophe(client):
    r, _ = _customer_token(client, email='o@example.com', first="O'Brien")
    assert r.status_code == 201


def test_flight_status_rejects_markup(client):
    r = client.get('/api/flights/status?flight=<IMG SRC=X ONERROR=&#97;>')
    assert r.status_code == 400


def test_customer_reset_uses_configured_base_url(client, app, monkeypatch):
    from backend.routes import auth_customer
    sent = {}
    monkeypatch.setattr(auth_customer, 'send_password_reset_email', lambda to, name, link: sent.update(link=link))
    _customer_token(client, email='r@example.com')
    client.post('/api/auth/forgot-password', json={'email': 'r@example.com'}, headers={'Host': 'evil.example'})
    assert sent['link'].startswith(app.config['PUBLIC_BASE_URL'])


def test_seeded_super_admin_must_change_password(app):
    with app.app_context():
        assert Staff.query.first().must_change_password is True


def test_security_headers(client):
    r = client.get('/api/flights/airports')
    assert r.headers['X-Content-Type-Options'] == 'nosniff'
    assert r.headers['X-Frame-Options'] == 'DENY'


# ---- token revocation -------------------------------------------------------
def _staff_token(client, app, email='admin@x.com', password='Str0ngPass!1', role='admin'):
    import bcrypt
    from backend.models.staff import StaffRole
    with app.app_context():
        s = Staff(email=email, password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
                  first_name='T', last_name='S', role=StaffRole(role), must_change_password=False)
        db.session.add(s)
        db.session.commit()
        sid = s.id
    r = client.post('/api/staff/auth/login', json={'email': email, 'password': password})
    return sid, r.get_json()['token']


def test_deactivated_staff_token_stops_working(client, app):
    sid, tok = _staff_token(client, app)
    h = {'Authorization': f'Bearer {tok}'}
    assert client.get('/api/admin/dashboard', headers=h).status_code == 200
    with app.app_context():
        s = db.session.get(Staff, sid); s.is_active = False; db.session.commit()
    assert client.get('/api/admin/dashboard', headers=h).status_code == 401


def test_deleted_staff_token_stops_working(client, app):
    sid, tok = _staff_token(client, app)
    with app.app_context():
        db.session.delete(db.session.get(Staff, sid)); db.session.commit()
    assert client.get('/api/admin/dashboard', headers={'Authorization': f'Bearer {tok}'}).status_code == 401


def test_role_comes_from_db_not_token(client, app):
    from backend.models.staff import StaffRole
    sid, tok = _staff_token(client, app, role='admin')
    with app.app_context():
        s = db.session.get(Staff, sid); s.role = StaffRole.FINANCE; db.session.commit()
    # token still says admin, DB says finance -> rejected
    assert client.get('/api/admin/dashboard', headers={'Authorization': f'Bearer {tok}'}).status_code == 401


def test_admin_password_reset_revokes_old_token(client, app):
    _, admin_tok = _staff_token(client, app, email='boss@x.com', role='super_admin')
    sid, victim_tok = _staff_token(client, app, email='victim@x.com', role='agent')
    r = client.post(f'/api/admin/staff/{sid}/reset-password', headers={'Authorization': f'Bearer {admin_tok}'})
    assert r.status_code == 200
    assert client.get('/api/admin/dashboard', headers={'Authorization': f'Bearer {victim_tok}'}).status_code == 401


def test_customer_password_change_revokes_old_token(client):
    _, tok = _customer_token(client, email='rev@example.com')
    h = {'Authorization': f'Bearer {tok}'}
    r = client.post('/api/auth/change-password', headers=h, json={
        'current_password': 'Passw0rd!', 'new_password': 'N3wPassw0rd!', 'confirm_password': 'N3wPassw0rd!'})
    assert r.status_code == 200
    assert client.get('/api/auth/me', headers=h).status_code == 401
    new_h = {'Authorization': f"Bearer {r.get_json()['token']}"}
    assert client.get('/api/auth/me', headers=new_h).status_code == 200


def test_temp_password_token_cannot_use_customer_endpoints(client, app):
    import bcrypt
    from backend.models.staff import StaffRole
    with app.app_context():
        db.session.add(Staff(email='tmp@x.com', password_hash=bcrypt.hashpw(b'TempPass123', bcrypt.gensalt()).decode(),
                             first_name='T', last_name='S', role=StaffRole.AGENT, must_change_password=True))
        db.session.commit()
    tok = client.post('/api/staff/auth/login', json={'email': 'tmp@x.com', 'password': 'TempPass123'}).get_json()['token']
    assert client.get('/api/bookings', headers={'Authorization': f'Bearer {tok}'}).status_code == 403


def test_cannot_deactivate_self(client, app):
    sid, tok = _staff_token(client, app, email='self@x.com', role='super_admin')
    r = client.put(f'/api/admin/staff/{sid}', json={'is_active': False}, headers={'Authorization': f'Bearer {tok}'})
    assert r.status_code == 400


# ---- email escaping / passport trimming -------------------------------------
def test_emails_escape_user_data(app, monkeypatch):
    from backend.services import email_service
    captured = []
    monkeypatch.setattr(email_service, 'send_email', lambda to, subj, body: captured.append(body))
    payload = '<script>alert(1)</script>'
    booking = {'reference': 'AF1', 'origin': 'LOS', 'destination': 'LHR', 'departure_date': '2026-12-01',
               'airline': payload, 'flight_number': payload, 'cabin_class': 'economy',
               'passengers': [{'first_name': payload, 'last_name': '"><img src=x onerror=1>'}],
               'pricing': {'total': 10}}
    with app.test_request_context():
        email_service.send_booking_confirmation_email('a@b.co', payload, booking)
        email_service.send_multicity_confirmation_email('a@b.co', payload, [booking], payload, 10)
        email_service.send_welcome_email('a@b.co', payload)
        email_service.send_password_reset_email('a@b.co', payload, 'http://x/"><script>1</script>')
        email_service.send_staff_credentials_email('a@b.co', payload, 'admin', payload)
    assert len(captured) == 5
    for body in captured:
        assert '<script>' not in body and '<img' not in body


def _booked_with_passport(client, app):
    _, tok = _customer_token(client, email='pp@example.com')
    h = {'Authorization': f'Bearer {tok}'}
    from backend.tests.conftest import with_quote
    b = client.post('/api/bookings', headers=h, json=with_quote(app, {
        **BOOKING, 'passengers': [{'first_name': 'A', 'last_name': 'B', 'passport': 'P1234567'}]})).get_json()['booking']
    return h, b['id']


def test_owner_sees_passport_staff_lists_do_not(client, app):
    h, bid = _booked_with_passport(client, app)
    assert 'P1234567' in client.get(f'/api/bookings/{bid}', headers=h).get_data(as_text=True)
    _, admin_tok = _staff_token(client, app, email='a1@x.com', role='admin')
    ah = {'Authorization': f'Bearer {admin_tok}'}
    for url in ('/api/bookings', '/api/admin/bookings'):
        assert 'P1234567' not in client.get(url, headers=ah).get_data(as_text=True)
    assert 'P1234567' in client.get(f'/api/bookings/{bid}', headers=ah).get_data(as_text=True)


def test_finance_never_sees_passport(client, app):
    h, bid = _booked_with_passport(client, app)
    _, fin_tok = _staff_token(client, app, email='fin@x.com', role='finance')
    fh = {'Authorization': f'Bearer {fin_tok}'}
    for url in ('/api/bookings', '/api/admin/bookings', f'/api/bookings/{bid}'):
        body = client.get(url, headers=fh).get_data(as_text=True)
        assert 'P1234567' not in body
    r = client.post(f'/api/bookings/{bid}/cancel', headers=fh)
    assert r.status_code == 200 and 'P1234567' not in r.get_data(as_text=True)


# ---- CSP ---------------------------------------------------------------------
def test_csp_header_blocks_inline_script(client):
    csp = client.get('/').headers['Content-Security-Policy']
    script_src = [d for d in csp.split(';') if d.strip().startswith('script-src')][0]
    assert "'unsafe-inline'" not in script_src and "'unsafe-eval'" not in script_src
    assert "frame-ancestors 'none'" in csp and "object-src 'none'" in csp


def test_frontend_has_no_inline_scripts_or_handlers():
    """Regression guard: anything inline would be blocked by the CSP (and is an XSS foothold)."""
    import pathlib, re
    root = pathlib.Path(__file__).resolve().parents[2] / 'frontend'
    bad = []
    for f in list(root.rglob('*.html')) + list(root.rglob('*.js')):
        text = f.read_text(encoding='utf-8')
        if f.suffix == '.html':
            for m in re.finditer(r'<script\b([^>]*)>', text):
                if 'src=' not in m.group(1):
                    bad.append(f'{f.relative_to(root)}: inline <script>')
        if re.search(r'\son(click|change|submit|input|focus|blur|load|error|keyup|keydown|mouse\w+)\s*=', text):
            bad.append(f'{f.relative_to(root)}: inline event handler')
        if re.search(r'(href|src)\s*=\s*["\']\s*javascript:', text, re.I):
            bad.append(f'{f.relative_to(root)}: javascript: URL')
    assert not bad, bad


# ---- signed fare quotes --------------------------------------------------------
def _post(client, tok, data):
    return client.post('/api/bookings', json=data, headers={'Authorization': f'Bearer {tok}'})


def test_booking_requires_valid_quote(client, app):
    from backend.tests.conftest import with_quote
    _, tok = _customer_token(client)
    good = with_quote(app, BOOKING)
    assert _post(client, tok, good).status_code == 201
    # no quote
    r = _post(client, tok, BOOKING)
    assert r.status_code == 400 and r.get_json()['code'] == 'quote_invalid'
    # garbage quote
    assert _post(client, tok, {**BOOKING, 'quote': 'x.y'}).status_code == 400
    assert _post(client, tok, {**BOOKING, 'quote': 12345}).status_code == 400


@pytest.mark.parametrize('field,value', [
    ('base_fare', 5), ('airline', 'Other Air'), ('flight_id', 'zzz'),
    ('origin', 'ABV'), ('destination', 'JFK'), ('departure_date', '2027-01-01'), ('cabin', 'first'),
])
def test_quote_binds_every_field(client, app, field, value):
    from backend.tests.conftest import with_quote
    _, tok = _customer_token(client)
    tampered = {**with_quote(app, BOOKING), field: value}
    assert _post(client, tok, tampered).status_code == 400


def test_expired_quote_rejected(client, app, monkeypatch):
    import time
    from backend.tests.conftest import with_quote
    from backend.services import quotes
    _, tok = _customer_token(client)
    good = with_quote(app, BOOKING)
    later = time.time() + quotes.QUOTE_TTL_SECONDS + 5
    monkeypatch.setattr(quotes.time, 'time', lambda: later)
    assert _post(client, tok, good).status_code == 400


def test_quote_signed_with_wrong_key_rejected(client, app):
    from backend.tests.conftest import with_quote
    _, tok = _customer_token(client)
    good = with_quote(app, BOOKING)
    exp, _, mac = good['quote'].partition('.')
    forged = {**good, 'quote': f"{exp}.{'0' * len(mac)}"}
    assert _post(client, tok, forged).status_code == 400


def test_search_results_carry_verifiable_quotes(client, app):
    r = client.get('/api/flights/search?origin=LOS&destination=LHR&departure_date=2026-12-01')
    flights = r.get_json()['results']
    assert flights and all('quote' in f for f in flights)
    f = flights[0]
    _, tok = _customer_token(client)
    r = _post(client, tok, {
        'flight_id': f['id'], 'origin': f['origin'], 'destination': f['destination'],
        'departure_date': f['departure_date'], 'airline': f['airline'], 'cabin': f['cabin'],
        'flight_number': f['flight_number'], 'base_fare': f['pricing']['base_fare'], 'quote': f['quote'],
        'passengers': [{'first_name': 'A', 'last_name': 'B'}]})
    assert r.status_code == 201
    assert r.get_json()['booking']['pricing']['base_fare'] == f['pricing']['base_fare']


def test_multicity_requires_quotes(client, app):
    _, tok = _customer_token(client)
    legs = []
    for d in ('2026-12-01', '2026-12-10'):
        res = client.get(f'/api/flights/search?origin=LOS&destination=LHR&departure_date={d}').get_json()['results'][0]
        legs.append({'flight_id': res['id'], 'origin': res['origin'], 'destination': res['destination'], 'date': d,
                     'airline': res['airline'], 'base_fare': res['pricing']['base_fare'], 'quote': res['quote']})
    body = {'legs': legs, 'passengers': [{'first_name': 'A', 'last_name': 'B'}], 'cabin': 'economy'}
    ok = client.post('/api/bookings/multicity', json=body, headers={'Authorization': f'Bearer {tok}'})
    assert ok.status_code == 201
    legs[1] = {**legs[1], 'base_fare': 1}
    bad = client.post('/api/bookings/multicity', json={**body, 'legs': legs}, headers={'Authorization': f'Bearer {tok}'})
    assert bad.status_code == 400 and 'Leg 2' in bad.get_json()['error']
    no_q = [{k: v for k, v in l.items() if k != 'quote'} for l in legs]
    assert client.post('/api/bookings/multicity', json={**body, 'legs': no_q}, headers={'Authorization': f'Bearer {tok}'}).status_code == 400


# ---- rate limiting -----------------------------------------------------------
def test_login_throttled_per_account_across_ips(client):
    codes = []
    for i in range(12):
        r = client.post('/api/auth/login', json={'email': 'victim@example.com', 'password': 'wrong-pass'},
                        environ_overrides={'REMOTE_ADDR': f'10.0.0.{i}'})
        codes.append(r.status_code)
    assert codes[:10] == [401] * 10
    assert 429 in codes[10:]


def test_staff_login_throttled_per_account(client):
    codes = [client.post('/api/staff/auth/login', json={'email': 'x@example.com', 'password': 'bad'},
                         environ_overrides={'REMOTE_ADDR': f'10.1.0.{i}'}).status_code for i in range(12)]
    assert 429 in codes


def test_other_accounts_unaffected_by_throttle(client):
    for i in range(11):
        client.post('/api/auth/login', json={'email': 'a@example.com', 'password': 'bad'},
                    environ_overrides={'REMOTE_ADDR': f'10.2.0.{i}'})
    r = client.post('/api/auth/login', json={'email': 'b@example.com', 'password': 'bad'},
                    environ_overrides={'REMOTE_ADDR': '10.2.9.9'})
    assert r.status_code == 401


def test_proxy_fix_uses_real_client_ip():
    from flask import Flask
    from backend.app import apply_proxy_fix

    def make(hops):
        a = Flask(__name__)
        a.add_url_rule('/ip', 'ip', lambda: __import__('flask').request.remote_addr)
        return apply_proxy_fix(a, hops).test_client()

    hdr = {'X-Forwarded-For': '203.0.113.9'}
    assert make(1).get('/ip', headers=hdr, environ_overrides={'REMOTE_ADDR': '10.0.0.1'}).get_data(as_text=True) == '203.0.113.9'
    # not trusted unless configured: a spoofed header is ignored
    assert make(0).get('/ip', headers=hdr, environ_overrides={'REMOTE_ADDR': '10.0.0.1'}).get_data(as_text=True) == '10.0.0.1'
    # only the last (trusted) hop counts: a client-prepended fake entry is ignored
    spoof = {'X-Forwarded-For': '6.6.6.6, 203.0.113.9'}
    assert make(1).get('/ip', headers=spoof, environ_overrides={'REMOTE_ADDR': '10.0.0.1'}).get_data(as_text=True) == '203.0.113.9'


# ---- deployment: database URL handling ------------------------------------------
@pytest.mark.parametrize('given,expected', [
    ('postgres://u:p@host:5432/db', 'postgresql+psycopg2://u:p@host:5432/db'),
    ('postgresql://u:p@host/db', 'postgresql+psycopg2://u:p@host/db'),
    ('postgresql+psycopg2://u:p@host/db', 'postgresql+psycopg2://u:p@host/db'),
    ('sqlite:///airfinder.db', 'sqlite:///airfinder.db'),
])
def test_database_uri_names_psycopg2_driver(monkeypatch, given, expected):
    from backend.config import _database_uri
    monkeypatch.setenv('DATABASE_URL', given)
    assert _database_uri() == expected
