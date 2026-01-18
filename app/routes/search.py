
from flask import Blueprint, render_template, jsonify, session, request
from sqlalchemy import exc

from app.exceptions import ValidationError, DatabaseError
from app.helpers import login_required, formatDate, process_text
from app.models import Post, User
from app.utils import get_friend_count, get_post_count, are_friends, findUserByID
from app.config import Config

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=["GET"])
@login_required
def search_user():
    current_user = User.query.filter_by(id=session["user_id"]).first()
    if current_user.primary_color == "#3985f8":
        logo = Config.SEARCH_LOGO_PRIMARY_DARK if current_user.dark_mode else Config.SEARCH_LOGO_PRIMARY_LIGHT
    else:
        logo = Config.SEARCH_LOGO_BW_DARK if current_user.dark_mode else Config.SEARCH_LOGO_BW_LIGHT
    return render_template("search.html", logo=logo)


@search_bp.route("/search_query", methods=["POST"])
@login_required
def search_query():
    
    current_user = User.query.filter_by(id=session["user_id"]).first()

    data = request.get_json()
    if not data:
            raise ValidationError("No JSON data provided")

    query = data["query"]
    if not query:
            raise ValidationError("Search query is required")
    
    if len(query.strip()) < 1:
            raise ValidationError("Search query cannot be empty")

    sanitized_query = process_text(query.strip())

    try:
        query_result_users = User.query.filter(User.username.ilike(f"%{sanitized_query}%")).limit(10).all()

        query_result_posts = Post.query.filter(Post.data.ilike(f"%{sanitized_query}%")).limit(20).all()
    except Exception:
        raise DatabaseError()
    
    query_results = []
    default_pic = "default-inverted.png" if current_user.dark_mode else "default.png"

    try:
        for user in query_result_users:
            query_results.append({
                "username": user.username,
                "pfp_file": user.pfp_file if user.pfp_file else default_pic,
                "friend_count": get_friend_count(user.id),
                "post_count": get_post_count(user.id),
                "isFriend": are_friends(user.id),
                "type":"user"
            })

        for post in query_result_posts:
            post_user = findUserByID(post.user_id)
            if not post_user.private_account or are_friends(post_user.id):
            
                query_results.append({
                "post_username": post_user.username,
                "post_pfp": post.user.pfp_file if post.user.pfp_file else default_pic,
                "content": post.data,
                "post_date": formatDate(post.date),
                "post_id": post.id,
                "type":"post"

            })
            
        return jsonify(query_results)
    except Exception:
        raise DatabaseError



