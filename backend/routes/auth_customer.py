import jwt
import bcrypt
import uuid
import re
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, g
from backend.models.database import db
from backend.models.user import User
from backend.middleware.jwt_guard import jwt_required
from backend.services.email_service import send_welcome_email, send_password_reset_email
from backend.services.security_logger import log_security_event
from backend.extensions import limiter

bp = Blueprint('auth_customer', __name__, url_prefix='/api/auth')

_EMAIL_RE = re.compile(r'^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$')
_NAME_RE = re.compile(r"^[^<>]{1,100}$")


def _bad_name(value):
    return not isinstance(value, str) or not _NAME_RE.match(value.strip())

@bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'JSON body required'}), 400
    required = ['email', 'password', 'first_name', 'last_name']
    if not all(data.get(f) for f in required):
        return jsonify({'error': 'All fields required: email, password, first_name, last_name'}), 400
    if not all(isinstance(data[f], str) for f in required):
        return jsonify({'error': 'Invalid field types'}), 400
    if not _EMAIL_RE.match(data['email']) or len(data['email']) > 255:
        return jsonify({'error': 'Invalid email address'}), 400
    if _bad_name(data['first_name']) or _bad_name(data['last_name']):
        return jsonify({'error': 'Names may not contain < or >'}), 400
    if len(data['password']) > 128:
        return jsonify({'error': 'Password too long'}), 400

    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already registered'}), 409

    if len(data['password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    verification_token = secrets.token_urlsafe(32)

    user = User(
        email=data['email'].lower(),
        password_hash=hashed.decode('utf-8'),
        first_name=data['first_name'].strip(),
        last_name=data['last_name'].strip(),
        phone=str(data['phone'])[:30] if data.get('phone') else None,
        verification_token=verification_token,
        is_verified=True,  # Auto-verify for demo; set False + send email for production
    )
    db.session.add(user)
    db.session.commit()

    send_welcome_email(user.email, user.first_name)
    token = _generate_token(user)

    return jsonify({
        'message': 'Account created successfully',
        'token': token,
        'user': user.to_dict()
    }), 201

@bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=data['email'].lower()).first()
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        log_security_event('login_failed', user_type='customer', email=data['email'].lower(), ip=request.remote_addr)
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account deactivated. Contact support.'}), 403

    token = _generate_token(user)
    return jsonify({'token': token, 'user': user.to_dict()})

@bp.route('/forgot-password', methods=['POST'])
@limiter.limit("5 per hour")
def forgot_password():
    data = request.get_json()
    email = data.get('email', '').lower()
    user = User.query.filter_by(email=email).first()

    # Always return success to prevent email enumeration
    if not user:
        return jsonify({'message': 'If that email exists, a reset link was sent.'})

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)
    db.session.commit()

    reset_link = f"{current_app.config['PUBLIC_BASE_URL']}/auth/reset-password.html#{token}"
    send_password_reset_email(user.email, user.first_name, reset_link)

    return jsonify({'message': 'If that email exists, a reset link was sent.'})

@bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('password')

    if not token or not new_password:
        return jsonify({'error': 'Token and new password required'}), 400

    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({'error': 'Invalid or expired token'}), 400

    if not user.is_active or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        return jsonify({'error': 'Reset link has expired. Request a new one.'}), 400

    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    user.password_hash = hashed.decode('utf-8')
    user.reset_token = None
    user.reset_token_expiry = None
    user.token_version = (user.token_version or 0) + 1
    db.session.commit()

    return jsonify({'message': 'Password reset successfully. You can now log in.'})

@bp.route('/me', methods=['GET'])
@jwt_required
def me():
    user = User.query.get(g.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict())

@bp.route('/me', methods=['PUT'])
@jwt_required
@limiter.limit("20 per hour")
def update_me():
    user = User.query.get(g.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    phone = data.get('phone', '').strip()

    if not first_name or not last_name:
        return jsonify({'error': 'First name and last name are required'}), 400
    if _bad_name(first_name) or _bad_name(last_name):
        return jsonify({'error': 'Names may not contain < or >'}), 400
    phone = phone[:30]

    user.first_name = first_name
    user.last_name = last_name
    user.phone = phone or None
    db.session.commit()

    return jsonify({'message': 'Profile updated', 'user': user.to_dict()})

@bp.route('/change-password', methods=['POST'])
@jwt_required
@limiter.limit("10 per hour")
def change_password():
    user = User.query.get(g.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    current = data.get('current_password', '')
    new_pw = data.get('new_password', '')
    confirm = data.get('confirm_password', '')

    if not current or not new_pw or not confirm:
        return jsonify({'error': 'All password fields are required'}), 400

    if not bcrypt.checkpw(current.encode('utf-8'), user.password_hash.encode('utf-8')):
        log_security_event('password_change_failed', user_type='customer', user_id=user.id, ip=request.remote_addr)
        return jsonify({'error': 'Current password is incorrect'}), 400

    if new_pw != confirm:
        return jsonify({'error': 'New passwords do not match'}), 400

    if len(new_pw) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    if new_pw == current:
        return jsonify({'error': 'New password must differ from current password'}), 400

    hashed = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt())
    user.password_hash = hashed.decode('utf-8')
    user.token_version = (user.token_version or 0) + 1
    db.session.commit()

    return jsonify({'message': 'Password changed successfully', 'token': _generate_token(user)})

def _generate_token(user) -> str:
    payload = {
        'user_id': user.id,
        'role': 'customer',
        'tv': user.token_version or 0,
        'exp': datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')
