# Setup File called by wsgi.py and Clicking_Game/app.py
import os
from pathlib import Path
from flask import Flask
from .models import database
from .routes import auth, main

# Helper function to construct a SQLite URI from a file path
def _sqlite_uri(database_path):
    if database_path == ":memory:":
        return "sqlite:///:memory:"
    return f"sqlite:///{Path(database_path).resolve().as_posix()}"

# Helper function to parse boolean environment variables
def _bool_env(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# Building and configuring the Flask application
def create_app(test_config=None):
    project_root = Path(__file__).resolve().parent.parent
    instance_path = project_root / "instance"
    default_database = instance_path / "app.db"

    # Create the Flask appication
    app = Flask(
        __name__,
        instance_path=str(instance_path),
        instance_relative_config=True,
    )
    # Sets configuration values
    app.config.from_mapping(
        PROJECT_ROOT=project_root,
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        DATABASE=os.environ.get("DATABASE", str(default_database)),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL"),
        AUTO_MIGRATE=_bool_env("AUTO_MIGRATE", True),
    )
    app.config.from_prefixed_env()

    if test_config is not None:
        app.config.update(test_config)

    # Ensure the instance folder exists and create parent directories for the database if needed
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if app.config["DATABASE"] != ":memory:":
        Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.config["SQLALCHEMY_DATABASE_URI"] = _sqlite_uri(app.config["DATABASE"])

    # Initializes database connection and registers route files
    database.init_app(app)
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)

    # Automatically apply database migrations if enabled
    if app.config["AUTO_MIGRATE"]:
        with app.app_context():
            database.upgrade_db()

    return app
