import json
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from app.exceptions import ValidationError, DatabaseError
from app.models import User
from app import db
from app.helpers import login_required
from app.utils import validate_registration, get_default_tab



auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login",methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    username = request.form.get("username")
    password = request.form.get("password")
    if not username or not password:
        raise ValidationError("Please enter both username and password")

    user = User.query.filter_by(username=username).first()
    if not user:
        return render_template("login.html", error="User not found")
    if not check_password_hash(user.password, password):
        return render_template("login.html", error="Incorrect Password")
    
    session["user_id"] = user.id

    if user.default_home_tab == "Home": return redirect("/")
    else: return redirect(f"/{user.default_home_tab}")


@auth_bp.route("/check_login_data", methods=["POST"])
def check_login_data():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            raise ValidationError("Please enter both username and password")
        
        user = User.query.filter_by(username=username).first()
        if not user:
            raise ValidationError("User not found")
        if not check_password_hash(user.password, password):
            raise ValidationError("Incorrect Password")
        
        session["user_id"] = user.id
        redirect_to = get_default_tab()
        return jsonify({"status_code": 200, "message": "Login successful", "redirect": redirect_to})
    except Exception as e:
        # Log the error for debugging
        print(f"Login error: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        else:
            raise DatabaseError("Login failed due to server error")
        
@auth_bp.route("/check_register_data", methods=["POST"])
def check_register_data():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        confirmation = data.get("confirmation")

        error = validate_registration(username, password, confirmation)
        if error:
            raise ValidationError(error)

        #Adding user to db
        new_user = User(username = username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        session["user_id"] = new_user.id
        return jsonify({"status_code": 200, "message": "Login successful"})
    except Exception as e:
        print(f"Login error: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        else:
            raise DatabaseError("Login failed due to server error")



@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))



@auth_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    #REGISTER CHECKING
    
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    error = validate_registration(username, password, confirmation)
    if error:
        return render_template("register.html", error=error)

    #Adding user to db
    new_user = User(username = username, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    session["user_id"] = new_user.id
    return redirect("/profile")


