# Handles authentication routes for login, signup, dashboards, history, profile, and logout
import os
import uuid
from pathlib import Path
from google import genai
from google.genai import errors as genai_errors
from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename
from datetime import timezone
from Clicking_Game.models import users, database
from Clicking_Game.utils.auth import (
    FORCED_LOGOUT_MESSAGE,
    login_required,
    pop_auth_notice,
    set_auth_notice,
)
from Clicking_Game import email_service


# Magic-byte prefixes for the file types we accept as avatar uploads.
# Checking the first bytes blocks an attacker from renaming a non-image
# (e.g. evil.exe → evil.png) and still getting it accepted.
AVATAR_MAGIC_PREFIXES = (
    b"\x89PNG\r\n\x1a\n",   # PNG
    b"\xff\xd8\xff",        # JPEG
    b"GIF87a",              # GIF87a
    b"GIF89a",              # GIF89a
)


def _avatar_extension(filename):
    """Return the lowercased extension of `filename` if it is on the allow-list."""
    if not filename or "." not in filename:
        return None

    ext = filename.rsplit(".", 1)[1].lower()

    if ext not in current_app.config["ALLOWED_AVATAR_EXTENSIONS"]:
        return None

    return ext


def _looks_like_image(file_storage):
    """Read the first few bytes and confirm the file starts with an image magic header."""
    head = file_storage.stream.read(16)
    file_storage.stream.seek(0)
    return any(head.startswith(prefix) for prefix in AVATAR_MAGIC_PREFIXES)

bp = Blueprint("auth", __name__)


def establish_login_session(user):
    session.clear()
    session["user_id"] = user.id
    session["email"] = user.email
    session["name"] = user.name
    session["role"] = user.role
    session["session_token"] = users.issue_active_session_token(user.id)


# Load the logged-in user before each request
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    session_token = session.get("session_token")

    if user_id is None:
        g.user = None
        return

    user = users.get_by_id(user_id)

    if user is None:
        session.clear()
        g.user = None
        return

    if session_token is None and user.active_session_token is None:
        session["session_token"] = users.issue_active_session_token(user.id)
        g.user = user
        return

    if user.active_session_token != session_token:
        set_auth_notice(FORCED_LOGOUT_MESSAGE)
        g.user = None
        return

    g.user = user

# Helper function to determine dashboard URL based on user role
def dashboard_url_for(user):
    if user.role == "admin":
        return url_for("auth.admin_dashboard")
    return url_for("auth.player_dashboard")

def send_verification_email(user):
    verification_url = url_for(
        "auth.verify_email",
        token=user.email_verification_token,
        _external=True,
    )

    body = (
        f"Hi {user.name},\n\n"
        "Thank you for signing up for Clicking Game.\n\n"
        "Please click the link below to verify your email address:\n\n"
        f"{verification_url}\n\n"
        "If you did not create this account, you can ignore this email."
    )

    email_service.send_email(
        subject="Verify your Clicking Game account",
        recipients=[user.email],
        body=body,
    )

# Route for user login
@bp.route("/login", methods=("GET", "POST"))
def login():
    forced_logout_message = pop_auth_notice()

    if g.user is not None:
        if g.user.is_deleted or not g.user.is_active:
            session.clear()
        else:
            return redirect(dashboard_url_for(g.user))

    error = None
    success = (
        "Your account has been deleted."
        if request.args.get("account_deleted") == "1"
        else None
    )
    if error is None and success is None and forced_logout_message:
        error = forced_logout_message

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
            elif user.is_deleted:
                error = "This account has been deleted."
            elif not user.is_active:
                error = "This account has been deactivated."
            elif not user.email_verified:
                error = "Please verify your email before logging in."
            else:
                establish_login_session(user)
                return redirect(dashboard_url_for(user))

    return render_template(
        "public/login.html",
        error=error,
        success=success,
        forced_logout_message=forced_logout_message,
    )

