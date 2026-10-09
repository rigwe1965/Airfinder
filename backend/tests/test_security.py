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
