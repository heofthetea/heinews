from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Password_Reset, Verify_Email, Delete_Account, User_Answer, User_Upvote, Banned_User, Promotion_Key, generate_id
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
            user_id = User.query.filter_by(email=new_user.email).first().id

            send_verification_email(user_id)

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

def reset_password(reset_id):
    log = lambda msg : print(f"auth.dreset_password -> {msg}")

    reset_token = Password_Reset.query.get(reset_id)
    log(f"found reset token:\n\tuser_id: {reset_token.user_id}\n\texpiry date: {reset_token.expiry_date}")
    Password_Reset.query.filter_by(id=reset_id).delete()

    if datetime.now() > reset_token.expiry_date:
        flash("Dein Reset Token ist abgelaufen! Auf Deinem Profil kannst Du einen neuen anfordern!", category="error")
        db.session.commit()
        log("successfully deleted expired token")
        return redirect(url_for("views.profile"))

    if request.method == "POST":
        user = User.query.get(reset_token.user_id)
        log(f"found user to reset password: {user.id}")

        if "cancel" in request.form:
            db.session.commit()
            log("successfully cancelled password reset")
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
            log(f"successfully changed password of user: {user.id}")
            
            flash("Passwort wurde erforlgreich geändert!", category="success")
            return(redirect(url_for("views.profile")))
    return render_template("auth/reset_password.html")


@auth.route("/deleteacc/<delete_id>", methods=["GET", "POST"])
#@login_required # TODO keep this or not??
def delete_account(delete_id):
    log = lambda msg : print(f"auth.delete_account -> {msg}")

    delete_token = Delete_Account.query.get(delete_id)

    log(f"found deletion token:\n\tuser_id: {delete_token.user_id}\n\texpiry date: {delete_token.expiry_date}")
    if datetime.now() > delete_token.expiry_date:
        flash("Dein Deletion Token ist abgelaufen! Auf Deinem Profil kannst Du einen neuen anfordern!", category="error")
        Delete_Account.query.filter_by(id=delete_id).delete()
        db.session.commit()
        log("deleted expired token")
        return redirect(url_for("views.profile"))

    elif request.method == "POST":
        user = User.query.get(delete_token.user_id)
        log(f"found user to delete: {user.id}")

        if "cancel" in request.form:
            db.session.commit()
            log("successfully cancelled deletion")
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
            log(f"successfully deleted user: {user.id}")

            Delete_Account.query.filter_by(id=delete_id).delete()
            db.session.commit()
            flash("Dein Account wurde erfolgreich gelöscht!", category="success")
            return(redirect(url_for("auth.signup")))
        else:
            flash("Das Passwort stimmt leider nicht :/", category="error")
            return(redirect(url_for("auth.profile")))
    return render_template("auth/delete_account.html")


@auth.route("/verify/<verify_id>")
def verify_email(verify_id):
    log = lambda msg : print(f"auth.verify_email -> {msg}")

    verification_token = Verify_Email.query.get(verify_id)
    log(f"found verification token:\n\tuser_id: {verification_token.user_id}\n\texpiry date: {verification_token.expiry_date}")

    if datetime.now() > verification_token.expiry_date:
        flash("Dein Verification Token ist abgelaufen! Auf Deinem Profil kannst Du einen neuen anfordern!", category="error")
        Verify_Email.query.filter_by(id=verify_id).delete()
        db.session.commit()
        log("deleted expired verification token")
        return redirect(url_for("views.profile"))
    
    user = User.query.get(verification_token.user_id)
    log(f"found user to verify: {user.id}")
    user.email_confirmed = True

    Verify_Email.query.filter_by(id=verify_id).delete()
    db.session.commit()

    flash("Deine Email wurde erfolgreich verifiziert! Jetzt verfügst Du über alle dir zustehenden Freiheiten!", category="success")
    log(f"successfully verified user: {user.id}")
    return redirect(url_for("views.profile"))


@auth.route("/promote", methods=["POST"])
@login_required
def promote():
    promotion_key = request.form.get("promotion_key")

    if current_user.role != "user":
        flash("Du kannst dich nur als User selbst befördern!", category="error")
    elif check_promotion_key(promotion_key): #TODO implement a counter to a maximum of tries, otherwise some trolls will crash the database
        current_user.role = "upload"
        db.session.commit()
        flash("Herzlichen Glückwunsch! Du bist nun berechtigt, Artikel etc. hochzuladen!", category="success")
    else:
        flash("Du hast entweder einen falschen Code eingegeben, oder Dein Code ist abgelaufen. Wende dich an die Leiter der Schülerzeitung, um einen Code zu bekommen!", category="error")
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


