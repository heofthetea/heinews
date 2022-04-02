from sqlalchemy import event, DDL
from sqlalchemy.sql import func
from . import db
from flask_login import UserMixin

# is it necessary to give everything a power of 2 as a length? No. Do I do it anyway? Yes, why not.


#TODO add something like Article.needs_modification for when an article is not approved by validation
class Article(db.Model):
    id = db.Column(db.String(6), primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.String(256))
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    validated = db.Column(db.Boolean(), default=False)
    upvotes = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(64), db.ForeignKey("category.name"))
    creator_email = db.Column(db.String(64), db.ForeignKey("user.email"))


class Article_Images(db.Model):
    id = db.Column(db.String(6), primary_key=True)
    location = db.Column(db.String(12), unique=True, nullable=False)
    

class Category(db.Model):
    name = db.Column(db.String(32), primary_key=True)


#TODO when new Tag are created and exceed length limit, flash message
class Tag(db.Model):
    tag = db.Column(db.String(32), primary_key=True)



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True)
    email_confirmed = db.Column(db.Boolean(), default=False)
    password = db.Column(db.String(128))
    notifications = db.Column(db.Boolean())
    role = db.Column(db.String(32), db.ForeignKey("role.name"))



class Role(db.Model):
    name = db.Column(db.String(32), primary_key=True)
    can_upload = db.Column(db.Boolean())
    can_validate = db.Column(db.Boolean())


#-----------------------------------------------------------------------------------------------------------------------------------
# @REGION connections

class Article_Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.String(6), db.ForeignKey("article.id"))
    tag = db.Column(db.String(32), db.ForeignKey("tag.tag"))


"""
if user upvotes an article, an entry is created
if that upvote gets removed, the entry is deleted again
in case an article gets deleted (for whatever reason), all entries involving this article should be deleted as well to save space
"""
class User_Upvote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    article_id = db.Column(db.String(6), db.ForeignKey("article.id"))


#-----------------------------------------------------------------------------------------------------------------------------------
"""
writes default entries into database when database is created
-> those values should never change
"""
event.listen(Category.__table__, "after_create", 
        DDL("INSERT INTO category (name) VALUES ('aktuelles'), ('wissen'), ('schulleben'), ('lifestyle'), ('unterhaltung'), ('kreatives')"))

event.listen(Role.__table__, "after_create",
        DDL("INSERT INTO role (name, can_upload, can_validate) "
        "VALUES ('user', False, False), ('upload', True, False), ('validate', False, True), ('developer', True, True)"))


"""
generates unique id following pattern:
1. generate random hexadecimal value
2. if there's already an article with that id, generate a new one

@return 6-digit unique hexadecimal id
"""
def generate_id(len: int) -> str:
    from random import choice

    digits = [str(i) for i in range(10)]
    digits.extend(['a', 'b', 'd', 'e', 'f'])

    generate_temp = lambda : ''.join([choice(digits) for _ in range(len)])

    temp_id = generate_temp()
    while Article.query.get(str(temp_id)):
        temp_id = generate_temp()
    
    return temp_id

"""
@param tag (as Tag instance): tag to look for articles having it 
@return: list containing all articles (as Article instance) marked by the tag

connections: Find all occurances where the given tag object is connected with an article
query in return statement: for every of these connections, find the corresponding Article object through its id
corresponding SQL query of this function: 
    SELECT * FROM article, tag, article_tag_connection 
    WHERE tag.tag = tag[function parameter]
    AND article_tag_connection.tag = tag.tag
    AND article_tag_connection.article_id = article.id;
"""
def get_articles(tag: Tag) -> list[Article]:
    connections = Article_Tag.query.filter_by(tag=tag.tag).all()
    return [Article.query.get(connection.article_id) for connection in connections]

"""
functions in the exact same way as `get_articles(tag: Tag)`, but the other way around
"""
def get_tags(article: Article) -> list[Tag]:
    connections = Article_Tag.query.filter_by(article_id=article.id).all()
    return [Tag.query.get(connection.tag) for connection in connections]

def get_user_role(user: User) -> Role:
    return Role.query.get(user.role)


"""
@return: DDL returns an sqlite query -> to effectively work with the dataset, functions like `.all()` have to be called on return
"""
def get_User_Upvote(user_id, article_id) -> DDL:
    return User_Upvote.query.filter_by(user_id=user_id).filter_by(article_id=article_id)

