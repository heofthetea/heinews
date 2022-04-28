from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User, Password_Reset, Verify_Email, generate_id
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, __DEVELOPERS__, __HOST__
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
                return redirect(url_for("views.profile"))
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
            role = "user"
            if is_dev(email):
                role = "developer"

            new_user = User(
                email=email,
                name=name,
                password=generate_password_hash(password1, method="sha256"),
                notifications=get_checkbutton(notifications),
                role=role
            )
            db.session.add(new_user)
            db.session.commit()

            send_verification_email(new_user.email)

            login_user(new_user, remember=get_checkbutton(loggedin))
            flash("Du erhältst demnächst eine Email mit Verifizierungscode. Sobald wir deine Email-Addresse verifiziert haben, hast du \
                Zugriff auf Aktionen wie Upvoten.", category="info")
            return redirect(url_for("views.profile"))
    return render_template("auth/signup.html", user=current_user)


@auth.route("/logout")
def logout():
    logout_user()
    flash("Erfolgreich abgemeldet! Hier kannst Du dich neu anmelden: ", category="success")
    return redirect(url_for("auth.login"))


def is_dev(email):
    for dev in __DEVELOPERS__:
        if check_password_hash(dev, email):
            return True
    return False

#----------------------------------------------------------------------------------------------------------------------------

@auth.route("/reset_link/<int:user_id>") # TODO rename
def create_reset_token(user_id):
    if Password_Reset.query.filter_by(user_id=user_id).first():
        flash("Du hast bereits einen Link zum Zurücksetzen!!", category="error")
    else:
        db.session.add(
            Password_Reset(
                id=generate_id(265, table=Password_Reset),
                user_id=int(user_id)
            )
        )
        db.session.commit()
    return redirect(url_for('views.profile'))



@auth.route("/resetpw/<reset_id>", methods=["GET", "POST"])
#@login_required # TODO keep this or not??
# -> IF PIPELINE WORKS: test with this on, then,
def reset_password(reset_id):
    if request.method == "POST":
        user = User.query.get(Password_Reset.query.get(reset_id).user_id)

        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        if password1 != password2:
            flash("Passwörter stimmen nicht überein", category="error")
        elif check_password_hash(user.password, password1):
            flash("Herzlichen Glückwunsch, du hast dein altes Passwort erraten :)", category="success")
        else:
            user.password = generate_password_hash(password1, method="sha256")
            Password_Reset.query.filter_by(id=reset_id).delete()
            db.session.commit()
            
            flash("Passwort wurde erforlgreich geändert!", category="success")
            return(redirect(url_for("views.profile")))
    return render_template("auth/reset_password.html")



@auth.route("/verify/<verify_id>")
def verify_email(verify_id):
    user = User.query.get(Verify_Email.query.get(verify_id).user_id)
    user.email_confirmed = True

    Verify_Email.query.filter_by(id=verify_id).delete()
    db.session.commit()

    flash("Deine Email wurde erfolgreich verifiziert! Jetzt verfügst du über alle dir zustehenden Freiheiten!", category="success")
    return redirect(url_for("views.profile"))

#----------------------------------------------------------------------------------------------------------------------------

# TODO change return type when actually sending link per email
def send_verification_email(email: str) -> str:
    user = User.query.filter_by(email=email).first()
    if Verify_Email.query.filter_by(user_id=user.id).first():
        return f"{__HOST__}/{url_for('auth.verify_email', verify_id=Verify_Email.query.filter_by(user_id=user.id).first().id)}"
    
    verification_token = Verify_Email(
        id=generate_id(256),
        user_id=user.id
    )
    db.session.add(verification_token)
    db.session.commit()
    
    link = f"{__HOST__}{url_for('auth.verify_email', verify_id=verification_token)}"
    print(link)
    return link

