from flask import Flask


"""
initializes application as Flask object
@return flask application
"""
def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = generate_key()

    from .views import views
    from .articles import articles

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(articles, url_prefix="/article/")
    
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
