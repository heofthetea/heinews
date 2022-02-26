from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path

#declare database for usage
db = SQLAlchemy()
DB_NAME = "test.db" #TODO rename this to something cool on production

"""
initializes application as Flask object
@return flask application
"""
def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = generate_key()

    #create blueprints and set up urls
    from .views import views
    from .articles import articles
    from .admin import admin_panel
    from.dev import dev

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(articles, url_prefix="/article/")
    app.register_blueprint(admin_panel, url_prefix="/admin/")
    app.register_blueprint(dev, url_prefix="/dev/")

    #initialize database
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

#watch out for issue on empty creation
def create_database(app) -> None:
    if not path.exists("app/" + DB_NAME):
        db.create_all(app=app)
        print("Created Database!")
