from multiprocessing import process
from flask import Blueprint, render_template, request, redirect, session, jsonify
import re

from sqlalchemy.exc import SQLAlchemyError

from app.models import User, Comment
from app.extensions import db
from app.helpers import formatDate, login_required, process_text, formatDate
from app.utils import are_friends, determine_relationship, get_friend_count, get_friend_list, get_post_count, getPostVoteRatio, getUserPostVote, save_image, save_audio, delete_file, userPostFilter
from app.config import Config
from app.exceptions import DatabaseError, RestrictedError, UserNotFound, FileuploadError, ValidationError



user_bp = Blueprint("user", __name__)


@user_bp.route("/user", methods=["GET"])
@login_required
def user():
    current_user = User.query.filter_by(id=session["user_id"]).first()

    username = request.args.get("u")

    if username:
        user = User.query.filter_by(username=username).first()
        if not user:
            raise UserNotFound(username)
        
        if user.id == current_user.id:
            return redirect("/profile")
    
        posts = userPostFilter(filterKey=request.args.get("filter"), user_id=user.id) 

        for post in posts:
            print(post.data)


        are_friends_var = are_friends(user.id)
        can_comment = False
        if are_friends_var and not Comment.query.filter_by(user_id=current_user.id, profile_id=user.id).first():
            can_comment = True



        return render_template("user.html", user=user, posts=posts, current_filter=request.args.get("filter"), relationship=determine_relationship(user.id), friend_count=get_friend_count(user.id), friend_list=get_friend_list(user.id), post_count=get_post_count(user.id), getPostVoteRatio=getPostVoteRatio, getUserPostVote=getUserPostVote, route=request.path, are_friends_var=are_friends_var, can_comment=can_comment)

    else:
        return redirect("/profile")

@user_bp.route("/add_profile_comment", methods=["POST"])
@login_required
def add_profile_comment():
    user_id = session["user_id"]
    data = request.get_json()
    raw_content = data["content"]
    profile_id = data["profile_id"]

    if not raw_content:
        raise ValidationError("Missing content")
    
    content = process_text(raw_content)

    if not profile_id:
        raise ValidationError("Missing profile")

    if not User.query.filter_by(id=profile_id).first():
        raise UserNotFound(f"id:{profile_id}")
    
    if not are_friends(profile_id) or Comment.query.filter_by(user_id=user_id, profile_id=profile_id).first():
        raise RestrictedError("No Permission To Comment")

    max_comments = Config.MAX_PROFILE_COMMENTS
    if len(Comment.query.filter_by(profile_id=profile_id).all()) >= max_comments:
        raise ValidationError(f"Limit of {max_comments} has been reached")

    new_profile_comment = Comment(user_id = user_id, profile_id = profile_id, data=content)

    try:
        db.session.add(new_profile_comment)
        db.session.commit()
        return jsonify(
            {
            "status_code": 200, 
            "message": "Comment Upload Successful", 
            "comment":content, 
            "date":formatDate(new_profile_comment.date), 
            "id":new_profile_comment.id
            })
    except SQLAlchemyError:
        raise DatabaseError("add_profile_comment()")




@user_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    current_user_id = session["user_id"]
    filter = request.args.get("filter")
    
    posts = userPostFilter(filterKey=filter, user_id=current_user_id)

    friend_count = get_friend_count(current_user_id)
    post_count = get_post_count(current_user_id)
    friend_list = get_friend_list(current_user_id)
    

    return render_template("user.html", posts=posts, current_filter=filter, friend_count=friend_count, friend_list=friend_list, post_count=post_count, route=request.path, are_friends_var=False, can_comment=False)
    


