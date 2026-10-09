import uuid
import enum
from datetime import datetime
from backend.models.database import db

class StaffRole(enum.Enum):
    SUPER_ADMIN = 'super_admin'
    ADMIN = 'admin'
    AGENT = 'agent'
    FINANCE = 'finance'

class Staff(db.Model):
    __tablename__ = 'staff'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(StaffRole), nullable=False, default=StaffRole.AGENT)
    must_change_password = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    token_version = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    created_by = db.Column(db.String(36), db.ForeignKey('staff.id'), nullable=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reset_token = db.Column(db.String(64), nullable=True, index=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value,
            'must_change_password': self.must_change_password,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }

ROLE_HIERARCHY = {
    StaffRole.SUPER_ADMIN: 4,
    StaffRole.ADMIN: 3,
    StaffRole.AGENT: 2,
    StaffRole.FINANCE: 1,
}

def can_manage(actor_role: StaffRole, target_role: StaffRole) -> bool:
    return ROLE_HIERARCHY.get(actor_role, 0) > ROLE_HIERARCHY.get(target_role, 0)
