from app import create_app
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

class Config:
    SEND_FILE_MAX_AGE_DEFAULT = 0
    PERMANENT_SESSION_LIFETIME = 3600
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "edna-web-app-secret-key")  # Load from environment variable

if __name__ == "__main__":
    app = create_app()

    # Enable CORS for all routes
    CORS(app)
    
    # Apply app configurations
    app.config.from_object(Config)

    # Configure the JWTManager
    jwt = JWTManager(app)

    # Home route
    @app.route('/')
    def home():
        return {"message": "Welcome to the EDNA Web App"}
    
    @app.route('/health', methods=['GET'])
    def health():     
        return {"status": "healthy"}, 200

    app.run(host='0.0.0.0', debug=False)
