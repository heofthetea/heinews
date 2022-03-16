from flask import Blueprint, render_template
from flask_login import current_user
from .models import Role, Category

views = Blueprint("views", __name__)

@views.route('/')
def index() -> str:
    return render_template("index.html", roles=Role.query.all())
