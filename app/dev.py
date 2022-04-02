from flask import Blueprint, render_template, render_template_string,  redirect, abort, url_for, request, session
from flask_login import login_required, current_user
from sqlalchemy import desc
from werkzeug.security import check_password_hash
from .models import Article, User, Tag, Role
from . import db
from os import remove
from glob import glob


dev = Blueprint("dev", __name__)
authorized = True # is set to True once dev is authorized

# TODO:  1. secure this section with password(s)
#        2. do all these options in the form of a GUI
#        3. get rid of eval(inp) as soon as possible to not risk losing everything
@dev.route('/')
@login_required
def dev_panel() -> None:
    if current_user.role != "developer":
        abort(418)
    if not authorized:
        # stored current url as session variable before prompting authorization to be redirected correctly 
        session["request_url"] = request.url
        return redirect(url_for("dev.check_password"))
    return render_template(
        "auth/dev.html",
        #users=User.__order_by_role__(User, descend=True),
        users=User.query.all(),
        articles=Article.query.all(),
        tags=Tag.query.all(),
        roles=Role.query.order_by(Role.hierarchy)
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
            
            # gets url stored as session variable, then deletes it to free up space
            redirect_to = session["request_url"]
            session.pop("request_url")
            return redirect(redirect_to)

    return render_template_string(
        """
        <h1>please verify it's you</h1>
        <form method="POST">
            <input type="password" name="password" class="form-control" id="password" placeholder="enter password">
            <button type="submit">Submit</button>
        </form>
        """
    )


@dev.route("yeet_user/<id>")
def delete_user(id):
    return redirect("/dev")


@dev.route("/change_role/<int:user>", methods=["POST"])
def change_role(user):
    changed_user = User.query.get(int(user))
    new_role = request.form.get("role")
    print(new_role)
    changed_user.role = new_role
    db.session.commit()
    return redirect("/dev")
