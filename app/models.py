from app.extensions import db
from datetime import datetime

# DATABASE CLASSES

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    value = db.Column(db.Integer, nullable=False)  # +1 or -1

    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_post_vote'),
        db.UniqueConstraint('user_id', 'comment_id', name='unique_comment_vote'),
    )


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    data = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    votes = db.relationship("Vote", backref="comment", cascade="all, delete-orphan")


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image_path = db.Column(db.String(100))
    
    comments = db.relationship('Comment', backref="post", cascade="all, delete-orphan")
    votes = db.relationship("Vote", backref="post", cascade="all, delete-orphan")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chat.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    data = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(100))
    read = db.Column(db.Boolean, default=False, nullable=False)


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    a = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    b = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    messages = db.relationship("Message", backref="chat", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint('a', 'b', name='unique_chat_pair'),
    )


class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    a = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    b = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(8), default="pending")
    date = db.Column(db.DateTime, default=datetime.now)


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    accountcreated = db.Column(db.DateTime, default=datetime.now)

    status = db.Column(db.String(50))
    bio = db.Column(db.String(500))
    pfp_file = db.Column(db.String(100), nullable=True)
    banner_file = db.Column(db.String(100))
    bg_file = db.Column(db.String(100))
    walk_in_file = db.Column(db.String(100))
    transparency = db.Column(db.Boolean, default=False, nullable=False)
    primary_color = db.Column(db.String, default="#3985f8", nullable=False)
    dark_mode = db.Column(db.Boolean, default=False, nullable=False)
    private_account = db.Column(db.Boolean, default=False, nullable=False)
    default_home_tab = db.Column(db.String, default="Home", nullable=False)
    hide_profile_customization = db.Column(db.Boolean, default=False)

    posts = db.relationship('Post', backref="user", cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='user', cascade="all, delete-orphan", foreign_keys='Comment.user_id')
    votes = db.relationship('Vote', backref='user', cascade="all, delete-orphan")

    profile_comments = db.relationship('Comment', backref="profile", cascade="all, delete-orphan", foreign_keys='Comment.profile_id')
    
    chats = db.relationship('Chat', primaryjoin='or_(User.id==Chat.a, User.id==Chat.b)',
                              cascade="all, delete-orphan")
    messages = db.relationship('Message', backref='user', cascade="all, delete-orphan")
    

    friends = db.relationship('Friend',
                              primaryjoin='or_(User.id==Friend.a, User.id==Friend.b)',
                              cascade="all, delete-orphan")