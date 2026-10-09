import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from backend.app import create_app
from backend.config import Config

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=Config.PORT, debug=Config.IS_DEV, use_reloader=False)
