import re
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from backend.services.mock_flights import search_flights, get_featured_routes, get_airports, get_cheapest_price
from backend.services.ai_search import parse_natural_language
from backend.services.pricing import calculate_total, BAGGAGE_FEES, SEAT_FEES
from backend.extensions import limiter

bp = Blueprint('flights', __name__, url_prefix='/api/flights')

@bp.route('/search', methods=['GET'])
@limiter.limit("60 per minute")
def search():
    origin = request.args.get('origin', '').upper()
    destination = request.args.get('destination', '').upper()
    departure_date = request.args.get('departure_date')
    passengers = request.args.get('passengers', 1, type=int)
    cabin = request.args.get('cabin', 'economy')
    return_date = request.args.get('return_date')

    if not origin or not destination or not departure_date:
        return jsonify({'error': 'origin, destination, and departure_date are required'}), 400

    passengers = max(1, min(passengers, 9))
    results = search_flights(origin, destination, departure_date, passengers, cabin, return_date)

    # Apply budget filter if provided
    budget = request.args.get('budget_max')
    if budget:
        try:
            results = [f for f in results if f['pricing']['total'] <= float(budget)]
        except (ValueError, TypeError):
            pass

    return jsonify({
        'results': results,
        'count': len(results),
        'origin': origin,
        'destination': destination,
        'departure_date': departure_date,
        'passengers': passengers,
        'cabin': cabin,
    })

@bp.route('/search/ai', methods=['POST'])
@limiter.limit("30 per minute")
def ai_search():
    data = request.get_json()
    query = str(data.get('query', '')).strip()[:200]
    if not query:
        return jsonify({'error': 'query is required'}), 400

    parsed = parse_natural_language(query)

    if not parsed['origin'] or not parsed['destination']:
        return jsonify({
            'parsed': parsed,
            'results': [],
            'suggestion': 'Could not identify origin or destination. Try: "flight from Lagos to London next month"'
        })

    results = search_flights(
        parsed['origin'],
        parsed['destination'],
        parsed['departure_date'],
        parsed['passengers'],
        parsed['cabin'],
    )

    if parsed.get('budget_max_usd'):
        results = [r for r in results if r['pricing']['total'] <= parsed['budget_max_usd']]

    return jsonify({
        'parsed': parsed,
        'results': results,
        'count': len(results),
    })

@bp.route('/search/multicity', methods=['POST'])
@limiter.limit("20 per minute")
def multicity_search():
    data = request.get_json()
    legs = data.get('legs', [])
    passengers = max(1, min(int(data.get('passengers', 1)), 9))
    cabin = data.get('cabin', 'economy')

    if len(legs) < 2:
        return jsonify({'error': 'At least 2 legs required'}), 400
    if len(legs) > 6:
        return jsonify({'error': 'Maximum 6 legs allowed'}), 400

    results = []
    for i, leg in enumerate(legs):
        origin = leg.get('origin', '').upper()
        destination = leg.get('destination', '').upper()
        date = leg.get('date', '')
        if not origin or not destination or not date:
            return jsonify({'error': f'Leg {i+1}: origin, destination, and date required'}), 400
        flights = search_flights(origin, destination, date, passengers, cabin)
        results.append({
            'leg_num': i + 1,
            'origin': origin,
            'destination': destination,
            'date': date,
            'flights': flights,
        })

    return jsonify({'legs': results, 'passengers': passengers, 'cabin': cabin})

@bp.route('/search/flexible', methods=['GET'])
@limiter.limit("20 per minute")
def flexible_search():
    origin = request.args.get('origin', '').upper()
    destination = request.args.get('destination', '').upper()
    date_str = request.args.get('date', '')
    passengers = max(1, min(int(request.args.get('passengers', 1)), 9))
    cabin = request.args.get('cabin', 'economy')

    if not origin or not destination or not date_str:
        return jsonify({'error': 'origin, destination, date required'}), 400

    try:
        center = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    grid = []
    for delta in range(-3, 4):
        d = center + timedelta(days=delta)
        d_str = d.strftime('%Y-%m-%d')
        price = get_cheapest_price(origin, destination, d_str, passengers, cabin)
        grid.append({
            'date': d_str,
            'day': d.strftime('%a'),
            'price': price,
            'is_target': delta == 0,
            'is_cheapest': False,
        })

    prices = [g['price'] for g in grid if g['price'] is not None]
    if prices:
        min_price = min(prices)
        for g in grid:
            g['is_cheapest'] = g['price'] == min_price

    return jsonify({'grid': grid, 'origin': origin, 'destination': destination})

@bp.route('/featured', methods=['GET'])
def featured():
    force = request.args.get('refresh', '').lower() == 'true'
    return jsonify(get_featured_routes(force_refresh=force))

@bp.route('/airports', methods=['GET'])
def airports():
    return jsonify(get_airports())

@bp.route('/pricing/calculate', methods=['POST'])
@limiter.limit("60 per minute")
def calculate_price():
    data = request.get_json()
    base_fare = data.get('base_fare')
    if base_fare is None:
        return jsonify({'error': 'base_fare required'}), 400

    result = calculate_total(
        base_fare=float(base_fare),
        passengers=int(data.get('passengers', 1)),
        baggage_option=data.get('baggage', 'carry_on'),
        seat_option=data.get('seat', 'standard'),
    )
    return jsonify(result)

