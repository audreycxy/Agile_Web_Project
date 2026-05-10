# Handles public routes that don't require authentication
from flask import Blueprint, render_template, g

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    return render_template("public/home.html")


@bp.route("/guest")
def guest():
    return render_template("public/guest.html")


@bp.route("/game")
def game():
    # Default game state for guest users or users without saved progress fields
    initial_state = {
        "points": 0,
        "current_infinity_level": 0,
        "current_type": "standard",
        "highest_type": "standard",
        "clicks_remaining": None,
        "progress_percent": 0,
        "is_guest": True,
    }

    # If a player is logged in, keep the user as non-guest.
    # getattr() prevents errors when the User model does not have progress fields yet.
    if g.user:
        initial_state.update(
            {
                "points": getattr(g.user, "points", 0),
                "current_infinity_level": getattr(
                    g.user, "current_infinity_level", 0
                ),
                "current_type": getattr(g.user, "current_type", "standard"),
                "highest_type": getattr(g.user, "highest_type", "standard"),
                "clicks_remaining": getattr(g.user, "clicks_remaining", None),
                "progress_percent": getattr(g.user, "progress_percent", 0),
                "is_guest": False,
            }
        )

    return render_template("player/game.html", state=initial_state)