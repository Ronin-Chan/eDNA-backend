from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from app.config import Config
from app.database import db
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS
    CORS(app)

    # Configure JWT
    JWTManager(app)

    # Initialize database
    db.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Home route
    @app.route('/')
    def home():
        return {"message": "Welcome to the EDNA Web App"}
    
    @app.route('/health', methods=['GET'])
    def health():
        return {"status": "healthy"}, 200
    
    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

    return app
