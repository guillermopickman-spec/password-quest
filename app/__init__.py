"""
Password Quest - Flask Application Factory

Initializes the Flask web application with proper configuration,
security headers, CORS support, and database integration.
"""

import os
from pathlib import Path
from flask import Flask
from flask_cors import CORS

from app.models import db, Badge

def create_app(config_name: str = "development") -> Flask:
    """
    Application factory pattern for creating Flask app instances.
    
    Args:
        config_name: Configuration environment (development, production, testing)
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    
    # Load configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["JSON_SORT_KEYS"] = False
    
    # Database configuration
    instance_path = Path(app.root_path).parent / "instance"
    instance_path.mkdir(exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{instance_path}/password_quest.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Session configuration
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["PERMANENT_SESSION_LIFETIME"] = 365 * 24 * 60 * 60  # 1 year

    # Rate Limiter configuration (removed)

    # Initialize database
    db.init_app(app)
    
    # Create tables and initialize badges
    with app.app_context():
        db.create_all()
        # Initialize badges if they don\"t exist
        from app.progress_service import initialize_badges
        try:
            initialize_badges()
        except Exception:
            pass  # Badges may already exist
    
    # Enable CORS for API endpoints
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["POST", "GET", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Content Security Policy (restrictive for security training app)
        response.headers["Content-Security-Policy"] = (
            "default-src *; "
            "script-src * \'unsafe-inline\' \'unsafe-eval\'; "
            "style-src * \'unsafe-inline\'; "
            "img-src * data:; "
            "font-src *; "
            "connect-src *;"
        )
        return response
    
    # Register blueprints
    from app.routes import main_bp, api_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    
    return app
