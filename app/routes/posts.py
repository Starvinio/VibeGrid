from flask import Blueprint, url_for, request, session, jsonify, render_template

from app.models import User, Post, Vote
from app.helpers import formatDate, login_required, process_text
from app.utils import *
from app.extensions import db
from app.exceptions import NotFoundError
from app.config import Config


posts_bp = Blueprint("posts", __name__)


@posts_bp.route("/", methods=["GET"])
@login_required
def index():
    user_id = session["user_id"]

    filter = request.args.get("filter")

    posts = postFilter(filter)


    return render_template("index.html", posts=posts,get_friend_requests=get_friend_requests(user_id), getPostVoteRatio=getPostVoteRatio,getUserPostVote=getUserPostVote, friend_list=get_friend_list(user_id), post_count=get_post_count(user_id), get_friend_count=get_friend_count(user_id), current_filter=filter)


@posts_bp.route("/post", methods=["GET"])
@login_required
def post():
    
    post_id = request.args.get("p")

    if not post_id:
        raise NotFoundError("Post")
        
    post = Post.query.filter_by(id=post_id).first()

    if not post:
        raise NotFoundError("Post")
    
    user = User.query.filter_by(id = post.user_id).first()

    return render_template("post.html", post=post, getCommentVoteRatio=getCommentVoteRatio,post_votes=getPostVoteRatio(post.id), user_post_vote=getUserPostVote(post.id),getUserCommentVote=getUserCommentVote, user=user)



@posts_bp.route("/request_posts", methods=["POST"])
@login_required
def request_posts():

    data = request.get_json()
    page_nr = data["pageNr"]
    filter = data["filter"]
    user_id = data["user"]

    current_user = User.query.filter_by(id=session["user_id"]).first()

    if user_id: posts = userPostFilter(filterKey=filter, page=page_nr, user_id=user_id)
    else: posts = postFilter(filterKey=filter, page=page_nr)
    
    post_list = []

    default_pic = "default-inverted.png" if current_user.dark_mode else "default.png"

    for post in posts:
        pfp = post.user.pfp_file if post.user.pfp_file else default_pic
        is_current_user = post.user.id == session["user_id"]

        post_list.append(
        {
            "post_id": post.id,
            "pfp": pfp,
            "username": post.user.username,
            "user_id": post.user.id,
            "postDate": formatDate(post.date),
            "postData": post.data,
            "imagePath": url_for('static', filename='post-content/' + post.image_path) if post.image_path else "",
            "voteRatio": getPostVoteRatio(post.id),
            "user_vote": getUserPostVote(post.id),
            "interactions": len(post.votes),
            "comment_count": len(post.comments),
            "is_current_user": is_current_user
            
        })
    
    return jsonify(post_list)



@posts_bp.route("/upload_post", methods=["POST"])
@login_required
def upload_post():

    current_user_id = session["user_id"]

    raw_content = request.form.get("content")
    image = request.files.get("image")

    if not image and not raw_content:
        return jsonify({
            "status": "error",
            "message": "Post content exceeds 500 character limit."
        }), 400

    content = process_text(raw_content) if raw_content else ""

    if len(content) > 500:
        return jsonify({
            "status": "error",
            "message": "Post content exceeds 500 character limit."
        }), 400
    
    post_img_path = None
    if image:
        post_img_path = save_image(image, Config.POST_FOLDER)
    new_post = Post(user_id = current_user_id, data=content, image_path=post_img_path if post_img_path else None)
    
    db.session.add(new_post)
    db.session.commit()


    return jsonify({"status": "success", "message": "Post uploaded"})



@posts_bp.route("/deletePost", methods=["POST"])
@login_required
def deletePost():
    data = request.get_json()
    post_id = data["postId"]
    
    post = Post.query.filter_by(id=post_id, user_id=session["user_id"]).first()

    if post:
        if post.image_path:
            delete_file(post.image_path, "POST_FOLDER")
        db.session.delete(post)
        db.session.commit()

    return jsonify()



@posts_bp.route("/votepost", methods=['POST'])
@login_required
def votepost():
    data = request.get_json()
    post_id = data['post_id']
    direction = data['direction']

    voted_by_user = Vote.query.filter_by(post_id=post_id, user_id=session["user_id"]).first()

    vote_value = 1 if direction == 'up' else -1
    if vote_value:
        if not voted_by_user:
            new_vote = Vote(user_id = session["user_id"], post_id=post_id, value=vote_value)
            db.session.add(new_vote)
        else:
            voted_by_user.value = vote_value

    db.session.commit()

    voteRatio = getPostVoteRatio(post_id)
    interactions = Vote.query.filter_by(post_id=post_id).count()
    
    return jsonify({'vote_count': voteRatio, 'interactions': interactions})

