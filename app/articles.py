from flask import Blueprint, render_template, abort, redirect
from jinja2.exceptions import TemplateNotFound
from .models import Article, User, Tag, get_tags, get_articles


articles = Blueprint("articles", __name__)

"""
check if article existes as a template (try-catch) and as a database entry, if so:
renders article as jinja2 template
"""
@articles.route('/<path:path>')
def find_article(path: str) -> None:
    try:
        article_id = path.split('.')[0]
        db_entry = Article.query.get(article_id)
        if not db_entry:
            abort(404)
        return render_template(f"articles/{path}", db_entry=db_entry, 
                                                   date_created=db_entry.date_created.date().strftime("%d.%m.%Y"),
                                                   created_by=User.query.filter_by(email=db_entry.creator_email).first().name,
                                                   tags=get_tags(db_entry))
        # that date_created query might be a little confusing, so to divide it up here:
        # 1. db_entry.date_created.date() gets ONLY the date of when the article was created
        # 2. strftime("%d.%m.%Y") formats it from yyyy-mm-dd to dd-mm-yyyy"""
    except TemplateNotFound:
        abort(404)


@articles.route("/all")
def all_articles() -> None:
    return render_template("overview.html", articles=Article.query.all(), type="article") #TODO rename template

#---------------------------------------------------------------------------------------------------------------------------------------------

tag = Blueprint("tag", __name__)

@tag.route("/<tag>")
def articles_by_tag(tag: str):
    tag = '#' + tag
    if not Tag.query.get(tag):
        abort(404)
    articles_with_tag = get_articles(Tag.query.get(tag))
    return render_template("overview.html", articles=articles_with_tag, type="article")


@tag.route("/")
def all_tags():
    return render_template("overview.html", tags=Tag.query.all(), type="tag")
