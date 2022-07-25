from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from .models import Survey, Answer, User_Answer
from . import db, user_loggedin

surveys = Blueprint("surveys", __name__)


@surveys.route("/all")
def all_surveys():
    return render_template("overview/surveys.html", surveys=Survey.query.all())

@surveys.route("/<id>")
def survey(id):
    db_entry = Survey.query.get(id)

    already_voted = False
    if user_loggedin(current_user):
        if User_Answer.query.filter_by(survey_id=id).filter_by(user_id=current_user.id).first():
            already_voted = True

    
    return render_template(
        "survey.html",
        db_entry=db_entry,
        answers=Answer.query.filter_by(survey=db_entry.id).all(),
        already_voted=already_voted
    )

@surveys.route("vote/<survey_id>", methods=["POST"])
def vote(survey_id):
    answer_id = request.form.get("answer")
    if not user_loggedin(current_user):
        flash("Du musst dich anmelden, um abstimmen zu können!", category="error")
        return redirect(url_for("auth.login"))
    # if user has already voted on that specific survey
    if User_Answer.query.filter_by(survey_id=survey_id).filter_by(user_id=current_user.id).first():
        flash("Du hast bereits abgestimmt!", category="error")
    elif not current_user.email_confirmed:
        flash("Hierfür musst du erst deine Email verifizieren! Schau mal in deinem Email-Postfach nach :)", category="error")
    else:
        db.session.add(
            User_Answer(
                answer_id=answer_id,
                user_id=current_user.id,
                survey_id=survey_id
            )
        )
        Answer.query.get(int(request.form.get("answer"))).votes += 1
        db.session.commit()
        
    return redirect(url_for("surveys.survey", id=survey_id))
