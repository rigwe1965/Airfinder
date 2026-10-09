def _get_customer_token(client):
    client.post('/api/auth/register', json={
        'email': 'booker@example.com', 'password': 'Test1234!',
        'first_name': 'Book', 'last_name': 'Er',
    })
    resp = client.post('/api/auth/login', json={'email': 'booker@example.com', 'password': 'Test1234!'})
    return resp.get_json()['token']

def test_create_booking(client, app):
    from backend.tests.conftest import with_quote
    token = _get_customer_token(client)
    resp = client.post('/api/bookings', json=with_quote(app, {
        'flight_id': 'P4101-2026-08-15-0',
        'origin': 'LOS', 'destination': 'LHR',
        'departure_date': '2026-08-15',
        'airline': 'Air Peace',
        'base_fare': 549.00,
        'passengers': [{'first_name': 'John', 'last_name': 'Doe', 'passport': 'A123456'}],
    }), headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['booking']['reference'].startswith('AF')
    assert data['booking']['status'] == 'confirmed'

def test_my_bookings(client):
    token = _get_customer_token(client)
    resp = client.get('/api/bookings', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

def test_booking_requires_auth(client):
    resp = client.post('/api/bookings', json={'flight_id': 'test'})
    assert resp.status_code == 401
