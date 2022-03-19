from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required
from sqlalchemy import desc
from .models import Article

views = Blueprint("views", __name__)

@views.route('/')
def index() -> str:
    return render_template("index.html")
