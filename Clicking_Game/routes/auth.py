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

# ADMIN
@bp.route("/admin_dashboard")
@login_required(role="admin")
def admin_dashboard():
    return render_template("admin_dashboard.html", name=g.user.name)


@bp.route("/player_dashboard")
@login_required(role="player")
def player_dashboard():
    return render_template("player_dashboard.html", name=g.user.name)


@bp.route("/history")
def history():
    sample_history = [
        {"score": 80, "date": "2026-04-20", "time": "14:32"},
        {"score": 95, "date": "2026-04-21", "time": "10:15"},
        {"score": 90, "date": "2026-04-22", "time": "18:40"},
        {"score": 120, "date": "2026-04-23", "time": "20:08"},
    ]

    scores = [game["score"] for game in sample_history]

    return render_template(
        "history.html",
        username="chd777",
        game_history=sample_history,
        highest_score=max(scores),
        latest_score=sample_history[-1]["score"],
        average_score=round(sum(scores) / len(scores), 1),
    )


@bp.route("/profile", methods=["GET", "POST"])
def profile():
    username = session.get("username", "chd777")
    email = session.get("email", "1417595655@qq.com")

    if request.method == "POST":
        new_username = request.form.get("username")
        new_email = request.form.get("email")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        
        if new_password or confirm_password:
            if new_password != confirm_password:
                return redirect(url_for("auth.profile"))

        session["username"] = new_username
        session["email"] = new_email

        return redirect(url_for("auth.profile"))

    return render_template(
        "profile.html",
        username=username,
        email=email,
    )


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))