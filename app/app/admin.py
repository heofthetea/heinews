from flask import Blueprint, render_template, url_for, redirect, flash, abort, request
from flask_login import current_user, login_required
from ._lib.docx_to_html import Tag, __IMAGE__, convert, htmlify, replace_links, create_image_placeholders, fill_image_placeholders
from ._lib.cache import Cache, CacheDistribution
from .models import Article, Role, Category, Tag, Article_Tag, Survey, Answer, User_Answer, Announcement, generate_id
from .articles import get_article_location
from .auth import get_checkbutton
from . import db, IMAGE_FOLDER, WORKING_DIR, __IN_PRODUCTION__
from datetime import datetime, timedelta
from sqlalchemy import asc
from os import path, mkdir
from werkzeug.utils import secure_filename
from typing import List, Tuple


ALLOWED_EXTENSIONS = {"txt", "docx", "doc"}
ALLOWED_IMAGES = {"png", "jpg"}

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

admin = Blueprint("admin", __name__)
cache_distr = CacheDistribution()


@admin.route("/")
@login_required
def admin_index():
    try:
        if current_user.role != "validate" and current_user.role != "developer":
            abort(403)
        if not current_user.email_confirmed:
            flash("Hierfür musst Du erst Deine Email verifizieren! Schau mal in Deinem Email-Postfach nach :)", category="error")
            return redirect(redirect(request.url))
    except AttributeError:
        abort(403)
    invalidated_articles = Article.query.filter_by(validated=False)
    return render_template("admin.html", invalidated_articles=invalidated_articles.order_by(asc(Article.date_created)).all())


#TODO split this up to 2 functions
@admin.route('/upload', methods=["GET", "POST"])
@login_required
def new_article() -> None:
    log = lambda msg : print(f"admin.new_article -> {msg}")

    try: # yeah this is absoutely ugly but there's no better way of logging what actually happened - Flask only throws 500's without context
    #prevents unauthorized users from reaching the upload section
        if not Role.query.get(current_user.role).can_upload:
            abort(403)
        if not current_user.email_confirmed:
            flash("Hierfür musst Du erst Deine Email verifizieren! Schau mal in Deinem Email-Postfach nach :)", category="error")
            return redirect("/admin")

        #handles file upload (including validation checks and docx to html conversion)
        if request.method == 'POST':
            if "create-survey" in request.form:
                session_id = generate_id(6, table=Survey)
                cache = cache_distr.create_cache(session_id)
                if get_checkbutton(request.form.get("text-answer")):
                    cache.set_num_answers(1)
                else:
                    cache.set_num_answers(request.form.get("num-answers"))
                log(f"created Cache: {cache.__repr__()}")
                return redirect(url_for("admin.create_survey", session_id=session_id))

            if "create-announcement" in request.form:
                return redirect(url_for("admin.create_announcement"))

            #--------------------------------------------------------------------------------------------------------------------------

            # id already has to be declared here, because the cache needs its unique key - otherwise, there won't be more than one person able to 
            # upload anything
            session_id = generate_id(6)
            cache = cache_distr.create_cache(session_id)
            log(f"created Cache: {cache.__repr__()}")
            if "upload-article" in request.form:
                # check if the post request has the file part
                if 'file' not in request.files:
                    flash("Bitte wähle eine Datei aus", category="error")
                    return redirect(request.url)
                file = request.files['file']
                log("received file from client")
                # If the user does not select a file, the browser submits an empty file without a filename.
                if file.filename == '':
                    flash("Bitte wähle eine Datei aus", category="error")
                    return redirect(request.url)
                if not allowed_file(file.filename):
                    flash("Dateityp nicht unterstützt (Unterstützt wird: .txt, .doc, .docx)", category="error")
                if file and allowed_file(file.filename):
                    log(f"accepted file: {file.filename}")
                    file_extension = file.filename.rsplit('.', 1)[1].lower()
                    if file_extension == "docx" or file_extension == "doc":
                        file_content = convert(file)
                        log("successfully converted DOCX file content to HTML")
                        
                    elif file_extension == "txt":
                        file_content = file.read().decode("utf-8") # file gets read as binary, thus needing to decode
                        file_content = file_content.replace("\n", "<br>")
                        log("successfully read TXT file")



                    file_content : str = replace_links(file_content)
                    log("converted links in file content to HTML")
                    # caching all data necessary to use in next step (and setting up image cache)
                    cache.set_article_content(file_content)
                    cache.set_num_images(int(request.form.get("num-images")))
                    log(f"updated cache: {cache.__repr__()}")
                    if cache.get_num_images() == 0:
                        return redirect(url_for("admin.edit_article", article_id=session_id))
                    return redirect(url_for("admin.add_images", article_id=session_id))
                
        return render_template("upload/upload.html")
    except Exception as e:
        log(e)


