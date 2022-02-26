from flask import Blueprint, render_template
from .models import Article

articles = Blueprint("articles", __name__)

#render requested article as template
@articles.route('/<path:path>')
def find_article(path) -> None:
    return render_template(f"articles/{path}")

@articles.route("/all")
def all() -> None:
    return render_template("overview.html", articles=Article.query.all())
