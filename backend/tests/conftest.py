import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app import create_app
from backend.models.database import db as _db

@pytest.fixture(scope='session')
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET'] = 'test-secret'
    return app

@pytest.fixture(scope='session')
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def clean_db(app):
    from backend.extensions import limiter
    limiter.reset()
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        from backend.models.database import _seed_super_admin
        _seed_super_admin(app)
    yield
    with app.app_context():
        _db.session.remove()
