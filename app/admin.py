from flask import Blueprint, render_template, url_for, redirect, flash, abort, request
from flask_login import current_user, login_required
from ._lib.docx_to_html import Tag, convert, htmlify, replace_links, create_image_placeholders, fill_image_placeholders
from .models import Article, Role, Category, Tag, Article_Tag, Survey, Answer, User_Answer, Announcement, generate_id
from .articles import get_article_location
from . import db, IMAGE_FOLDER, WORKING_DIR
from datetime import datetime, timedelta
from sqlalchemy import asc
from os import path, mkdir
from werkzeug.utils import secure_filename


#TODO! find places in articles for images

ALLOWED_EXTENSIONS = {"txt", "docx", "doc"}
ALLOWED_IMAGES = {"png", "jpg"}


def __IMAGE__(html_source: str, user_source: str, description: str, *, id="article-image") -> str:
    # these parantheses are important
    return (
# write your html into that multiline string
# css for that html is currently stored in `articles.css`
f"""
<figure>
    <img src="{html_source}" alt="Bild konnte nicht geladen werden" id="{id}">
    <figcaption id="{id}">
        <i>Quelle: {user_source}</i> - {description}
    </figcaption>
</figure>
"""
)

"""
source: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html#xss-prevention-rules-summary
&    &amp;
<    &lt;
>    &gt;
"    &quot;
'    &#x27;
/    &#x2F;
"""
__DANGEROUS_CHARACTERS__ = {
    "<": "&lt;",
    ">": "&gt;",
    "&": "&amp;",
    '"': "&quot;",
    "'": "&#x27;",
    "/": "&#x2F;"
}

"""
replaces every potentially dangerous character with its safe version as per the dictionary above
"""
def replace_dangerous_characters(text: str) -> str:
    for char in __DANGEROUS_CHARACTERS__:
        text = text.replace(char, __DANGEROUS_CHARACTERS__[char])
    return text

# I don't like putting this explicitly into my code, but using the built-in `session` dictionary failed handling big enough texts for some reason
cache : dict = {}

admin = Blueprint("admin", __name__)


@admin.route("/")
@login_required
def admin_index():
    try:
        if current_user.role != "validate" and current_user.role != "developer":
            abort(403)
        if not current_user.email_confirmed:
            flash("Hierfür musst du erst deine Email verifizieren! Schau mal in deinem Email-Postfach nach :)", category="error")
            return redirect(redirect(request.url))
    except AttributeError:
        abort(403)
    invalidated_articles = Article.query.filter_by(validated=False)
    return render_template("admin.html", invalidated_articles=invalidated_articles.order_by(asc(Article.date_created)).all())


#TODO split this up to 2 functions
@admin.route('/upload', methods=["GET", "POST"])
@login_required
def new_article() -> None:
    #prevents unauthorized users from reaching the upload section
    if not Role.query.get(current_user.role).can_upload:
        abort(403)
    if not current_user.email_confirmed:
        flash("Hierfür musst du erst deine Email verifizieren! Schau mal in deinem Email-Postfach nach :)", category="error")
        return redirect("/admin")

    #handles file upload (including validation checks and docx to html conversion)
    if request.method == 'POST':
        if "create-survey" in request.form:
            session_id = generate_id(6, table=Survey)
            cache[f"{session_id}-num_answers"] = request.form.get("num-answers")
            return redirect(url_for("admin.create_survey", session_id=session_id))

        if "create-announcement" in request.form:
            return redirect(url_for("admin.create_announcement"))

        #--------------------------------------------------------------------------------------------------------------------------

        # id already has to be declared here, because the cache needs its unique key - otherwise, there won't be more than one person able to 
        # upload anything
        session_id = generate_id(6)
        if "upload-article" in request.form:
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
                flash("Dateityp nicht unterstützt (Unterstützt wird: .txt, .doc, .docx)", category="error")
            if file and allowed_file(file.filename):
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                if file_extension == "docx" or file_extension == "doc":
                    file_content = convert(file)
                    
                elif file_extension == "txt":
                    file_content = file.read().decode("utf-8") # file gets read as binary, thus needing to decode
                    file_content = file_content.replace("\n", "<br>")


                file_content : str = replace_links(file_content)
                # caching all data necessary to use in next step (and setting up image cache)
                cache[f"{session_id}-uploaded_content"] = file_content
                cache[f"{session_id}-num_images"] = int(request.form.get("num-images"))
                cache[f"{session_id}-images"] = []
                if cache[f"{session_id}-num_images"] == 0:
                    return redirect(url_for("admin.edit_article", article_id=session_id))
                return redirect(url_for("admin.add_images", article_id=session_id))
            
    return render_template("upload/upload.html")



