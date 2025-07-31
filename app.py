import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database with performance optimizations
database_url = os.environ.get("DATABASE_URL", "sqlite:///instance/linebot.db")

# Enhanced database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Reduce overhead
app.config["SQLALCHEMY_RECORD_QUERIES"] = False  # Disable query recording in production

# Determine database type for optimization
is_postgres = database_url.startswith('postgresql')
is_sqlite = database_url.startswith('sqlite')

# Database-specific optimizations
if is_postgres:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 20,  # Connection pool size
        "pool_recycle": 3600,  # Recycle connections every hour
        "pool_pre_ping": True,  # Verify connections before use
        "pool_timeout": 30,  # Connection timeout
        "max_overflow": 40,  # Max overflow connections
        "connect_args": {
            "connect_timeout": 10,
            "application_name": "thai_sme_linebot",
            "options": "-c default_transaction_isolation=read_committed"
        }
    }
elif is_sqlite:
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 5,  # Smaller pool for SQLite
        "connect_args": {
            "timeout": 20,
            "check_same_thread": False  # Allow multiple threads
        }
    }
else:
    # Default configuration
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

# Initialize the app with the extension
db.init_app(app)

# Register blueprints
from routes.webhook import webhook_bp
from routes.admin import admin_bp

app.register_blueprint(webhook_bp)
app.register_blueprint(admin_bp)

with app.app_context():
    # Import models to ensure tables are created
    import models  # noqa: F401
    
    # Create all tables with indexes
    db.create_all()
    
    # Additional database optimizations for PostgreSQL
    if is_postgres:
        try:
            # Enable database statistics collection for query optimization
            db.session.execute("ANALYZE;")
            db.session.commit()
            logging.info("Database statistics updated for PostgreSQL")
        except Exception as e:
            logging.warning(f"Could not update database statistics: {e}")
    
    # SQLite optimizations
    elif is_sqlite:
        try:
            # Enable WAL mode for better concurrency
            db.session.execute("PRAGMA journal_mode=WAL;")
            # Optimize for performance
            db.session.execute("PRAGMA synchronous=NORMAL;")
            db.session.execute("PRAGMA cache_size=10000;")
            db.session.execute("PRAGMA temp_store=memory;")
            db.session.execute("PRAGMA mmap_size=268435456;")  # 256MB
            db.session.commit()
            logging.info("SQLite performance optimizations applied")
        except Exception as e:
            logging.warning(f"Could not apply SQLite optimizations: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
