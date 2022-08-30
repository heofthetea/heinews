from flask import Blueprint, render_template, redirect, flash, url_for, request
from flask_login import login_required, current_user
from .models import Article, User_Upvote, Password_Reset, Delete_Account, Survey, User_Answer, Answer, Announcement, get_user_role
from .auth import send_verification_email
from . import db
from sqlalchemy import desc
from random import choice

views = Blueprint("views", __name__)


def title_image_or_placeholder(article):
    return article.primary_image if article.primary_image is not None else "../static/img/placeholder.png"


@views.context_processor
def inject_title_image():
    return dict(title_image_or_placeholder=title_image_or_placeholder)

@views.route('/')
def index() -> str:
    most_upvoted = Article.__validated_articles__(Article).order_by(desc(Article.upvotes)).first()
    most_recent = Article.__validated_articles__(Article).order_by(desc(Article.date_created)).first()
    announcements: list = Announcement.query.filter_by(validated=True).order_by(desc(Announcement.date_created)).all()
    surveys = Survey.query.all()

    aktuelles = Article.__validated_articles__(Article).filter_by(category="aktuelles").order_by(desc(Article.date_created)).all()
    wissen = Article.__validated_articles__(Article).filter_by(category="wissen").order_by(desc(Article.date_created)).all()
    schulleben = Article.__validated_articles__(Article).filter_by(category="schulleben").order_by(desc(Article.date_created)).all()
    lifestyle = Article.__validated_articles__(Article).filter_by(category="lifestyle").order_by(desc(Article.date_created)).all()
    unterhaltung = Article.__validated_articles__(Article).filter_by(category="unterhaltung").order_by(desc(Article.date_created)).all()
    kreatives = Article.__validated_articles__(Article).filter_by(category="kreatives").order_by(desc(Article.date_created)).all()
    try:
        random_article = choice(Article.__validated_articles__(Article).all())
    except IndexError:
        random_article = []
    return render_template(
        "index.html",
        announcements=announcements,
        most_upvoted_article=most_upvoted,
        most_recent_article=most_recent,
        random_article=random_article,
        surveys=surveys,

        aktuelles=aktuelles,
        wissen=wissen,
        schulleben=schulleben,
        lifestyle=lifestyle,
        unterhaltung=unterhaltung,
        kreatives=kreatives,

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

    # tuple: (survey_id, answer_id)
    surveys: list[tuple[str, int]] = []
    user_answers = User_Answer.query.filter_by(user_id=current_user.id).all()
    for user_answer in user_answers:
        surveys.append((
            Survey.query.get(user_answer.survey_id), 
            Answer.query.get(user_answer.answer_id)
        ))

    uploaded = [] # declared as empty list instead of None because of later use of `len(uploaded)`
    if get_user_role(current_user).can_upload:
        uploaded = Article.query.filter_by(creator_email=current_user.email).all()
    #TODO similar stuff depending on features added
    #TODO! add option to change email notification settings

    reset = Password_Reset.query.filter_by(user_id=current_user.id).first() is not None
    delete = Delete_Account.query.filter_by(user_id=current_user.id).first() is not None

        
    return render_template(
        "auth/profile.html", 
        upvoted=upvoted, 
        uploaded=uploaded,
        surveys=surveys,
        reset=reset,
        delete=delete
    )


class ErrorPages:
    def __404__():
        return render_template("error/404.html")

    def __403__():
        return render_template("error/403.html")

