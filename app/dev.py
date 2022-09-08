from flask import Blueprint, render_template, render_template_string,  redirect, abort, url_for, flash, request, session
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from ._lib.send_mail import send_mail
from .models import Article, User, Verify_Email, Password_Reset, Tag, Article_Tag, Role, Survey, Answer, User_Answer, Banned_User, Announcement, get_users_to_notify
from .articles import get_article_location
from .auth import is_eternal_dev
from ._lib.mail_contents import account_yeeted, announcement as announcement_mail
from . import db, send_database, __MAIL_ACCOUNT__
from os import remove
from os.path import exists, isdir
from shutil import rmtree

dev = Blueprint("dev", __name__)
#TODO! set timer to reset this to false after certain amount of time (~15 minutes)
#TODO implement counter for wrong passwords (use url parameter overloading?)
#TODO also delete images related to an article
authorized = False # used to control if user is allowed to view the panel


@dev.route('/', methods=["GET", "POST"])
@login_required
def dev_panel() -> None:
    if current_user.role != "developer":
        abort(418)
    if not authorized:
        # stored current url as session variable before prompting authorization to be redirected correctly 
        return authorize_dev()


    users = User.__order_by_role__(User, descend=True)
    articles = Article.query.order_by(Article.validated).order_by(Article.title)
    announcements = Announcement.query.order_by(Announcement.validated).order_by(Announcement.date_created)
    filtered = False
    if request.method == "POST":
        if request.form.get("backup"):
            return send_database()

        if request.form.get("reset_user"):
            filtered = False
        elif request.form.get("id"):
            users = User.query.filter_by(id=int(request.form.get("id")))
            filtered = True
        elif request.form.get("name"):
            # https://stackoverflow.com/questions/3325467/sqlalchemy-equivalent-to-sql-like-statement
            users = User.query.filter(User.name.like(f"%{request.form.get('name')}%"))
            filtered = True
        elif request.form.get("email"):
            users = User.query.filter(User.email.like(f"{request.form.get('email')}"))
            filtered = True
    return render_template(
        "auth/dev.html",
        users=users,
        #users=User.query.all(),
        articles=articles,
        announcements=announcements,
        tags=Tag.query.all(),
        surveys=Survey.query.order_by(Survey.title), #TODO rework this to date when it's actually implemented
        roles=Role.query.order_by(Role.hierarchy),
        banned_users=Banned_User.query.order_by(Banned_User.expiry_date),
        users_filtered=filtered
    )


"""
prompts the user to confirm his password to verify he is the developer.

@return redirect(redirect_to): url requesting an authorization is stored in cache. Redirects to this cached url.
@return render_template_strintg([...]): returns password prompt
"""

@dev.route("/verify", methods=["GET", "POST"])
@login_required
def check_password():
    global authorized

    if request.method == "POST":
        password = request.form.get("password")

        if check_password_hash(current_user.password, password):
            authorized = True
            session["needs_authorization"] = False # session variable used to not "unauthorize" user every time password is required
            
            # gets url stored as session variable, then deletes it to free up space
            redirect_to = session["request_url"]
            session.pop("request_url")
            return redirect(redirect_to)
        flash("incorrect password", category="error")

    return render_template_string(
        """
        {% extends 'base.html' %}

        {% block navbar %}{% endblock %}

        {% block content %}
        <div class="container-xl">
            <br>
            <h1>please verify it's you</h1>
            <br>
            <form method="POST">
                <input type="password" name="password" class="form-control" id="password" placeholder="enter password">
                <br>
                <button class="btn btn-primary" type="submit">Submit</button>
            </form>
            <b><a href='/dev' style="text-decoration: none">back</a></b>
            {% endblock %}
        </div>
        """
    )
    

@dev.route("yeet_user/<int:id>")
def delete_user(id):
    user_email = User.query.get(id).email
    if is_eternal_dev(user_email):
        flash("Can't delete eternal developer!", category="error")
        return redirect("/dev")
    if session["needs_authorization"]:
        return authorize_dev()
    User.query.filter_by(id=id).delete()
    Verify_Email.query.filter_by(user_id=id).delete()
    Password_Reset.query.filter_by(user_id=id).delete()

    db.session.add(
        Banned_User(
            email=user_email
        )
    )
    db.session.commit()

    content = account_yeeted()
    if send_mail(
        from_email=__MAIL_ACCOUNT__["email"],
        password=__MAIL_ACCOUNT__["password"],
        recipients=user_email,
        subject=content["head"],
        content=content["body"],
        smtp=__MAIL_ACCOUNT__["smtp"][0],
        port=__MAIL_ACCOUNT__["smtp"][1]
    ):
        flash("User notified of deletion", category="info")
    else:
        flash("Couldn't notify user of deletion", category="info")
    
    flash("User deleted successfully!", category="success")
    return redirect("/dev")



@dev.route("/change_role/<int:user>")
def change_role(user):
    changed_user = User.query.get(int(user))
    if is_eternal_dev(changed_user.email):
        flash("Can't demote eternal developer!", category="error")
        return redirect("/dev")
    if session["needs_authorization"]:
        return authorize_dev()
    changed_user.role = session["new_user_role"]
    db.session.commit()
    session.pop("new_user_role")
    flash("Role changed successfully!", category="success")
    return redirect("/dev")


