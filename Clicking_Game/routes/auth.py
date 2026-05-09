# Handles authentication routes for login, signup, dashboards, history, profile, and logout
from flask import Blueprint, g, redirect, render_template, request, session, url_for, jsonify
from Clicking_Game.models import users
from Clicking_Game.utils.auth import login_required

bp = Blueprint("auth", __name__)

# Load the logged-in user before each request
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = users.get_by_id(user_id) if user_id is not None else None

# Helper function to determine dashboard URL based on user role
def dashboard_url_for(user):
    if user.role == "admin":
        return url_for("auth.admin_dashboard")
    return url_for("auth.player_dashboard")

# Route for user login
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
            # The user experience is clearer and more like a complete function
            # Wrong password/email → Invalid email or password.
            # Deactivated account → This account has been deactivated.
            # Unverified email → Please verify your email before logging in.
            user = users.get_by_email(email)

            if user is None or not user.check_password(password):
                error = "Invalid email or password."
            elif not user.is_active:
                error = "This account has been deactivated."
            elif not user.email_verified:
                error = "Please verify your email before logging in."
            else:
                session.clear()
                session["user_id"] = user.id
                session["email"] = user.email
                session["name"] = user.name
                session["role"] = user.role

                return redirect(dashboard_url_for(user))

    return render_template("public/login.html", error=error)

# Route for user signup
# New users are created with the "player" role by default
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
                verification_url = url_for(
                    "auth.verify_email",
                    token=user.email_verification_token,
                    _external=True,
                )

                return render_template(
                    "public/signup.html",
                    success="Account created. Please verify your email before logging in.",
                    verification_url=verification_url,
                    error=None,
                )

    return render_template("public/signup.html", error=error)

# Verify_email(token) route
# When the user clicks the verification link, they will be redirected to the login page.
@bp.route("/verify-email/<token>")
def verify_email(token):
    if users.verify_email_token(token):
        return render_template(
            "public/login.html",
            success="Email verified successfully. You can now log in.",
            error=None,
        )

    return render_template(
        "public/login.html",
        error="Invalid or expired verification link.",
        success=None,
    )

# ADMIN ROUTES
# Admin dashboard shows user stats and recent game results
@bp.route("/admin_dashboard")
# Only admin can access it
@login_required(role="admin")
def admin_dashboard():
    search = request.args.get("search", "").strip()
    all_users = users.list_users(search=search)
    player_progress = users.list_player_progress(search=search)
    recent_player_progress = users.list_player_progress(search=search, limit=10, sort_by="updated")

    return render_template(
        "admin/admin_dashboard.html",
        name=g.user.name,
        search=search,
        total_users=len(all_users),
        player_count=len([user for user in all_users if user.role == "player"]),
        tracked_players=len([user for user in player_progress if user.points > 0]),
        highest_score=max((user.points for user in player_progress), default=0),
        recent_players=recent_player_progress,
    )

# Admin accounts page allows searching and filtering users by role
@bp.route("/admin_accounts")
@login_required(role="admin")
def admin_accounts():
    search = request.args.get("search", "").strip()
    selected_role = request.args.get("role", "all")

    accounts = users.list_users(
        search=search,
        role=selected_role if selected_role != "all" else None,
    )

    return render_template(
        "admin/admin_accounts.html",
        name=g.user.name,
        accounts=accounts,
        total_accounts=len(accounts),
        search=search,
        selected_role=selected_role,
    )

# Admin results page shows saved scores across all players
@bp.route("/admin_player_results")
@login_required(role="admin")
def admin_player_results():
    search = request.args.get("search", "").strip()
    players = users.list_player_progress(search=search)

    return render_template(
        "admin/admin_player_results.html",
        players=players,
        search=search,
    )

# PLAYER ROUTES
# Player dashboard shows links to game and history
@bp.route("/player_dashboard")
@login_required(role="player")
def player_dashboard():
    results = users.list_results(user_id=g.user.id)
    scores = [result.score for result in results]

    return render_template(
        "player/player_dashboard.html",
        name=g.user.name,
        highest_score=max(scores) if scores else 0,
        latest_result=results[0].score if results else 0,
    )

# Player history page shows past game scores and stats
@bp.route("/history")
@login_required(role="player")
def history():
    # list_results returns newest first; flip to chronological for the table.
    results = list(reversed(users.list_results(user_id=g.user.id)))
    game_history = [
        {
            "score": result.score,
            "date": result.created_at.strftime("%Y-%m-%d"),
            "time": result.created_at.strftime("%H:%M"),
        }
        for result in results
    ]

    scores = [result.score for result in results]

    return render_template(
        "player/history.html",
        username=g.user.name,
        game_history=game_history,
        highest_score=max(scores) if scores else 0,
        latest_score=scores[-1] if scores else 0,
        average_score=round(sum(scores) / len(scores), 1) if scores else 0,
    )

# Player profile page allows updating username, email, and password
@bp.route("/profile", methods=["GET", "POST"])
@login_required(role="player")
def profile():
    error = None
    success = None
    form_username = g.user.name
    form_email = g.user.email

    if request.method == "POST":
        new_username = request.form.get("username", "").strip()
        new_email = request.form.get("email", "").strip().lower()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Repopulate the form with what the user typed if validation fails.
        form_username = new_username
        form_email = new_email

        password_changing = bool(new_password)

        if not new_username or not new_email:
            error = "Username and email are required."
        elif password_changing and not current_password:
            error = "Current password is required to change your password."
        elif password_changing and not g.user.check_password(current_password):
            error = "Current password is incorrect."
        elif password_changing and new_password != confirm_password:
            error = "New passwords do not match."
        elif new_email != g.user.email and users.get_by_email(new_email) is not None:
            error = "Email already in use."
        elif users.update_profile(
            g.user,
            name=new_username,
            email=new_email,
            password=new_password or None,
        ):
            session["name"] = g.user.name
            session["email"] = g.user.email
            success = "Profile updated."
            form_username = g.user.name
            form_email = g.user.email
        else:
            error = "Email already in use."

    return render_template(
        "player/profile.html",
        username=form_username,
        email=form_email,
        error=error,
        success=success,
    )

# Route for user logout
@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))

@bp.route("/save_game_state", methods=["POST"])
@login_required(role="player")
def save_game_state():
    data = request.get_json() or {}

    users.update_user_game_state(
        user_id=g.user.id,
        points=int(data.get("points", 0)),
        current_infinity_level=int(data.get("current_infinity_level", 0)),
        current_type=data.get("current_type", "standard"),
        highest_type=data.get("highest_type", "standard"),
        clicks_remaining=data.get("clicks_remaining"),
        progress_percent=int(data.get("progress_percent", 0)),
    )

    return jsonify({"success": True})


@bp.route("/restart_game", methods=["POST"])
@login_required(role="player")
def restart_game():
    users.reset_user_game_state(g.user.id)
    return jsonify({"success": True})