@admin.route("/addimage/<article_id>", methods=["GET", "POST"])
@login_required
def add_images(article_id):
    log = lambda msg : print(f"admin.add_images -> {msg}")
    cache: Cache = cache_distr.get_cache(article_id)

    log(f"loaded cache: {cache.__repr__()}")
    try:
        num_images = cache.get_num_images()
        log(f"loaded @{article_id}-num_images from cache: {num_images}")
        
        if request.method == "POST":
            relative_img_folder = path.join(f"{'/'.join(IMAGE_FOLDER)}", article_id)
            log(f"established relative image folder: {relative_img_folder}")
            for i in range(num_images):
                if f"image-{i}" not in request.files:
                    flash("Bitte wähle für jedes Feld ein Bild aus", category="error")
                    return redirect(request.url)
                image = request.files.get(f'image-{i}')
                log(f"loaded image {i}")

                if not allowed_file(image.filename, ext_dict=ALLOWED_IMAGES):
                    flash("Dateityp nicht unterstützt (Unterstützt wird: .png, .jpg)")
                if image and allowed_file(image.filename, ext_dict=ALLOWED_IMAGES):

                    # FUCK IT. Since on the server, the static folder is in a different place, this entire shit has to be rewritten. 
                    # HOWEVERRRRRR that then would not work locally so FUCK IT I'm just saving every image twice. FUCK YOU FLASK.
                    # and yes these two blocks LITERALLY ONLY DIFFERENTIATE BY ONE `app` THIS IS SO RIDICULOUSLYS STUPID
                    if not __IN_PRODUCTION__:
                        if not path.isdir(path.join(WORKING_DIR, f"app/{'/'.join(IMAGE_FOLDER)}")):
                            mkdir(path.join(WORKING_DIR, f"app/{'/'.join(IMAGE_FOLDER)}"))

                        absoulute_img_folder = path.join(WORKING_DIR, f"app/{'/'.join(IMAGE_FOLDER)}/{article_id}")
                        if not path.isdir(absoulute_img_folder):
                            mkdir(absoulute_img_folder)
                            log(f"created image folder at: {absoulute_img_folder}")

                        image.filename = f"{generate_id(8)}.{image.filename.rsplit('.', 1)[1].lower()}"
                        filename = secure_filename(image.filename)
                        img_location = path.join(relative_img_folder, filename)
                        log(f"established image location: {'app/' + img_location}")
                        image.save("app/" + img_location)
                        log(f"saved image to established location")
                        cache.add_image(img_location)
                        log(f"added image location to cache: {cache.get_images()}")

                    elif __IN_PRODUCTION__:
                        if not path.isdir(path.join(WORKING_DIR, f"{'/'.join(IMAGE_FOLDER)}")):
                            mkdir(path.join(WORKING_DIR, f"{'/'.join(IMAGE_FOLDER)}"))

                        absoulute_img_folder = path.join(WORKING_DIR, f"{'/'.join(IMAGE_FOLDER)}/{article_id}")
                        if not path.isdir(absoulute_img_folder):
                            mkdir(absoulute_img_folder)
                            log(f"created image folder at: {absoulute_img_folder}")

                        image.filename = f"{generate_id(8)}.{image.filename.rsplit('.', 1)[1].lower()}"
                        filename = secure_filename(image.filename)
                        img_location = path.join(relative_img_folder, filename)
                        log(f"established image location: {img_location}")
                        image.save(f"/{img_location}") # please just don't ask why the slash has to be there it just has to
                        log(f"saved image to established location")
                        cache.add_image(img_location)
                        log(f"added image location to cache: {cache.get_images()}")

            return redirect(url_for("admin.edit_article", article_id=article_id))

        log("rendering template: upload/upload_images.html")
        return render_template(
            "upload/upload_images.html",
            num_images=num_images
        )
    except Exception as e:
        log(e)


