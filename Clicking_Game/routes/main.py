# Handles public routes that don't require authentication 
from flask import Blueprint, render_template

bp = Blueprint("main", __name__)

@bp.route("/")
def home():
    return render_template("home.html")

@bp.route("/guest")
def guest():
    return render_template("guest.html")

@bp.route("/game")
def game():
    return render_template("game.html")