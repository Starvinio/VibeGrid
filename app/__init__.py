from flask import Flask, session
from flask_session import Session

from app.helpers import darken_hex, formatDate
from app.models import User
from app.error_handlers import register_error_handlers
from app.limiter import limiter


from app.extensions import db, socketio
from app.routes import register_blueprints
from app.utils import  are_friends, hasUnreads, get_friend_list, getPostVoteRatio, getUserPostVote, findUserByID, determine_relationship

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")
    db.init_app(app) # Attatches Independent Object to app

    with app.app_context():
        db.create_all()


    socketio.init_app(app)
    limiter.init_app(app)
    Session(app)
    register_blueprints(app)
    register_error_handlers(app)


    @app.context_processor
    def inject_utilities():
        current_user = None
        if session.get("user_id"):
            try:
                current_user = User.query.filter_by(id=session["user_id"]).first()
                # If user doesn't exist in database, clear the invalid session
                if not current_user:
                    session.clear()
            except Exception:
                # Clear session if database query fails
                session.clear()
                current_user = None

        return dict(
            current_user=current_user,
            darken_hex=darken_hex,
            are_friends=are_friends,
            hasUnreads=hasUnreads,
            get_friend_list=get_friend_list,
            formatDate=formatDate,
            getPostVoteRatio=getPostVoteRatio,
            getUserPostVote=getUserPostVote,
            findUserByID=findUserByID,
            determine_relationship=determine_relationship
        )

    return app
