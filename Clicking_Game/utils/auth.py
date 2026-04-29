from functools import wraps

from flask import g, redirect, url_for

# Decorator to enforce login and role-based access control
def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for("auth.login"))

            if role is not None and g.user.role != role:
                return redirect(url_for("auth.login"))

            return view(**kwargs)

        return wrapped_view

    return decorator
