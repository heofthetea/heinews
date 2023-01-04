from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import current_user, login_required
from .models import Survey, Answer, User_Answer, Text_Answer, get_user_role
from . import db, user_loggedin

surveys = Blueprint("surveys", __name__)


@surveys.route("/all")
def all_surveys():
    return render_template("overview/surveys.html", surveys=Survey.query.all())


@surveys.route("/<id>")
def survey(id):
    db_entry = Survey.query.get(id)

    if not db_entry.validated and not get_user_role(current_user).can_validate:
        abort(403)

    user_answer = None
    answers = Answer.query.filter_by(survey=db_entry.id)
    correct_answer = answers.filter_by(correct=True).first()
    if user_loggedin(current_user):
        # first get all answers of the survey, then search if current user is in one of them
        if not db_entry.text_answer:
            user_answer = User_Answer.query.filter_by(survey_id=id).filter_by(user_id=current_user.id).first()
        else:
            user_answer = Text_Answer.query.filter_by(survey=id).filter_by(user_id=current_user.id).first()

    template = "survey/survey.html"

    if db_entry.text_answer:
        template = "survey/open_survey.html"
        # only getting all submitted answers if they're actually rendered, which is only when upload role is viewing
        if get_user_role(current_user).can_upload:
            answers = Text_Answer.query.filter_by(survey=db_entry.id).order_by(Text_Answer.date_submitted.asc())

    if db_entry.expired() or user_answer:
        template = "survey/results.html"

    return render_template(
        template,
        db_entry=db_entry,
        answers=answers.all(),
        #already_voted=already_voted
        user_answer=user_answer,
        correct_answer=correct_answer,
        survey_expired=db_entry.expired()
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
        flash("Hierfür musst Du erst Deine Email verifizieren! Schau mal in Deinem Email-Postfach nach :)", category="error")
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


@surveys.route("text-answer/<survey_id>", methods=["POST"])
def text_answer(survey_id):
    content = request.form.get("content")
    if not user_loggedin(current_user):
        flash("Du musst dich anmelden, um abstimmen zu können!", category="error")
        return redirect(url_for("auth.login"))
    if Survey.query.get(survey_id).expired():
        flash("Zu spät, die Umfrage ist abgelaufen!", category="error")
        return redirect(url_for("survey.survey", id=survey_id))
    # if user has already voted on that specific survey
    if Text_Answer.query.filter_by(survey=survey_id).filter_by(user_id=current_user.id).first():
        flash("Du hast bereits abgestimmt!", category="error")
    elif not current_user.email_confirmed:
        flash("Hierfür musst Du erst Deine Email verifizieren! Schau mal in Deinem Email-Postfach nach :)", category="error")
    else:
        db.session.add(
            Text_Answer(
                value=content,
                user_id=current_user.id,
                survey=survey_id
            )
        )
        db.session.commit()

    return redirect(url_for("surveys.survey", id=survey_id))



@surveys.route("/approve/<id>")
@login_required
def approve(id):
    if not current_user.email_confirmed:
        flash("Hierfür musst Du erst Deine Email verifizieren! Schau mal in Deinem Email-Postfach nach :)", category="error")
        abort(403)
    Survey.query.get(id).validated = True
    db.session.commit()

    flash("Die Umfrage wurde erfolgreich validiert!", category="success")
    return redirect(url_for("surveys.survey", id=id))


@surveys.route("/feedback/<id>")
@login_required
def feedback(id):
    if not current_user.email_confirmed:
        flash("Hierfür musst Du erst Deine Email verifizieren! Schau mal in Deinem Email-Postfach nach :)", category="error")
        abort(403)
    return redirect(f"mailto:{survey.creator_email}")
