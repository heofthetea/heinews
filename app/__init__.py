from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from os import path

# declare database for usage
db = SQLAlchemy()
DB_NAME = "test.db" # TODO rename this to something cool on production

UPLOAD_FOLDER = "/test_upload"

"""
initializes application as Flask object
@return flask application
"""
def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = generate_key()
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # create blueprints and set up urls
    from .views import views
    app.register_blueprint(views, url_prefix='/')

    from .articles import articles
    app.register_blueprint(articles, url_prefix="/article/")

    from .admin import admin_panel
    app.register_blueprint(admin_panel, url_prefix="/admin/")

    from .auth import auth
    app.register_blueprint(auth, url_prefix='/')

    from.dev import dev
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
    
    return app




#------------------------------------------------------------------------------------------------------------------------------------
"""
generates random string used as a secure private key
"""
def generate_key() -> str:
    from random import choice

    chars, len, key = range(32, 126), 256, ""
    for _ in range(len):
        key += chr(choice(chars))
    return key

# creates database if it does not exist
def create_database(app : Flask) -> None:
    if not path.exists("app/" + DB_NAME):
        db.create_all(app=app)
        print("Created Database!")
