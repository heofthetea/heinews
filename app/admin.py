from flask import Blueprint, render_template, url_for, redirect, flash, abort, request
from flask_login import current_user, login_required
from ._lib.docx_to_html import Tag, convert, htmlify, replace_links, create_image_placeholders, fill_image_placeholders
from .models import Article, Role, Category, Tag, Article_Tag, generate_id
from .articles import get_article_location
from . import db, IMAGE_FOLDER, WORKING_DIR
from datetime import datetime
from sqlalchemy import asc
from os import path, mkdir
from werkzeug.utils import secure_filename


#TODO for friday:
# TODO find places in articles for images

PLACEHOLDER = {
    "title": "__title__",
    "category": "__category__"
}
ALLOWED_EXTENSIONS = {"txt", "docx", "doc"} # TODO support txt files because I like them
ALLOWED_IMAGES = {"png", "jpg"}

# I don't like putting this explicitly into my code, but using the built-in `session` dictionary failed handling big enough texts for some reason
cache : dict = {}

admin = Blueprint("admin", __name__)


@login_required
@admin.route("/")
def admin_index():
    try:
        if current_user.role != "validate" and current_user.role != "developer":
            abort(403)
    except AttributeError:
        abort(403)
    invalidated_articles = Article.query.filter_by(validated=False)
    return render_template("admin.html", invalidated_articles=invalidated_articles.order_by(asc(Article.date_created)))
    

@admin.route("/upload")
def redir_upload():
    return redirect(url_for("admin.upload", phase="new"))


#TODO split this up to 2 functions
@admin.route('/upload/<phase>', methods=["GET", "POST"])
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
                flash("Bitte wähle eine Datei aus", category="error")
                return redirect(request.url)
            file = request.files['file']
            # If the user does not select a file, the browser submits an empty file without a filename.
            if file.filename == '':
                flash("Bitte wähle eine Datei aus", category="error")
                return redirect(request.url)
            if not allowed_file(file.filename):
                flash("Dateityp nicht unterstützt (Unterstützt wird: .txt, .doc, .docx)")
            if file and allowed_file(file.filename):
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                if file_extension == "docx" or file_extension == "doc":
                    file_content = convert(file)
                    
                #TODO something
                elif file_extension == "txt":
                    file_content = file.read().decode("utf-8") # file gets read as binary, thus needing to decode
                    file_content = file_content.replace("\n", "<br>")


                file_content : str = replace_links(file_content)
                # caching all data necessary to use in next step (and setting up image cache)
                cache["uploaded_content"] = file_content
                cache["article_id"] = generate_id(6)
                cache["images"] = []
                return redirect(url_for("admin.add_images", article_id=cache["article_id"]))
                
        return render_template("upload/upload.html")

    elif phase == "edit":
        # TODO integrate images with database and article html files
        # contains all necessary operations when article is completely finished (all needed additional arguments are given)
        temp_article_id = cache["article_id"]
        #images = cache["images"]

        if request.method == "POST":
            # receiving data cached in "new" phase
            content = cache["uploaded_content"]


            # replacing placeholders created in conversion with values entered manually in panel form
            title = request.form.get("title")
            content = content.replace(PLACEHOLDER["title"], title)

            category = request.form.get("category")
            content = content.replace(PLACEHOLDER["category"], category)


            primary_image = request.form.get("primary-img")
            for src in cache["images"]:
                image_sauce = request.form.get(f"{src}_source")
                image_description = request.form.get(f"{src}_description") # TODO is None in article

                # TODO make images childs of respective divs
                if src == primary_image:
                    content = f"<figcaption id='primary-image'>{image_sauce}: {image_description}</figcaption>\n</figcaption>\n" + content
                    content = f"<figure>\n<img src='{src}' alt='some image lul u stupid' id='article_img'>\n" + content
                else:
                    #TODO rework to actually display in right place
                    content += f"<figure>\n<img src='{src}' alt='some image lul u stupid' id='article_img'>\n"
                    content += f"<figcaption>{image_sauce}: {image_description}</figcaption>\n</figcaption>\n"

            tags = request.form.get("tags")

            for tag in tags.split(" "):
                if not Tag.query.get(tag): # if tag doesn't already exist
                    db.session.add(Tag(tag=tag))
                db.session.add(Article_Tag(article_id=temp_article_id, tag=tag))
            db.session.commit()

            #TODO implement preview ?

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
            with open(get_article_location(temp_article_id), "w+", encoding="utf-8") as new_article:
                new_article.write(htmlify(content))

            flash("Artikel wurde erfolgreich hochgeladen!", category="success")

            # removing now unecessary cache
            cache.pop("uploaded_content")
            cache.pop("article_id")
            cache.pop("images")
            return redirect(url_for("articles.find_article", path=f"{temp_article_id}.html"))

        return render_template(
            "upload/upload_panel.html", 
            categories=Category.query.all(), 
            article_id=temp_article_id,
            images=cache["images"]
        )


"""
TODO do this as extra step before entering all further information OR integrate it entirely into the primary form (if even possible)

"""

@admin.route("/addimage/<article_id>", methods=["GET","POST"])
def add_images(article_id):
    if request.method == "POST":
        if 'image' not in request.files:
            flash("Bitte wähle eine Bild aus", category="error") 
            return redirect(request.url)
        images = request.files.getlist('image')

        # If the user does not select a file, the browser submits an empty file without a filename.
        if images[0].filename == '':
            flash("Bitte wähle eine Datei aus", category="error")
            return redirect(request.url)
        
        img_folder = path.join(IMAGE_FOLDER, article_id)
        for image in images:
            if not allowed_file(image.filename, ext_dict=ALLOWED_IMAGES):
                flash("Dateityp nicht unterstützt (Unterstützt wird: .png, .jpg)")
            if image and allowed_file(image.filename, ext_dict=ALLOWED_IMAGES):
                if not path.isdir(path.join(WORKING_DIR, "app" + img_folder)):
                    mkdir("app" + img_folder)
                    
                filename = secure_filename(image.filename)
                img_location = path.join(img_folder, filename)
                image.save("app" + img_location)
                cache["images"].append(img_location)
        return redirect(url_for("admin.upload", phase="edit"))
    return render_template("upload/image_upload.html")



#--------------------------------------------------------------------------------------------------------------------------------------------
# I have no idea what this does but it's copied straight from flask documentation and works
def allowed_file(filename, ext_dict : dict=ALLOWED_EXTENSIONS):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ext_dict

