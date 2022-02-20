from flask import Blueprint, send_from_directory

articles = Blueprint("articles", __name__)

#render static html file
# -> article files probably cannot inherit from html template -> store every new article as fully functioning html file
@articles.route('/<path:path>')
def find_article(path):
    return send_from_directory('articles', path)
