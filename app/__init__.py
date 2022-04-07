from flask import Flask, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, AnonymousUserMixin
from os import path
from werkzeug.security import generate_password_hash as hash
from os import getcwd

# declare database for usage
db = SQLAlchemy()
DB_NAME = "test.db" # TODO rename this to something cool on production

WORKING_DIR = getcwd()
IMAGE_FOLDER = "/static/img/articles"

"""
These are the "super-developers". On signup, only these email addresses get immediate developer status, which cannot be revoked.
Why am I caring so much about keeping the addresses hashed and hidden? I don't know. It's fun.
"""
# TODO store these (already hashed) in file (database would again need to be hardcoded into code)
__DEVELOPERS__ = (hash("fyoug8gle@gmail.com"), hash("egruemer@gmail.com"))

"""
initializes application as Flask object
registers all Blueprints for url routing and sets up functions accessed by the entire application (e.g. error handlers)
@return flask application
"""
def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = generate_key()
    app.config['IMAGE_FOLDER'] = IMAGE_FOLDER

    # create blueprints and set up urls
    from .views import views, ErrorPages
    app.register_blueprint(views, url_prefix='/')

    from .articles import articles
    app.register_blueprint(articles, url_prefix="/article/") #TODO rename url routings ? (to "/articles/") and the overview to "/"

    from .articles import tag
    app.register_blueprint(tag, url_prefix="/tags/")

    from .admin import admin
    app.register_blueprint(admin, url_prefix="/admin/")

    from .auth import auth
    app.register_blueprint(auth, url_prefix='/')

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
    #these functions, used by the entire website, have to go here to access the Flask application

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

    @app.errorhandler(404)
    def page_not_found(error):
        return ErrorPages.__404__()

    
    return app




#------------------------------------------------------------------------------------------------------------------------------------
"""
generates random string used as a secure private key
"""
def generate_key(len=256) -> str:
    from random import choice

    chars, key = range(32, 126), ""
    for _ in range(len):
        key += chr(choice(chars))
    return key

# creates database if it does not exist
def create_database(app : Flask) -> None:
    if not path.exists("app/" + DB_NAME):
        db.create_all(app=app)
        print("Created Database!")

def user_loggedin(current_user):
    return not isinstance(current_user, AnonymousUserMixin)
