from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Password_Reset, Verify_Email, Delete_Account, User_Answer, User_Upvote, Banned_User, generate_id
from ._lib.mail_contents import verification, reset, delete
from . import db, __DEVELOPERS__, __HOST__, __MAIL_ACCOUNT__
from ._lib.send_mail import send_mail
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime


auth = Blueprint("auth", __name__)
get_checkbutton = lambda val : val == "on"

#----------------------------------------------------------------------------------------------------------------------------

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
        is_banned = user_banned(email)

        if user:
            flash("Email bereits vergeben", category="error")
        elif len(name) < 2:
            flash("Name muss mindestens 2 Zeichen lang sein", category="error")
        elif password1 != password2:
            flash("Passwörter stimmen nicht überein", category="error")
        elif is_banned is not None:
            flash(f"Dein Account wurde von Moderatoren gelöscht. Warte bis zum {is_banned.strftime('%d.%m.%Y um %H:%M')} \
                , um einen neuen Account erstellen zu können!", category="error")
        else:
            # add user to data base
            role = "user"
            if is_eternal_dev(email):
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
            return redirect(url_for("views.profile"))
    return render_template("auth/signup.html", user=current_user)


@auth.route("/logout")
def logout():
    logout_user()
    flash("Erfolgreich abgemeldet! Hier kannst Du dich neu anmelden: ", category="success")
    return redirect(url_for("auth.login"))


def is_eternal_dev(email):
    for dev in __DEVELOPERS__:
        if check_password_hash(dev, email):
            return True
    return False

#----------------------------------------------------------------------------------------------------------------------------

@auth.route("/resetpw/<reset_id>", methods=["GET", "POST"])
#@login_required # TODO keep this or not??
# -> IF PIPELINE WORKS: test with this on, then,
# future me: then what??

# TODO! add option to cancel process
def reset_password(reset_id):
    reset_token = Password_Reset.query.get(reset_id)
    Password_Reset.query.filter_by(id=reset_id).delete()

    if datetime.now() > reset_token.expiry_date:
        flash("Dein Reset Token ist abgelaufen! Auf Deinem Profil kannst Du einen neuen anfordern!", category="error")
        db.session.commit()
        return redirect(url_for("views.profile"))

    if request.method == "POST":
        user = User.query.get(reset_token.user_id)

        if "cancel" in request.form:
            db.session.commit()
            flash("Vorgang erfolgreich abgebrochen", category="success")
            return redirect(url_for("views.profile"))

        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        if password1 != password2:
            flash("Passwörter stimmen nicht überein", category="error")
        elif check_password_hash(user.password, password1):
            flash("Herzlichen Glückwunsch, Du hast Dein altes Passwort erraten :)", category="success")
        else:
            user.password = generate_password_hash(password1, method="sha256")
            db.session.commit()
            
            flash("Passwort wurde erforlgreich geändert!", category="success")
            return(redirect(url_for("views.profile")))
    return render_template("auth/reset_password.html")


@auth.route("/deleteacc/<delete_id>", methods=["GET", "POST"])
#@login_required # TODO keep this or not??
def delete_account(delete_id):
    delete_token = Delete_Account.query.get(delete_id)
    Delete_Account.query.filter_by(id=delete_id).delete()

    if datetime.now() > delete_token.expiry_date:
        flash("Dein Deletion Token ist abgelaufen! Auf Deinem Profil kannst Du einen neuen anfordern!", category="error")
        db.session.commit()
        return redirect(url_for("views.profile"))

    elif request.method == "POST":
        user = User.query.get(delete_token.user_id)

        if "cancel" in request.form:
            db.session.commit()
            flash("Vorgang erfolgreich abgebrochen", category="success")
            return redirect(url_for("views.profile"))

        password = request.form.get("password")

        if check_password_hash(user.password, password):
            User.query.filter_by(id=user.id).delete()

            # when a user deletes his own account, all his traces are erased
            # when instead a user gets deleted by devs, his upvotes and survey answers should remain
            User_Answer.query.filter_by(user_id=user.id).delete()
            User_Upvote.query.filter_by(user_id=user.id).delete()
            Verify_Email.query.filter_by(user_id=user.id).delete()
            Password_Reset.query.filter_by(user_id=user.id).delete()

            db.session.commit()
            flash("Dein Account wurde erfolgreich gelöscht!", category="success")
            return(redirect(url_for("auth.signup")))
        else:
            flash("Das Passwort stimmt leider nicht :/", category="error")
            return(redirect(url_for("auth.profile")))
    return render_template("auth/delete_account.html")


@auth.route("/verify/<verify_id>")
def verify_email(verify_id):
    verification_token = Verify_Email.query.get(verify_id)

    if datetime.now() > verification_token.expiry_date:
        flash("Dein Verification Token ist abgelaufen! Auf Deinem Profil kannst Du einen neuen anfordern!", category="error")
        Verify_Email.query.filter_by(id=verify_id).delete()
        db.session.commit()
        return redirect(url_for("views.profile"))
    
    user = User.query.get(verification_token.user_id)
    user.email_confirmed = True

    Verify_Email.query.filter_by(id=verify_id).delete()
    db.session.commit()

    flash("Deine Email wurde erfolgreich verifiziert! Jetzt verfügst Du über alle dir zustehenden Freiheiten!", category="success")
    return redirect(url_for("views.profile"))


@auth.route("/promote", methods=["POST"])
@login_required
def promote():
    admin_password = request.form.get("admin_password")

    if current_user.role != "user":
        flash("Du kannst dich nur als User selbst befördern!", category="error")
    elif check_admin_password(admin_password): #TODO implement a counter to a maximum of tries, otherwise some trolls will crash the database
        current_user.role = "upload"
        db.session.commit()
        flash("Herzlichen Glückwunsch! Du bist nun berechtigt, Artikel etc. hochzuladen!", category="success")
    return redirect(url_for("views.profile"))


