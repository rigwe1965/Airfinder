import bcrypt
import secrets
import string
from flask import Blueprint, request, jsonify, g
from backend.models.database import db
from backend.models.staff import Staff, StaffRole, can_manage
from backend.middleware.role_guard import require_role
from backend.services.email_service import send_staff_credentials_email

bp = Blueprint('staff_mgmt', __name__, url_prefix='/api/admin/staff')

MANAGEABLE_ROLES = ('super_admin', 'admin')

@bp.route('', methods=['GET'])
@require_role('super_admin', 'admin')
def list_staff():
    staff_list = Staff.query.order_by(Staff.created_at.desc()).all()
    return jsonify([s.to_dict() for s in staff_list])

@bp.route('', methods=['POST'])
@require_role('super_admin', 'admin')
def create_staff():
    data = request.get_json()
    required = ['email', 'first_name', 'last_name', 'role']
    if not all(data.get(f) for f in required):
        return jsonify({'error': f'Required: {", ".join(required)}'}), 400

    try:
        role = StaffRole(data['role'])
    except ValueError:
        return jsonify({'error': f'Invalid role. Valid: {[r.value for r in StaffRole]}'}), 400

    actor_role = StaffRole(g.role)
    if actor_role != StaffRole.SUPER_ADMIN and not can_manage(actor_role, role):
        return jsonify({'error': 'Cannot assign a role equal to or above your own'}), 403

    if Staff.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already registered'}), 409

    temp_password = (data.get('temp_password') or '').strip()
    if temp_password:
        if len(temp_password) < 8:
            return jsonify({'error': 'Temporary password must be at least 8 characters'}), 400
    else:
        temp_password = _generate_temp_password()
    hashed = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt())

    staff = Staff(
        email=data['email'].lower(),
        password_hash=hashed.decode('utf-8'),
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=role,
        must_change_password=True,
        is_active=True,
        created_by=g.user_id,
    )
    db.session.add(staff)
    db.session.commit()

    send_staff_credentials_email(staff.email, staff.first_name, role.value, temp_password)

    return jsonify({
        'message': 'Staff account created. Credentials sent to email.',
        'staff': staff.to_dict(),
        'temp_password': temp_password,
    }), 201

@bp.route('/<staff_id>', methods=['GET'])
@require_role('super_admin', 'admin')
def get_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    return jsonify(staff.to_dict())

@bp.route('/<staff_id>', methods=['PUT'])
@require_role('super_admin', 'admin')
def update_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    actor_role = StaffRole(g.role)

    if actor_role != StaffRole.SUPER_ADMIN and not can_manage(actor_role, staff.role):
        return jsonify({'error': 'Cannot modify staff with equal or higher role'}), 403

    data = request.get_json()

    if 'role' in data:
        try:
            new_role = StaffRole(data['role'])
        except ValueError:
            return jsonify({'error': 'Invalid role'}), 400
        if not can_manage(actor_role, new_role):
            return jsonify({'error': 'Cannot assign role equal to or above your own'}), 403
        if new_role != staff.role:
            staff.token_version = (staff.token_version or 0) + 1
        staff.role = new_role

    if 'email' in data:
        new_email = data['email'].lower().strip()
        if new_email != staff.email:
            if Staff.query.filter_by(email=new_email).first():
                return jsonify({'error': 'Email already in use'}), 409
            staff.email = new_email
            staff.token_version = (staff.token_version or 0) + 1
    if 'first_name' in data:
        staff.first_name = data['first_name']
    if 'last_name' in data:
        staff.last_name = data['last_name']
    if 'is_active' in data:
        new_active = bool(data['is_active'])
        if not new_active and staff.id == g.user_id:
            return jsonify({'error': 'Cannot deactivate your own account'}), 400
        if new_active != staff.is_active:
            staff.token_version = (staff.token_version or 0) + 1
        staff.is_active = new_active

    db.session.commit()
    return jsonify(staff.to_dict())

@bp.route('/<staff_id>/reset-password', methods=['POST'])
@require_role('super_admin', 'admin')
def reset_staff_password(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    actor_role = StaffRole(g.role)

    if actor_role != StaffRole.SUPER_ADMIN and not can_manage(actor_role, staff.role):
        return jsonify({'error': 'Cannot reset password for staff with equal or higher role'}), 403

    temp_password = _generate_temp_password()
    hashed = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt())
    staff.password_hash = hashed.decode('utf-8')
    staff.must_change_password = True
    staff.token_version = (staff.token_version or 0) + 1
    db.session.commit()

    send_staff_credentials_email(staff.email, staff.first_name, staff.role.value, temp_password)

    return jsonify({
        'message': 'Password reset. New credentials sent to staff email.',
        'temp_password': temp_password,
    })

@bp.route('/<staff_id>', methods=['DELETE'])
@require_role('super_admin')
def delete_staff(staff_id):
    if staff_id == g.user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    staff = Staff.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    return jsonify({'message': 'Staff account permanently deleted'})

def _generate_temp_password():
    chars = string.ascii_letters + string.digits + '!@#$%'
    return ''.join(secrets.choice(chars) for _ in range(12))
