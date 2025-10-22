from flask import Flask
from flask_session import Session
from dotenv import load_dotenv
import os

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

    app.config.from_object('app.config.Config')
    Session(app)  # Uses filesystem session

    # Register blueprints
    from app.routes.chat_routes import chat_bp
    app.register_blueprint(chat_bp)

    # Error handling setup
    @app.errorhandler(400)
    def bad_request_error(e):
        return {"error": "Bad Request", "message": str(e)}, 400

    @app.errorhandler(404)
    def not_found_error(e):
        return {"error": "Resource Not Found"}, 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"Internal error: {e}")
        return {"error": "Internal Server Error"}, 500

    return app
