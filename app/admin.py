from flask import Blueprint, render_template, url_for, redirect, request, session
from .models import Article, User, Role, Category, generate_id
from flask_login import current_user, login_required
from . import db
from datetime import datetime

placeholder = {
    "title": "__title__",
    "category": "__category__"
}

admin_panel = Blueprint("admin", __name__)


@admin_panel.route('/upload/<phase>', methods=["GET", "POST"])
@login_required
def upload(phase) -> None:
    if phase == "new":
        if not Role.query.filter_by(name=current_user.role).first().can_upload:
            return render_template("upload.html", authorized=False)
        #TODO: connect to docx converter here

        print(request.method)
        if request.method == "POST":
            page_content = generate_html(current_user)
            session["uploaded_content"] = page_content
            return redirect(url_for("admin.upload", phase="edit"))
        return render_template("upload.html", authorized=Role.query.filter_by(name=current_user.role).first().can_upload)
        #return render_template("upload.html", authorized=True)
    elif phase == "edit":
        if request.method == "POST":
            content = session["uploaded_content"]
            title = request.form.get("title")
            content = content.replace(placeholder["title"], title)

            category = request.form.get("category")
            content = content.replace(placeholder["category"], category)

            temp_id = generate_id(6)
            new_article = Article(id=temp_id, 
                                  title=title,
                                  date_created=datetime.utcnow(),
                                  validated=False,
                                  category=category,
                                  creator_email=current_user.email)
            db.session.add(new_article)
            db.session.commit()
            with open(f"app/templates/articles/{temp_id}.html", "w+") as new_article:
                new_article.write(content)
            return redirect(url_for("articles.find_article", path=f"{temp_id}.html"))

        return render_template("upload_panel.html", categories = Category.query.all())





"""
creates article as a jinga template
TODO pass Article object as parameter and extract all necessary information from that
"""
def generate_html(author : User) -> None:
    #TODO: add implementation of docx -> html converter here
    #with open(f"app/templates/articles/{id}.html", "w+") as new_article:
    content = ""
    content += '{% extends "article.html" %}\n'
    #content += '{% block title %}' + id + '{% endblock %}\n'
    content += '{% block title %}' + placeholder["title"] + '{% endblock %}\n'
    content += '{% block article %}\n'
    content += f'<h1 style="text-align: center">{placeholder["title"]}</h1>\n'
    content += '<a href="/">homepage</a>\n'
    content += '<br>'
    content += '<a href="{{ url_for(\'articles.all\') }}"> all articles </a>\n'
    content += f"<br>created by: {author.email}\n"
    content += '{% endblock %}\n'

    return content

