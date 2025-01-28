from flask import Flask
from app.config import Config
from app.database import db
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Register all blueprints
    register_blueprints(app)

    return app
