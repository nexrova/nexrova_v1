from flask import Flask
from flask_session import Session
from app.config import Config
import os

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates')
    )
    app.config.from_object(Config)
    
    Session(app)
    
    from app.routes.auth_routes import auth_bp
    from app.routes.chat_routes import chat_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    
    return app
