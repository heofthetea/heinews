from flask import Blueprint, render_template, redirect, request
from flask_login import login_required, current_user
from .models import Article, User_Upvote, get_user_role
from sqlalchemy import desc
from random import choice

views = Blueprint("views", __name__)

@views.route('/')
def index() -> str:
    return render_template(
        "index.html",
        most_upvoted_article=Article.query.order_by(desc(Article.upvotes)).first(),
        most_recent_article=Article.query.order_by(desc(Article.date_created)).first(),
        random_article=choice(Article.query.all())
    )


@views.route("/search", methods=["POST"])
def search():
    search_content = request.form.get("search")
    return redirect('/')


@views.route("/user")
@login_required
def profile():
    # get all articles upvoted
    upvote_connections = User_Upvote.query.filter_by(user_id=current_user.id).all()
    upvoted = [Article.query.get(article.article_id) for article in upvote_connections]
    #TODO if admin: access all articles uploaded
    if get_user_role(current_user).can_upload:
        uploaded = Article.query.filter_by(creator_email=current_user.email).all()
    #TODO similar stuff depending on features added
    #TODO add option to change password, notifications, verify email
    return render_template("auth/profile.html", upvoted=upvoted, uploaded=uploaded)



class ErrorPages:
    def __404__():
        return render_template("error/404.html")

