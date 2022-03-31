from flask import Blueprint, render_template, abort, redirect, url_for, flash
from jinja2.exceptions import TemplateNotFound
from flask_login import current_user, AnonymousUserMixin
from .models import Article, User, Tag, User_Upvote, get_tags, get_articles, get_User_Upvote
from . import db


articles = Blueprint("articles", __name__)

"""
check if article existes as a template (try-catch) and as a database entry, if so:
renders article as jinja2 template

@param path: name of html file article is stored at
"""
@articles.route('/<path:path>')
def find_article(path: str) -> None:
    try:
        article_id = path.split('.')[0]
        db_entry = Article.query.get(article_id)
        if not db_entry:
            abort(404)
        try:
            if  get_User_Upvote(current_user.id, article_id).first():
                user_upvoted = True
            else:
                user_upvoted = False
        except AttributeError:
            user_upvoted = False


        return render_template(f"articles/{path}", db_entry=db_entry,
                                                   created_by=User.query.filter_by(email=db_entry.creator_email).first().name,
                                                   tags=get_tags(db_entry),
                                                   upvoted=user_upvoted)
    except TemplateNotFound:
        abort(404)


@articles.route("/all")
def all_articles() -> None:
    return render_template("overview/all.html", articles=Article.query.all())


@articles.route("/category/<category>")
def by_category(category: str):
    return render_template(f"overview/{category}.html", articles=Article.query.filter_by(category=category).all())


@articles.route("/upvote/<id>", methods=["POST"])
def upvote(id):
    try:
        db.session.add(User_Upvote(user_id=current_user.id,
                        article_id=id))
        Article.query.get(id).upvotes += 1
        db.session.commit()
    except AttributeError:
        flash("Schön, dass Dir der Artikel gefällt! Nur musst Du dich anmelden, um das zu zeigen :)", category="error")
        return redirect(url_for("auth.login"))
    return redirect(url_for("articles.find_article", path=id+".html")) # redirects back to article


# yep that's supposed to be funny
# nope it stays that way
@articles.route("/yeet/<id>")
def remove_upvote(id):
    db.session.delete(get_User_Upvote(current_user.id, id).first())
    Article.query.get(id).upvotes -= 1
    db.session.commit()
    return redirect(url_for("articles.find_article", path=id+".html"))
    
#---------------------------------------------------------------------------------------------------------------------------------------------

@articles.route("/feedback/<id>")
def feedback(id):
    article = Article.query.get(id)
    return redirect(f"mailto:{article.creator_email}")


@articles.route("/approve/<id>")
def approve(id):
    article = Article.query.get(id)
    article.validated = True
    db.session.commit()
    flash("Artikel wurde erfolgreich validiert!", category="success")
    return redirect(url_for("articles.find_article", path=id+".html"))


#---------------------------------------------------------------------------------------------------------------------------------------------

tag = Blueprint("tag", __name__)

@tag.route("/<tag>")
def articles_by_tag(tag: str):
    tag = '#' + tag
    if not Tag.query.get(tag):
        abort(404)
    articles_with_tag = get_articles(Tag.query.get(tag))
    return render_template("overview/all.html", articles=articles_with_tag)


@tag.route("/")
def all_tags():
    return render_template("overview/tags.html", tags=Tag.query.all())