@user_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    current_user = User.query.filter_by(id=session["user_id"]).first()
    if request.method == "GET":
        return render_template("settings.html", current_user=current_user, default_tab = current_user.default_home_tab)
    

    # Update Status
    status = request.form.get("status")
    if status:
        if len(status) > 50:
            return render_template("settings.html", current_user=current_user, error="Invalid user status"), 400
        current_user.status = status
    else:
        current_user.status = None


    # Update Bio
    bio = process_text(request.form.get("bio"))
    if bio:
        if len(bio) > 500:
            return render_template("settings.html", current_user=current_user, error="Invalid user bio"), 400
        current_user.bio = bio
    else:
        current_user.bio = None
    

    # Handle Profile Picture Upload

    custom_pfp = request.form.get("use_custom_pfp")
    old_pfp = current_user.pfp_file    
    if custom_pfp:
        try:
            pfp_filename = save_image(request.files.get("pfp_file"), Config.PFP_FOLDER)
            if pfp_filename:
                current_user.pfp_file = pfp_filename
                if old_pfp and old_pfp != pfp_filename:
                    delete_file(old_pfp, Config.PFP_FOLDER)
        except (OSError, IOError, ValueError):
            raise FileuploadError("Profile Picture Upload Failed")
    elif not custom_pfp and old_pfp:
        current_user.pfp_file = None
        delete_file(old_pfp, Config.PFP_FOLDER)
    


    # Handle Background Upload
    custom_bg = request.form.get("use_image")
    old_bg = current_user.bg_file
    if custom_bg:
        try:
            bg_filename = save_image(request.files.get("bg_file"), Config.BG_FOLDER)
            if bg_filename:
                current_user.bg_file = bg_filename
                if old_bg and old_bg != bg_filename:
                    delete_file(old_bg, Config.BG_FOLDER)
        except (OSError, IOError, ValueError):
            raise FileuploadError("Background Image Upload Failed")
    elif not custom_bg and old_bg:
        current_user.bg_file = None
        delete_file(old_bg, Config.BG_FOLDER)


    # Handle Banner Upload
    custom_banner = request.form.get("use_custom_banner")
    old_banner = current_user.banner_file
    if custom_banner:
        try:
            banner_filename = save_image(request.files.get("banner_file_selector"), Config.BANNER_FOLDER)
            if banner_filename:
                current_user.banner_file = banner_filename
                if old_banner and old_banner != banner_filename:
                    delete_file(old_banner, Config.BANNER_FOLDER)
        except (OSError, IOError, ValueError):
            raise FileuploadError("Banner Image Upload Failed")
    elif not custom_banner and old_banner:
        current_user.banner_file = None
        delete_file(old_banner, Config.BANNER_FOLDER)
    

    # Handle Walk In Upload
    custom_walk_in = request.form.get("use_walk_in")
    old_walk_in = current_user.walk_in_file
    if custom_walk_in:
        try:
            walk_in_filename = save_audio(request.files.get("walk_in"), Config.WALK_IN_FOLDER)
            if walk_in_filename:
                current_user.walk_in_file = walk_in_filename
                if old_walk_in and old_walk_in != walk_in_filename:
                    delete_file(old_walk_in, Config.WALK_IN_FOLDER)
        except (OSError, IOError, ValueError):
            raise FileuploadError("Walk In Audio upload failed")
    elif not custom_walk_in and old_walk_in:
        current_user.walk_in_file = None
        delete_file(old_walk_in, Config.WALK_IN_FOLDER)


    # Update Primary Color
    primary_color = request.form.get("primary_color")
    # Check if it's a valid hex color
    if primary_color and re.match(Config.HEX_PATTERN, primary_color):
        current_user.primary_color = primary_color
    
    
    # Update Transparency
    current_user.transparency = True if request.form.get("transparency") else False

    # Update Account Privacy
    current_user.private_account = True if request.form.get("private_account") else False

    # Update Dark Mode
    current_user.dark_mode = True if request.form.get("use_dark_mode") else False

    current_user.hide_profile_customization = True if request.form.get("hide_profile_customization") else False

    #Update Default Tab
    default_tab_selection = request.form.get("default_tab")
    if default_tab_selection and default_tab_selection in ["home", "profile", "messages"]:
        current_user.default_home_tab = default_tab_selection 

    try:
        db.session.commit()
    except Exception:
        raise DatabaseError()
    return redirect("/profile")


def get_profile_comments(user_id:int):
    return Comment.query.filter_by(profile_id=user_id).all()