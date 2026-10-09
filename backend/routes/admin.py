from flask import Blueprint, jsonify, request, g
from backend.models.database import db
from backend.models.user import User
from backend.models.staff import Staff, StaffRole
from backend.models.booking import Booking, BookingStatus
from backend.middleware.role_guard import require_role
from sqlalchemy import func

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@bp.route('/dashboard', methods=['GET'])
@require_role('super_admin', 'admin', 'agent', 'finance')
def dashboard():
    total_bookings = Booking.query.count()
    confirmed = Booking.query.filter_by(status=BookingStatus.CONFIRMED).count()
    cancelled = Booking.query.filter_by(status=BookingStatus.CANCELLED).count()
    total_revenue = db.session.query(func.sum(Booking.total_usd)).filter_by(status=BookingStatus.CONFIRMED).scalar() or 0
    total_commission = db.session.query(func.sum(Booking.commission_usd)).filter_by(status=BookingStatus.CONFIRMED).scalar() or 0
    total_customers = User.query.count()
    total_staff = Staff.query.count()

    data = {
        'bookings': {
            'total': total_bookings,
            'confirmed': confirmed,
            'cancelled': cancelled,
            'pending': total_bookings - confirmed - cancelled,
        },
        'revenue': {
            'total_usd': round(total_revenue, 2),
            'commission_usd': round(total_commission, 2),
            'service_fees_usd': round(confirmed * 15, 2),
        },
        'customers': total_customers,
    }

    if g.role in ('super_admin', 'admin'):
        data['staff'] = total_staff

    return jsonify(data)

@bp.route('/customers', methods=['GET'])
@require_role('super_admin', 'admin', 'agent')
def customers():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    search = request.args.get('search', '')

    query = User.query
    if search:
        query = query.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )

    paginated = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    customers_data = []
    for u in paginated.items:
        d = u.to_dict()
        d['booking_count'] = Booking.query.filter_by(user_id=u.id).count()
        d['total_spent'] = round(
            db.session.query(func.sum(Booking.total_usd))
            .filter_by(user_id=u.id, status=BookingStatus.CONFIRMED).scalar() or 0, 2
        )
        customers_data.append(d)

    return jsonify({
        'customers': customers_data,
        'total': paginated.total,
        'pages': paginated.pages,
        'page': page,
    })

@bp.route('/bookings', methods=['GET'])
@require_role('super_admin', 'admin', 'agent', 'finance')
def all_bookings():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    status_filter = request.args.get('status')

    query = Booking.query
    if status_filter:
        try:
            query = query.filter_by(status=BookingStatus(status_filter))
        except ValueError:
            pass

    paginated = query.order_by(Booking.created_at.desc()).paginate(page=page, per_page=per_page)
    bookings = []
    for b in paginated.items:
        d = b.to_dict(passenger_detail=False)
        user = User.query.get(b.user_id)
        d['customer_name'] = f"{user.first_name} {user.last_name}" if user else "Guest"
        d['customer_email'] = user.email if user else "—"
        bookings.append(d)
    return jsonify({
        'bookings': bookings,
        'total': paginated.total,
        'pages': paginated.pages,
        'page': page,
    })

@bp.route('/bookings/<booking_id>', methods=['PUT'])
@require_role('super_admin', 'admin', 'agent')
def update_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json()

    if 'status' in data:
        try:
            booking.status = BookingStatus(data['status'])
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400

    if 'notes' in data:
        booking.notes = data['notes']

    db.session.commit()
    return jsonify(booking.to_dict(passenger_detail=False))

@bp.route('/finance/summary', methods=['GET'])
@require_role('super_admin', 'admin', 'finance')
def finance_summary():
    confirmed_bookings = Booking.query.filter_by(status=BookingStatus.CONFIRMED).all()
    total_revenue = sum(b.total_usd for b in confirmed_bookings)
    total_commission = sum(b.commission_usd for b in confirmed_bookings)
    total_markup = sum(b.markup_usd for b in confirmed_bookings)
    total_service_fees = sum(b.service_fee_usd for b in confirmed_bookings)
    total_baggage = sum(b.baggage_fee_usd for b in confirmed_bookings)

    return jsonify({
        'total_revenue_usd': round(total_revenue, 2),
        'commission_usd': round(total_commission, 2),
        'markup_usd': round(total_markup, 2),
        'service_fees_usd': round(total_service_fees, 2),
        'baggage_fees_usd': round(total_baggage, 2),
        'total_bookings': len(confirmed_bookings),
        'avg_booking_value': round(total_revenue / max(len(confirmed_bookings), 1), 2),
    })

@bp.route('/settings', methods=['GET'])
@require_role('super_admin')
def get_settings():
    from backend.config import Config
    return jsonify({
        'markup_percent': Config.MARKUP_PERCENT,
        'service_fee_usd': Config.SERVICE_FEE_USD,
        'commission_percent': Config.COMMISSION_PERCENT,
    })
