from flask import Blueprint, render_template, redirect, request

views = Blueprint("views", __name__)

@views.route('/')
def index() -> str:
    return render_template("index.html")

@views.route("/search", methods=["POST"])
def search():
    search_content = request.form.get("search")
    print(search_content)
    return redirect('/')

class ErrorPages:
    def __404__():
        return render_template("error/404.html")