@auth.route("/changenotifications", methods=["POST"])
@login_required
def change_notification_settings():
    email_notifications = get_checkbutton(request.form.get("notifications"))
    current_user.notifications = email_notifications
    db.session.commit()
    flash(
        "Du erhältst ab jetzt Benachrichtigungen per Mail über neuen Content auf der Website!" if email_notifications 
        else "Wir werden dich nicht mehr per Mail über neuen Content auf der Website benachrichtigen!", 
        category="success"
    )
    return redirect(url_for("views.profile"))


#----------------------------------------------------------------------------------------------------------------------------
# @REGION sending links per mail

# check comment on send_reset_mail for explanation
def send_verification_email(email: str) -> None:
    user = User.query.filter_by(email=email).first()
    temp_id = generate_id(256, table=Verify_Email)
    
    link = f"{__HOST__}{url_for('auth.verify_email', verify_id=temp_id)}"
    content = verification(link)
    # sending mail before adding database entry because that is much more likely to go wrong and in that case won't create
    # a DB entry that cannot be accessed in any way
    if send_mail(
        from_email=__MAIL_ACCOUNT__["email"],
        password=__MAIL_ACCOUNT__["password"],
        recipients=email,
        subject=content["head"],
        content=content["body"],
        smtp=__MAIL_ACCOUNT__["smtp"][0],
        port=__MAIL_ACCOUNT__["smtp"][1]
    ):
        db.session.add(
            Verify_Email(
                id=temp_id,
                user_id=user.id
            )
        )
        db.session.commit()
        flash("Du erhältst demnächst eine Email mit Verifizierungscode. Sobald wir Deine Email-Addresse verifiziert haben, hast Du \
                Zugriff auf Aktionen wie Upvoten.", category="info")
    else:
        flash("Whoops... Da ist wohl was schief gelaufen! Wir konnten dir keine Mail senden :/", category="error")


"""
Sends a link to reset the users password per Mail and creates a reset token in the database. First the mail gets sent, because this 
process is far more likely to go wrong than a simple DB operation, and if it were to happen the other way around and something did go 
wrong, there would exist a reset token which a) cannot be accessed from anywhere and b) will prevent the user from requesting another.
"""
@auth.route("/reset_link/<int:user_id>")
def send_reset_mail(user_id):
    # if the user already has a reset token, he should not request another
    if Password_Reset.query.filter_by(user_id=user_id).first():
        flash("Du hast bereits einen Link zum Zurücksetzen!!", category="error")
    else:
        temp_id = generate_id(256, table=Password_Reset) # id is created here because it is used in both the DB entry and the link

        link = f"{__HOST__}{url_for('auth.reset_password', reset_id=temp_id)}"
        content = reset(link)
        if send_mail(
            from_email=__MAIL_ACCOUNT__["email"],
            password=__MAIL_ACCOUNT__["password"],
            recipients=User.query.get(user_id).email,
            subject=content["head"],
            content=content["body"],
            smtp=__MAIL_ACCOUNT__["smtp"][0],
            port=__MAIL_ACCOUNT__["smtp"][1]
        ):
            db.session.add(
                Password_Reset(
                    id=temp_id,
                    user_id=int(user_id)
                )
            )
            db.session.commit()
            flash("Dir wurde eine Mail mit einem Link gesendet, unter dem Du Dein Passwort zurücksetzen kannst.", category="info")
        else:
            flash("Whoops... Da ist wohl was schief gelaufen! Wir konnten dir keine Mail senden :/", category="error")

    return redirect(url_for('views.profile'))


@auth.route("/delete_link/<int:user_id>")
def send_delete_mail(user_id):
    if Delete_Account.query.filter_by(user_id=user_id).first():
        flash("Du hast bereits einen Link zum Löschen!!", category="error")
    else:
        temp_id = generate_id(256, table=Delete_Account)

        link = f"{__HOST__}{url_for('auth.delete_account', delete_id=temp_id)}"
        content = delete(link)
        if send_mail(
            from_email=__MAIL_ACCOUNT__["email"],
            password=__MAIL_ACCOUNT__["password"],
            recipients=User.query.get(user_id).email,
            subject=content["head"],
            content=content["body"],
            smtp=__MAIL_ACCOUNT__["smtp"][0],
            port=__MAIL_ACCOUNT__["smtp"][1]
        ):
            db.session.add(
                Delete_Account(
                    id=temp_id,
                    user_id=int(user_id)
                )
            )
            db.session.commit()
            flash("Dir wurde eine Mail mit einem Link gesendet, unter dem Du Deinen Account löschen kannst.", category="info")
        else:
            flash("Whoops... Da ist wohl was schief gelaufen! Wir konnten dir keine Mail senden :/", category="error")
    return redirect(url_for('views.profile'))
    

#----------------------------------------------------------------------------------------------------------------------------

def check_admin_password(pw: str) -> bool:
    with open("__admin__.txt", "r") as f:
        if check_password_hash(f.readline(), pw):
            return True
    return False

"""
checks if a user is banned. If ban is expired, the ban gets lifted, i.e. the DB entry deleted
@param email: the email, the user entered on signup
@return the expiry date of the ban if there is one, None if user is not banned
"""
def user_banned(email: str) -> datetime:
    ban = Banned_User.query.filter_by(email=email).first()
    
    if ban:
        if datetime.now() > ban.expiry_date:
            Banned_User.query.filter_by(email=email).delete()
            db.session.commit()
            return None
        return ban.expiry_date
    return None