# Route for user signup
# New users are created with the "player" role by default
@bp.route("/signup", methods=("GET", "POST"))
def signup():
    if g.user is not None:
        if g.user.is_deleted or not g.user.is_active:
            session.clear()
        else:
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
                # The account row has already been committed. If the email
                # backend fails (e.g. SMTP blocked on the host, Resend API
                # rejected the recipient), log it and tell the user to ask
                # an admin for help rather than crashing on a 500.
                try:
                    send_verification_email(user)
                except Exception:
                    from flask import current_app

                    current_app.logger.exception(
                        "Failed to send verification email to %s", user.email
                    )

                    return render_template(
                        "public/signup.html",
                        success=None,
                        error=(
                            "Account created, but we could not send the "
                            "verification email. Please contact an "
                            "administrator to verify your account, or use "
                            "the seeded demo credentials documented in the "
                            "README."
                        ),
                    )

                return render_template(
                    "public/signup.html",
                    success="Account created. Please check your email to verify your account before logging in.",
                    error=None,
                )

    return render_template("public/signup.html", error=error)

# Verify-email route
# When the user clicks the verification link in the signup email, mark the
# account as verified, start a logged-in session for them, and send them
# straight to their dashboard. This removes the awkward "verify then log in
# manually" two-step that used to come right after signup.
@bp.route("/verify-email/<token>")
def verify_email(token):
    user = users.verify_email_token(token)

    # Token did not match any user (expired, already-used, typo).
    if user is None:
        return render_template(
            "public/login.html",
            error="Invalid or expired verification link.",
            success=None,
        )

    # An admin may have disabled the account between signup and verification.
    # Refuse to auto-login but tell the user clearly what happened.
    if user.is_deleted:
        return render_template(
            "public/login.html",
            error="This account has been deleted.",
            success=None,
        )

    if not user.is_active:
        return render_template(
            "public/login.html",
            error="This account has been deactivated. Please contact an administrator.",
            success=None,
        )

    # Start a logged-in session, identical to the /login success path.
    session.clear()
    session["user_id"] = user.id
    session["email"] = user.email
    session["name"] = user.name
    session["role"] = user.role

    return redirect(dashboard_url_for(user))

