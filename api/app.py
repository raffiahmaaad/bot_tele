"""
BotStore API Backend - Main Application

Flask API server for the BotStore multi-tenant SaaS platform.
"""

import sys
import os

# Add api directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta

from config import config
from database import init_database
from routes import auth_bp, bots_bp, products_bp, transactions_bp, broadcast_bp, sheerid_bp


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=config.JWT_ACCESS_TOKEN_EXPIRES)
    
    # Initialize extensions
    CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)
    JWTManager(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(bots_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(broadcast_bp)
    app.register_blueprint(sheerid_bp)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'botstore-api'})
    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'name': 'BotStore API',
            'version': '1.0.0',
            'docs': '/api/docs'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Endpoint tidak ditemukan'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


def main():
    """Main entry point."""
    print("=" * 50)
    print("🚀 BotStore API Backend")
    print("=" * 50)
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("\n❌ Configuration errors:")
        for error in errors:
            print(f"   • {error}")
        print("\n📝 Please set up your .env file with required values.")
        sys.exit(1)
    
    print("\n✅ Configuration loaded")
    
    # Initialize database
    print("\n📦 Initializing database...")
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        sys.exit(1)
    
    # Create and run app
    app = create_app()
    
    port = int(os.getenv('PORT', 5001))
    print(f"\n🌐 Starting server on port {port}...")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    main()
