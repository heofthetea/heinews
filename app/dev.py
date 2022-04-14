from flask import Blueprint, render_template, render_template_string,  redirect, abort, url_for, flash, request, session
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash
from .models import Article, User, Tag, Role
from .articles import get_article_location
from . import db
from os import remove
from os.path import exists, isdir
from shutil import rmtree


dev = Blueprint("dev", __name__)
#TODO set timer to reset this to false after certain amount of time (~15 minutes)
#TODO implement counter for wrong passwords (use url parameter overloading?)
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
    filtered = False
    if request.method == "POST":
        if request.form.get("reset_user"):
            filtered = False
        elif request.form.get("id"):
            users = User.query.filter_by(id=int(request.form.get("id")))
            filtered = True
        elif request.form.get("name"):
            users = User.query.filter_by(name=request.form.get("name"))
            filtered = True
        elif request.form.get("email"):
            users = User.query.filter_by(email=request.form.get("email")) 
            filtered = True
    return render_template(
        "auth/dev.html",
        users=users,
        #users=User.query.all(),
        articles=articles,
        tags=Tag.query.all(),
        roles=Role.query.order_by(Role.hierarchy),
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
        <h1>please verify it's you</h1>
        <form method="POST">
            <input type="password" name="password" class="form-control" id="password" placeholder="enter password">
            <button type="submit">Submit</button>
        </form>
        <a href='/dev'>back</a>
        {% endblock %}
        """
    )


@dev.route("yeet_user/<int:id>")
def delete_user(id):
    if session["needs_authorization"]:
        return authorize_dev()
    User.query.filter_by(id=id).delete()
    db.session.commit()
    flash("User deleted successfully!", category="success")
    return redirect("/dev")



@dev.route("/change_role/<int:user>")
def change_role(user):
    if session["needs_authorization"]:
        return authorize_dev()
    changed_user = User.query.get(int(user))
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
    db.session.commit()
    flash("Article deleted successfully!", category="success")
    return redirect("/dev")

#-------------------------------------------------------------------------------------------------------------------------------------------
# @REGION authorization redirects
"""
the way this works is that for every operation, the dev has to enter his password (security and stuff), so all forms action attribute point to
functions that set a session variable to "needing authorization" The actual authorization is handled by an if statement in the "follow-up" 
function redirecting to the password check.
"""

@dev.route("/change_role/<int:user>/authorize", methods=["POST"])
def authorize_to_change_role(user):
    session["needs_authorization"] = True # tells "follow-up" function that authorization is needed via cache
    session["new_user_role"] = request.form.get("role") # caching data necessary to "follow-up" function 
    return redirect(url_for("dev.change_role", user=user)) #authorization is handled by if-statement in "follow-up" function


@dev.route("yeet_user/<int:id>/authorize")
def authorize_to_delete_user(id):
    session["needs_authorization"] = True
    return redirect(url_for("dev.delete_user", id=id))


@dev.route("yeet_article/<id>/authorize")
def authorize_to_delete_article(id):
    session["needs_authorization"] = True
    return redirect(url_for("dev.delete_article", id=id))


def authorize_dev():
    session["request_url"] = request.url
    return redirect(url_for("dev.check_password"))
    
