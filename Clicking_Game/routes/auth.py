from flask import Blueprint, g, redirect, render_template, request, session, url_for
from sqlalchemy import select

from Clicking_Game.models import users
from Clicking_Game.utils.auth import login_required

bp = Blueprint("auth", __name__)


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = users.get_by_id(user_id) if user_id is not None else None


def dashboard_url_for(user):
    if user.role == "admin":
        return url_for("auth.admin_dashboard")
    return url_for("auth.player_dashboard")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user is not None:
        return redirect(dashboard_url_for(g.user))

    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            error = "Please fill in all fields."
        else:
            user = users.authenticate(email, password)

            if user is None:
                error = "Invalid email or password."
            else:
                session.clear()
                session["user_id"] = user.id
                session["email"] = user.email
                session["name"] = user.name
                session["role"] = user.role

                return redirect(dashboard_url_for(user))

    return render_template("login.html", error=error)


@bp.route("/signup", methods=("GET", "POST"))
def signup():
    if g.user is not None:
        return redirect(dashboard_url_for(g.user))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password or not confirm_password:
            error = "Please fill in all fields."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif users.get_by_email(email) is not None:
            error = "Account already exists."
        else:
            user = users.create_user(username, email, password)

            if user is None:
                error = "Account already exists."
            else:
                return redirect(url_for("auth.login"))

    return render_template("signup.html", error=error)


@bp.route("/admin_dashboard")
@login_required(role="admin")
def admin_dashboard():
    return render_template("admin_dashboard.html", name=g.user.name)


@bp.route("/admin_account_management")
@login_required(role="admin")
def admin_account_management():
    user_list = users.get_session().scalars(
        select(users.User).order_by(users.User.id.asc())
    ).all()

    return render_template(
        "admin_account_management.html",
        users=user_list
    )


@bp.route("/admin_player_results")
@login_required(role="admin")
def admin_player_results():
    result_list = users.get_session().scalars(
        select(users.GameResult).order_by(users.GameResult.created_at.desc())
    ).all()

    highest_scores = {}

    for result in result_list:
        if result.user_id is not None:
            current_highest = highest_scores.get(result.user_id, 0)
            highest_scores[result.user_id] = max(current_highest, result.score)

    return render_template(
        "admin_player_results.html",
        results=result_list,
        highest_scores=highest_scores
    )


@bp.route("/player_dashboard")
@login_required(role="player")
def player_dashboard():
    return render_template("player_dashboard.html", name=g.user.name)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))