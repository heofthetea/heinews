from flask import Blueprint, render_template
from flask_login import current_user
from .models import Role

views = Blueprint("views", __name__)

@views.route('/')
def index() -> str:
    return render_template("index.html", roles=Role.query.all())

#TODO make this work
@views.errorhandler(404)
def page_not_found(error):
    return "<h1> this page does not exist</h1><br><a href='/'>homepage</a>"
