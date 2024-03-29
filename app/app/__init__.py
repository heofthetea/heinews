from os import getcwd, chdir
from flask import Flask, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, AnonymousUserMixin
from os import path
from werkzeug.security import generate_password_hash as hash
from werkzeug.exceptions import HTTPException
from os import getcwd

# declare database for usage
db = SQLAlchemy()
DB_NAME = "heinews.db"



def send_database() -> SQLAlchemy:
    return send_file(DB_NAME)

try:
    with open("__machine__.txt", "r") as f:
        __IN_PRODUCTION__ = f.read().splitlines()[0] == "production" #idk why the splitlines()[0] but server wants it that way
except FileNotFoundError:
    with open("app/__machine__.txt", "r") as f:
        __IN_PRODUCTION__ = f.read().splitlines()[0] == "production" #idk why the splitlines()[0] but server wants it that way

if not __IN_PRODUCTION__:
    #set this path to the directory `main.py` is in
    chdir("/home/ccdr574/projects/heinews/app")


def get_host() -> tuple:
    return ("217.78.162.125", 80) if __IN_PRODUCTION__ else ("127.0.0.1", 80)

WORKING_DIR = getcwd()
IMAGE_FOLDER = ("static", "img", "articles")
__HOST__ = None

"""
These are the "super-developers". On signup, only these email addresses get immediate developer status, which cannot be revoked.
Why am I caring so much about keeping the addresses hashed and hidden? I don't know. It's fun.
"""
with open("__devs__.txt", "r") as f:
    __DEVELOPERS__ = f.read().splitlines()




__MAIL_ACCOUNT__  = {
    "email": "dev.heinews@gmx.de",
    "password": "H31n3w$^w^3",
    "smtp": ("mail.gmx.net", 587)
}


"""
initializes application as Flask object
registers all Blueprints for url routing and sets up functions accessed by the entire application (e.g. error handlers)
@return flask application
"""
def create_app(host: tuple=None) -> Flask:
    global __HOST__
    __HOST__ = f"{host[0]}:{host[1]}"

    print(__HOST__)
    app = Flask(__name__)
    app.config["SECRET_KEY"] = generate_key()
    app.config['IMAGE_FOLDER'] = IMAGE_FOLDER

    # create blueprints and set up urls
    from .views import views, ErrorPages
    app.register_blueprint(views, url_prefix='/')

    from .auth import auth
    app.register_blueprint(auth, url_prefix='/')

    from .articles import articles
    app.register_blueprint(articles, url_prefix="/article/") #TODO rename url routings ? (to "/articles/") and the overview to "/"

    from .articles import tag
    app.register_blueprint(tag, url_prefix="/tags/")
    
    from .surveys import surveys
    app.register_blueprint(surveys, url_prefix="/survey/")

    from .admin import admin
    app.register_blueprint(admin, url_prefix="/admin/")

    from .dev import dev
    app.register_blueprint(dev, url_prefix="/dev/")


    from . import models

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return models.User.query.get(int(id))

    # initialize database
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_NAME}"
    db.init_app(app)
    create_database(app)

    #---------------------------------------------------------------------------------------------
    # these functions, used by the entire website, have to go here to access the Flask application

    # used to give every template access to the categories (in order to display nav-bar)
    @app.context_processor
    def inject_categories():
        return dict(categories=models.Category.query.all())

    # user needs to be accessable throughout entire website
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user, get_user_role=models.get_user_role, loggedin=user_loggedin)

    # raising http errors in frontend might prove useful
    @app.context_processor
    def inject_httperror():
        return dict(abort=abort)

    # injects functions the frontend may need for article previews etc
    @app.context_processor
    def article_functions():
        return dict(
            cap_text=cap_text,
            title_image_or_placeholder=lambda a: a.primary_image if a.primary_image is not None else "../static/img/placeholder.png"
        )

    @app.errorhandler(Exception)
    def handle_http(error):
        if isinstance(error, HTTPException):
            if error.code in (403, 404, 418, 500):
                return ErrorPages.__special__(error)
            return ErrorPages.__generic__(error)
    
    
    return app


#------------------------------------------------------------------------------------------------------------------------------------
"""
generates random string used as a secure private key
"""
def generate_key(len=256, bounds=(32, 126)) -> str:
    from random import choice

    key = ''.join([chr(choice(range(bounds[0], bounds[1]))) for _ in range(len)])
    return key


# creates database if it does not exist
def create_database(app : Flask) -> None:
    if not path.exists("app/" + DB_NAME):
        with app.app_context():
            db.create_all()
        #db.create_all(app=app)
        print("Created Database!")


def user_loggedin(current_user):
    return not isinstance(current_user, AnonymousUserMixin)


def cap_text(text: str, *, cap: int=27, end: str="...") -> str:
    return text[:cap] + end if len(text) > (cap + len(end)) else text
