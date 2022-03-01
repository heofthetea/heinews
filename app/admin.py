from flask import Blueprint, render_template, request, redirect, url_for
from .models import Article, User, Role, generate_id
from flask_login import current_user, login_required
from . import db


admin_panel = Blueprint("admin", __name__)


@admin_panel.route('/upload/<phase>', methods=["GET", "POST"])
@login_required
def upload(phase) -> None:
    if phase == "":
        if not Role.query.filter_by(name=current_user.role).first().can_upload:
            return render_template("upload.html", authorized=False)
        #TODO: connect to docx converter here

        #store article address in database
        if request.method == "POST":
            temp_id = generate_id(6)
            new_article = Article(id=temp_id, title="Hello World", category="test", creator_email=current_user.email)
            db.session.add(new_article)
            db.session.commit()
            page_content = generate_html(temp_id, current_user)

            #return redirect(url_for("articles.find_article", path=f"{temp_id}.html")) #TODO redirect to editor panel
            #return render_template("upload_panel.html", content=page_content)
        #return render_template("upload.html", authorized=Role.query.filter_by(name=current_user.role).first().can_upload)
        return render_template("upload.html", authorized=True)
    elif phase == "edit":
        return render_template("upload_panel.html")





"""
creates article as a jinga template
TODO pass Article object as parameter and extract all necessary information from that
"""
def generate_html(id : str, author : User) -> None:
    #TODO: add implementation of docx -> html converter here
    #with open(f"app/templates/articles/{id}.html", "w+") as new_article:
    content = ""
    content += '{% extends "article.html" %}\n'
    content += '{% block title %}' + id + '{% endblock %}\n'
    content += '{% block article %}\n'
    content += f'<h1 style="text-align: center">{id}</h1>\n'
    content += '<a href="/">homepage</a>\n'
    content += '<br>'
    content += '<a href="{{ url_for(\'articles.all\') }}"> all articles </a>\n'
    content += f"<br>created by: {author.email}\n"
    content += '{% endblock %}\n'

    return content

