from flask import Flask
from app.config import Config
from app.services.rag_service import initialize_rag_chain

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register Blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Initialize RAG Chain
    with app.app_context():
        initialize_rag_chain()
        
    return app
