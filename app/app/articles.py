from flask import Blueprint, render_template, abort, redirect, url_for, flash, request
from jinja2.exceptions import TemplateNotFound
from flask_login import current_user, AnonymousUserMixin, login_required
from .models import Article, User, Role, Tag, User_Upvote, Announcement, get_tags, get_articles, get_User_Upvote, get_user_role, get_users_to_notify
from . import db, user_loggedin, __MAIL_ACCOUNT__
from ._lib.send_mail import send_mail
from ._lib.mail_contents import article as article_notification


# TODO change phone number in footer

articles = Blueprint("articles", __name__)

def get_article_location(id):
    return f"app/templates/articles/{id}.html"
    

"""
check if article existes as a template (try-catch) and as a database entry, if so:
renders article as jinja2 template

@param path: name of html file article is stored at (with the '.html' extension)
"""
@articles.route('/<path:path>')
def find_article(path: str) -> None:
    try:
        loggedin = user_loggedin(current_user)
        article_id = path.split('.')[0]
        db_entry = Article.query.get(article_id)
        if not db_entry:
            abort(404)

        if not db_entry.validated:
            if not get_user_role(current_user).can_validate:
                abort(403)

        user_upvoted = False
        if loggedin:
            if get_User_Upvote(current_user.id, article_id).first():
                user_upvoted = True


        return render_template(
            f"articles/{path}", 
            db_entry=db_entry,
            created_by=User.query.filter_by(email=db_entry.creator_email).first().name,
            tags=get_tags(db_entry),
            upvoted=user_upvoted
        )
    except TemplateNotFound:
        abort(404)


@articles.route("/announcement/<id>")
def announcement(id):
    announcement = Announcement.query.get(id)
    if announcement:
        return render_template(
            "announcement.html",
            announcement=announcement
        )
    abort(404)


@articles.route("/all")
def all_articles() -> None:
    return render_template(
        "overview/all.html", 
        articles=Article.__validated_articles__(Article).all()
    )


@articles.route("/category/<category>")
def by_category(category: str):
    return render_template(
        "overview.html", 
        articles=Article.__validated_articles__(Article).filter_by(category=category).all()
    )


@articles.route("/upvote/<id>", methods=["POST"])
def upvote(id):
    try:
        if not current_user.email_confirmed:
            flash("Hierfür musst Du erst Deine Email verifizieren! Schau mal in Deinem Email-Postfach nach :)", category="error")
            abort(403)
        db.session.add(
            User_Upvote(
                user_id=current_user.id,
                article_id=id
            )
        )
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
@login_required
def feedback(id):
    if not current_user.email_confirmed:
        flash("Hierfür musst Du erst Deine Email verifizieren! Schau mal in Deinem Email-Postfach nach :)", category="error")
        abort(403)
    article = Article.query.get(id)
    return redirect(f"mailto:{article.creator_email}")


@articles.route("/approve/<id>")
@login_required
def approve(id):
    if not current_user.email_confirmed:
        flash("Hierfür musst Du erst Deine Email verifizieren! Schau mal in Deinem Email-Postfach nach :)", category="error")
        abort(403)
    article = Article.query.get(id)
    article.validated = True
    db.session.commit()

    content = article_notification(article.title, article.description, article.id)
    if send_mail(
        from_email=__MAIL_ACCOUNT__["email"],
        password=__MAIL_ACCOUNT__["password"],
        recipients=get_users_to_notify(),
        subject=content["head"],
        content=content["body"],
        smtp=__MAIL_ACCOUNT__["smtp"][0],
        port=__MAIL_ACCOUNT__["smtp"][1]
    ):
        pass
    flash("Artikel wurde erfolgreich validiert!", category="success")
    return redirect(url_for("articles.find_article", path=id+".html"))


#---------------------------------------------------------------------------------------------------------------------------------------------

tag = Blueprint("tag", __name__)

# @param tag: tag WITHOUT '#' (because that won't work with URL encoding)
@tag.route("/<tag>")
def articles_by_tag(tag: str):
    tag = '#' + tag
    if not Tag.query.get(tag):
        abort(404)
    articles_with_tag = get_articles(Tag.query.get(tag))
    # articles without validation are handled in frontend to make them visible to roles that can validate only
    return render_template("overview/all.html", articles=articles_with_tag)


@tag.route("/")
def all_tags():
    five_articles_for_tag = {}
    tags = Tag.query.all()
    for tag in tags:
        five_articles_for_tag[tag.tag] = get_articles(tag=tag, limit=10)

    return render_template(
        "overview/tags.html", 
        tags=tags,
        five_articles_for_tag=five_articles_for_tag
    )
