from flask import Blueprint, render_template, redirect, flash, url_for, request
from flask_login import login_required, current_user
from .models import Article, Tag, User_Upvote, Password_Reset, Delete_Account, Survey, User_Answer, Answer, Announcement, get_user_role, get_articles
from .auth import send_verification_email
from . import db
from sqlalchemy import desc, or_
from random import choice

views = Blueprint("views", __name__)

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


"""
Enables the user to search through the entire content of the website. Searched are:
    i) Articles:
        - titles
        - descriptions
        - NO html files - so the content of an article will not be searched
    ii) Surveys (matched either title or description)
    iii) Tags (this is the primary way the search function is supposed to be used)
    iv) Announcements (matched either title or content)
    v) Pages:
        - categories (I was too lazy to figure out an algorithm for that and since there's only 6 of them they're in the match dict as well)
        - Profile (see `match` dictionary for clarification, which search terms point to the profile (yes I hardcoded that))

Search term is splitted by spaces and for each individual term, exact matches are found.
"""

# `url_for()` appearantly only works inside a `redirect()` function - thus, urls are hardcoded here...
# OH GOD THIS IS DEFINITELY THE WORST CODE IN THIS PROJECT XDDD
category_url = "/article/category"
# format: `(url, title): (list of key words that point to that page)`
__MATCH__: dict = {
    (f"{category_url}/aktuelles", "Kategorie: Aktuelles"): "aktuelles kategorien",
    (f"{category_url}/wissen", "Kategorie: Wissen"): "wissen kategorien",
    (f"{category_url}/schulleben", "Kategorie: Schulleben"): "schulleben kategorien",
    (f"{category_url}/lifestyle", "Kategorie: Lifestyle"): "lifestyle kategorien",
    (f"{category_url}/unterhaltung", "Kategorie: Unterhaltung"): "unterhaltung kategorien",
    (f"{category_url}/kreatives", "Kategorie: Kreatives"): "kreatives kategorien",

    # because of the `in` operator, everything that should point to the profile can just be written into one giant string
    ("/user", "Dein Profil"): 
"""profil account konto löschen passwort zurücksetzen neues passwort resetten email e-mail benachrichtigungen deaktivieren 
einstellungen upvoted hochgeladen teilgenommen rolle befördern nutzername""",

    ("/survey/all", "Alle Umfragen"): "umfrage",
    ("/admin/", "Admin Panel"): "admin panel validieren",
    ("/admin/upload", "Upload Panel"): "hochladen neuer erstellen",
    ("/tags/all", "Alle Tags"): "tags"
}

@views.route("/search", methods=["POST"])
def search():
    try:
        search_content = request.form.get("search")
        if search_content == '':
            return redirect('/')
    except KeyError:
        return redirect('/')
    
    terms = search_content.split(' ')

    # deals with double spaces by removing every space still left in the split terms
    while '' in terms:
        terms.remove('')
    while ' ' in terms:
        terms.remove(' ')

    tags: list[str] = []
    five_articles_for_tag: dict = {} # yes that is a stupid name
    # list of (article.id, article.title) (title is needed for frontend display - more efficient than storing entire objects)
    titles: list[list[str, str]] = [] 
    descriptions: list[list[str, str]] = []
    surveys: list[list[str, str]] = [] # (Survey.id, Survey.title)
    announcements: list[list[str, str]] = [] # is actually list[list[str, str, datetime]], for the date created is stored as well
    pages: list[str] = []

    for term in terms:
        tags.extend(
            db.session.query(Tag.tag)
            .filter(Tag.tag.like(f"%{term}%"))
            .all()
        )
        titles.extend(
            db.session.query(Article.id, Article.title)
            .filter(Article.validated == True)
            .filter(Article.title.like(f"%{term}%"))
            .all()
        )
        descriptions.extend(
            db.session.query(Article.id, Article.title, Article.description)
            .filter(Article.validated == True)
            .filter(Article.description.like(f"%{term}%"))
            .all()
        )
        surveys.extend(
            db.session.query(Survey.id, Survey.title)
            .filter(
                or_(
                    Survey.title.like(f"%{term}%"), 
                    Survey.description.like(f"%{term}%")
                )
            )
            .all()
        )
        announcements.extend(
            db.session.query(Announcement.id, Announcement.title, Announcement.date_created)
            .filter(Announcement.validated == True)
            .filter(
                or_(
                    Announcement.title.like(f"%{term}%"),
                    Announcement.content.like(f"%{term}%")
                )
            )
            .order_by(desc(Announcement.date_created))
            .all()
        )

        for match in __MATCH__.items():
            if term in match[1]:
                pages.append(match[0]) # appends dictionary key (which is a url)

        for tag in tags:
            five_articles_for_tag[tag[0]] = get_articles(tag=tag, limit=5)
            
    # `list(dict.fromkeys(list))` is essentially just a way of removing duplicates in a list
    return render_template(
        "search.html",
        tags=list(dict.fromkeys(tags)),
        five_articles_for_tag=five_articles_for_tag,
        titles=list(dict.fromkeys(titles)),
        descriptions=list(dict.fromkeys(descriptions)),
        surveys=list(dict.fromkeys(surveys)),
        announcements=list(dict.fromkeys(announcements)),
        pages=list(dict.fromkeys(pages)),

        search=search_content
    )


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
   

    # used for uncommon Errors that should rarely ever occur
    def __generic__(e):
        return render_template(
            "error/error.html",
            error = {
                "code": e.code,
                "name": e.name
            }
        )

    # used for common errors the user is more likely to stumble upon and it's worth further customizing the page
    def __special__(e):
        error = {
            "code": e.code,
            "name": e.name
        }
        
        if e.code == 403:
            error["description"] = \
"Du bist nicht berechtigt dazu, diese Seite zu besuchen oder diese Aktion durchzuführen. Vielleicht ist Deine Email noch nicht verifiziert, oder Du musst einfach in Die Schülerzeitung kommen :)"
            

        elif e.code == 404:
            error["description"] = \
"Die Seite, die Du besuchen willst, existiert nicht. Vielleicht wurde der Artikel gelöscht, oder Du hast dich vertippt."

        elif e.code == 418:
            error["description"] = e.description
            error["image"] = "teapot"

        elif e.code == 500:
            error["description"] = \
                "Da ist was hinter den Kulissen zusammengebrochen... Wenn Du diesen exakten Error sehr häufig bekommst, wende Dich doch mal an uns. Vielleicht hilfst Du uns dadurch, Fehler zu entdecken :)"
        
        
        return render_template(
            "error/error.html",
            error=error
        )


