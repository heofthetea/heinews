from flask import Blueprint, render_template, url_for, redirect, flash, abort, request, session
from ._lib.docx_to_html import Tag, convert, htmlify, replace_links
from .models import Article, Role, Category, Tag, Article_tag_connection, generate_id
from flask_login import current_user, login_required
from . import db
from datetime import datetime
from sqlalchemy import asc
# from os import path
# from werkzeug.utils import secure_filename


PLACEHOLDER = {
    "title": "__title__",
    "category": "__category__"
}
ALLOWED_EXTENSIONS = {"txt", "docx", "doc"} # TODO support txt files because I like them

admin_panel = Blueprint("admin", __name__)


@login_required
@admin_panel.route("/")
def admin_index():
    try:
        if current_user.role != "validate" and current_user.role != "developer":
            abort(403)
    except AttributeError:
        abort(403)
    invalidated_articles = Article.query.filter_by(validated=False)
    return render_template("admin.html", invalidated_articles=invalidated_articles.order_by(asc(Article.date_created)))

@admin_panel.route("/upload")
def redir_upload():
    return redirect(url_for("admin.upload", phase="new"))


@admin_panel.route('/upload/<phase>', methods=["GET", "POST"])
@login_required
def upload(phase) -> None:
    #prevents unauthorized users from reaching the upload section
    if not Role.query.get(current_user.role).can_upload:
        abort(403)

    #handles file upload (including validation checks and docx to html conversion)
    if phase == "new":
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash("Bitte wähle eine Datei aus", category="error") # TODO replace with flash
                return redirect(request.url)
            file = request.files['file']
            # If the user does not select a file, the browser submits an empty file without a filename.
            if file.filename == '':
                flash("Bitte wähle eine Datei aus", category="error") # TODO replace with flash
                return redirect(request.url)
            if not allowed_file(file.filename):
                flash("Dateityp nicht unterstützt (Unterstützt wird: .txt, .doc, .docx)")
            if file and allowed_file(file.filename):
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                if file_extension == "docx" or file_extension == "doc":
                    file_content = convert(file)
                    
                elif file_extension == "txt":
                    file_content = file.read().decode("utf-8") # file gets read as binary, thus needing to decode
                    file_content = file_content.replace("\n", "<br>")

                file_content = replace_links(file_content)
                session["uploaded_content"] = file_content  # caching content of file in order to work with it in next step
                return redirect(url_for("admin.upload", phase="edit"))
                
        return render_template("upload.html")

    elif phase == "edit":
        # contains all necessary operations when article is completely finished (all needed additional arguments are given)
        if request.method == "POST":
            # replacing placeholders created in conversion with values entered manually in panel form
            content = session["uploaded_content"]
            title = request.form.get("title")
            #content = content.replace(PLACEHOLDER["title"], title)

            category = request.form.get("category")
            content = content.replace(PLACEHOLDER["category"], category)

            tags = request.form.get("tags")

            temp_article_id = generate_id(6)
            for tag in tags.split(" "):
                if not Tag.query.get(tag): # if tag doesn't already exist
                    db.session.add(Tag(tag=tag))
                db.session.add(Article_tag_connection(article_id=temp_article_id, tag=tag))
            db.session.commit()

            #TODO implement preview (including ability to insert images "into preview" etc.)

            # creating entry in database
            
            new_article = Article(id=temp_article_id, 
                                  title=title,
                                  date_created=datetime.utcnow(),
                                  category=category,
                                  creator_email=current_user.email)
                                  
            db.session.add(new_article)
            db.session.commit()
            # storing html file (happens after db entry because db operations are more likely to go wrong 
            #                    -> avoids having a file without a corresponding db entry)
            with open(f"app/templates/articles/{temp_article_id}.html", "w+", encoding="utf-8") as new_article:
                new_article.write(htmlify(content))

            flash("Artikel wurde erfolgreich hochgeladen!", category="success")
            session.pop("uploaded_content") # getting rid of unecessary cache
            return redirect(url_for("articles.find_article", path=f"{temp_article_id}.html"))

        return render_template("upload_panel.html", categories=Category.query.all())



#-------------------------------------------------------------------------------------------------------------------------------------------------------
# I have no idea what this does but it's copied straight from flask documentation and works
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

