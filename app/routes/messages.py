from flask import Blueprint, render_template, jsonify, session, request, redirect
from sqlalchemy import or_, func
from flask_socketio import send

from app.extensions import socketio, db
from app.helpers import formatDate, login_required, darken_hex, process_text
from app.models import Chat, Message, User
from app.utils import messageFilter, get_friend_requests, findUserByID, getMostRecentMessage, get_friend_list, get_post_count, get_friend_count, get_mutuals, are_friends


messages_bp = Blueprint("messages", __name__)

@messages_bp.route("/messages", methods=["GET", "POST"])
@login_required
def messages():
    current_user_id = session["user_id"]

    friend_requests = get_friend_requests(current_user_id)
    

    all_chats = (
    db.session.query(Chat)
    .filter(or_(Chat.a == current_user_id, Chat.b == current_user_id))
    .join(Message, Message.chat_id == Chat.id)
    .group_by(Chat.id)
    .order_by(func.max(Message.date).desc())
    .all()
    )


    return render_template("messages.html", friend_requests=friend_requests, friend_request_count=len(friend_requests), all_chats=all_chats, findUserByID=findUserByID, getMostRecentMessage=getMostRecentMessage, viewAllChats=True, friend_list=get_friend_list(current_user_id), post_count=get_post_count(current_user_id), friend_count=get_friend_count(current_user_id), get_mutuals=get_mutuals)



@messages_bp.route("/chat", methods=["GET"])
@login_required
def chat():
    current_user = User.query.filter_by(id=session["user_id"]).first()

    other_name = request.args.get("with")
    if other_name:
        other = User.query.filter_by(username=other_name).first()

        if other:
            a = other if other.id < current_user.id else current_user
            b = current_user if current_user.id > other.id else other
        
            chat = Chat.query.filter_by(a=a.id, b=b.id).first()
            
            if not chat and are_friends(other.id):
                new_chat = Chat(a=a.id, b=b.id)
                db.session.add(new_chat)
                db.session.commit()

                return redirect(f"/chat?with={other.username}")

            elif chat:
                unread = Message.query.filter_by(chat_id=chat.id, user_id = other.id, read=False).all()
                for message in unread:
                    message.read = True
                    db.session.add(message)
                db.session.commit()
                messages = messageFilter(chat_id=chat.id)

                return render_template("messages.html", other=other, current_chat=chat, messages=messages, are_friends=are_friends(other.id), friend_requests=get_friend_requests(current_user.id), post_count=get_post_count(current_user.id), friend_count=get_friend_count(current_user.id), other_post_count=get_post_count(other.id), other_friend_count=get_friend_count(other.id))
    
    return render_template("error.html", error=[404, "Chat not found"])





@messages_bp.route("/request_messages", methods=["POST"])
@login_required
def request_messages():
    current_user = User.query.filter_by(id=session["user_id"]).first()

    data = request.get_json()
    chat_id = data["chat_id"]
    page = data["page"]

    messages = messageFilter(chat_id=chat_id, page=page)

    message_list = []

    for message in messages:
        if message.user_id == current_user.id:
            background = f"background: linear-gradient(to bottom, {current_user.primary_color}, {darken_hex(current_user.primary_color, 0.8)});"
        else:
            background = "background: linear-gradient(to bottom, #2f2f2f, #2b2b2b)" if current_user.dark_mode else "background: linear-gradient(to bottom, #cccccc, #b1b1b1);"

        message_list.append({
            "user_id": message.user_id,
            "username": message.user.username,
            "date": formatDate(message.date),
            "data": message.data,
            "background": background
        })

    return jsonify(message_list)



@socketio.on('message')
def handle_message(data):
    current_user = User.query.filter_by(id=session["user_id"]).first()
    message_text = process_text(data.get("message"))
    chat_id = data.get("chat_id")

    if message_text and chat_id:
        new_msg = Message(
        chat_id=chat_id,
        user_id=current_user.id,
        data=message_text
    )
        db.session.add(new_msg)
        db.session.commit()

        message_data = {
            'username': current_user.username,
            'primary_color': current_user.primary_color,
            "darken_color": darken_hex(current_user.primary_color, 0.8),
            "date": formatDate(new_msg.date),
            "data": message_text

        }
    print(f"Received Message: {message_text}")
    send(message_data, broadcast=True)