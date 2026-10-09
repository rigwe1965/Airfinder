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


def _booked_with_passport(client):
    _, tok = _customer_token(client, email='pp@example.com')
    h = {'Authorization': f'Bearer {tok}'}
    b = client.post('/api/bookings', headers=h, json={
        **BOOKING, 'passengers': [{'first_name': 'A', 'last_name': 'B', 'passport': 'P1234567'}]}).get_json()['booking']
    return h, b['id']


def test_owner_sees_passport_staff_lists_do_not(client, app):
    h, bid = _booked_with_passport(client)
    assert 'P1234567' in client.get(f'/api/bookings/{bid}', headers=h).get_data(as_text=True)
    _, admin_tok = _staff_token(client, app, email='a1@x.com', role='admin')
    ah = {'Authorization': f'Bearer {admin_tok}'}
    for url in ('/api/bookings', '/api/admin/bookings'):
        assert 'P1234567' not in client.get(url, headers=ah).get_data(as_text=True)
    assert 'P1234567' in client.get(f'/api/bookings/{bid}', headers=ah).get_data(as_text=True)


def test_finance_never_sees_passport(client, app):
    h, bid = _booked_with_passport(client)
    _, fin_tok = _staff_token(client, app, email='fin@x.com', role='finance')
    fh = {'Authorization': f'Bearer {fin_tok}'}
    for url in ('/api/bookings', '/api/admin/bookings', f'/api/bookings/{bid}'):
        body = client.get(url, headers=fh).get_data(as_text=True)
        assert 'P1234567' not in body
    r = client.post(f'/api/bookings/{bid}/cancel', headers=fh)
    assert r.status_code == 200 and 'P1234567' not in r.get_data(as_text=True)