@bp.route('/pricing/options', methods=['GET'])
def pricing_options():
    return jsonify({
        'baggage': [{'id': k, 'label': k.replace('_', ' ').title(), 'fee_usd': v} for k, v in BAGGAGE_FEES.items()],
        'seats': [{'id': k, 'label': k.replace('_', ' ').title(), 'fee_usd': v} for k, v in SEAT_FEES.items()],
    })

@bp.route('/status', methods=['GET'])
@limiter.limit("60 per minute")
def flight_status():
    from backend.services.mock_flights import AIRPORTS, AIRLINES
    import random, hashlib

    flight_number = request.args.get('flight', '').upper().strip()
    date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))

    if not flight_number:
        return jsonify({'error': 'flight number required'}), 400
    if not re.fullmatch(r'[A-Z0-9]{2,3}\d{1,4}[A-Z]?', flight_number):
        return jsonify({'error': 'invalid flight number'}), 400
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Derive deterministic but realistic mock data from flight number + date
    seed = int(hashlib.md5(f"{flight_number}{date_str}".encode()).hexdigest(), 16) % (2**31)
    rng = random.Random(seed)

    # Identify airline from code prefix
    airline = None
    for a in AIRLINES:
        if flight_number.startswith(a['code']):
            airline = a
            break
    if not airline:
        airline = rng.choice(AIRLINES)

    # Pick plausible origin/destination from airport pool
    airport_list = [{'code': k, **v} for k, v in AIRPORTS.items()]
    origin_ap = rng.choice(airport_list)
    dest_pool = [a for a in airport_list if a['code'] != origin_ap['code'] and a['region'] != origin_ap['region']]
    if not dest_pool:
        dest_pool = [a for a in airport_list if a['code'] != origin_ap['code']]
    dest_ap = rng.choice(dest_pool)

    # Scheduled times
    sched_dep_h = rng.randint(5, 22)
    sched_dep_m = rng.choice([0, 15, 30, 45])

    from backend.services.mock_flights import _haversine_km, _estimate_duration
    dist = _haversine_km(origin_ap['lat'], origin_ap['lon'], dest_ap['lat'], dest_ap['lon'])
    duration_h = _estimate_duration(origin_ap['code'], dest_ap['code'], 0)
    arr_h = int((sched_dep_h + duration_h) % 24)
    arr_m = sched_dep_m
    next_day = (sched_dep_h + duration_h) >= 24

    # Current status based on time-of-day simulation
    now = datetime.utcnow()
    status_roll = rng.randint(0, 99)
    if status_roll < 5:
        status = 'cancelled'
        delay_min = 0
        status_color = 'red'
    elif status_roll < 20:
        delay_min = rng.choice([15, 20, 30, 45, 60, 90, 120])
        status = 'delayed'
        status_color = 'amber'
    elif status_roll < 35:
        status = 'boarding'
        delay_min = 0
        status_color = 'blue'
    elif status_roll < 55:
        status = 'departed'
        delay_min = 0
        status_color = 'green'
    elif status_roll < 75:
        status = 'arrived'
        delay_min = 0
        status_color = 'green'
    else:
        status = 'on_time'
        delay_min = 0
        status_color = 'green'

    gate = f"{rng.choice('ABCDEFGH')}{rng.randint(1,30)}"
    terminal = f"T{rng.randint(1,3)}"

    actual_dep_h = int((sched_dep_h * 60 + sched_dep_m + delay_min) / 60) % 24
    actual_dep_m = (sched_dep_m + delay_min) % 60

    status_labels = {
        'on_time': 'On Time',
        'delayed': f'Delayed {delay_min} min',
        'boarding': 'Boarding',
        'departed': 'Departed',
        'arrived': 'Arrived',
        'cancelled': 'Cancelled',
    }

    return jsonify({
        'flight_number': flight_number,
        'date': date_str,
        'airline': airline['name'],
        'airline_code': airline['code'],
        'origin': {
            'code': origin_ap['code'],
            'name': origin_ap['name'],
            'city': origin_ap['city'],
            'country': origin_ap['country'],
        },
        'destination': {
            'code': dest_ap['code'],
            'name': dest_ap['name'],
            'city': dest_ap['city'],
            'country': dest_ap['country'],
        },
        'scheduled_departure': f"{sched_dep_h:02d}:{sched_dep_m:02d}",
        'scheduled_arrival': f"{arr_h:02d}:{arr_m:02d}",
        'actual_departure': f"{actual_dep_h:02d}:{actual_dep_m:02d}" if status not in ('on_time', 'cancelled') else f"{sched_dep_h:02d}:{sched_dep_m:02d}",
        'estimated_arrival': f"{int((arr_h * 60 + arr_m + delay_min) / 60) % 24:02d}:{(arr_m + delay_min) % 60:02d}",
        'status': status,
        'status_label': status_labels[status],
        'status_color': status_color,
        'delay_minutes': delay_min,
        'gate': gate,
        'terminal': terminal,
        'duration_hours': round(duration_h, 1),
        'distance_km': round(dist),
        'next_day_arrival': next_day,
        'aircraft': rng.choice(['Boeing 737-800', 'Airbus A320', 'Boeing 787-9', 'Airbus A350-900', 'Boeing 777-300ER', 'Airbus A380', 'Embraer E195', 'Airbus A321neo']),
        'baggage_belt': rng.randint(1, 12) if status == 'arrived' else None,
    })
