from flask import request, jsonify, session, Blueprint

from app.models import User, Comment, Vote
from app.extensions import db
from app.helpers import login_required, process_text, formatDate
from app.utils import getCommentVoteRatio
from app.config import Config


comments_bp = Blueprint("comments", __name__)

@comments_bp.route("/postComment", methods=["POST"])
@login_required
def postComment():
    data = request.get_json()
    postID = data['postID']
    userID = data['userID']
    content = process_text(data['content'])
    if postID and userID and content:
        new_comment = Comment(post_id=postID, data=content, user_id=userID)

        db.session.add(new_comment)
        db.session.commit()

        current_user = User.query.filter_by(id=userID).first()

        if current_user.pfp_file:
            pfp = f"/static/profile-pics/{current_user.pfp_file}"
        else: 
            pfp = Config.DEFAULTPIC_INVERTED if current_user.dark_mode else Config.DEFAULTPIC 

        return jsonify({'date': formatDate(new_comment.date), 'pfp': pfp, 'comment_id':new_comment.id, 'content':content})
    
    else: return jsonify({
            "status": "error",
            "message": "Post content exceeds 500 character limit."
        }), 400
    


@comments_bp.route("/deleteComment", methods=["POST"])
@login_required
def deleteComment():
    user_id = session["user_id"]
    data = request.get_json()
    comment_id = data["commentId"]
    
    comment = Comment.query.filter_by(id=comment_id).first()
    if comment and comment.user_id == user_id or comment.profile_id == user_id:
        db.session.delete(comment)
        db.session.commit()

        return jsonify({"status_code": 200, "message": "Comment Upload Successful"})
    else: return jsonify({
            "status": "error",
            "message": "Deletion permission not granted"
        }), 403

    



@comments_bp.route("/votecomment", methods=['POST'])
@login_required
def votecomment():
    data = request.get_json()
    comment_id = data['comment_id']
    direction = data['direction']

    voted_by_user = Vote.query.filter_by(comment_id=comment_id, user_id=session["user_id"]).first()

    vote_value = 1 if direction == 'up' else -1
    if vote_value:
        if not voted_by_user:
            new_vote = Vote(user_id = session["user_id"], comment_id=comment_id, value=vote_value)
            db.session.add(new_vote)
        else:
            voted_by_user.value = vote_value

    db.session.commit()

    voteRatio = getCommentVoteRatio(comment_id)
    interactions = Vote.query.filter_by(comment_id=comment_id).count()
    print(interactions)
    
    return jsonify({'vote_count': voteRatio, 'interactions': interactions})
