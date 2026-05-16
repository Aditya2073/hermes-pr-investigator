from flask import Flask
from src.routes.api import api_bp
from src.routes.login import login_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    app.register_blueprint(login_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