@auth.route("resend-verification")
def resend_verification_mail(user_id):
    print(f"auth.resend_verification_mail -> {user_id}")
    send_verification_email(user_id)
    return redirect(url_for("views.profile"))


#----------------------------------------------------------------------------------------------------------------------------
# @REGION sending links per mail

# check comment on send_reset_mail for explanation
def send_verification_email(id: int) -> None:
    log = lambda msg : print(f"auth.send_verification_email -> {msg}")
    try:
        user = User.query.get(int(id))
        if Verify_Email.query.filter_by(user_id=user.id).first():
            log(f"user {user.id} already has a verification token")
            Verify_Email.query.filter_by(user_id=user.id).delete()
        temp_id = generate_id(256, table=Verify_Email)
        
        link = f"{__HOST__}{url_for('auth.verify_email', verify_id=temp_id)}"
        log("established link")
        content = verification(link, user.name)
        # sending mail before adding database entry because that is much more likely to go wrong and in that case won't create
        # a DB entry that cannot be accessed in any way
        if send_mail(
            from_email=__MAIL_ACCOUNT__["email"],
            password=__MAIL_ACCOUNT__["password"],
            recipients=user.email,
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
    except Exception as e:
        log(e)


"""
Sends a link to reset the users password per Mail and creates a reset token in the database. First the mail gets sent, because this 
process is far more likely to go wrong than a simple DB operation, and if it were to happen the other way around and something did go 
wrong, there would exist a reset token which a) cannot be accessed from anywhere and b) will prevent the user from requesting another.
"""
@auth.route("/reset_link/<int:user_id>")
def send_reset_mail(user_id):
    log = lambda msg : print(f"auth.send_reset_mail -> {msg}")
    try:
        # if the user already has a reset token, he should not request another
        if Password_Reset.query.filter_by(user_id=user_id).first():
            log(f"user {user_id} already has a password reset token")
            Password_Reset.query.filter_by(user_id=user_id).delete()
        temp_id = generate_id(256, table=Password_Reset) # id is created here because it is used in both the DB entry and the link

        link = f"{__HOST__}{url_for('auth.reset_password', reset_id=temp_id)}"
        log("established link")
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
            log("successfully created Password Reset token")
            flash("Dir wurde eine Mail mit einem Link gesendet, unter dem Du Dein Passwort zurücksetzen kannst. Schau auch im Spam-Ordner nach, Tests haben gezeigt dass diese Mails dort gerne landen :)", category="info")
        else:
            flash("Whoops... Da ist wohl was schief gelaufen! Wir konnten dir keine Mail senden :/", category="error")

        return redirect(url_for('views.profile'))
    except Exception as e:
        log(e)


@auth.route("/delete_link/<int:user_id>")
def send_delete_mail(user_id):
    log = lambda msg : print(f"auth.send_delete_mail -> {msg}")
    try:
        if Delete_Account.query.filter_by(user_id=user_id).first():
            log(f"user {user_id} already has a deletion token")
            Delete_Account.query.filter_by(user_id=user_id).delete()
        temp_id = generate_id(256, table=Delete_Account)

        link = f"{__HOST__}{url_for('auth.delete_account', delete_id=temp_id)}"
        log("established link")
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
            log("successfully creted Deletion token")
            flash("Dir wurde eine Mail mit einem Link gesendet, unter dem Du Deinen Account löschen kannst. Schau auch im Spam-Ordner nach, Tests haben gezeigt dass diese Mails dort gerne landen :)", category="info")
        else:
            flash("Whoops... Da ist wohl was schief gelaufen! Wir konnten dir keine Mail senden :/", category="error")

        return redirect(url_for('views.profile'))
    except Exception as e:
        log(e)
    

#----------------------------------------------------------------------------------------------------------------------------

def check_promotion_key(t_key: str) -> bool:
    found_key = Promotion_Key.query.get(t_key)
    if found_key:
        Promotion_Key.query.filter_by(key=t_key).delete()
        if not datetime.now() > found_key.expiry_date:
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


