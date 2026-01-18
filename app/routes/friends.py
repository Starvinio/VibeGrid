from flask import Blueprint, request, session, jsonify, render_template, redirect
from sqlalchemy import or_, and_

from app.models import User, Friend
from app.extensions import db
from app.helpers import login_required
from app.utils import determine_relationship, get_friend_count, are_friends, get_friend_list, get_post_count


friends_bp = Blueprint("friends", __name__)

@friends_bp.route("/friends")
@login_required
def friends():
    current_user = User.query.filter_by(id=session["user_id"]).first()
    if request.method == "GET":
        username = request.args.get("u")

        if not username:
            return render_template("friends.html", get_friend_count=get_friend_count, friend_list=get_friend_list(current_user.id), get_post_count=get_post_count, are_friends=are_friends)
        
        if username == current_user.username:
            return redirect ("/friends")
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return render_template("error.html", error=[404, "User not found"])
        

        return render_template("friends.html", user=user, get_friend_count=get_friend_count, friend_list=get_friend_list(user.id), get_post_count=get_post_count, are_friends=are_friends)


@friends_bp.route("/friend_actions", methods=["POST"])
@login_required
def friend_actions():
    data = request.get_json()
    current_user = User.query.filter_by(id=session["user_id"]).first()
    other = User.query.filter_by(id=data["otherId"]).first()
    action = data["action"]

    print(f"{session['user_id']} and {other.id} are currently {determine_relationship(other.id)}.")

    relationship = Friend.query.filter(
        or_(
        and_(Friend.a==session["user_id"], Friend.b==other.id), 
        and_(Friend.a==other.id, Friend.b==session["user_id"])
        )
    ).first()

    if relationship:
        if relationship.status == "pending" and relationship.a == other.id and action == "accept":
            relationship.status = "accepted"
        elif action == "remove":
            db.session.delete(relationship)
    elif action == "add":
        db.session.add(Friend(a=session["user_id"], b=other.id))

    db.session.commit()

    print(f"{session['user_id']} and {other.id} are now {determine_relationship(other.id)}.")

    if other.pfp_file:
        pfp = other.pfp_file
    else: pfp = "default-inverted.png" if current_user.dark_mode else "default.png"

    return jsonify({"updated_status": determine_relationship(other.id), 'other_username':other.username, 'pfp':pfp})