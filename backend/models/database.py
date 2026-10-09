from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect as sa_inspect

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        from backend.models import user, staff, booking  # noqa: F401
        db.create_all()
        _migrate_existing(app)
        _seed_super_admin(app)

def _migrate_existing(app):
    """Add columns introduced after initial schema without dropping data."""
    inspector = sa_inspect(db.engine)
    tables = set(inspector.get_table_names())
    additions = []

    def cols(table):
        return {c['name'] for c in inspector.get_columns(table)} if table in tables else None

    bookings = cols('bookings')
    if bookings is not None:
        if 'group_reference' not in bookings:
            additions.append('ALTER TABLE bookings ADD COLUMN group_reference VARCHAR(20)')
        if 'is_multicity' not in bookings:
            additions.append('ALTER TABLE bookings ADD COLUMN is_multicity BOOLEAN DEFAULT 0')
    staff = cols('staff')
    if staff is not None:
        if 'reset_token' not in staff:
            additions.append('ALTER TABLE staff ADD COLUMN reset_token VARCHAR(64)')
        if 'reset_token_expires' not in staff:
            additions.append('ALTER TABLE staff ADD COLUMN reset_token_expires DATETIME')
        if 'token_version' not in staff:
            additions.append('ALTER TABLE staff ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0')
    users = cols('users')
    if users is not None and 'token_version' not in users:
        additions.append('ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0')
    if additions:
        with db.engine.connect() as conn:
            for stmt in additions:
                conn.execute(text(stmt))
            conn.commit()

def _seed_super_admin(app):
    from backend.models.staff import Staff, StaffRole
    from backend.config import Config
    import bcrypt

    if Staff.query.filter_by(role=StaffRole.SUPER_ADMIN).first():
        return

    hashed = bcrypt.hashpw(Config.SUPER_ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt())
    super_admin = Staff(
        email=Config.SUPER_ADMIN_EMAIL,
        password_hash=hashed.decode('utf-8'),
        first_name='Super',
        last_name='Admin',
        role=StaffRole.SUPER_ADMIN,
        must_change_password=True,
        is_active=True
    )
    db.session.add(super_admin)
    db.session.commit()
    print(f"[SEED] Super admin created: {Config.SUPER_ADMIN_EMAIL}")
