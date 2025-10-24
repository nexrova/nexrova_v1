"""
Main Flask Application Entry Point for Hotel PMS
"""
from flask import Flask
from config import Config

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Register blueprints
    from routes.web_routes import web_bp
    from routes.api_routes import api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

if __name__ == '__main__':
    # Validate configuration
    Config.validate()

    # Create app
    app = create_app()

    print(f"\n{'='*60}")
    print(f"  Hotel PMS Server Starting")
    print(f"{'='*60}")
    print(f"  Hotel: {Config.HOTEL_INFO['name']}")
    print(f"  Location: {Config.HOTEL_INFO['location']}")
    print(f"  Running on: http://{Config.HOST}:{Config.PORT}")
    print(f"  Debug mode: {Config.DEBUG}")
    print(f"{'='*60}\n")

    # Run app
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
