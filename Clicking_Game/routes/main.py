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
            "is_guest": False
        })
        if not g.user.game_state:
            db_session = database.get_session()
            new_gs = users.GameState(
                user_id=g.user.id,
                clicks_remaining=EGG_CONFIG["standard"]["base_clicks"]
            )
            db_session.add(new_gs)
            db_session.commit()
            db_session.close()
    
    # Check if the player has an account and if they have a save:
    if g.user and g.user.game_state:
        gs = g.user.game_state
        if gs.clicks_remaining is not None:
            percentage = int((1 - (gs.clicks_remaining/EGG_CONFIG[gs.current_type]["base_clicks"]))*100)
        else:
            percentage = 0
        initial_state.update({
            "points": gs.points,
            "current_infinity_level": gs.current_infinity_level,
            "current_type": gs.current_type,
            "highest_type": gs.highest_type,
            "clicks_remaining": gs.clicks_remaining,
            "progress_percent": percentage,

            "click_power_lvl": gs.click_power_lvl,
            "autoclicker_lvl": gs.autoclicker_lvl
        })
    
    return render_template("player/game.html", state=initial_state, config=EGG_CONFIG)

@bp.route("/api/sync", methods=["POST"])
def sync_game():
    if not g.user:
        return jsonify({"error": "login required to save progress."})
    
    db_session = database.get_session()

    try:
        # "Merge" existing game state into session so it can be saved
        gs = db_session.merge(g.user.game_state)

        # Calculate reward
        reward = EGG_CONFIG[gs.current_type]["base_points"]
        gs.points += reward

        # Egg advancement
        egg_keys = list(EGG_CONFIG.keys())
        current_index = egg_keys.index(gs.current_type)

        if current_index + 1 < len(egg_keys):
            old_type = gs.current_type
            gs.current_type = egg_keys[current_index + 1]

            if gs.highest_type == old_type:
                gs.highest_type = gs.current_type
        else:
            print("DEBUG: Final egg reached, staying on current type", flush=True)
            gs.current_type = egg_keys[current_index]
        
        # Set required clicks for new egg
        gs.clicks_remaining = EGG_CONFIG[gs.current_type]["base_clicks"]

        new_result = users.GameResult(user_id=g.user.id, score=gs.points)
        db_session.add(new_result)

        # Save
        db_session.commit()

        return jsonify({
            "status": "success",
            "new_points": gs.points,
            "current_type": gs.current_type,
            "highest_type": gs.highest_type,
            "clicks_remaining": gs.clicks_remaining
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.close()

@bp.route("/api/navigate", methods=["POST"])
def navigate_egg():
    if not g.user:
        return jsonify({"status": "guest"})
    data = request.get_json()
    target_type = data.get("type")

    if target_type not in EGG_CONFIG:
        return jsonify({"error": "invalid egg type"}), 400
    
    db_session = database.get_session()
    try:
        gs = db_session.merge(g.user.game_state)

        egg_keys = list(EGG_CONFIG.keys())
        target_index = egg_keys.index(target_type)
        highest_index = egg_keys.index(gs.highest_type)

        if target_index > highest_index or target_index < 0:
            return jsonify({"error": "Egg is still locked"})

        gs.current_type = target_type
        gs.clicks_remaining = EGG_CONFIG[target_type]["base_clicks"]

        db_session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)})
    finally:
        db_session.close()
