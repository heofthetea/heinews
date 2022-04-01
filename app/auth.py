from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User
# used for password hashing
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint("auth", __name__)
get_checkbutton = lambda val : val == "on"


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        loggedin = request.form.get("loggedin")
        
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=get_checkbutton(loggedin))
                flash("Anmeldung erfolgreich", category="success")
                return redirect('/')
            else:
                flash("Inkorrektes Password", category="error")
        else:
            flash("Email existiert nicht", category="error")
            
    return render_template("auth/login.html", user=current_user)

"""
template signup method - for production, this needs to be refactored to either only devs being able to add new users
or some form of confirmation for owning a specific role
"""
@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        name = request.form.get("name")
        loggedin = request.form.get("loggedin")
        notifications = request.form.get("notifications")

        user = User.query.filter_by(email=email).first()

        if user:
            flash("Email bereits vergeben", category="error")
        elif len(name) < 2:
            flash("Name muss mindestens 2 Zeichen lang sein", category="error")
        elif password1 != password2:
            flash("Passwörter stimmen nicht überein", category="error")

        else:
            # add user to data base
            new_user = User(email=email,
                            name=name,
                            password=generate_password_hash(password1, method="sha256"),
                            notifications=get_checkbutton(notifications),
                            role="developer")
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user, remember=get_checkbutton(loggedin))
            return redirect("/")
    return render_template("auth/signup.html", user=current_user)


@auth.route("/logout")
def logout():
    logout_user()
    flash("Erfolgreich abgemeldet! Hier kannst Du dich neu anmelden: ", category="success")
    return redirect(url_for("auth.login"))
