from app.routes.auth_routes import auth_bp
from app.routes.user_routes import user_bp
from app.routes.file_routes import file_bp
from app.routes.role_routes import role_bp
from app.routes.farm_routes import farm_bp
from app.routes.visualization_routes import visualization_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix='/auth')    # Auth routes
    app.register_blueprint(user_bp, url_prefix='/user')    # User routes
    app.register_blueprint(file_bp, url_prefix='/file')    # File routes
    app.register_blueprint(role_bp, url_prefix='/role')    # Role routes
    app.register_blueprint(farm_bp, url_prefix='/farm')    # Farm routes
    app.register_blueprint(visualization_bp, url_prefix='/visualization')    # Visualization routes
    
