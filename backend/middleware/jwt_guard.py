import jwt
from functools import wraps
from flask import request, jsonify, current_app, g
from backend.models.user import User
from backend.models.staff import Staff

STAFF_ROLES = ('super_admin', 'admin', 'agent', 'finance')


def _decode():
    """Return (payload, error_response). Signature and expiry are verified here."""
    token = _extract_token()
    if not token:
        return None, (jsonify({'error': 'Authorization token required'}), 401)
    try:
        return jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256']), None
    except jwt.ExpiredSignatureError:
        return None, (jsonify({'error': 'Token expired'}), 401)
    except jwt.InvalidTokenError:
        return None, (jsonify({'error': 'Invalid token'}), 401)


def load_principal(payload):
    """Re-validate a token against the DB. Returns (row, error_response).

    Role, active flag and must_change_password come from the database, never the
    token, and the token must carry the account's current token_version.
    """
    claimed_role = payload.get('role', '')
    model = Staff if claimed_role in STAFF_ROLES else User if claimed_role == 'customer' else None
    row = model.query.get(payload.get('user_id')) if model else None
    if not row or not row.is_active or (row.token_version or 0) != payload.get('tv', 0):
        return None, (jsonify({'error': 'Invalid token'}), 401)
    if model is Staff and row.role.value != claimed_role:
        return None, (jsonify({'error': 'Invalid token'}), 401)
    return row, None


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payload, err = _decode()
        if err:
            return err
        row, err = load_principal(payload)
        if err:
            return err
        g.user_id = row.id
        if isinstance(row, Staff):
            if row.must_change_password:
                return jsonify({'error': 'Password change required', 'must_change_password': True}), 403
            g.role = row.role.value
            g.must_change_password = False
        else:
            g.role = 'customer'
            g.must_change_password = False
        return f(*args, **kwargs)
    return decorated


def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payload, err = _decode()
        if err:
            return err
        if payload.get('role', '') not in STAFF_ROLES:
            return jsonify({'error': 'Staff access required'}), 403
        staff, err = load_principal(payload)
        if err:
            return err
        g.user_id = staff.id
        g.role = staff.role.value
        g.must_change_password = bool(staff.must_change_password)
        # Block any action if password change is required
        if g.must_change_password:
            return jsonify({'error': 'Password change required', 'must_change_password': True}), 403
        return f(*args, **kwargs)
    return decorated


def _extract_token():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None
