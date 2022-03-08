from sqlalchemy import event, DDL
from sqlalchemy.sql import func
from . import db
from flask_login import UserMixin

#TODO NEEDS TESTING!!!!!!!!!
class Article(db.Model):
    id = db.Column(db.String(6), primary_key=True) #serves as id and address at the same time
    title = db.Column(db.String(128)) #both for identification and search in database and the title tag in html file
    date_created = db.Column(db.DateTime(timezone=True), default=func.now()) 
    validated = db.Column(db.Boolean(), default=False) #True if valued as "okay" by proofreader
    category = db.Column(db.String(64), db.ForeignKey("category.name")) #used to group articles under broad topics
    creator_email = db.Column(db.String(64), db.ForeignKey("user.email"))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(128))
    role = db.Column(db.String(32), db.ForeignKey("role.name"))


class Role(db.Model):
    name = db.Column(db.String(32), primary_key=True)
    can_upload = db.Column(db.Boolean())


class Category(db.Model):
    name = db.Column(db.String(32), primary_key=True)


class Tag(db.Model):
    tag = db.Column(db.String(32), primary_key=True)

"""
creates default entries into database when database is created
"""
event.listen(Category.__table__, "after_create", 
        DDL("INSERT INTO category (name) VALUES ('Aktuelles'), ('Wissen'), ('Schulleben'), ('Lifestyle'), ('Unterhaltung'), ('Kreatives')"))

event.listen(Role.__table__, "after_create",
        DDL("INSERT INTO role (name, can_upload) VALUES ('user', False), ('upload', True), ('validate', False), ('developer', True)"))
#-----------------------------------------------------------------------------------------------------------------------------------
"""

generates unique id following pattern:
1. generate random hexadecimal value
2. if there's already an article with that id, generate a new one

@return 6-digit unique hexadecimal id
"""
def generate_id(len) -> str:
    from random import choice

    digits = [str(i) for i in range(10)]
    digits.extend(['a', 'b', 'd', 'e', 'f'])

    generate_temp = lambda : ''.join([choice(digits) for _ in range(len)])

    temp_id = generate_temp()
    while Article.query.get(str(temp_id)):
        temp_id = generate_temp()
    
    return temp_id


