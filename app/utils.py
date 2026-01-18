
from flask import session
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
import os

from app.models import User, Friend, Post, Vote, Message, Chat
from app.helpers import allowed_pic, allowed_audio
from app.extensions import db
from app.exceptions import FileuploadError
from app.config import Config
from sqlalchemy.exc import SQLAlchemyError
import logging


def validate_registration(username:str, password:str, confirmation:str):
    if not username:
        return "Please enter a username"
    if not password:
        return "Please enter a password"
    if " " in username or " " in password:
        return "Invalid Character: ' '"
    if not confirmation or password != confirmation:
        return "Passwords do not match"
    if len(username) < 3 or len(username) > 30:
        return "Username must contain 3 to 30 characters"
    if len(password) < 8 or len(password) > 50:
        return "Password must contain 8 to 50 characters"
    if not (username + password + confirmation).isascii():
        return "Invalid Characters"
    try:
        if User.query.filter_by(username=username).first():
            return "Username already taken, please choose another"
    except SQLAlchemyError as e:
        logging.error(f"DB error in validate_registration: {e}")
        return "Database error. Please try again later."
    return None  # No errors



def save_image(file, folder):
    try:
        # Check file size (in bytes)
        file.seek(0, 2)  # Go to end of file
        file_size = file.tell()  # Get current position (file size)
        file.seek(0)  # Reset to beginning
        
        if file_size > 5 * 1024 * 1024:  # 5MB limit
            raise FileuploadError("File too large (max 5MB)")

        if file and allowed_pic(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"user_{session['user_id']}_{filename}"
            file_path = os.path.join(folder, unique_filename)
            file.save(file_path)

            return unique_filename
    except (OSError, ValueError):
        raise FileuploadError()



def save_audio(file, folder):
    try:
        if file and allowed_audio(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"user_{session['user_id']}_{filename}"
            file_path = os.path.join(folder,unique_filename)
            file.save(file_path)

            return unique_filename
    except Exception:
        raise FileuploadError()
        


def delete_file(filename, folder):
    try:
        file_path = os.path.join(folder, filename)
        if os.path.exists(file_path): os.remove(file_path)
    except OSError:
        raise FileuploadError()



def get_friend_list(user_id:int):
    friend_list = []
    try:
        relationships = Friend.query.filter(
            or_(
                Friend.a == user_id, Friend.b == user_id
            )
        )
        for relationship in relationships:
            if relationship.status == "accepted":
                try:
                    if relationship.a == user_id:
                        is_friend = User.query.filter_by(id=relationship.b).first()
                    else:
                        is_friend = User.query.filter_by(id=relationship.a).first()
                    friend_list.append(is_friend)
                except SQLAlchemyError as e:
                    logging.error(f"DB error in get_friend_list (User lookup): {e}")
    except SQLAlchemyError as e:
        logging.error(f"DB error in get_friend_list: {e}")
        return []
    return friend_list



def determine_relationship(other_id:int):
    
    relationship = Friend.query.filter(
        or_(
            and_(Friend.a == session["user_id"], Friend.b == other_id,), 
            and_(Friend.b == session["user_id"], Friend.a == other_id,)
            )
        ).first()

    if relationship:
        if relationship.status == "accepted":
            return "accepted"
        elif relationship.status == "pending" and relationship.b == session["user_id"]:
            return "pending-accept"
        else:
            return "pending-waiting"
    else:
        return "none"



def findUserByID(user_id:int):
    return User.query.filter_by(id=user_id).first()



def get_friend_requests(user_id:int):
    friend_requests = []
    all_pending = Friend.query.filter_by(b=user_id, status="pending").all()
    for user in all_pending:
        friend_requests.append(User.query.filter_by(id=user.a).first())
    return friend_requests



def get_friend_count(user_id:int):
    return Friend.query.filter(and_(Friend.status == "accepted", or_(Friend.a == user_id, Friend.b == user_id))).count()



def are_friends(other_id:int):
    relationship = Friend.query.filter(
        or_(
            and_(Friend.a==session["user_id"], Friend.b==other_id,), 
            and_(Friend.b==session["user_id"], Friend.a==other_id,)
            )
        ).first()
    
    return True if relationship and relationship.status == "accepted" else False



def get_mutuals(other_id:int):
    friend_list_current_user = get_friend_list(session["user_id"])
    friend_list_other = get_friend_list(other_id)

    current_user_ids = {friend.id for friend in friend_list_current_user}
    other_user_ids = {friend.id for friend in friend_list_other}

    return len(current_user_ids & other_user_ids)



def get_post_count(user_id:int):
    return Post.query.filter_by(user_id=user_id).count()



def getPostVoteRatio(post_id:int):
    upvotes= Vote.query.filter_by(post_id=post_id, value=1).count()
    downvotes = Vote.query.filter_by(post_id=post_id, value=-1).count()
    return (upvotes - downvotes)


def getCommentVoteRatio(comment_id:int):
    upvotes= Vote.query.filter_by(comment_id=comment_id, value=1).count()
    downvotes = Vote.query.filter_by(comment_id=comment_id, value=-1).count()
    return (upvotes - downvotes)



def getUserCommentVote(user_id:int, comment_id:int):
    vote = Vote.query.filter_by(user_id=user_id, comment_id=comment_id).first()
    return vote.value if vote else 0


def getUserPostVote(post_id:int):
    vote = Vote.query.filter_by(user_id = session["user_id"], post_id = post_id).first()
    return vote.value if vote else 0



def getMostRecentMessage(chat_id:int):
    return Message.query.filter_by(chat_id=chat_id).order_by(Message.date.desc()).first()



def hasUnreads(user_id:int):
    if user_id:
        chats = Chat.query.filter(or_(Chat.a == user_id, Chat.b == user_id)).all()
        if chats:
            for chat in chats:
                most_recent = getMostRecentMessage(chat.id)
                if most_recent and most_recent.read == False and most_recent.user_id != user_id:
                    return True
    return False



def postFilter(filterKey=None, page=0, posts_per_page=10):

    offset = page * posts_per_page


    if filterKey == "new-old" or filterKey == None:
        posts = (
            Post.query
            .join(User)
            .filter(User.private_account == False)
            .order_by(Post.date.desc())
            .offset(offset)
            .limit(posts_per_page)
            .all()
        )
    elif filterKey == "old-new":
        posts = (
            Post.query
            .join(User)
            .filter(User.private_account == False)
            .order_by(Post.date.asc())
            .offset(offset)
            .limit(posts_per_page)
            .all()
        )
    elif filterKey == "most-popular":
        posts = (
            Post.query
            .join(User)
            .outerjoin(Vote, Post.id == Vote.post_id)
            .filter(User.private_account == False)
            .group_by(Post.id)
            .order_by(db.func.coalesce(db.func.sum(Vote.value), 0).desc())
            .offset(offset)
            .limit(posts_per_page)
            .all()
        )
    elif filterKey == "friends":
        # Subquery to get all friend user IDs for the current user
        current_user_id = session["user_id"]
        friends_subquery = (
            db.session.query(
                db.case(
                    (Friend.a == current_user_id, Friend.b),
                    else_=Friend.a
                ).label('friend_id')
            )
            .filter(
                db.or_(Friend.a == current_user_id, Friend.b == current_user_id),
                Friend.status == 'accepted'
            )
            .subquery()
        )
        
        posts = (
            Post.query
            .join(User)
            .join(friends_subquery, User.id == friends_subquery.c.friend_id)
            .group_by(Post.id)
            .order_by(Post.date.desc())
            .offset(offset)
            .limit(posts_per_page)
            .all()
        )

    return posts if posts else []


def userPostFilter(filterKey=None, page=0, posts_per_page=20, user_id=0):

    offset = page * posts_per_page

    if filterKey == "new-old" or filterKey == None:
        posts = (
            Post.query
            .join(User)
            .filter(Post.user_id == user_id)
            .order_by(Post.date.desc())
            .offset(offset)
            .limit(posts_per_page)
            .all()
        )
    elif filterKey == "old-new":
        posts = (
            Post.query
            .join(User)
            .filter(Post.user_id == user_id)
            .order_by(Post.date.asc())
            .offset(offset)
            .limit(posts_per_page)
            .all()
        )
    elif filterKey == "most-popular":
        posts = (
            Post.query
            .join(User)
            .outerjoin(Vote, Post.id == Vote.post_id)
            .group_by(Post.id)
            .filter(Post.user_id == user_id)
            .order_by(db.func.coalesce(db.func.sum(Vote.value), 0).desc())
            .offset(offset)
            .limit(posts_per_page)
            .all()
        )

    return posts


def messageFilter(chat_id, msg_per_page=20, page=0):
    offset = page * msg_per_page
    
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.date.desc()).offset(offset).limit(msg_per_page).all()

    return messages[::-1]

def get_default_tab():
    current_user = User.query.filter_by(id=session["user_id"]).first()
    if current_user.default_home_tab == "home": return "/"
    else: return f"/{current_user.default_home_tab}"