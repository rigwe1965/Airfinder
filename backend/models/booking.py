import uuid
import enum
from datetime import datetime
from backend.models.database import db

class BookingStatus(enum.Enum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    flight_id = db.Column(db.String(100), nullable=False)

    # Flight snapshot (stored at booking time)
    origin = db.Column(db.String(10), nullable=False)
    destination = db.Column(db.String(10), nullable=False)
    departure_date = db.Column(db.String(20), nullable=False)
    airline = db.Column(db.String(100), nullable=False)
    flight_number = db.Column(db.String(20))
    cabin_class = db.Column(db.String(20), default='economy')

    # Passengers JSON stored as string
    passengers_json = db.Column(db.Text, nullable=False)
    passenger_count = db.Column(db.Integer, default=1)

    # Pricing breakdown
    base_fare_usd = db.Column(db.Float, nullable=False)
    markup_usd = db.Column(db.Float, default=0)
    service_fee_usd = db.Column(db.Float, default=0)
    baggage_fee_usd = db.Column(db.Float, default=0)
    seat_fee_usd = db.Column(db.Float, default=0)
    total_usd = db.Column(db.Float, nullable=False)
    commission_usd = db.Column(db.Float, default=0)

    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.PENDING)
    notes = db.Column(db.Text)
    agent_id = db.Column(db.String(36), db.ForeignKey('staff.id'), nullable=True)
    group_reference = db.Column(db.String(20), nullable=True, index=True)
    is_multicity = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, passenger_detail=True):
        """passenger_detail=False returns names only (no passport/DOB/etc.)."""
        import json
        passengers = json.loads(self.passengers_json)
        if not passenger_detail:
            passengers = [
                {'first_name': p.get('first_name', ''), 'last_name': p.get('last_name', '')}
                for p in passengers if isinstance(p, dict)
            ]
        return {
            'id': self.id,
            'reference': self.reference,
            'user_id': self.user_id,
            'flight_id': self.flight_id,
            'origin': self.origin,
            'destination': self.destination,
            'departure_date': self.departure_date,
            'airline': self.airline,
            'flight_number': self.flight_number,
            'cabin_class': self.cabin_class,
            'passengers': passengers,
            'passenger_count': self.passenger_count,
            'pricing': {
                'base_fare': self.base_fare_usd,
                'markup': self.markup_usd,
                'service_fee': self.service_fee_usd,
                'baggage_fee': self.baggage_fee_usd,
                'seat_fee': self.seat_fee_usd,
                'total': self.total_usd,
                'commission': self.commission_usd,
            },
            'status': self.status.value,
            'notes': self.notes,
            'group_reference': self.group_reference,
            'is_multicity': self.is_multicity or False,
            'created_at': self.created_at.isoformat()
        }

def generate_reference():
    import random, string
    return 'AF' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
