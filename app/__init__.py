from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app():
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False)
    
    # App Configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///finance_tracker.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    with app.app_context():
        # Import routes
        from app.auth import routes as auth_routes
        from app.transactions import routes as transaction_routes
        from app.dashboard import routes as dashboard_routes
        
        # Register blueprints
        app.register_blueprint(auth_routes.auth_bp)
        app.register_blueprint(transaction_routes.transaction_bp)
        app.register_blueprint(dashboard_routes.dashboard_bp)
        
        # Create database tables if they don't exist
        db.create_all()

        @app.route('/')
        def index():
            return redirect(url_for('dashboard.dashboard'))
        
        return app