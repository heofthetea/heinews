from flask import Blueprint, redirect
from .models import Article
from . import db
from os import remove
from glob import glob


dev = Blueprint("dev", __name__)

#TODO:  1. secure this section with password(s)
#       2. do all these options in the form of a GUI
#       3. get rid of eval(inp) as soon as possible to not risk losing everything
@dev.route('/delete')
def delete() -> None:
    #yes this is a terrible weakness that cannot go into release like that
    inp = input("> ")
    eval(inp)
    return redirect('/')


"""
deletes articles according to parameters. Will be combined with a (secure) user interface and is necessary, because there is no phpMyAdmin :(
"""
def delete(all=False, *ids) -> None:
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
    
