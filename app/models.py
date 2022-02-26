from sqlalchemy.sql import func
from . import db
#from flask_login import UserMixin

#TODO NEEDS TESTING!!!!!!!!!
class Article(db.Model):
    id = db.Column(db.String(6), primary_key=True) #serves as id and address at the same time
    title = db.Column(db.String(128)) #both for identification and search in database and the title tag in html file
    date_created = db.Column(db.DateTime(timezone=True), default=func.now()) 
    validated = db.Column(db.Boolean(), default=False) #True if valued as "okay" by proofreader
    category = db.Column(db.String(64)) #used to group articles under broad topics
    #creator_email = db.Column(db.Integer, db.ForeignKey("user.email"))

"""
class User(db.Model):
    email = db.Column(db.String(64), unique=True)
    role = db.Column(db.String(32))
    password = password = db.Column(db.String(128))
"""

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



