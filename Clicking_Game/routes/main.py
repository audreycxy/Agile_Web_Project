# Handles public routes that don't require authentication 
from flask import Blueprint, render_template, g, request, jsonify
from Clicking_Game.models import users, database
from Clicking_Game.game_logic import EGG_CONFIG

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

        "click_power_lvl": 1,
        "autoclicker_lvl": 0
    }
    # Check if the player has an account
    if g.user:
        initial_state.update({
            "points": g.user.points,
            "current_infinity_level": g.user.current_infinity_level,
            "current_type": g.user.current_type,
            "highest_type": g.user.highest_type,
            "clicks_remaining": g.user.clicks_remaining,
            "progress_percent": g.user.progress_percent,
            "is_guest": False
        })
    
    return render_template("player/game.html", state=initial_state)

@bp.route("/leaderboard")
def leaderboard():
    players = users.list_leaderboard(limit=10)

    return jsonify({
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "points": player.points,
            }
            for player in players
        ],
        "current_user_id": g.user.id if g.user else None,
    })