# Decorator to enforce login and role-based access control
from functools import wraps
from flask import g, redirect, session, url_for

# Check if the user is logged in, active, and has a specific role when required
def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for("auth.login"))

            if not g.user.is_active:
                session.clear()
                return redirect(url_for("auth.login"))

            if role is not None and g.user.role != role:
                return redirect(url_for("auth.login"))

            return view(**kwargs)

        return wrapped_view

    return decorator