@admin.route("/upload/<article_id>", methods=["GET", "POST"])
@login_required
def edit_article(article_id):
    log = lambda msg : print(f"admin.edit_article -> {msg}")
    cache: Cache = cache_distr.get_cache(article_id)
    
    # contains all necessary operations when article is completely finished (all needed additional arguments are given)
    try:
        if request.method == "POST":
            content = cache.get_article_content()
            log(f"successfully loaded content from cache: {content[:8]}...")
            content = create_image_placeholders(content)
            log("successfully created image placeholders")


            # replacing placeholders created in conversion with values entered manually in panel form
            title = request.form.get("title")
            category = request.form.get("category")
            description = request.form.get("description")
            submitted = request.form.get("submitted")
            log("received metadata from form")

            primary_image = request.form.get("primary-img")
            title_image = None # declared as None so that if no primary image is given it will be None in the database
            image_data: List[Tuple[str, str]] = []
            # loops over uploaded images
            for image in cache.get_images():
                if image == primary_image:
                    content = __IMAGE__(
                        image, request.form.get(f"{image}_source"), 
                        request.form.get(f"{image}_description"), 
                        id="primary-image") \
                    + content
                    title_image = image
                    cache.set_num_images(cache.get_num_images() - 1)  # necessary to not place title image twice in article
                    log(f"successfully appended title image to cache: {image_data}")
                else:
                    image_data.append((
                        image,
                        request.form.get(f"{image}_source"), 
                        request.form.get(f"{image}_description"))
                    )
                    log(f"successfully appended regular image to cache: {image_data}")

            content = fill_image_placeholders(content, image_data)
            log("successfully placed images in HTML")
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
                log(f"successfully created Article_Tag entity for {tag}")

            # creating entry in database
            new_article = Article(
                id=article_id,
                title=title,
                description=description,
                date_created=datetime.utcnow(),
                official=not(get_checkbutton(submitted)),
                primary_image=title_image,
                category=category,
                creator_email=current_user.email,
            )
            log(f"successfully created Article entity {new_article}")
                                    
            db.session.add(new_article)
            db.session.commit()
            log("successfully commited to database")
            # storing html file (happens after db entry because db operations are more likely to go wrong 
            #                    -> avoids having a file without a corresponding db entry)
            with open(get_article_location(article_id), "w+", encoding="utf-8") as new_article:
                new_article.write(htmlify(content))
                log("successfully created template")

            flash("Artikel wurde erfolgreich hochgeladen!", category="success")
            cache_distr.remove_cache(article_id)
            return redirect(url_for("articles.find_article", path=f"{article_id}.html"))
            

        log("rendering template: upload/upload_panel.html")
        return render_template(
            "upload/upload_panel.html", 
            categories=Category.query.all(), 
            article_id=article_id,
            images=cache.get_images()
        )
    except Exception as e:
        log(e)

#--------------------------------------------------------------------------------------------------------------------------------------------

# create system to view (results of) survey
# 
@admin.route("/newsurvey/<session_id>", methods=["GET", "POST"])
@login_required
def create_survey(session_id):
    log = lambda msg : print(f"admin.create_survey -> {msg}")
    cache: Cache = cache_distr.get_cache(session_id)
    log(f"loaded cache: {cache.__repr__()}")
    
    try:
        if Survey.query.get(session_id):
            log(f"survey id already in use: {session_id}")
            abort(409)
        num_answers = int(cache.get_num_answers())
        if request.method == "POST":
            correct_answer = request.form.get("correct-answer")
            
            new_survey = Survey (
                id=session_id,
                title=request.form.get("title"),
                description=request.form.get("description"),
                text_answer=(num_answers == 1),
                expiry_date=datetime.now() + timedelta(int(request.form.get("expiry-date"))),
                results_visible=get_checkbutton(request.form.get("results-visible"))
            )
            db.session.add(new_survey)
            log(f"created Survey entity {new_survey}")
            if num_answers > 1: # survey works with non-text answers
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
                    log(f"successfully created Answer entitiy for answer {i}")

            db.session.commit()
            log("successfully commited to database")
            cache_distr.remove_cache(new_survey.id)
            return redirect(url_for("surveys.survey", id=new_survey.id))
        return render_template("upload/upload_survey.html", num_answers=num_answers, text_answer=num_answers == 1)
    except Exception as e:
        log(e)


@admin.route("/newannouncement", methods=["GET", "POST"])
@login_required
def create_announcement():
    log = lambda msg : print(f"admin.create_announcement -> {msg}")

    try:
        if request.method == "POST":
            title = request.form.get("title")
            content = replace_dangerous_characters(replace_links(request.form.get("content")))
            log("received metadata from form")

            db.session.add(
                Announcement(
                    id=generate_id(6, table=Announcement),
                    title=title,
                    content=content,
                    creator_email=current_user.email
                )
            )
            log("successfully created Announcement entity")
            db.session.commit()
            log("successfully commited to database")
            flash("Die Ankündigung wurde erstellt. Jetzt muss nur noch ein Chefredakteur drüber schauen, und dann geht's an die Schüler!", 
                category="success")
            return redirect('/')

        return render_template("upload/upload_announcement.html")
    except Exception as e:
        log(e)

#--------------------------------------------------------------------------------------------------------------------------------------------

# I have no idea what this does but it's copied straight from flask documentation and works
def allowed_file(filename, ext_dict: dict=ALLOWED_EXTENSIONS) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ext_dict

