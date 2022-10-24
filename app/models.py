from sqlalchemy import event, DDL
from sqlalchemy import asc, desc
from . import db, user_loggedin
from flask_login import UserMixin
from datetime import timedelta, datetime

# is it necessary to give everything a power of 2 as a length? No. Do I do it anyway? Yes, why not.

class Article(db.Model):
    id = db.Column(db.String(6), primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.String(512))
    date_created = db.Column(db.DateTime(timezone=True), default=datetime.now())
    validated = db.Column(db.Boolean(), default=False)
    upvotes = db.Column(db.Integer, nullable=False, default=0)
    primary_image = db.Column(db.String(128))
    category = db.Column(db.String(64), db.ForeignKey("category.name"))
    creator_email = db.Column(db.String(64), db.ForeignKey("user.email"))

    def __validated_articles__(self):
        return self.query.filter_by(validated=True)
    

class Category(db.Model):
    name = db.Column(db.String(32), primary_key=True)


#TODO when new Tag are created and exceed length limit, flash message
#TODO deal with ominous ''-tag
class Tag(db.Model):
    tag = db.Column(db.String(32), primary_key=True)


class Role(db.Model):
    name = db.Column(db.String(32), primary_key=True)
    # low -> high = lower hierarchy -> higher hierarchy (check default db pupulation DDLs below for further clarification)
    hierarchy = db.Column(db.Integer, nullable=False)
    can_upload = db.Column(db.Boolean())
    can_validate = db.Column(db.Boolean())


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True)
    email_confirmed = db.Column(db.Boolean(), default=False)
    password = db.Column(db.String(128))
    notifications = db.Column(db.Boolean())
    role = db.Column(db.String(32), db.ForeignKey("role.name"), default="user")

    # no this is not necessary I'm just too lazy to learn joins
    def __order_by_role__(self, *, ascend=False, descend=False, order_by=None) -> list:
        if order_by is None:
            order_by = User.name
        role_hierarchy = []
        if ascend:
            roles = Role.query.order_by(asc(Role.hierarchy))
        elif descend:
            roles = Role.query.order_by(desc(Role.hierarchy))
        else:
            roles = Role.query.order_by(asc(Role.hierarchy))

        for role in roles:
            role_hierarchy.append(role.name)

        users_sorted = []
        for role in role_hierarchy:
            users_sorted.extend(self.query.filter_by(role=role).order_by(order_by))
        return users_sorted


class Banned_User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True)
    expiry_date = db.Column(db.DateTime(), default=datetime.now() + timedelta(weeks=1))


class Announcement(db.Model):
    id = db.Column(db.String(6), primary_key=True)
    title = db.Column(db.String(128))
    content = db.Column(db.String(2048))
    # that should be checked through the dev-panel, just so that no troll releases announcement after announcement on his own
    validated = db.Column(db.Boolean(), default=False) 
    date_created = db.Column(db.DateTime(), default=datetime.now())
    creator_email = db.Column(db.String(64), db.ForeignKey("user.email"))


#-----------------------------------------------------------------------------------------------------------------------------------

#TODO give surveys tags?
class Survey(db.Model):
    id = db.Column(db.String(6), primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.String(512))
    text_answer = db.Column(db.Boolean(), default=False)
    validated = db.Column(db.Boolean(), default=False)
    expiry_date = db.Column(db.DateTime())
    results_visible = db.Column(db.Boolean(), default=False)

    def total_votes(self):
        if self.text_answer:
            return db.session.query(Text_Answer).filter(Text_Answer.survey == self.id).count()
        else:
            return db.session.query(Answer).filter(Answer.survey == self.id).count()

    def expired(self):
        return datetime.now() > self.expiry_date


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(256))
    votes = db.Column(db.Integer, default=0)
    correct = db.Column(db.Boolean, default=None)
    survey = db.Column(db.String, db.ForeignKey("survey.id"))


class Text_Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    survey = db.Column(db.String, db.ForeignKey("survey.id"))

#-----------------------------------------------------------------------------------------------------------------------------------

class Password_Reset(db.Model):
    id = db.Column(db.String(256), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    expiry_date = db.Column(db.DateTime(), default=datetime.now() + timedelta(days=1))


class Verify_Email(db.Model):
    id = db.Column(db.String(256), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    expiry_date = db.Column(db.DateTime(), default=datetime.now() + timedelta(days=1))

            
class Delete_Account(db.Model):
    id = db.Column(db.String(256), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    expiry_date = db.Column(db.DateTime(), default=datetime.now() + timedelta(days=1))


# used to store temporary passwords, a user can promote himself to developer
# keys don't get hashed due to their comparitively low importance relative to the small risk of actually being stolen
class Promotion_Key(db.Model):
    key = db.Column(db.String(16), primary_key=True)
    expiry_date = db.Column(db.DateTime(), default=datetime.now() + timedelta(days=1))
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


class User_Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey("answer.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    # slight data redundancy but makes things a lot easier and should not lead to any inconsistancies (id should never be changed)
    survey_id = db.Column(db.String, db.ForeignKey("survey.id"))


#-----------------------------------------------------------------------------------------------------------------------------------
"""
writes default entries into database when database is created
-> those values should never change
"""
event.listen(Category.__table__, "after_create", 
        DDL("INSERT INTO category (name) VALUES ('aktuelles'), ('wissen'), ('schulleben'), ('lifestyle'), ('unterhaltung'), ('kreatives')"))

event.listen(Role.__table__, "after_create",
        DDL(
        "INSERT INTO role (name, hierarchy, can_upload, can_validate) "
        "VALUES ('user', 0, False, False), \
                ('upload', 1, True, False), \
                ('validate', 2, False, True), \
                ('vamosi', 3, False, True), \
                ('developer', 69, True, True)"
        ))


"""
generates unique id following pattern:
1. generate random hexadecimal value
2. if there's already an article with that id, generate a new one

@return 6-digit unique hexadecimal id
"""
def generate_id(len: int, table=Article) -> str:
    from random import choice

    digits = [str(i) for i in range(10)]
    digits.extend(['a', 'b', 'd', 'e', 'f'])

    generate_temp = lambda : ''.join([choice(digits) for _ in range(len)])

    temp_id = generate_temp()
    while table.query.get(str(temp_id)):
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
def get_articles(tag: Tag, limit=None) -> list[Article]:
    if limit:
        connections = Article_Tag.query.filter_by(tag=tag.tag).limit(limit).all()
    else:
        connections = Article_Tag.query.filter_by(tag=tag.tag).all()
    return [Article.query.get(connection.article_id) for connection in connections]

"""
functions in the exact same way as `get_articles(tag: Tag)`, but the other way around
"""
def get_tags(article: Article) -> list[Tag]:
    connections = Article_Tag.query.filter_by(article_id=article.id).all()
    return [Tag.query.get(connection.tag) for connection in connections]

"""
@return: The Role object corresponding to the given user or, if the user is not loggedin, a new role which has no admin rights
"""
def get_user_role(user: User) -> Role:
    return Role.query.get(user.role) if user_loggedin(user) else Role(can_validate=False, can_upload=False)

"""
@return: DDL returns an sqlite query -> to effectively work with the dataset, functions like `.all()` have to be called on return
"""
def get_User_Upvote(user_id, article_id) -> DDL:
    return User_Upvote.query.filter_by(user_id=user_id).filter_by(article_id=article_id)


def get_users_to_notify():
    return User.query.filter_by(notifications=True).all()

