from flask import Blueprint, render_template

views = Blueprint("views", __name__)

@views.route('/')
def index() -> str:
    return render_template("index.html")


class ErrorPages:
    def __404__():
        return render_template("error/404.html")

