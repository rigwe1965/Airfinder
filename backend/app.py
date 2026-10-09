from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
from backend.config import Config
from backend.models.database import init_db
from backend.extensions import limiter, mail

# No inline scripts or handlers are allowed (see frontend/js/csp-actions.js). Styles keep
# 'unsafe-inline' because pages use style="" attributes; Google Fonts is the only third party.
CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)


def create_app():
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                static_folder=os.path.join(_base, 'frontend'),
                static_url_path='',
                instance_path=os.path.join(_base, 'instance'))
    app.config.from_object(Config)

    _weak = {'dev-secret-key', 'dev-jwt-secret', 'Admin@2024!'}
    for key in ('SECRET_KEY', 'JWT_SECRET', 'SUPER_ADMIN_EMAIL', 'SUPER_ADMIN_PASSWORD'):
        val = app.config.get(key)
        if not val:
            raise RuntimeError(f'{key} must be set (see .env.example / Render env vars)')
        if not Config.IS_DEV and (val in _weak or (key != 'SUPER_ADMIN_EMAIL' and len(val) < 12)):
            raise RuntimeError(f'{key} is missing or too weak for production')

    allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000').split(',')
    CORS(app, resources={r'/api/*': {'origins': [o.strip() for o in allowed_origins]}})
    limiter.init_app(app)
    mail.init_app(app)

    init_db(app)

    from backend.routes import auth_customer, auth_staff, flights, bookings, admin, staff_mgmt
    app.register_blueprint(auth_customer.bp)
    app.register_blueprint(auth_staff.bp)
    app.register_blueprint(flights.bp)
    app.register_blueprint(bookings.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(staff_mgmt.bp)

    @app.route('/api/demo-request', methods=['POST'])
    @limiter.limit('3 per hour')
    def demo_request():
        from flask import request
        import json, datetime
        data = request.get_json(silent=True) or {}
        entry = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'name': str(data.get('name', ''))[:100],
            'company': str(data.get('company', ''))[:100],
            'email': str(data.get('email', ''))[:150],
            'phone': str(data.get('phone', ''))[:40],
            'message': str(data.get('message', ''))[:1000],
        }
        log_path = os.path.join(os.path.dirname(__file__), '..', 'demo_requests.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        print(f"[DEMO REQUEST] {entry['name']} <{entry['email']}> — {entry['company']}")
        return jsonify({'message': 'Request received'}), 201

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/auth/<path:filename>')
    def auth_pages(filename):
        return send_from_directory(os.path.join(app.static_folder, 'auth'), filename)

    @app.route('/account/<path:filename>')
    def account_pages(filename):
        return send_from_directory(os.path.join(app.static_folder, 'account'), filename)

    @app.route('/admin/<path:filename>')
    def admin_pages(filename):
        return send_from_directory(os.path.join(app.static_folder, 'admin'), filename)

    @app.after_request
    def security_headers(resp):
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        resp.headers['X-Frame-Options'] = 'DENY'
        resp.headers['Referrer-Policy'] = 'same-origin'
        resp.headers['Content-Security-Policy'] = CSP
        if not Config.IS_DEV:
            resp.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return resp

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=Config.PORT, debug=Config.IS_DEV)
