from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required
from sqlalchemy import desc
from .models import Article

views = Blueprint("views", __name__)

@views.route('/')
def index() -> str:
    return render_template("index.html")

@login_required
@views.route("/admin")
def admin_index():
    if current_user.role != "validate" and current_user.role != "developer":
        abort(403)
    invalidated_articles = Article.query.filter_by(validated=False)
    return render_template("admin.html", invalidated_articles=invalidated_articles.order_by(desc(Article.date_created)))
