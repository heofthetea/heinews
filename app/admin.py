from flask import Blueprint, render_template, request, redirect, url_for
from .models import Article, User, Role, generate_id
from flask_login import current_user, login_required
from . import db


admin_panel = Blueprint("admin", __name__)


@admin_panel.route('/upload', methods=["GET", "POST"])
@login_required
def upload() -> None:
    print(current_user.role)
    if not Role.query.filter_by(name=current_user.role).first().can_upload:
        return render_template("upload.html", authorized=False)
    #TODO: connect to docx converter here

    #store article address in database
    if request.method == "POST":
        temp_id = generate_id(6)
        new_article = Article(id=temp_id, title="Hello World", category="test", creator_email=current_user.email)
        db.session.add(new_article)
        db.session.commit()
        add_article(temp_id, current_user)

        return redirect(url_for("articles.find_article", path=f"{temp_id}.html")) #TODO redirect to editor panel
    #return render_template("upload.html", authorized=Role.query.filter_by(name=current_user.role).first().can_upload)
    return render_template("upload.html", authorized=True)


"""
creates article as a jinga template
TODO pass Article object as parameter and extract all necessary information from that
"""
def add_article(id : str, author : User) -> None:
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
        new_article.write(f"<br>created by: {author.email}\n")
        new_article.write('{% endblock %}\n')

