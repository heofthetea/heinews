from sqlalchemy import event, DDL
from sqlalchemy.sql import func
from . import db
from flask_login import UserMixin

# is it necessary to give everything a power of 2 as a length? No. Do I do it anyway? Yes, why not.

class Article(db.Model):
    id = db.Column(db.String(6), primary_key=True)
    title = db.Column(db.String(128))
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    validated = db.Column(db.Boolean(), default=False)
    tags = db.Column(db.String(256))
    category = db.Column(db.String(64), db.ForeignKey("category.name"))
    creator_email = db.Column(db.String(64), db.ForeignKey("user.email"))


class Category(db.Model):
    name = db.Column(db.String(32), primary_key=True)


#TODO when new Tag are created and exceed length limit, flash message
class Tag(db.Model):
    tag = db.Column(db.String(32), primary_key=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(128))
    role = db.Column(db.String(32), db.ForeignKey("role.name"))


class Role(db.Model):
    name = db.Column(db.String(32), primary_key=True)
    can_upload = db.Column(db.Boolean())

"""
writes default entries into database when database is created
-> those values should never change
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
def generate_id(len: int) -> str:
    from random import choice

    digits = [str(i) for i in range(10)]
    digits.extend(['a', 'b', 'd', 'e', 'f'])

    generate_temp = lambda : ''.join([choice(digits) for _ in range(len)])

    temp_id = generate_temp()
    while Article.query.get(str(temp_id)):
        temp_id = generate_temp()
    
    return temp_id