@dev.route("/delete_article/<id>")
def delete_article(id):
    if session["needs_authorization"]:
        return authorize_dev()
    article_location = get_article_location(id)
    article_image_location = f"app/static/img/articles/{id}"
    Article.query.filter_by(id=id).delete()
    if exists(article_location):
        remove(article_location)
    if isdir(article_image_location):
        rmtree(article_image_location)

    connections = Article_Tag.query.filter_by(article_id=id).all()

    # checking to see if deleting that article will leave any tag without any article - if so, delete it
    for article_tag in connections:
        if not len(Article_Tag.query.filter_by(tag=article_tag.tag).all()) > 1:
            Tag.query.filter_by(tag=article_tag.tag).delete()
    Article_Tag.query.filter_by(article_id=id).delete()
    db.session.commit()
    
    flash("Article deleted successfully!", category="success")
    return redirect("/dev")


@dev.route("/delete_survey/<id>")
def delete_survey(id):
    if session["needs_authorization"]:
        return authorize_dev()
    Survey.query.filter_by(id=id).delete()
    Answer.query.filter_by(survey=id).delete()
    User_Answer.query.filter_by(survey_id=id).delete()
    db.session.commit()
    flash("Survey deleted successfully!", category="success")
    return redirect("/dev")


@dev.route("/delete_tag/<tag>")
def delete_tag(tag):
    if session["needs_authorization"]:
        return authorize_dev()
    Tag.query.filter_by(tag=tag).delete()
    Article_Tag.query.filter_by(tag=tag).delete()
    db.session.commit()
    flash("Tag deleted successfully!", category="success")
    return redirect("/dev")


@dev.route("/change-admin-password")
def change_admin_password():
    if session["needs_authorization"]:
        return authorize_dev()
    new_password = session["new_admin_password"]
    if len(new_password) < 4:
        flash("Password must be at least 4 characters long", category="error")
    else:
        with open("__admin__.txt", "w+") as f:
            f.write(generate_password_hash(new_password))
        flash("Admin Password changed successfully!", category="success")
    
    session.pop("new_admin_password")
    return redirect("/dev")


@dev.route("/unban/<int:id>")
def unban(id):
    if session["needs_authorization"]:
        return authorize_dev()
    Banned_User.query.filter_by(id=id).delete()
    db.session.commit()
    flash("User unbanned successfully", category="success")
    return redirect("/dev")


@dev.route("/delete-announcement/<id>")
def delete_announcement(id):
    # since this function is accessed from outside the dev panel, that token might not exist - hence the try-catch, to enable non-developers
    # to be able to review announcements properly
    try:
        if session["needs_authorization"]:
                return authorize_dev()
    except KeyError: pass

    Announcement.query.filter_by(id=id).delete()
    db.session.commit()
    flash("Announcement deleted successfully", category="success")
    return redirect("/dev")



@dev.route("/approve-announcement/<id>")
@login_required
def approve_announcement(id):
    announcement = Announcement.query.get(id)
    if current_user.role != "developer":
        abort(418)
    announcement.validated = True
    db.session.commit()
    flash("Announcement is now public!", category="success")
    
    mail = announcement_mail(announcement)
    if send_mail(
        from_email=__MAIL_ACCOUNT__["email"],
        password=__MAIL_ACCOUNT__["password"],
        recipients=get_users_to_notify(),
        subject=mail["head"],
        content=mail["body"],
        smtp=__MAIL_ACCOUNT__["smtp"][0],
        port=__MAIL_ACCOUNT__["smtp"][1]
    ):
        flash("Mail notifications sent successfully!", category="success")
    else:
        flash("Mail could not be sent", category="info")
    return redirect("/dev")



#-------------------------------------------------------------------------------------------------------------------------------------------
# @REGION authorization redirects
"""
the way this works is that for every operation, the dev has to enter his password (security and stuff), so all forms action attribute point to
functions that set a session variable to "needing authorization" The actual authorization is handled by an if statement in the "follow-up" 
function redirecting to the password check.
"""

# edit: I fucking hate it. This is by far the worst code in this entire project.

@dev.route("/change_role/<int:user>/authorize", methods=["POST"])
def authorize_to_change_role(user):
    session["needs_authorization"] = True # tells "follow-up" function that authorization is needed via cache
    session["new_user_role"] = request.form.get("role") # caching data necessary to "follow-up" function 
    return redirect(url_for("dev.change_role", user=user)) #authorization is handled by if-statement in "follow-up" function


@dev.route("/yeet_user/<int:id>/authorize")
def authorize_to_delete_user(id):
    session["needs_authorization"] = True
    return redirect(url_for("dev.delete_user", id=id))


@dev.route("/yeet_article/<id>/authorize")
def authorize_to_delete_article(id):
    session["needs_authorization"] = True
    return redirect(url_for("dev.delete_article", id=id))


@dev.route("/yeet_survey/<id>/authorize")
def authorize_to_delete_survey(id):
    session["needs_authorization"] = True
    return redirect(url_for("dev.delete_survey", id=id))


@dev.route("/yeet_tag/<tag>/authorize")
def authorize_to_delete_tag(tag):
    session["needs_authorization"] = True
    return redirect(url_for("dev.delete_tag", tag=tag))


@dev.route("/change-admin-password/authorize", methods=["POST"])
def authorize_to_change_admin_password():
    session["new_admin_password"] = request.form.get("admin_password")
    session["needs_authorization"] = True
    return redirect(url_for("dev.change_admin_password"))


@dev.route("/unban/<int:id>/athorize")
def authorize_to_unban(id):
    session["needs_authorization"] = True
    return redirect(url_for("dev.unban", id=id))


@dev.route("/delete-announcement/<id>/authorize")
def authorize_to_delete_announcement(id):
    session["needs_authorization"] = True
    return redirect(url_for("dev.delete_announcement", id=id))


def authorize_dev():
    session["request_url"] = request.url
    return redirect(url_for("dev.check_password"))
    
#-------------------------------------------------------------------------------------------------------------------------------------------

