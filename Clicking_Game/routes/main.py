# Handles public routes that don't require authentication 
from flask import Blueprint, render_template, g
from Clicking_Game.models import users

bp = Blueprint("main", __name__)

@bp.route("/")
def home():
    return render_template("public/home.html")

@bp.route("/guest")
def guest():
    return render_template("public/guest.html")

@bp.route("/game")
def game():
    initial_state = {
        "points": 0,
        "current_level": 1,
        "current_type": "standard",
        "clicks_remaining": None,
        "progress_percent": 0,
        "is_guest": True
    }

    # Check if auth.py set g.user
    if g.user:
        initial_state.update({
            "points": g.user.points,
            "current_level": g.user.current_level,
            "current_type": g.user.current_type,
            "clicks_remaining": g.user.clicks_remainiing,
            "progress_percent": g.user.progress_percent,
            "is_guest": False
        })
    
    return render_template("player/game.html", state=initial_state)
