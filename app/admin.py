from flask import Blueprint, render_template, request, redirect, url_for
from .models import Article, generate_id
from . import db


admin_panel = Blueprint("admin", __name__)


@admin_panel.route('/upload', methods=["GET", "POST"])
def upload() -> None:
    #TODO: connect to docx converter here

    #store article address in database
    if request.method == "POST":
        temp_id = generate_id(6)
        new_article = Article(id=temp_id, title="Hello World", category="test")
        db.session.add(new_article)
        db.session.commit()
        add_article(temp_id)

        return redirect(url_for("articles.find_article", path=f"{temp_id}.html")) #TODO redirect to editor panel
        #find_article(f"{temp_id}.html")
    return render_template("upload.html")


"""
creates article as a jinga template
"""
def add_article(id) -> None:
    #TODO: add implementation of docx -> html converter here
    with open(f"app/templates/articles/{id}.html", "w+") as new_article:
        new_article.write('{% extends "article.html" %}\n')
        new_article.write('{% block title %}' + id + '{% endblock %}\n')
        new_article.write('{% block article %}\n')
        new_article.write(
            f'<h1 style="text-align: center">{id}</h1>\n')
        new_article.write('<a href="/">homepage</a>\n')
        new_article.write('<br>')
        new_article.write('<a href="{{ url_for(\'articles.all\') }}"> all articles </a>\n')
        new_article.write('{% endblock %}\n')