@admin.route("/addimage/<article_id>", methods=["GET", "POST"])
@login_required
def add_images(article_id):
    if request.method == "POST":
        img_folder = path.join(IMAGE_FOLDER, article_id)
        for i in range(cache[f"{article_id}-num_images"]):
            if f"image-{i}" not in request.files:
                flash("Bitte wähle für jedes Feld ein Bild aus", category="error")
                return redirect(request.url)
            image = request.files.get(f'image-{i}')

            if not allowed_file(image.filename, ext_dict=ALLOWED_IMAGES):
                flash("Dateityp nicht unterstützt (Unterstützt wird: .png, .jpg)")
            if image and allowed_file(image.filename, ext_dict=ALLOWED_IMAGES):
                if not path.isdir(path.join(WORKING_DIR, "app" + img_folder)):
                    mkdir("app" + img_folder)

                image.filename = f"{generate_id(8)}.{image.filename.rsplit('.', 1)[1].lower()}"
                filename = secure_filename(image.filename)
                img_location = path.join(img_folder, filename)
                image.save("app" + img_location)
                cache[f"{article_id}-images"].append(img_location)

        return redirect(url_for("admin.edit_article", article_id=article_id))

    return render_template(
        "upload/upload_images.html",
        num_images=cache[f"{article_id}-num_images"]
        )


@admin.route("/upload/<article_id>", methods=["GET", "POST"])
@login_required
def edit_article(article_id):
    # contains all necessary operations when article is completely finished (all needed additional arguments are given)

    if request.method == "POST":
        # receiving data cached in "new" phase
        content = cache[f"{article_id}-uploaded_content"]


        # replacing placeholders created in conversion with values entered manually in panel form
        title = request.form.get("title")
        category = request.form.get("category")
        description = request.form.get("description")

        primary_image = request.form.get("primary-img")
        title_image = None # declared as None so that if no primary image is given it will be None in the database
        for image in cache[f"{article_id}-images"]:
            image_source = request.form.get(f"{image}_source")
            image_description = request.form.get(f"{image}_description")

            # TODO make images children of respective divs
            if image == primary_image:
                content = __IMAGE__(image, image_source, image_description, id="primary-image") + content
                title_image = image
            else:
                #TODO rework to actually display in right place
                content += __IMAGE__(image, image_source, image_description)

        tags = request.form.get("tags")

        for tag in tags.split(" "):
            if not Tag.query.get(tag): # if tag doesn't already exist
                db.session.add(Tag(tag=tag))
            db.session.add(
                Article_Tag(
                    article_id=article_id, 
                    tag=tag
                )
            )
        db.session.commit()

        # creating entry in database
        
        new_article = Article(
            id=article_id,
            title=title,
            description=description,
            date_created=datetime.utcnow(),
            primary_image=title_image,
            category=category,
            creator_email=current_user.email,
        )
                                
        db.session.add(new_article)
        db.session.commit()
        # storing html file (happens after db entry because db operations are more likely to go wrong 
        #                    -> avoids having a file without a corresponding db entry)
        with open(get_article_location(article_id), "w+", encoding="utf-8") as new_article:
            new_article.write(htmlify(content))

        flash("Artikel wurde erfolgreich hochgeladen!", category="success")

        # removing now unecessary cache
        cache.pop(f"{article_id}-uploaded_content")
        cache.pop(f"{article_id}-num_images")
        cache.pop(f"{article_id}-images")
        return redirect(url_for("articles.find_article", path=f"{article_id}.html"))

    return render_template(
        "upload/upload_panel.html", 
        categories=Category.query.all(), 
        article_id=article_id,
        images=cache[f"{article_id}-images"]
    )

#--------------------------------------------------------------------------------------------------------------------------------------------

# create system to view (results of) survey
# 
@admin.route("/newsurvey/<session_id>", methods=["GET", "POST"])
@login_required
def create_survey(session_id):
    num_answers = int(cache[f"{session_id}-num_answers"])
    if request.method == "POST":
        correct_answer = request.form.get("correct-answer")
        print(request.form.get("expiry-date"))

        new_survey = Survey(
            id=session_id,
            title=request.form.get("title"),
            description=request.form.get("description"),
            expiry_date=datetime.now() + timedelta(int(request.form.get("expiry-date")))
        )
        db.session.add(new_survey)

        for i in range(num_answers):
            if correct_answer is None:
                correct = None
            else:
                correct = True if i == int(correct_answer) else False

            db.session.add(
                Answer(
                    value=request.form.get(f"answer-{i}"),
                    correct=correct,
                    survey=new_survey.id
                )
            )

        db.session.commit()
        cache.pop(f"{session_id}-num_answers")
        return redirect(url_for("surveys.survey", id=new_survey.id))
    return render_template("upload/upload_survey.html", num_answers=num_answers)


@admin.route("/newannouncement", methods=["GET", "POST"])
@login_required
def create_announcement():
    if request.method == "POST":
        title = request.form.get("title")
        content = replace_dangerous_characters(replace_links(request.form.get("content")))

        db.session.add(
            Announcement(
                id=generate_id(6, table=Announcement),
                title=title,
                content=content,
                creator_email=current_user.email
            )
        )
        db.session.commit()
        flash("Die Ankündigung wurde erstellt. Jetzt muss nur noch ein Chefredakteur drüber schauen, und dann geht's an die Schüler!", 
            category="success")
        return redirect('/')

    return render_template("upload/upload_announcement.html")

#--------------------------------------------------------------------------------------------------------------------------------------------

# I have no idea what this does but it's copied straight from flask documentation and works
def allowed_file(filename, ext_dict: dict=ALLOWED_EXTENSIONS) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ext_dict