# ADMIN ROUTES
# Admin dashboard shows user stats and recent game results
@bp.route("/admin_dashboard")
# Only admin can access it
@login_required(role="admin")
def admin_dashboard():
    search = request.args.get("search", "").strip()
    all_users = users.list_users(search=search)
    player_progress = users.list_player_progress(search=search)
    all_results = users.list_results(search=search)
    recent_results = users.list_results(search=search, limit=10)
    recent_player_progress = users.list_player_progress(search=search, limit=10, sort_by="updated")

    return render_template(
        "admin/admin_dashboard.html",
        name=g.user.name,
        search=search,
        total_users=len(all_users),
        player_count=len([user for user in all_users if user.role == "player"]),
        total_results=len(all_results),
        tracked_players=len([user for user in player_progress if user.points > 0]),
        highest_score=max((user.points for user in player_progress), default=0),
        recent_results=recent_results,
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

@bp.route("/admin_accounts/<int:user_id>/role", methods=("POST",))
@login_required(role="admin")
def update_account_role(user_id):
    new_role = request.form.get("role")

    if user_id == g.user.id:
        return redirect(url_for("auth.admin_accounts"))

    users.update_user_role(user_id, new_role)
    return redirect(url_for("auth.admin_accounts"))


@bp.route("/admin_accounts/<int:user_id>/status", methods=("POST",))
@login_required(role="admin")
def update_account_status(user_id):
    new_status = request.form.get("is_active")

    if user_id == g.user.id:
        return redirect(url_for("auth.admin_accounts"))

    users.set_user_active(user_id, new_status == "true")
    return redirect(url_for("auth.admin_accounts"))

# Admin results page shows saved scores across all players
@bp.route("/admin_player_results")
@login_required(role="admin")
def admin_player_results():
    search = request.args.get("search", "").strip()
    results = users.list_results(search=search)
    highest_scores = {}

    for result in results:
        if result.user_id is None:
            continue

        highest_scores[result.user_id] = max(
            highest_scores.get(result.user_id, result.score),
            result.score,
        )

    return render_template(
        "admin/admin_player_results.html",
        results=results,
        highest_scores=highest_scores,
        search=search,
    )

# PLAYER ROUTES
# Player dashboard shows links to game and history
@bp.route("/player_dashboard")
@login_required(role="player")
def player_dashboard():
    results = users.list_results(user_id=g.user.id)
    scores = [result.score for result in results]

    highest_type = "standard"

    if g.user.game_state and g.user.game_state.highest_type:
        highest_type = g.user.game_state.highest_type

    highest_type_display = highest_type.replace("-", " ").title()

    return render_template(
        "player/player_dashboard.html",
        name=g.user.name,
        highest_score=max(scores) if scores else 0,
        latest_result=g.user.game_state.points if g.user.game_state else 0,
        highest_type=highest_type_display,
    )

# Player history page shows past game scores and stats
@bp.route("/history")
@login_required(role="player")
def history():
    # list_results returns newest first; flip to chronological for the table.
    results = list(reversed(users.list_results(user_id=g.user.id)))
    game_history = []
    for result in results:
        dt = result.created_at
        # If the DB timestamp is naive, assume it's UTC and convert to local
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local_dt = dt.astimezone()
        game_history.append({
            "score": result.score,
            "date": local_dt.strftime("%Y-%m-%d"),
            "time": local_dt.strftime("%H:%M"),
        })

    scores = [result.score for result in results]

    current_score = g.user.game_state.points if g.user.game_state else 0

    # This is used for the chart so the final point matches the latest/current score.
    score_progress = game_history.copy()
    score_progress.append({
        "score": current_score,
        "date": "Current",
        "time": "Now",
        "is_current": True,
    })

    return render_template(
        "player/history.html",
        username=g.user.name,
        game_history=game_history,
        score_progress=score_progress,
        highest_score=max(scores + [current_score]) if scores else current_score,
        latest_score=current_score,
        average_score=round(sum(scores) / len(scores), 1) if scores else current_score,
    )
# AI feedback route for player performance coaching
@bp.route("/ai_feedback", methods=["POST"])
@login_required(role="player")
def ai_feedback():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return jsonify({
            "feedback": "AI feedback is unavailable because the Gemini API key is not configured."
        }), 503

    recent_results = users.list_results(user_id=g.user.id, limit=5)

    if not recent_results:
        return jsonify({
            "feedback": "Play a few rounds first, then I can give you more useful performance feedback."
        })

    scores = [result.score for result in recent_results]
    latest_score = scores[0]
    highest_score = max(scores)
    average_score = round(sum(scores) / len(scores), 1)

    prompt = (
        "You are an AI performance coach for a browser clicking game called Egg Clicker.\n\n"
        f"The player's recent scores from newest to oldest are: {scores}.\n"
        f"Latest score: {latest_score}.\n"
        f"Highest score: {highest_score}.\n"
        f"Average score: {average_score}.\n\n"
        "Give one short, encouraging, practical suggestion for improving future game performance. "
        "Keep it under 40 words. Do not mention anything outside the game."
    )

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        feedback = response.text or "AI feedback is unavailable right now."

        return jsonify({
            "feedback": feedback
        })

    except genai_errors.APIError as e:
        print("Gemini API error:", repr(e))
        return jsonify({
            "feedback": "AI feedback is unavailable because the Gemini API request failed. Please check the API key, quota, or model access."
        }), 500

    except Exception as e:
        print("Gemini feedback error:", repr(e))
        return jsonify({
            "feedback": "AI feedback is unavailable right now. Please try again later."
        }), 500

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


@bp.route("/profile/delete", methods=["POST"])
@login_required(role="player")
def delete_account():
    current_password = request.form.get("delete_password", "")

    if not current_password:
        return render_template(
            "player/profile.html",
            username=g.user.name,
            email=g.user.email,
            error="Current password is required to delete your account.",
            success=None,
        )

    if not g.user.check_password(current_password):
        return render_template(
            "player/profile.html",
            username=g.user.name,
            email=g.user.email,
            error="Current password is incorrect.",
            success=None,
        )

    users.soft_delete_user(g.user)
    session.clear()
    return redirect(url_for("auth.login", account_deleted="1"))


# AVATAR UPLOAD ROUTES
# A player can upload a profile avatar from /profile. The image is saved
# under instance/uploads/avatars/avatar_<user_id>.<ext> and the filename
# is recorded on the user row. Other pages reference /avatar/<user_id> to
# render the image (with a default-egg fallback when no avatar is set).

@bp.route("/profile/avatar", methods=["POST"])
@login_required(role="player")
def upload_avatar():
    error = None
    success = None

    uploaded_file = request.files.get("avatar")

    if uploaded_file is None or uploaded_file.filename == "":
        error = "Please choose an image file to upload."
    else:
        # Sanitise the original filename so anything weird (path separators,
        # null bytes, etc.) is stripped before we look at the extension.
        safe_name = secure_filename(uploaded_file.filename)
        ext = _avatar_extension(safe_name)

        if ext is None:
            allowed = sorted(current_app.config["ALLOWED_AVATAR_EXTENSIONS"])
            error = f"Avatar must be one of: {', '.join(allowed)}."
        elif not _looks_like_image(uploaded_file):
            error = "Uploaded file does not look like a real image."
        else:
            upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
            upload_folder.mkdir(parents=True, exist_ok=True)

            # Remove any previous avatar file for this user so we never
            # leave orphaned images on disk after an extension change.
            if g.user.avatar_filename:
                old_path = upload_folder / g.user.avatar_filename
                try:
                    old_path.unlink(missing_ok=True)
                except OSError:
                    pass

            # Use the user id (plus a short suffix to bust caches) so we
            # don't have to track historical filenames.
            new_basename = f"avatar_{g.user.id}_{uuid.uuid4().hex[:8]}.{ext}"
            target_path = upload_folder / new_basename
            uploaded_file.save(str(target_path))

            db_session = database.get_session()
            user = db_session.merge(g.user)
            user.avatar_filename = new_basename
            db_session.commit()

            g.user.avatar_filename = new_basename
            success = "Avatar updated."

    return render_template(
        "player/profile.html",
        username=g.user.name,
        email=g.user.email,
        error=error,
        success=success,
    )


@bp.route("/profile/avatar/delete", methods=["POST"])
@login_required(role="player")
def delete_avatar():
    if g.user.avatar_filename:
        upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
        old_path = upload_folder / g.user.avatar_filename
        try:
            old_path.unlink(missing_ok=True)
        except OSError:
            pass

        db_session = database.get_session()
        user = db_session.merge(g.user)
        user.avatar_filename = None
        db_session.commit()

        g.user.avatar_filename = None

    return render_template(
        "player/profile.html",
        username=g.user.name,
        email=g.user.email,
        error=None,
        success="Avatar removed.",
    )


@bp.route("/avatar/<int:user_id>")
def serve_avatar(user_id):
    """Serve a user's uploaded avatar, or fall back to the default egg image."""
    user = users.get_by_id(user_id)

    if user is None or not user.avatar_filename:
        # Fall back to the bundled default egg image so callers can always
        # use <img src="/avatar/<id>"> without checking for emptiness.
        return redirect(
            url_for("static", filename="images/defaultegg_nobackground.png")
        )

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    avatar_path = Path(upload_folder) / user.avatar_filename

    if not avatar_path.exists():
        # File got cleaned up on a Render redeploy or similar — degrade to
        # the default instead of returning 404.
        return redirect(
            url_for("static", filename="images/defaultegg_nobackground.png")
        )

    return send_from_directory(upload_folder, user.avatar_filename)

# Route for user logout
@bp.route("/logout")
def logout():
    users.clear_active_session_token(session.get("user_id"))
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
