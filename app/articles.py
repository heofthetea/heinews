from flask import Blueprint, render_template

articles = Blueprint("articles", __name__)

#render requested article as template
@articles.route('/<path:path>')
def find_article(path):
    #return send_from_directory('articles', path)
    return render_template(f"articles/{path}")
