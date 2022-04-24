from flask import Blueprint, render_template, redirect, flash, url_for, request
from flask_login import login_required, current_user
from .models import Article, User_Upvote, Password_Reset, get_user_role
from .auth import send_verification_email
from . import db
from sqlalchemy import desc
from random import choice

views = Blueprint("views", __name__)

@views.route('/')
def index() -> str:
    most_upvoted = Article.__validated_articles__(Article).order_by(desc(Article.upvotes)).first()
    most_recent = Article.__validated_articles__(Article).order_by(desc(Article.date_created)).first()
    try:
        random_article = choice(Article.__validated_articles__(Article).all())
    except IndexError:
        random_article = []
    return render_template(
        "index.html",
        most_upvoted_article=most_upvoted,
        most_recent_article=most_recent,
        random_article=random_article,
        articles=len(Article.__validated_articles__(Article).all()) > 0
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
    uploaded = [] # declared as empty list instead of None because of later use of `len(uploaded)`
    if get_user_role(current_user).can_upload:
        uploaded = Article.query.filter_by(creator_email=current_user.email).all()
    #TODO similar stuff depending on features added
    #TODO add option to change password, notifications, verify email

    reset = Password_Reset.query.filter_by(user_id=current_user.id).first()
    if reset:
        reset = reset.id
    return render_template(
        "auth/profile.html", 
        upvoted=upvoted, 
        uploaded=uploaded,
        reset=reset,
        # TODO remove this when sending verification link by email
        verification_link=send_verification_email(current_user.email) if not current_user.email_confirmed else "already verified"
    )

# TODO new error for "email not verified?"
class ErrorPages:
    def __404__():
        return render_template("error/404.html")

    def __403__():
        return render_template("error/403.html")

