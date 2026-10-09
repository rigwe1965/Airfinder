"""Signed fare quotes.

Search results are generated randomly, so the server cannot re-derive a fare at booking time.
Instead every search result carries an HMAC-signed `quote` binding the flight id, route, date,
cabin, airline and base fare. Booking endpoints accept a fare only if its quote verifies, so a
client can no longer choose its own price.
"""
import hashlib
import hmac
import time

from flask import current_app

QUOTE_TTL_SECONDS = 2 * 60 * 60


def _canonical(flight_id, origin, destination, date, cabin, airline, base_fare) -> bytes:
    parts = [flight_id, origin, destination, date, cabin, airline, f'{float(base_fare):.2f}']
    return '|'.join(str(p).strip().upper() for p in parts).encode('utf-8')


def _mac(payload: bytes, expires: int) -> str:
    key = current_app.config['SECRET_KEY'].encode('utf-8')
    return hmac.new(key, payload + b'|' + str(expires).encode(), hashlib.sha256).hexdigest()


def sign_quote(flight_id, origin, destination, date, cabin, airline, base_fare) -> str:
    expires = int(time.time()) + QUOTE_TTL_SECONDS
    return f'{expires}.{_mac(_canonical(flight_id, origin, destination, date, cabin, airline, base_fare), expires)}'


def verify_quote(token, flight_id, origin, destination, date, cabin, airline, base_fare) -> bool:
    if not isinstance(token, str) or '.' not in token:
        return False
    exp_str, _, mac = token.partition('.')
    try:
        expires = int(exp_str)
        payload = _canonical(flight_id, origin, destination, date, cabin, airline, base_fare)
    except (TypeError, ValueError):
        return False
    if expires < time.time():
        return False
    return hmac.compare_digest(mac, _mac(payload, expires))


def attach_quotes(flights):
    """Add a `quote` to each search-result dict (in place) and return the list."""
    for f in flights:
        f['quote'] = sign_quote(f['id'], f['origin'], f['destination'], f['departure_date'],
                                f['cabin'], f['airline'], f['pricing']['base_fare'])
    return flights
