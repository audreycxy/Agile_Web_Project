# Decorator to enforce login and role-based access control
from functools import wraps
from flask import g, jsonify, redirect, request, session, url_for


FORCED_LOGOUT_MESSAGE = (
    "You were logged out because this account was signed in somewhere else."
)


def set_auth_notice(message):
    session.clear()
    session["auth_notice"] = message


def pop_auth_notice():
    return session.pop("auth_notice", None)


def auth_redirect_or_json(message=None, consume_notice=False):
    is_api_request = request.path.startswith("/api/") or request.is_json

    if message is None:
        if consume_notice and is_api_request:
            message = pop_auth_notice()
        else:
            message = session.get("auth_notice")

    if is_api_request and message:
        return jsonify({
            "status": "error",
            "message": message or "Authentication required.",
            "redirect_url": url_for("auth.login"),
        }), 401

    return redirect(url_for("auth.login"))

# Check if the user is logged in, active, and has a specific role when required
def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return auth_redirect_or_json(consume_notice=True)

            if g.user.is_deleted or not g.user.is_active:
                session.clear()
                return auth_redirect_or_json()

            if role is not None and g.user.role != role:
                return auth_redirect_or_json()

            return view(**kwargs)

        return wrapped_view

    return decorator
