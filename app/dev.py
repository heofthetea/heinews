from flask import Blueprint, redirect, abort
from flask_login import logout_user, current_user
from .models import Article, User
from . import db
from os import remove
from glob import glob


dev = Blueprint("dev", __name__)

# TODO:  1. secure this section with password(s)
#        2. do all these options in the form of a GUI
#        3. get rid of eval(inp) as soon as possible to not risk losing everything
@dev.route('/')
def delete() -> None:
    if current_user.role != "dev":
        abort(418)
    # yes this is a terrible weakness that cannot go into release like that
    inp = input("> ")
    eval(inp)
    return redirect('/')


"""
deletes articles according to parameters. Will be combined with a (secure) user interface and is necessary, because there is no phpMyAdmin :(
"""
def delete_article(all=False, *ids) -> None:
    if not all:
        for id in ids:
            remove(f"app/templates/articles/{id}.html")
            Article.query.filter(Article.id == id).delete()
            db.session.commit()
    else:
        for article in glob("app/templates/articles/*"):
            remove(article)
        Article.query.delete()
        db.session.commit()


def remove_user(all=False):
    if all:
        if current_user:
            logout_user()
        User.query.delete()
    
