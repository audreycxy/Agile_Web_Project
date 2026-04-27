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
    
    search = request.args.get("search", "").strip()

    total_users = 2
    player_count = 1
    total_results = 3
    highest_score = 42

    recent_results = [
        {
            "user": {"name": "Player One", "email": "player1@example.com"},
            "score": 42,
            "created_at": "22 Apr 2026 13:30",
        },
        {
            "user": {"name": "Player Two", "email": "player2@example.com"},
            "score": 35,
            "created_at": "22 Apr 2026 13:10",
        },
        {
            "user": {"name": "Player Three", "email": "player3@example.com"},
            "score": 28,
            "created_at": "22 Apr 2026 12:50",
        },
    ]

    if search:
        recent_results = [
            result for result in recent_results
            if search.lower() in result["user"]["name"].lower()
            or search.lower() in result["user"]["email"].lower()
        ]
        
    return render_template(
        "admin_dashboard.html",
        name=session.get("name", "Admin"),
        total_users=total_users,
        player_count=player_count,
        total_results=total_results,
        highest_score=highest_score,
        search=search,
        recent_results=recent_results,
    )
    
    # all_users = users.list_users()
    # admin_count = sum(1 for user in all_users if user.role == "admin")
    # player_count = sum(1 for user in all_users if user.role == "player")
    # search = request.args.get("search", "").strip()
    # recent_results = users.list_recent_results(limit=5, search=search or None)

    # return render_template(
    #     "admin_dashboard.html",
    #     name=g.user.name,
    #     total_users=len(all_users),
    #     admin_count=admin_count,
    #     player_count=player_count,
    #     total_results=users.total_results_count(),
    #     highest_score=users.highest_score(),
    #     search=search,
    #     recent_results=recent_results,
    # )

@bp.route("/admin/accounts")
@login_required(role="admin")
def admin_accounts():
    search = request.args.get("search", "").strip()
    role = request.args.get("role", "all").strip().lower()
    selected_role = role if role in {"admin", "player"} else "all"
    role_filter = None if selected_role == "all" else selected_role

    account_list = users.list_users(search=search, role=role_filter)

    return render_template(
        "admin_accounts.html",
        name=g.user.name,
        accounts=account_list,
        search=search,
        selected_role=selected_role,
        total_accounts=len(account_list),
    )

@bp.route("/admin_account_management")
@login_required(role="admin")
def admin_account_management():
    user_list = users.get_session().scalars(
        select(users.User).order_by(users.User.id.asc())
    ).all()

    return render_template(
        "admin_account_management.html",
        users=user_list,
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
        highest_scores=highest_scores,
    )


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