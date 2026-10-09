import json
import math
import random
import string
from flask import Blueprint, request, jsonify, g
from backend.models.database import db
from backend.models.booking import Booking, BookingStatus, generate_reference
from backend.models.user import User
from backend.middleware.jwt_guard import jwt_required
from backend.services.pricing import calculate_total
from backend.services.email_service import send_booking_confirmation_email, send_multicity_confirmation_email
from backend.extensions import limiter

bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')

MAX_PASSENGERS = 9
MAX_LEGS = 6
MIN_FARE, MAX_FARE = 1.0, 20000.0


def _valid_fare(value):
    try:
        fare = float(value)
    except (TypeError, ValueError):
        return None
    return fare if math.isfinite(fare) and MIN_FARE <= fare <= MAX_FARE else None


def _valid_passengers(pax):
    if not isinstance(pax, list) or not 1 <= len(pax) <= MAX_PASSENGERS:
        return False
    return all(isinstance(p, dict) for p in pax)


def _clean(value, limit=100):
    return str(value).strip()[:limit]

@bp.route('', methods=['POST'])
@jwt_required
@limiter.limit("10 per minute")
def create_booking():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'JSON body required'}), 400
    required = ['flight_id', 'origin', 'destination', 'departure_date', 'airline', 'base_fare', 'passengers']
    if not all(data.get(f) for f in required):
        return jsonify({'error': f'Required fields: {", ".join(required)}'}), 400

    base_fare = _valid_fare(data['base_fare'])
    if base_fare is None:
        return jsonify({'error': 'Invalid base_fare'}), 400
    if not _valid_passengers(data['passengers']):
        return jsonify({'error': f'passengers must be a list of 1-{MAX_PASSENGERS} objects'}), 400

    pricing = calculate_total(
        base_fare=base_fare,
        passengers=len(data['passengers']),
        baggage_option=data.get('baggage', 'carry_on'),
        seat_option=data.get('seat', 'standard'),
    )

    # Prevent duplicate booking reference collision
    ref = generate_reference()
    while Booking.query.filter_by(reference=ref).first():
        ref = generate_reference()

    booking = Booking(
        reference=ref,
        user_id=g.user_id,
        flight_id=_clean(data['flight_id']),
        origin=_clean(data['origin'], 10).upper(),
        destination=_clean(data['destination'], 10).upper(),
        departure_date=_clean(data['departure_date'], 20),
        airline=_clean(data['airline']),
        flight_number=_clean(data['flight_number'], 20) if data.get('flight_number') else None,
        cabin_class=_clean(data.get('cabin', 'economy'), 20),
        passengers_json=json.dumps(data['passengers']),
        passenger_count=len(data['passengers']),
        base_fare_usd=pricing['base_fare'],
        markup_usd=pricing['markup'],
        service_fee_usd=pricing['service_fee'],
        baggage_fee_usd=pricing['baggage_fee'],
        seat_fee_usd=pricing['seat_fee'],
        total_usd=pricing['total'],
        commission_usd=pricing['commission'],
        status=BookingStatus.CONFIRMED,
    )
    db.session.add(booking)
    db.session.commit()

    user = User.query.get(g.user_id)
    if user:
        send_booking_confirmation_email(user.email, user.first_name, booking.to_dict())

    return jsonify({'booking': booking.to_dict(), 'message': 'Booking confirmed!'}), 201

@bp.route('/multicity', methods=['POST'])
@jwt_required
@limiter.limit("5 per minute")
def create_multicity_booking():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'JSON body required'}), 400
    legs = data.get('legs', [])
    passengers = data.get('passengers', [])
    baggage = data.get('baggage', 'carry_on')
    seat = data.get('seat', 'standard')
    cabin = data.get('cabin', 'economy')

    if not isinstance(legs, list) or len(legs) < 2:
        return jsonify({'error': 'At least 2 legs required for multi-city booking'}), 400
    if len(legs) > MAX_LEGS:
        return jsonify({'error': f'Maximum {MAX_LEGS} legs allowed'}), 400
    if not _valid_passengers(passengers):
        return jsonify({'error': f'passengers must be a list of 1-{MAX_PASSENGERS} objects'}), 400

    leg_fields = ('base_fare', 'flight_id', 'origin', 'destination', 'date', 'airline')
    for i, leg in enumerate(legs, 1):
        if not isinstance(leg, dict) or not all(leg.get(f) for f in leg_fields):
            return jsonify({'error': f'Leg {i}: required fields: {", ".join(leg_fields)}'}), 400
        if _valid_fare(leg['base_fare']) is None:
            return jsonify({'error': f'Leg {i}: invalid base_fare'}), 400

    group_ref = 'AF' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    created = []
    combined_total = 0.0

    for leg in legs:
        pricing = calculate_total(
            base_fare=_valid_fare(leg['base_fare']),
            passengers=len(passengers),
            baggage_option=baggage,
            seat_option=seat,
        )
        ref = generate_reference()
        while Booking.query.filter_by(reference=ref).first():
            ref = generate_reference()

        booking = Booking(
            reference=ref,
            user_id=g.user_id,
            flight_id=_clean(leg['flight_id']),
            origin=_clean(leg['origin'], 10).upper(),
            destination=_clean(leg['destination'], 10).upper(),
            departure_date=_clean(leg['date'], 20),
            airline=_clean(leg['airline']),
            flight_number=_clean(leg['flight_number'], 20) if leg.get('flight_number') else None,
            cabin_class=_clean(cabin, 20),
            passengers_json=json.dumps(passengers),
            passenger_count=len(passengers),
            base_fare_usd=pricing['base_fare'],
            markup_usd=pricing['markup'],
            service_fee_usd=pricing['service_fee'],
            baggage_fee_usd=pricing['baggage_fee'],
            seat_fee_usd=pricing['seat_fee'],
            total_usd=pricing['total'],
            commission_usd=pricing['commission'],
            group_reference=group_ref,
            is_multicity=True,
            status=BookingStatus.CONFIRMED,
        )
        db.session.add(booking)
        created.append(booking)
        combined_total += pricing['total']

    db.session.commit()

    user = User.query.get(g.user_id)
    if user and created:
        send_multicity_confirmation_email(
            user.email, user.first_name,
            [b.to_dict() for b in created],
            group_ref, combined_total
        )

    return jsonify({
        'group_reference': group_ref,
        'bookings': [b.to_dict() for b in created],
        'total_legs': len(created),
        'combined_total_usd': round(combined_total, 2),
        'message': f'Multi-city booking confirmed! {len(created)} flights booked.',
    }), 201

@bp.route('', methods=['GET'])
@jwt_required
def my_bookings():
    role = g.role
    if role == 'customer':
        bookings = Booking.query.filter_by(user_id=g.user_id).order_by(Booking.created_at.desc()).all()
    else:
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return jsonify([b.to_dict() for b in bookings])

@bp.route('/<booking_id>', methods=['GET'])
@jwt_required
def get_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if g.role == 'customer' and booking.user_id != g.user_id:
        return jsonify({'error': 'Access denied'}), 403
    return jsonify(booking.to_dict())

@bp.route('/<booking_id>/cancel', methods=['POST'])
@jwt_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if g.role == 'customer' and booking.user_id != g.user_id:
        return jsonify({'error': 'Access denied'}), 403

    if booking.status == BookingStatus.CANCELLED:
        return jsonify({'error': 'Booking already cancelled'}), 400

    booking.status = BookingStatus.CANCELLED
    db.session.commit()
    return jsonify({'message': 'Booking cancelled', 'booking': booking.to_dict()})
