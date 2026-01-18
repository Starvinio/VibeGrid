
# Blueprints 
from .auth import auth_bp
from .user import user_bp
from .posts import posts_bp
from .friends import friends_bp
from .messages import messages_bp
from .search import search_bp
from .comments import comments_bp

def register_blueprints(app):
    """
    Attach all blueprint objects to the main Flask app.
    This keeps your route registration in one clean place.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(comments_bp)